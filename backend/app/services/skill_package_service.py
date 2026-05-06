from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from app.config import get_settings
from app.models.skill import Skill
from app.utils.minio_client import download_object_to_file

logger = logging.getLogger(__name__)

OPENCLAW_SKILLS_ROOT = Path("/home/bazzite/.openclaw/skills")


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
