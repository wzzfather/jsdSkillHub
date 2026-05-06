from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.config import get_settings


def _run_lightweight_static_scan(src_dir: Path) -> tuple[bool, dict]:
    rules: list[tuple[str, re.Pattern[str], str]] = [
        ("python.eval", re.compile(r"\beval\s*\("), "检测到 eval 调用，存在代码注入风险"),
        ("python.exec", re.compile(r"\bexec\s*\("), "检测到 exec 调用，存在动态执行风险"),
        ("python.os_system", re.compile(r"os\.system\s*\("), "检测到 os.system 调用，建议改用安全子进程接口"),
        (
            "python.subprocess_shell",
            re.compile(r"subprocess\.(run|Popen)\s*\([^)]*shell\s*=\s*True", re.DOTALL),
            "检测到 subprocess 使用 shell=True，存在命令注入风险",
        ),
    ]

    findings: list[dict] = []
    allowed_suffix = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".toml", ".md"}
    files = [p for p in src_dir.rglob("*") if p.is_file() and p.suffix.lower() in allowed_suffix]
    for file_path in files[:400]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for rule_id, pattern, message in rules:
            for m in pattern.finditer(content):
                line_no = content.count("\n", 0, m.start()) + 1
                findings.append(
                    {
                        "check_id": rule_id,
                        "path": str(file_path.relative_to(src_dir)),
                        "start": {"line": line_no},
                        "extra": {"message": message, "severity": "WARNING"},
                    }
                )
                if len(findings) >= 50:
                    break
            if len(findings) >= 50:
                break
        if len(findings) >= 50:
            break

    passed = len(findings) == 0
    summary = {
        "mode": "lightweight_fallback",
        "findings_count": len(findings),
        "errors_count": 0,
        "findings": findings,
        "errors": [],
        "message": "Semgrep 不可用，已使用内置轻量静态规则扫描作为兜底",
    }
    return passed, summary


async def run_semgrep_on_directory(src_dir: Path) -> tuple[bool, dict | list]:
    settings = get_settings()
    out_file = Path(tempfile.mkdtemp()) / "semgrep.json"
    semgrep_cmd = (
        ["semgrep", "scan"] if shutil.which("semgrep") else [sys.executable, "-m", "semgrep", "scan"]
    )

    def _run() -> None:
        subprocess.run(
            semgrep_cmd
            + [
                "--config",
                "auto",
                "--quiet",
                "--json",
                "-o",
                str(out_file),
                str(src_dir),
            ],
            check=False,
            timeout=settings.semgrep_timeout_seconds,
            capture_output=True,
            text=True,
        )

    try:
        await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        return False, {"error": "timeout", "message": "Semgrep 扫描超时"}
    except FileNotFoundError:
        return _run_lightweight_static_scan(src_dir)

    if not out_file.exists():
        return _run_lightweight_static_scan(src_dir)

    raw = out_file.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False, {"error": "invalid_json", "raw_preview": raw[:500]}

    findings = data.get("results") or []
    errors = data.get("errors") or []
    passed = len(findings) == 0 and len(errors) == 0
    summary = {
        "findings_count": len(findings),
        "errors_count": len(errors),
        "findings": findings[:50],
        "errors": errors[:20],
    }
    return passed, summary
