from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Awaitable, TypeVar

import httpx
import typer
from rich import print as rich_print
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from skillhub.client import SkillHubClient
from skillhub.config import load_config, save_config

cli = typer.Typer(no_args_is_help=True)
console = Console()
SKILLS_DIR = Path.home() / ".openclaw" / "skills"
T = TypeVar("T")


def _abort(message: str) -> None:
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


def _http_error_message(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    try:
        payload = response.json()
    except ValueError:
        return f"请求失败: HTTP {response.status_code}"

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            text = detail.get("detail")
            if isinstance(text, str) and text.strip():
                return text
        if isinstance(detail, str) and detail.strip():
            return detail
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message

    return f"请求失败: HTTP {response.status_code}"


def _run_async(awaitable: Awaitable[T]) -> T:
    try:
        return asyncio.run(awaitable)
    except typer.Exit:
        raise
    except httpx.HTTPStatusError as exc:
        _abort(_http_error_message(exc))
    except httpx.HTTPError as exc:
        _abort(f"网络请求失败: {exc}")
    except ValueError as exc:
        _abort(str(exc))
    except Exception as exc:
        _abort(f"命令执行失败: {exc}")


def _make_client() -> SkillHubClient:
    try:
        config = load_config()
    except Exception as exc:
        _abort(f"读取配置失败: {exc}")
    return SkillHubClient(config["server"], config.get("token", ""))


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


async def _search_skills(client: SkillHubClient, keyword: str) -> list[dict[str, Any]]:
    data = await client.get(
        "/api/skills",
        params={"search": keyword, "page": 1, "page_size": 100},
    )
    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError("技能列表响应格式不正确")
    return items


def _print_skill_table(items: list[dict[str, Any]], title: str) -> None:
    table = Table(title=title)
    table.add_column("名称", style="cyan")
    table.add_column("版本", style="magenta")
    table.add_column("描述")
    table.add_column("状态", style="green")

    for item in items:
        table.add_row(
            str(item.get("name", "")),
            str(item.get("version", "")),
            str(item.get("description") or ""),
            str(item.get("status", "")),
        )

    console.print(table)


async def _resolve_skill(client: SkillHubClient, name: str) -> dict[str, Any]:
    items = await _search_skills(client, name)
    if not items:
        raise ValueError(f"未找到技能: {name}")

    exact_matches = [item for item in items if _normalize_name(str(item.get("name", ""))) == _normalize_name(name)]
    if exact_matches:
        return exact_matches[0]

    if len(items) == 1:
        return items[0]

    startswith_matches = [
        item for item in items if _normalize_name(str(item.get("name", ""))).startswith(_normalize_name(name))
    ]
    if len(startswith_matches) == 1:
        return startswith_matches[0]

    _print_skill_table(items, title="匹配到多个技能")
    raise ValueError(f"找到多个匹配技能，请使用更精确的名称: {name}")


async def _fetch_skill_detail(client: SkillHubClient, name: str) -> dict[str, Any]:
    skill = await _resolve_skill(client, name)
    return await client.get(f"/api/skills/{skill['id']}")


async def _fetch_download_url(client: SkillHubClient, skill_id: str) -> str:
    if not client.token:
        raise ValueError("请先执行 login，再安装或更新技能")
    data = await client.get(f"/api/skills/{skill_id}/download")
    download_url = data.get("download_url")
    if not isinstance(download_url, str) or not download_url.strip():
        raise ValueError("下载地址缺失")
    return download_url


async def _download_zip(download_url: str, target_path: Path) -> None:
    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as http_client:
        response = await http_client.get(download_url)
        response.raise_for_status()
        target_path.write_bytes(response.content)


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()

    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            try:
                member_path.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError("压缩包路径不安全") from exc
        archive.extractall(destination)


def _select_project_root(extract_root: Path) -> Path:
    children = [item for item in extract_root.iterdir() if item.name != "__MACOSX"]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return extract_root


def _find_package_json_dir(root: Path) -> Path | None:
    direct = root / "package.json"
    if direct.is_file():
        return root

    matches = sorted(root.rglob("package.json"))
    if not matches:
        return None
    return matches[0].parent


def _run_npm_install(package_dir: Path) -> None:
    try:
        result = subprocess.run(
            ["npm", "install", "--production"],
            cwd=package_dir,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except FileNotFoundError as exc:
        raise ValueError("未找到 npm 命令，请先安装 Node.js 并确保 npm 在 PATH 中") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("npm install --production 执行超时") from exc

    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        raise ValueError(output or "npm install --production 执行失败")


async def _install_skill(name: str, replace: bool) -> tuple[dict[str, Any], Path, bool]:
    client = _make_client()
    skill = await _resolve_skill(client, name)
    download_url = await _fetch_download_url(client, str(skill["id"]))
    skill_name = str(skill["name"])
    target_dir = SKILLS_DIR / skill_name

    if target_dir.exists():
        if not replace:
            raise ValueError(f"技能已安装: {skill_name}，如需覆盖请执行 update {skill_name}")
        shutil.rmtree(target_dir)

    temp_dir = Path(tempfile.mkdtemp(prefix="skillhub_"))
    zip_path = temp_dir / f"{skill_name}.zip"
    extract_root = temp_dir / "extract"

    try:
        await _download_zip(download_url, zip_path)
        try:
            _safe_extract_zip(zip_path, extract_root)
        except zipfile.BadZipFile as exc:
            raise ValueError("下载的安装包不是有效的 ZIP 文件") from exc

        project_root = _select_project_root(extract_root)
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(project_root, target_dir)

        package_dir = _find_package_json_dir(target_dir)
        npm_installed = False
        if package_dir is not None:
            await asyncio.to_thread(_run_npm_install, package_dir)
            npm_installed = True

        return skill, target_dir, npm_installed
    except Exception:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def _login(username: str, password: str) -> str:
    client = _make_client()
    data = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    token = data.get("access_token")
    if not isinstance(token, str) or not token.strip():
        raise ValueError("登录成功但未返回 token")
    return token


@cli.command()
def login() -> None:
    username = Prompt.ask("用户名").strip()
    password = Prompt.ask("密码", password=True)

    if not username:
        _abort("用户名不能为空")
    if not password:
        _abort("密码不能为空")

    token = _run_async(_login(username, password))
    try:
        config = load_config()
    except Exception as exc:
        _abort(f"读取配置失败: {exc}")
    config["token"] = token
    try:
        save_config(config)
    except Exception as exc:
        _abort(f"保存配置失败: {exc}")
    console.print("[green]登录成功，token 已保存[/green]")


@cli.command()
def search(keyword: str = typer.Argument(..., help="搜索关键字")) -> None:
    client = _make_client()
    items = _run_async(_search_skills(client, keyword))
    if not items:
        console.print("[yellow]未找到匹配技能[/yellow]")
        return
    _print_skill_table(items, title=f"搜索结果: {keyword}")


@cli.command()
def install(name: str = typer.Argument(..., help="技能名称")) -> None:
    skill, target_dir, npm_installed = _run_async(_install_skill(name, replace=False))
    console.print(f"[green]安装成功[/green] {skill['name']} {skill['version']}")
    console.print(f"安装目录: {target_dir}")
    if npm_installed:
        console.print("已执行 npm install --production")
    else:
        console.print("未检测到 package.json，跳过 npm install --production")


@cli.command()
def update(name: str = typer.Argument(..., help="技能名称")) -> None:
    skill, target_dir, npm_installed = _run_async(_install_skill(name, replace=True))
    console.print(f"[green]更新成功[/green] {skill['name']} {skill['version']}")
    console.print(f"安装目录: {target_dir}")
    if npm_installed:
        console.print("已执行 npm install --production")
    else:
        console.print("未检测到 package.json，跳过 npm install --production")


@cli.command()
def uninstall(name: str = typer.Argument(..., help="技能名称")) -> None:
    target_dir = SKILLS_DIR / name
    if not target_dir.exists():
        _abort(f"未安装技能: {name}")
    try:
        shutil.rmtree(target_dir)
    except OSError as exc:
        _abort(f"卸载失败: {exc}")
    console.print(f"[green]已卸载[/green] {name}")


@cli.command(name="list")
def list_skills() -> None:
    if not SKILLS_DIR.exists():
        console.print("[yellow]暂无已安装技能[/yellow]")
        return

    installed = sorted((item for item in SKILLS_DIR.iterdir() if item.is_dir()), key=lambda item: item.name.casefold())
    if not installed:
        console.print("[yellow]暂无已安装技能[/yellow]")
        return

    table = Table(title="已安装技能")
    table.add_column("名称", style="cyan")
    for item in installed:
        table.add_row(item.name)
    console.print(table)


@cli.command()
def info(name: str = typer.Argument(..., help="技能名称")) -> None:
    client = _make_client()
    skill = _run_async(_fetch_skill_detail(client, name))

    table = Table(title=f"技能详情: {skill.get('name', name)}")
    table.add_column("字段", style="cyan")
    table.add_column("值")
    table.add_row("ID", str(skill.get("id", "")))
    table.add_row("名称", str(skill.get("name", "")))
    table.add_row("版本", str(skill.get("version", "")))
    table.add_row("状态", str(skill.get("status", "")))
    table.add_row("描述", str(skill.get("description") or ""))
    table.add_row("分类", str(skill.get("category") or ""))
    table.add_row("作者", str(skill.get("author_id") or ""))
    table.add_row("创建时间", str(skill.get("created_at") or ""))
    table.add_row("包地址", str(skill.get("package_url") or ""))
    console.print(table)

    scans = skill.get("scans") or []
    if scans:
        scan_table = Table(title="扫描结果")
        scan_table.add_column("类型", style="cyan")
        scan_table.add_column("通过", style="green")
        scan_table.add_column("创建时间")
        for scan in scans:
            scan_table.add_row(
                str(scan.get("scan_type", "")),
                "yes" if scan.get("passed") else "no",
                str(scan.get("created_at") or ""),
            )
        console.print(scan_table)


@cli.command("config_set")
def config_set(
    key: str = typer.Argument(..., help="配置键"),
    value: str | None = typer.Argument(None, help="配置值；也支持传入 key=value"),
) -> None:
    if value is None:
        if "=" not in key:
            _abort("请使用 config_set <key> <value> 或 config_set <key=value>")
        key, value = key.split("=", 1)

    key = key.strip()
    value = value.strip()
    if not key:
        _abort("配置键不能为空")

    try:
        config = load_config()
    except Exception as exc:
        _abort(f"读取配置失败: {exc}")
    config[key] = value
    try:
        save_config(config)
    except Exception as exc:
        _abort(f"保存配置失败: {exc}")

    display_value = "***" if key == "token" else value
    console.print(f"[green]配置已更新[/green] {key}={display_value}")


@cli.command("config_show")
def config_show() -> None:
    try:
        rich_print(load_config())
    except Exception as exc:
        _abort(f"读取配置失败: {exc}")


def app() -> None:
    try:
        cli()
    except typer.Exit:
        raise
    except Exception as exc:
        _abort(f"命令执行失败: {exc}")
