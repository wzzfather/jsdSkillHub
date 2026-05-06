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
from app.schemas.common import MessageResponse, ReviewActionRequest, ReviewPendingItem, ScanLayerSummary, SkillResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewPendingItem])
async def list_pending_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> list[ReviewPendingItem]:
    stmt = (
        select(Skill)
        .where(Skill.status == "pending_review")
        .options(selectinload(Skill.scan_results))
        .order_by(Skill.created_at.desc())
    )
    skills = (await db.scalars(stmt)).all()
    items: list[ReviewPendingItem] = []
    for sk in skills:
        scans = [
            ScanLayerSummary(
                scan_type=s.scan_type,
                passed=s.passed,
                result=s.result,
                created_at=s.created_at,
            )
            for s in sorted(sk.scan_results, key=lambda x: x.scan_type)
        ]
        items.append(ReviewPendingItem(skill=SkillResponse.model_validate(sk), scans=scans))
    return items


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

