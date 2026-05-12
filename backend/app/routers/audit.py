import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


@router.get("/audit/logs")
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    user_id: str | None = Query(None),
    resource_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    """Admin-only audit log query endpoint."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        try:
            query = query.where(AuditLog.created_at >= datetime.fromisoformat(start_date))
        except ValueError:
            pass
    if end_date:
        try:
            query = query.where(AuditLog.created_at <= datetime.fromisoformat(end_date))
        except ValueError:
            pass

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
