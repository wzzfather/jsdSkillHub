import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import create_access_token
from app.models.user import User
from app.schemas.common import (
    LoginRequest,
    RegisterRequest,
    SendCodeRequest,
    SendCodeResponse,
    TokenResponse,
    UserPublic,
    VerifyCodeRequest,
)
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# MVP：内存验证码；key 为规范化邮箱，value 为 {code, expires_at}
_email_codes: dict[str, dict[str, Any]] = {}
_CODE_TTL = timedelta(minutes=5)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=UserPublic)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    existing = await db.scalar(select(User).where(User.username == body.username))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "用户名已存在", "code": "USERNAME_EXISTS"},
        )
    email_norm: str | None = None
    if body.email is not None:
        email_norm = _normalize_email(str(body.email))
        taken = await db.scalar(select(User.id).where(User.email == email_norm))
        if taken:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "邮箱已被注册", "code": "EMAIL_EXISTS"},
            )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role="user",
        is_active=True,
        email=email_norm,
        email_verified=email_norm is None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user: User | None = None
    if body.email is not None and str(body.email).strip():
        email_norm = _normalize_email(str(body.email))
        user = await db.scalar(select(User).where(User.email == email_norm))
    if user is None:
        uname = body.username.strip() if body.username else ""
        if uname:
            user = await db.scalar(select(User).where(User.username == uname))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "用户名或密码错误", "code": "LOGIN_FAILED"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "账号不可用", "code": "USER_DISABLED"},
        )
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(body: SendCodeRequest) -> SendCodeResponse:
    """MVP：生成 6 位验证码并写入内存；响应体直接返回验证码。后续接入 SMTP 后改为仅发邮件。"""
    email = _normalize_email(str(body.email))
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.now(tz=UTC) + _CODE_TTL
    _email_codes[email] = {"code": code, "expires_at": expires_at}
    logger.info(
        "MVP 邮箱验证码（生产环境应通过 SMTP 发送，勿在日志中明文长期使用）email=%s code=%s",
        email,
        code,
    )
    return SendCodeResponse(
        message="验证码已生成（MVP：开发联调用，生产请接邮件）",
        code=code,
    )


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    body: VerifyCodeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    email = _normalize_email(str(body.email))
    entry = _email_codes.get(email)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "请先获取验证码", "code": "CODE_NOT_FOUND"},
        )
    expires_at: datetime = entry["expires_at"]
    if datetime.now(tz=UTC) > expires_at:
        del _email_codes[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "验证码已过期", "code": "CODE_EXPIRED"},
        )
    if entry["code"] != body.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "验证码错误", "code": "CODE_MISMATCH"},
        )

    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "用户不存在", "code": "USER_NOT_FOUND"},
        )
    user.email_verified = True
    db.add(user)
    await db.commit()
    del _email_codes[email]

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
