import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.models.user import User
from app.utils.minio_client import ensure_bucket
from app.utils.password import hash_password

logger = logging.getLogger(__name__)


async def run_startup_seed(session: AsyncSession) -> None:
    try:
        await ensure_bucket()
    except Exception as exc:
        logger.warning("MinIO 初始化跳过（服务不可用时上传将失败）：%s", exc)

    admin = await session.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    count_result = await session.scalar(select(func.count()).select_from(Skill))
    if count_result and count_result >= 3:
        return

    demos = [
        {
            "name": "周报助手",
            "description": "根据日历与任务自动生成周报草稿（演示）。",
            "version": "1.0.0",
            "category": "productivity",
            "package_url": "minio://app-store/demo/weekly-report.zip",
        },
        {
            "name": "SQL 审计 Skill",
            "description": "对 SELECT 语句做静态风险提示（演示）。",
            "version": "0.9.1",
            "category": "security",
            "package_url": "minio://app-store/demo/sql-audit.zip",
        },
        {
            "name": "工单摘要",
            "description": "读取工单文本生成极简摘要（演示）。",
            "version": "2.3.0",
            "category": "support",
            "package_url": "minio://app-store/demo/ticket-summary.zip",
        },
        {
            "name": "内部文档检索",
            "description": "限定知识库的语义检索 Skill（演示）。",
            "version": "1.4.2",
            "category": "knowledge",
            "package_url": "minio://app-store/demo/internal-search.zip",
        },
    ]
    admin_id = (await session.scalar(select(User.id).where(User.username == "admin")))
    for d in demos:
        exists = await session.scalar(select(Skill.id).where(Skill.name == d["name"]))
        if exists:
            continue
        skill = Skill(
            name=d["name"],
            description=d["description"],
            version=d["version"],
            author_id=admin_id,
            status="published",
            category=d["category"],
            package_url=d["package_url"],
        )
        session.add(skill)
    await session.commit()
