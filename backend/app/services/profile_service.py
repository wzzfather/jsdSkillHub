from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UpdateProfileRequest, UserMeResponse
from app.utils.password import hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_me_response(user: User) -> UserMeResponse:
    return UserMeResponse.model_validate(user)


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
