from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UpdateProfileRequest, UserMeResponse
from app.utils.minio_client import upload_bytes
from app.utils.password import hash_password, verify_password

_MAX_AVATAR_BYTES = 2 * 1024 * 1024
_ALLOWED_EXT_KIND: dict[str, str] = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".webp": "webp",
}
_KIND_TO_MIME = {"jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
_PIL_KIND_FROM_FORMAT = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_me_response(user: User) -> UserMeResponse:
    """对外始终返回 API 代理相对路径，兼容历史数据中存过的 MinIO 绝对 URL。"""
    me = UserMeResponse.model_validate(user)
    if me.avatar_url:
        me = me.model_copy(update={"avatar_url": f"/api/avatars/{user.id}.webp"})
    return me


async def update_user_profile(
    db: AsyncSession,
    user: User,
    body: UpdateProfileRequest,
) -> User:
    if body.username is not None:
        conflict = await db.scalar(
            select(User.id).where(User.username == body.username, User.id != user.id)
        )
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "用户名已存在", "code": "USERNAME_EXISTS"},
            )
        user.username = body.username

    if body.email is not None:
        email_norm = normalize_email(str(body.email))
        conflict = await db.scalar(
            select(User.id).where(User.email == email_norm, User.id != user.id)
        )
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "邮箱已被使用", "code": "EMAIL_EXISTS"},
            )
        prev_norm = normalize_email(user.email) if user.email else None
        user.email = email_norm
        if prev_norm != email_norm:
            user.email_verified = False

    return user


def apply_password_change(user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "当前密码错误", "code": "CURRENT_PASSWORD_INVALID"},
        )
    user.hashed_password = hash_password(new_password)


def _normalize_content_type(ct: str | None) -> str | None:
    if not ct:
        return None
    return ct.split(";")[0].strip().lower()


def _magic_image_kind(raw: bytes) -> str | None:
    if len(raw) < 12:
        return None
    if raw[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


def _avatar_validate_headers(filename: str | None, content_type: str | None, raw: bytes) -> str:
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "头像文件为空", "code": "AVATAR_EMPTY"},
        )
    if len(raw) > _MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "头像不能超过 2MB", "code": "AVATAR_TOO_LARGE"},
        )

    suffix = Path(filename or "").suffix.lower()
    ext_kind = _ALLOWED_EXT_KIND.get(suffix)
    if ext_kind is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "仅支持 .jpg、.jpeg、.png、.webp", "code": "AVATAR_EXTENSION_INVALID"},
        )

    magic_kind = _magic_image_kind(raw)
    if magic_kind is None or magic_kind != ext_kind:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "图片格式无效或与扩展名不符", "code": "AVATAR_MAGIC_MISMATCH"},
        )

    ct = _normalize_content_type(content_type)
    expected_mime = _KIND_TO_MIME[magic_kind]
    if ct is not None and ct != expected_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Content-Type 与图片格式不符", "code": "AVATAR_MIME_MISMATCH"},
        )

    return magic_kind


def _process_avatar_bytes(raw: bytes, declared_kind: str) -> bytes:
    """验证 Pillow 可读图，等比缩放到最长边 256px，导出 WebP（quality 85）。"""
    try:
        with Image.open(BytesIO(raw)) as img:
            img.load()
            fmt = (img.format or "").upper()
            pil_kind = _PIL_KIND_FROM_FORMAT.get(fmt)
            if pil_kind != declared_kind:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"detail": "无法解析为有效图片", "code": "AVATAR_INVALID_IMAGE"},
                )
            img = ImageOps.exif_transpose(img)
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            buf = BytesIO()
            img.save(buf, format="WEBP", quality=85, method=6)
            return buf.getvalue()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "无法解析为有效图片", "code": "AVATAR_INVALID_IMAGE"},
        ) from None


async def apply_user_avatar_upload(
    db: AsyncSession,
    user: User,
    *,
    filename: str | None,
    content_type: str | None,
    raw: bytes,
) -> str:
    """校验头像，处理后写入 MinIO（avatars/{user_id}.webp），avatar_url 存相对路径 /api/avatars/{id}.webp。"""
    kind = _avatar_validate_headers(filename, content_type, raw)
    webp_data = _process_avatar_bytes(raw, kind)
    key = f"avatars/{user.id}.webp"
    await upload_bytes(key, webp_data, content_type="image/webp")
    rel = f"/api/avatars/{user.id}.webp"
    user.avatar_url = rel
    db.add(user)
    return rel
