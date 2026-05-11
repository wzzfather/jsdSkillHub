from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """登录标识：邮箱优先校验；仅用户名登录时需 username 非空（min_length=1）。"""

    username: str = Field(default="", max_length=64)
    password: str = Field(min_length=1, max_length=128)
    email: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_login_email_as_none(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def username_or_email_required(self) -> LoginRequest:
        has_email = self.email is not None and str(self.email).strip()
        u = self.username.strip() if self.username else ""
        if has_email:
            return self
        if len(u) < 1:
            raise ValueError("必须提供用户名或邮箱")
        self.username = u
        return self


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: EmailStr | None = None
    captcha_id: str = Field(min_length=1, description="图形验证码 ID")
    captcha_code: str = Field(min_length=1, description="图形验证码")

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_as_none(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("email")
    @classmethod
    def email_min_length(cls, v: EmailStr | None) -> EmailStr | None:
        if v is None:
            return None
        if len(str(v)) < 5:
            raise ValueError("邮箱长度至少 5 个字符")
        return v


class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class SendCodeResponse(BaseModel):
    """MVP：响应体携带验证码；接入 SMTP 后应移除 code 字段，仅发送邮件。"""

    message: str
    code: str


class UserPublic(BaseModel):
    id: str
    username: str
    role: str
    email: str | None = None
    email_verified: bool = False

    model_config = {"from_attributes": True}


class ScanLayerSummary(BaseModel):
    scan_type: str
    passed: bool
    result: dict | list | None = None
    created_at: datetime | None = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str | None
    version: str
    author_id: str | None
    status: str
    category: str | None
    package_url: str | None
    offline_comment: str | None = None
    namespace: str | None = None
    tags: list[str] | None = None
    homepage_url: str | None = None
    repository_url: str | None = None
    icon_url: str | None = None
    status_message: str | None = None
    deprecated_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillDetailResponse(SkillResponse):
    metadata_json: dict | list | None = None
    scans: list[ScanLayerSummary] = []


class PaginatedSkills(BaseModel):
    items: list[SkillResponse]
    total: int
    page: int
    page_size: int


class SkillCategoriesResponse(BaseModel):
    """已上架技能中出现的分类，去重排序。"""

    items: list[str]


class SkillAdminRow(SkillResponse):
    author_username: str | None = None


class PaginatedAdminSkills(BaseModel):
    items: list[SkillAdminRow]
    total: int
    page: int
    page_size: int


class ReviewPendingItem(BaseModel):
    skill: SkillResponse
    scans: list[ScanLayerSummary]
    source: str | None = None  # new_upload | resubmit | republish
    author_username: str | None = None


class ReviewSourceStatsResponse(BaseModel):
    new_upload: int
    resubmit: int
    republish: int


class ReviewActionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class MessageResponse(BaseModel):
    message: str


class OfflineRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class DeprecateRequest(BaseModel):
    message: str | None = None


class SkillVersionItem(BaseModel):
    version: str
    package_url: str | None
    changelog: str | None
    created_at: datetime
    created_by: str | None

    model_config = {"from_attributes": True}


class ActionResponse(BaseModel):
    message: str
    new_status: str


class DownloadResponse(BaseModel):
    download_url: str


class InstallResponse(BaseModel):
    message: str
    path: str
    npm_installed: bool = False


class WorkflowStep(BaseModel):
    key: str
    title: str
    description: str
    route: str


class WorkflowOverviewResponse(BaseModel):
    total: int
    scanning: int
    pending_review: int
    published: int
    rejected: int
