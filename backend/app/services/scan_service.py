from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_result import ScanResult
from app.models.skill import Skill
from app.services import clamav_scan, llm_scan, semgrep_scan

logger = logging.getLogger(__name__)


async def execute_three_layer_scan(session: AsyncSession, skill_id: str, zip_path: Path) -> None:
    extract_dir = Path(tempfile.mkdtemp(prefix=f"skill_{skill_id}_"))
    try:
        try:
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_dir)
            except zipfile.BadZipFile:
                await _persist_scan(session, skill_id, "semgrep", False, {"error": "bad_zip"})
                await _persist_scan(session, skill_id, "llm", False, {"error": "bad_zip"})
                await _finalize_skill(session, skill_id)
                return

            semgrep_passed, semgrep_payload = await semgrep_scan.run_semgrep_on_directory(extract_dir)
            await _persist_scan(session, skill_id, "semgrep", semgrep_passed, semgrep_payload)

            clamav_passed, clamav_payload = await clamav_scan.run_clamav_on_zip(zip_path)
            await _persist_scan(session, skill_id, "clamav", clamav_passed, clamav_payload)

            llm_passed, llm_payload = await llm_scan.run_llm_semantic(zip_path)
            await _persist_scan(session, skill_id, "llm", llm_passed, llm_payload)

            await _finalize_skill(session, skill_id)
        except Exception as exc:
            logger.exception("扫描异常（已跳过 ClamAV） skill_id=%s", skill_id)
            await _persist_scan(session, skill_id, "system", False, {"error": "scan_exception", "detail": str(exc)})
            await _finalize_skill(session, skill_id)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


async def _persist_scan(
    session: AsyncSession,
    skill_id: str,
    scan_type: str,
    passed: bool,
    payload: dict | list,
) -> None:
    session.add(ScanResult(skill_id=skill_id, scan_type=scan_type, result=payload, passed=passed))
    await session.commit()


async def _finalize_skill(session: AsyncSession, skill_id: str) -> None:
    skill = await session.get(Skill, skill_id)
    if skill is None:
        return
    skill.status = "pending_review"
    await session.commit()
