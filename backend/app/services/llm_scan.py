from __future__ import annotations

import asyncio
import json
import logging
import zipfile
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def extract_manifest_snippet(zip_path: Path, max_chars: int = 12000) -> str:
    texts: list[str] = []
    manifest_names = (
        "manifest.json",
        "skill.yaml",
        "skill.yml",
        "SKILL.md",
        "package.json",
        "agent.yaml",
        "config.yaml",
        "config.yml",
    )
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = set(zf.namelist())
            for mn in manifest_names:
                candidates = [n for n in names if n.endswith(mn) or n.split("/")[-1] == mn]
                for c in candidates[:2]:
                    try:
                        content = zf.read(c).decode("utf-8", errors="replace")
                        texts.append(f"--- {c} ---\n{content[:4000]}")
                    except Exception:
                        continue
            if not texts:
                for info in zf.infolist()[:15]:
                    if info.is_dir():
                        continue
                    lower = info.filename.lower()
                    if any(lower.endswith(ext) for ext in (".yaml", ".yml", ".json", ".md", ".toml")):
                        try:
                            content = zf.read(info.filename).decode("utf-8", errors="replace")
                            texts.append(f"--- {info.filename} ---\n{content[:2500]}")
                        except Exception:
                            continue
    except zipfile.BadZipFile:
        return ""
    blob = "\n\n".join(texts)
    return blob[:max_chars]


async def run_llm_semantic(zip_path: Path) -> tuple[bool, dict]:
    settings = get_settings()
    snippet = await asyncio.to_thread(lambda: extract_manifest_snippet(zip_path))
    if not snippet.strip():
        snippet = "(压缩包内未找到可读 manifest/yaml/config，以下为占位)\nempty"

    if not settings.qwen_api_key:
        return False, {"error": "missing_api_key", "message": "未配置 QWEN_API_KEY"}

    prompt = (
        "你是企业 Agent Skill 安全审查助手。请仅基于下列 Skill 包元数据片段判断是否存在明显风险："
        "权限过大、任意代码执行、数据外传、钓鱼或后门暗示等。"
        '输出严格 JSON：{"passed": true/false, "risks": [字符串], "summary": "一句话"}。\n\n'
        f"元数据片段:\n{snippet}"
    )

    url = f"{settings.qwen_api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.qwen_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.qwen_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.exception("LLM scan failed")
        return False, {"error": str(exc)}

    parsed: dict | None = None
    try:
        text = content.strip()
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"raw": content[:2000], "parse_error": True}

    if isinstance(parsed, dict) and "passed" in parsed:
        passed = bool(parsed.get("passed"))
        return passed, parsed

    lower = content.lower()
    passed = "passed\": true" in lower.replace(" ", "") or '"passed":true' in lower.replace(" ", "")
    return passed, {"raw_response": content[:2000], "heuristic_passed": passed}
