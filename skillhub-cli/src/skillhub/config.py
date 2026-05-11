from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None
    try:
        import toml
    except ModuleNotFoundError:
        toml = None
else:
    toml = None

CONFIG_PATH = Path.home() / ".skillhub" / "config.toml"
_DEFAULT_CONFIG: dict[str, str] = {"server": "http://localhost:8000", "token": ""}


def _normalize_config(data: dict[str, Any]) -> dict[str, str]:
    return {str(key): "" if value is None else str(value) for key, value in data.items()}


def _ensure_toml_support() -> None:
    if tomllib is None and toml is None:
        raise ValueError("当前 Python 版本缺少 TOML 支持，请安装 toml 依赖")


def _load_toml(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}

    _ensure_toml_support()

    if tomllib is not None:
        try:
            payload = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"配置文件格式无效: {CONFIG_PATH}") from exc
    else:
        assert toml is not None
        try:
            payload = toml.loads(raw)
        except toml.TomlDecodeError as exc:
            raise ValueError(f"配置文件格式无效: {CONFIG_PATH}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"配置文件格式无效: {CONFIG_PATH}")
    return payload


def _dump_toml(data: dict[str, str]) -> str:
    _ensure_toml_support()

    lines: list[str] = []
    for key, value in data.items():
        lines.append(f"{json.dumps(key, ensure_ascii=False)} = {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines) + ("\n" if lines else "")


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return _DEFAULT_CONFIG.copy()

    try:
        raw = CONFIG_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"读取配置文件失败: {CONFIG_PATH}") from exc

    payload = _load_toml(raw)
    return {**_DEFAULT_CONFIG, **_normalize_config(payload)}


def save_config(cfg: dict[str, str]) -> None:
    serialized = _normalize_config({**_DEFAULT_CONFIG, **cfg})

    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(_dump_toml(serialized), encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"写入配置文件失败: {CONFIG_PATH}") from exc
