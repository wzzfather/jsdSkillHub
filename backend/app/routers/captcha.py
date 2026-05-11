from __future__ import annotations

import base64
import random
import secrets
import time
from io import BytesIO
from typing import TypedDict
from uuid import uuid4

from fastapi import APIRouter
from PIL import Image, ImageDraw, ImageFont

router = APIRouter(prefix="/captcha", tags=["captcha"])

_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_CAPTCHA_TTL_SECONDS = 5 * 60
_IMAGE_WIDTH = 120
_IMAGE_HEIGHT = 40
_INTERFERENCE_LINE_COUNT = 6


class CaptchaEntry(TypedDict):
    code: str
    expires: float


_captcha_store: dict[str, CaptchaEntry] = {}
_font = ImageFont.load_default()


def _cleanup_expired_captchas() -> None:
    now = time.time()
    expired_ids = [captcha_id for captcha_id, entry in _captcha_store.items() if entry["expires"] <= now]
    for captcha_id in expired_ids:
        del _captcha_store[captcha_id]


def _generate_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(4))


def _random_color(min_value: int = 0, max_value: int = 180) -> tuple[int, int, int]:
    return (
        random.randint(min_value, max_value),
        random.randint(min_value, max_value),
        random.randint(min_value, max_value),
    )


def _render_captcha_image(code: str) -> str:
    image = Image.new("RGB", (_IMAGE_WIDTH, _IMAGE_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for _ in range(_INTERFERENCE_LINE_COUNT):
        draw.line(
            (
                random.randint(0, _IMAGE_WIDTH - 1),
                random.randint(0, _IMAGE_HEIGHT - 1),
                random.randint(0, _IMAGE_WIDTH - 1),
                random.randint(0, _IMAGE_HEIGHT - 1),
            ),
            fill=_random_color(120, 220),
            width=1,
        )

    for index, char in enumerate(code):
        draw.text(
            (14 + index * 24 + random.randint(-2, 2), 10 + random.randint(-4, 4)),
            char,
            font=_font,
            fill=_random_color(20, 160),
        )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@router.get("/image")
async def get_captcha_image() -> dict[str, str]:
    _cleanup_expired_captchas()

    captcha_id = str(uuid4())
    code = _generate_code()
    _captcha_store[captcha_id] = {
        "code": code,
        "expires": time.time() + _CAPTCHA_TTL_SECONDS,
    }

    return {
        "captcha_id": captcha_id,
        "image": _render_captcha_image(code),
    }


def verify_captcha(captcha_id: str, code: str) -> bool:
    _cleanup_expired_captchas()

    entry = _captcha_store.get(captcha_id)
    if entry is None:
        return False
    if entry["expires"] <= time.time():
        del _captcha_store[captcha_id]
        return False
    if entry["code"] != code.strip().upper():
        return False

    del _captcha_store[captcha_id]
    return True


__all__ = ["router", "verify_captcha"]
