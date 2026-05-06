from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_admin
from app.models.review import Review
from app.models.skill import Skill
from app.models.user import User
from app.schemas.common import (
    MessageResponse,
    ReviewActionRequest,
    ReviewPendingItem,
    ReviewSourceStatsResponse,
    ScanLayerSummary,
    SkillResponse,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _classify_pending_source(skill: Skill) -> str:
    """根据最近一次审批结论区分待审队列来源。"""
    if not skill.reviews:
        return "new_upload"
    ordered = sorted(skill.reviews, key=lambda r: r.created_at, reverse=True)
    last_decision = ordered[0].decision
    if last_decision == "rejected":
        return "resubmit"
    if last_decision == "approved":
        return "republish"
    return "new_upload"


def _build_pending_item(sk: Skill) -> ReviewPendingItem:
    scans = [
        ScanLayerSummary(
            scan_type=s.scan_type,
            passed=s.passed,
            result=s.result,
            created_at=s.created_at,
        )
        for s in sorted(sk.scan_results, key=lambda x: x.scan_type)
    ]
    source = _classify_pending_source(sk)
    author_username = sk.author.username if sk.author is not None else None
    return ReviewPendingItem(
        skill=SkillResponse.model_validate(sk),
        scans=scans,
        source=source,
        author_username=author_username,
    )


async def _load_pending_skills(db: AsyncSession) -> list[Skill]:
    stmt = (
        select(Skill)
        .where(Skill.status == "pending_review")
        .options(
            selectinload(Skill.scan_results),
            selectinload(Skill.author),
            selectinload(Skill.reviews),
        )
        .order_by(Skill.created_at.desc())
    )
    return list((await db.scalars(stmt)).all())


@router.get("/source-stats", response_model=ReviewSourceStatsResponse)
async def review_source_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ReviewSourceStatsResponse:
    skills = await _load_pending_skills(db)
    n_new = n_resubmit = n_republish = 0
    for sk in skills:
        src = _classify_pending_source(sk)
        if src == "new_upload":
            n_new += 1
        elif src == "resubmit":
            n_resubmit += 1
        elif src == "republish":
            n_republish += 1
    return ReviewSourceStatsResponse(new_upload=n_new, resubmit=n_resubmit, republish=n_republish)


@router.get("", response_model=list[ReviewPendingItem])
async def list_pending_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> list[ReviewPendingItem]:
    skills = await _load_pending_skills(db)
    return [_build_pending_item(sk) for sk in skills]


async def _get_pending_skill(db: AsyncSession, skill_id: str) -> Skill:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "未找到", "code": "NOT_FOUND"})
    if skill.status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "当前状态不可审批", "code": "INVALID_STATE"},
        )
    return skill


@router.post("/{skill_id}/approve", response_model=MessageResponse)
async def approve_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    body: Annotated[ReviewActionRequest, Body()] = ReviewActionRequest(),
) -> MessageResponse:
    skill = await _get_pending_skill(db, skill_id)
    skill.status = "published"
    db.add(
        Review(
            skill_id=skill.id,
            reviewer_id=admin.id,
            decision="approved",
            comment=body.comment,
        )
    )
    await db.commit()
    return MessageResponse(message="已通过上架")


@router.post("/{skill_id}/reject", response_model=MessageResponse)
async def reject_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    body: Annotated[ReviewActionRequest, Body()] = ReviewActionRequest(),
) -> MessageResponse:
    skill = await _get_pending_skill(db, skill_id)
    skill.status = "rejected"
    db.add(
        Review(
            skill_id=skill.id,
            reviewer_id=admin.id,
            decision="rejected",
            comment=body.comment,
        )
    )
    await db.commit()
    return MessageResponse(message="已驳回")
