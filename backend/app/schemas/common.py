from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserPublic(BaseModel):
    id: str
    username: str
    role: str

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
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillDetailResponse(SkillResponse):
    scans: list[ScanLayerSummary] = []


class PaginatedSkills(BaseModel):
    items: list[SkillResponse]
    total: int
    page: int
    page_size: int


class ReviewPendingItem(BaseModel):
    skill: SkillResponse
    scans: list[ScanLayerSummary]


class ReviewActionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class MessageResponse(BaseModel):
    message: str


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
