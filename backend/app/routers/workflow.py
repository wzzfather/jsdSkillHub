from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.skill import Skill
from app.schemas.common import WorkflowOverviewResponse, WorkflowStep

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/steps", response_model=list[WorkflowStep])
async def list_workflow_steps() -> list[WorkflowStep]:
    return [
        WorkflowStep(
            key="upload",
            title="上传 Skill ZIP",
            description="开发者上传技能压缩包并填写基础元数据。",
            route="/submit",
        ),
        WorkflowStep(
            key="scan",
            title="自动双层扫描",
            description="系统自动执行 Semgrep 与 LLM 语义扫描（已跳过 ClamAV）。",
            route="/submit",
        ),
        WorkflowStep(
            key="review",
            title="审批工作台审核",
            description="管理员查看扫描结果并执行人工审核决策。",
            route="/review",
        ),
        WorkflowStep(
            key="publish",
            title="通过后上架可浏览",
            description="审批通过后状态转为 published，用户可在市场浏览。",
            route="/explore",
        ),
    ]


@router.get("/overview", response_model=WorkflowOverviewResponse)
async def workflow_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowOverviewResponse:
    total = int(await db.scalar(select(func.count()).select_from(Skill)) or 0)
    scanning = int(await db.scalar(select(func.count()).select_from(Skill).where(Skill.status == "scanning")) or 0)
    pending_review = int(
        await db.scalar(select(func.count()).select_from(Skill).where(Skill.status == "pending_review")) or 0
    )
    published = int(await db.scalar(select(func.count()).select_from(Skill).where(Skill.status == "published")) or 0)
    rejected = int(await db.scalar(select(func.count()).select_from(Skill).where(Skill.status == "rejected")) or 0)
    return WorkflowOverviewResponse(
        total=total,
        scanning=scanning,
        pending_review=pending_review,
        published=published,
        rejected=rejected,
    )
