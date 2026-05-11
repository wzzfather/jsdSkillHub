from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skillhub.client import SkillHubClient

SKILLS_DIR = Path.home() / ".openclaw" / "skills"


def list_installed() -> list[str]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(directory.name for directory in SKILLS_DIR.iterdir() if directory.is_dir())


def _safe_extract(zip_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    destination_root = target_dir.resolve()

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        for member in zip_file.infolist():
            member_path = (target_dir / member.filename).resolve()
            try:
                member_path.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError("压缩包包含不安全路径") from exc

        zip_file.extractall(target_dir)


def _run_npm_install(package_dir: Path) -> None:
    try:
        result = subprocess.run(
            ["npm", "install", "--production"],
            cwd=str(package_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise ValueError("未找到 npm 命令，请先安装 Node.js 并确保 npm 在 PATH 中") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("npm install --production 执行超时") from exc

    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        raise ValueError(output or "npm install --production 执行失败")


async def install_skill(client: SkillHubClient, name: str, version: str | None = None) -> tuple[Path, bool]:
    """Download a skill from the store and install to local OpenClaw skills dir."""
    data = await client.get("/api/skills", params={"search": name, "page": 1, "page_size": 50})
    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError("技能列表响应格式不正确")
    if not items:
        raise FileNotFoundError(f"未找到 skill: {name}")

    skill: dict[str, Any] | None = None
    for item in items:
        if isinstance(item, dict) and item.get("name") == name:
            skill = item
            break
    if skill is None:
        first_item = items[0]
        if not isinstance(first_item, dict):
            raise ValueError("技能列表响应格式不正确")
        skill = first_item

    skill_id = skill.get("id")
    skill_name = skill.get("name")
    if skill_id is None:
        raise ValueError("技能信息缺少 id")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("技能信息缺少名称")

    dl_data = await client.get(f"/api/skills/{skill_id}/download")
    download_url = dl_data.get("download_url")
    if not isinstance(download_url, str) or not download_url.strip():
        raise ValueError("无法获取下载链接")

    target_dir = SKILLS_DIR / skill_name
    temp_dir = Path(tempfile.mkdtemp(prefix="skillhub_"))
    zip_path = temp_dir / f"{skill_name}.zip"

    try:
        zip_path.write_bytes(await client.download(download_url))

        if target_dir.exists():
            shutil.rmtree(target_dir)

        _safe_extract(zip_path, target_dir)

        pkg_json = target_dir / "package.json"
        npm_installed = False
        if pkg_json.exists():
            _run_npm_install(target_dir)
            npm_installed = True

        return target_dir, npm_installed
    except zipfile.BadZipFile as exc:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise ValueError("下载的安装包不是有效的 ZIP 文件") from exc
    except Exception:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def uninstall_skill(name: str) -> bool:
    """Remove a locally installed skill. Returns True if it existed."""
    target_dir = SKILLS_DIR / name
    if not target_dir.exists():
        return False
    shutil.rmtree(target_dir)
    return True
