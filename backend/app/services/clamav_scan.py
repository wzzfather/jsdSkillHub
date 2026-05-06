from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import pyclamd

from app.config import get_settings

logger = logging.getLogger(__name__)


async def run_clamav_on_zip(zip_path: Path) -> tuple[bool, dict]:
    settings = get_settings()

    def _scan() -> tuple[bool, dict]:
        try:
            cd = pyclamd.ClamdNetworkSocket(settings.clamav_host, settings.clamav_port)
            if not cd.ping():
                return False, {"error": "ping_failed", "message": "无法连接 ClamAV"}
            with zip_path.open("rb") as f:
                result = cd.scan_stream(f)
            if result is None:
                return True, {"status": "OK"}
            _stream, info = next(iter(result.values()))
            status, virus_name = info if isinstance(info, tuple) else (info, None)
            if status == "OK":
                return True, {"status": "OK"}
            return False, {"status": status, "signature": virus_name}
        except Exception as exc:
            logger.exception("ClamAV scan failed")
            return False, {"error": str(exc)}

    return await asyncio.to_thread(_scan)
