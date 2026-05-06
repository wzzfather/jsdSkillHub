from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

security_optional = HTTPBearer(auto_error=False)
security_required = HTTPBearer(auto_error=True)

settings = get_settings()


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(tz=UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_required)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"detail": "无效或未登录", "code": "AUTH_INVALID"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials.scheme.lower() != "bearer":
        raise credentials_exc
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "需要管理员权限", "code": "FORBIDDEN"},
        )
    return user
