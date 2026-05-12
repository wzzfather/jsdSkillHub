from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserMeResponse(BaseModel):
    """当前登录用户信息（不包含敏感字段）。"""

    username: str
    email: str | None = None
    email_verified: bool = False
    role: str
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvatarUploadResponse(BaseModel):
    avatar_url: str


class UpdateProfileRequest(BaseModel):
    """部分更新资料；至少提供 username 或 email 之一。"""

    username: str | None = Field(default=None, max_length=64)
    email: EmailStr | None = None

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return v

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) < 2 or len(v) > 64:
            raise ValueError("用户名长度需在 2-64 个字符之间")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_as_none(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def at_least_one_field(self) -> UpdateProfileRequest:
        if self.username is None and self.email is None:
            raise ValueError("至少需要提供 username 或 email 之一")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("新密码需包含至少一个字母")
        if not re.search(r"\d", v):
            raise ValueError("新密码需包含至少一个数字")
        return v
