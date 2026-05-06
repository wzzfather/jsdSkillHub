from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import create_access_token
from app.models.user import User
from app.schemas.common import LoginRequest, MessageResponse, RegisterRequest, TokenResponse, UserPublic
from app.utils.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


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
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role="user",
        is_active=True,
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
    user = await db.scalar(select(User).where(User.username == body.username))
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
