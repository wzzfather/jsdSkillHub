from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

from app.config import get_settings
from app.models.skill import Skill
from app.utils.minio_client import download_object_to_file

logger = logging.getLogger(__name__)

OPENCLAW_SKILLS_ROOT = Path.home() / ".openclaw" / "skills"


def package_object_key(skill: Skill) -> str:
    """从 package_url 解析 S3 Key，否则按上传约定推断。"""
    s = get_settings()
    if skill.package_url:
        prefix = f"{s.minio_endpoint_url.rstrip('/')}/{s.minio_bucket}/"
        if skill.package_url.startswith(prefix):
            return skill.package_url[len(prefix) :]
    return f"skills/{skill.id}/{skill.version}.zip"


def skill_install_dir_name(skill_name: str) -> str:
    """名称转小写、空白与下划线为连字符，并去掉非法字符。"""
    raw = skill_name.strip().lower()
    raw = re.sub(r"[\s_]+", "-", raw)
    raw = re.sub(r"[^a-z0-9\-]", "", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw or "skill"


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = (dest / info.filename).resolve()
            try:
                target.relative_to(dest)
            except ValueError as e:
                raise ValueError("压缩包路径不安全（疑似 zip slip）") from e
        zf.extractall(dest)


async def install_skill_to_openclaw(skill: Skill) -> str:
    """
    从 MinIO 下载 zip，解压到 ~/.openclaw/skills/{skill_name}/。
    若目录已存在则先备份再覆盖。
    """
    key = package_object_key(skill)
    slug = skill_install_dir_name(skill.name)
    OPENCLAW_SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    target_dir = OPENCLAW_SKILLS_ROOT / slug

    fd, tmp_zip = tempfile.mkstemp(prefix="skill_dl_", suffix=".zip")
    os.close(fd)
    tmp_path = Path(tmp_zip)

    try:
        await download_object_to_file(key, str(tmp_path))
        if target_dir.exists():
            backup = OPENCLAW_SKILLS_ROOT / f"{slug}.bak.{int(time.time())}"
            shutil.move(str(target_dir), str(backup))
            logger.info("已备份已有目录 %s -> %s", target_dir, backup)
        _safe_extract_zip(tmp_path, target_dir)
    finally:
        tmp_path.unlink(missing_ok=True)

    return str(target_dir.resolve())


def _find_npm_project_root(extract_root: Path) -> Path:
    """定位含 package.json 的项目根；否则返回解压根目录用于整包复制。"""
    if (extract_root / "package.json").is_file():
        return extract_root
    subdirs = [p for p in extract_root.iterdir() if p.is_dir()]
    if len(subdirs) == 1 and (subdirs[0] / "package.json").is_file():
        return subdirs[0]
    return extract_root


def _run_npm_install_production(project_dir: Path) -> None:
    """在 project_dir 执行 npm install --production；失败时抛出带友好信息的 ValueError。"""
    try:
        result = subprocess.run(
            ["npm", "install", "--production"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=900,
        )
    except FileNotFoundError as e:
        raise ValueError("未找到 npm 命令，请先安装 Node.js 并确保其在 PATH 中") from e
    except subprocess.TimeoutExpired as e:
        raise ValueError("npm install 执行超时，请检查依赖体积或网络") from e
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        if len(err) > 800:
            err = err[:800] + "…"
        raise ValueError(err or "npm install 失败（无详细输出）")


async def install_skill_with_npm_to_openclaw(skill: Skill) -> tuple[str, bool]:
    """
    从 MinIO 下载 zip，解压到临时目录；若存在 package.json 则 npm install --production，
    再将项目目录（含 node_modules）复制到 ~/.openclaw/skills/{skill_name}/。
    返回 (安装路径, 是否执行了 npm)。
    """
    key = package_object_key(skill)
    slug = skill_install_dir_name(skill.name)
    OPENCLAW_SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    target_dir = OPENCLAW_SKILLS_ROOT / slug

    fd, tmp_zip = tempfile.mkstemp(prefix="skill_dl_", suffix=".zip")
    os.close(fd)
    tmp_path = Path(tmp_zip)
    extract_dir = Path(tempfile.mkdtemp(prefix="skill_npm_ext_"))

    try:
        await download_object_to_file(key, str(tmp_path))
        _safe_extract_zip(tmp_path, extract_dir)

        project_root = _find_npm_project_root(extract_dir)
        npm_installed = False
        if (project_root / "package.json").is_file():
            await asyncio.to_thread(_run_npm_install_production, project_root)
            npm_installed = True

        if target_dir.exists():
            backup = OPENCLAW_SKILLS_ROOT / f"{slug}.bak.{int(time.time())}"
            shutil.move(str(target_dir), str(backup))
            logger.info("已备份已有目录 %s -> %s", target_dir, backup)

        shutil.copytree(project_root, target_dir)
    finally:
        tmp_path.unlink(missing_ok=True)
        shutil.rmtree(extract_dir, ignore_errors=True)

    return str(target_dir.resolve()), npm_installed
