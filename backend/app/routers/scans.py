from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import require_admin
from app.models.skill import Skill
from app.models.user import User
from app.schemas.common import ScanLayerSummary

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("/{skill_id}", response_model=list[ScanLayerSummary])
async def get_scan_results_for_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> list[ScanLayerSummary]:
    stmt = select(Skill).options(selectinload(Skill.scan_results)).where(Skill.id == skill_id)
    skill = (await db.scalars(stmt)).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "未找到", "code": "NOT_FOUND"})
    scans = [
        ScanLayerSummary(
            scan_type=s.scan_type,
            passed=s.passed,
            result=s.result,
            created_at=s.created_at,
        )
        for s in sorted(skill.scan_results, key=lambda x: x.scan_type)
    ]
    return scans
