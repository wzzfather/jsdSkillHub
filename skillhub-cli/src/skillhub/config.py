from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".jsdhub"
CONFIG_PATH = CONFIG_DIR / "config.json"
_DEFAULT_CONFIG: dict[str, str] = {"server": "http://localhost:8000", "token": ""}


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return _DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"读取配置文件失败: {CONFIG_PATH}") from exc
    return {**_DEFAULT_CONFIG, **{str(k): str(v) for k, v in data.items()}}


def save_config(cfg: dict[str, str]) -> None:
    merged = {**_DEFAULT_CONFIG, **{str(k): str(v) for k, v in cfg.items()}}
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"写入配置文件失败: {CONFIG_PATH}") from exc
