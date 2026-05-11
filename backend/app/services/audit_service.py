import logging
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    user_id=None,
    action="",
    resource_type=None,
    resource_id=None,
    detail=None,
    ip_address=None,
):
    try:
        audit_log = AuditLog(
            id=str(uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(audit_log)
        await db.commit()
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
