from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal, get_db
from app.dependencies import get_current_user, get_current_user_optional, require_admin
from app.models.scan_result import ScanResult
from app.models.skill import Skill
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.schemas.common import (
    ActionResponse,
    DownloadResponse,
    InstallResponse,
    OfflineRequest,
    PaginatedAdminSkills,
    PaginatedSkills,
    ScanLayerSummary,
    SkillAdminRow,
    SkillDetailResponse,
    SkillResponse,
)
from app.services import scan_service
from app.services.skill_package_service import install_skill_to_openclaw, package_object_key
from app.utils.minio_client import generate_download_url, upload_bytes

router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)

_STANDARD_MARKET_CATEGORIES = ("productivity", "security", "support", "knowledge")


def _norm_category_column():
    """lower(trim(coalesce(category, '')))"""
    trimmed = func.trim(func.coalesce(Skill.category, ""))
    return func.lower(trimmed)


def _clamp_page_size(page_size: int) -> int:
    return max(1, min(page_size, 100))


@router.get("", response_model=PaginatedSkills)
async def list_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    category: Annotated[str | None, Query()] = None,
    sort: str = "newest",
    search: Annotated[str | None, Query()] = None,
) -> PaginatedSkills:
    page_size = _clamp_page_size(page_size)
    if page < 1:
        page = 1

    stmt = select(Skill)
    count_stmt = select(func.count()).select_from(Skill)

    effective_status = status_filter if status_filter is not None else "published"
    stmt = stmt.where(Skill.status == effective_status)
    count_stmt = count_stmt.where(Skill.status == effective_status)

    if category is not None and category.strip():
        cat_key = category.strip().lower()
        norm = _norm_category_column()
        if cat_key == "other":
            cat_filter = or_(norm == "", ~norm.in_(_STANDARD_MARKET_CATEGORIES))
        elif cat_key in _STANDARD_MARKET_CATEGORIES:
            cat_filter = norm == cat_key
        else:
            cat_filter = norm == cat_key
        stmt = stmt.where(cat_filter)
        count_stmt = count_stmt.where(cat_filter)

    q = search.strip() if search and search.strip() else None
    if q:
        like = f"%{q}%"
        search_filter = or_(Skill.name.ilike(like), Skill.description.ilike(like))
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    sort_norm = sort.strip().lower() if sort else "newest"
    if sort_norm not in {"newest", "popular"}:
        sort_norm = "newest"
    if sort_norm == "popular":
        stmt = stmt.order_by(Skill.name.asc(), Skill.created_at.desc())
    else:
        stmt = stmt.order_by(Skill.created_at.desc())

    total = int(await db.scalar(count_stmt) or 0)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    items = [SkillResponse.model_validate(r) for r in rows]
    return PaginatedSkills(items=items, total=total, page=page, page_size=page_size)


@router.get("/admin/all", response_model=PaginatedAdminSkills)
async def list_skills_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedAdminSkills:
    page_size = _clamp_page_size(page_size)
    if page < 1:
        page = 1

    stmt = select(Skill).options(selectinload(Skill.author))
    count_stmt = select(func.count()).select_from(Skill)

    if status_filter is not None and status_filter.strip():
        sf = status_filter.strip()
        stmt = stmt.where(Skill.status == sf)
        count_stmt = count_stmt.where(Skill.status == sf)

    total = int(await db.scalar(count_stmt) or 0)
    stmt = stmt.order_by(Skill.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    items: list[SkillAdminRow] = []
    for r in rows:
        base = SkillResponse.model_validate(r)
        uname = r.author.username if r.author is not None else None
        items.append(SkillAdminRow(**base.model_dump(), author_username=uname))
    return PaginatedAdminSkills(items=items, total=total, page=page, page_size=page_size)


async def _run_scan_job(skill_id: str, zip_path: str) -> None:
    path = Path(zip_path)
    async with AsyncSessionLocal() as session:
        try:
            await scan_service.execute_three_layer_scan(session, skill_id, path)
        except Exception:
            logger.exception("后台扫描失败 skill_id=%s", skill_id)
            skill = await session.get(Skill, skill_id)
            if skill:
                skill.status = "pending_review"
                session.add(
                    ScanResult(
                        skill_id=skill_id,
                        scan_type="system",
                        result={"error": "scan_job_failed"},
                        passed=False,
                    )
                )
                await session.commit()
        finally:
            path.unlink(missing_ok=True)


@router.post("/upload", response_model=SkillResponse)
async def upload_skill(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(description="Skill zip 包")],
    name: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    version: Annotated[str, Form()] = "1.0.0",
    category: Annotated[str | None, Form()] = None,
) -> Skill:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "请上传 .zip 文件", "code": "INVALID_ARCHIVE"},
        )
    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "空文件", "code": "EMPTY_FILE"},
        )

    skill = Skill(
        name=name.strip(),
        description=description,
        version=version.strip(),
        author_id=current_user.id,
        status="scanning",
        category=category,
        package_url=None,
    )
    db.add(skill)
    await db.flush()

    key = f"skills/{skill.id}/{version}.zip"
    package_url = await upload_bytes(key, raw)
    skill.package_url = package_url

    db.add(
        SkillVersion(
            skill_id=skill.id,
            version=version.strip(),
            package_url=package_url,
            changelog=None,
        )
    )
    await db.commit()
    await db.refresh(skill)

    fd, tmp_path = tempfile.mkstemp(prefix=f"skill_{skill.id}_", suffix=".zip")
    os.close(fd)
    Path(tmp_path).write_bytes(raw)

    background_tasks.add_task(_run_scan_job, str(skill.id), tmp_path)
    return skill


@router.get("/mine", response_model=PaginatedSkills)
async def list_my_skills(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedSkills:
    page_size = _clamp_page_size(page_size)
    if page < 1:
        page = 1

    stmt = select(Skill).where(Skill.author_id == current_user.id)
    count_stmt = select(func.count()).select_from(Skill).where(Skill.author_id == current_user.id)

    total = int(await db.scalar(count_stmt) or 0)
    stmt = stmt.order_by(Skill.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    items = [SkillResponse.model_validate(r) for r in rows]
    return PaginatedSkills(items=items, total=total, page=page, page_size=page_size)


@router.post("/{skill_id}/offline", response_model=ActionResponse)
async def offline_skill(
    skill_id: str,
    body: OfflineRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ActionResponse:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "未找到", "code": "NOT_FOUND"},
        )
    if skill.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "仅已上架技能可下架", "code": "INVALID_STATE"},
        )
    comment = (body.comment or "").strip()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "请填写下架原因", "code": "COMMENT_REQUIRED"},
        )
    skill.status = "offline"
    skill.offline_comment = comment
    await db.commit()
    return ActionResponse(message="已下架", new_status="offline")


@router.post("/{skill_id}/resubmit", response_model=ActionResponse)
async def resubmit_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ActionResponse:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "未找到", "code": "NOT_FOUND"},
        )
    if skill.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "仅作者可重新提交", "code": "FORBIDDEN"},
        )
    if skill.status != "rejected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "仅已驳回技能可重新提交", "code": "INVALID_STATE"},
        )
    skill.status = "pending_review"
    await db.commit()
    return ActionResponse(message="已重新提交，进入审批队列", new_status="pending_review")


@router.post("/{skill_id}/republish", response_model=ActionResponse)
async def republish_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ActionResponse:
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "未找到", "code": "NOT_FOUND"},
        )
    if skill.status != "offline":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "仅已下架技能可重新上架", "code": "INVALID_STATE"},
        )
    skill.status = "pending_review"
    skill.offline_comment = None
    await db.commit()
    return ActionResponse(message="已提交重新上架审批", new_status="pending_review")


def _require_published_package(skill: Skill | None) -> Skill:
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "未找到", "code": "NOT_FOUND"})
    if skill.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "仅已上架 Skill 可下载或安装", "code": "NOT_PUBLISHED"},
        )
    if not skill.package_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "缺少安装包", "code": "NO_PACKAGE"},
        )
    return skill


@router.get("/{skill_id}/download", response_model=DownloadResponse)
async def download_skill_package(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DownloadResponse:
    _ = current_user
    skill = _require_published_package(await db.get(Skill, skill_id))
    key = package_object_key(skill)
    url = await asyncio.to_thread(generate_download_url, key, 3600)
    return DownloadResponse(download_url=url)


@router.post("/{skill_id}/install", response_model=InstallResponse)
async def install_skill_endpoint(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InstallResponse:
    _ = current_user
    skill = _require_published_package(await db.get(Skill, skill_id))
    try:
        path_str = await install_skill_to_openclaw(skill)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(e), "code": "INSTALL_FAILED"},
        ) from e
    except Exception:
        logger.exception("安装 Skill 失败 skill_id=%s", skill_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "安装失败", "code": "INSTALL_FAILED"},
        )
    return InstallResponse(message="安装成功", path=path_str)


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> SkillDetailResponse:
    stmt = (
        select(Skill)
        .options(selectinload(Skill.scan_results))
        .where(Skill.id == skill_id)
    )
    skill = (await db.scalars(stmt)).first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "未找到", "code": "NOT_FOUND"})

    if skill.status != "published":
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"detail": "需要登录", "code": "AUTH"})
        if current_user.role != "admin" and skill.author_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"detail": "无权访问", "code": "FORBIDDEN"})

    scans = [
        ScanLayerSummary(
            scan_type=s.scan_type,
            passed=s.passed,
            result=s.result,
            created_at=s.created_at,
        )
        for s in sorted(skill.scan_results, key=lambda x: x.scan_type)
    ]
    base = SkillResponse.model_validate(skill)
    return SkillDetailResponse(**base.model_dump(), scans=scans)
