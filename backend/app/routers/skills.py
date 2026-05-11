from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

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
    DeprecateRequest,
    DownloadResponse,
    InstallResponse,
    OfflineRequest,
    PaginatedAdminSkills,
    PaginatedSkills,
    ScanLayerSummary,
    SkillAdminRow,
    SkillCategoriesResponse,
    SkillDetailResponse,
    SkillResponse,
    SkillVersionItem,
)
from app.services import scan_service
from app.services.audit_service import log_action
from app.services.skill_package_service import install_skill_to_openclaw, install_skill_with_npm_to_openclaw, package_object_key
from app.utils.minio_client import generate_download_url, upload_bytes

router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)

_NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-((0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(\+([0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*))?$"
)

_STANDARD_MARKET_CATEGORIES = ("productivity", "security", "support", "knowledge")


def _norm_optional_str(v: str | None) -> str | None:
    if v is None:
        return None
    s = v.strip()
    return s if s else None


def _find_skill_json_member(zf: zipfile.ZipFile) -> str | None:
    names = [n.rstrip("/") for n in zf.namelist() if n and not n.endswith("/")]
    if not names:
        return None
    candidates = [n for n in names if n.rsplit("/", 1)[-1] == "skill.json"]
    if not candidates:
        return None
    candidates.sort(key=lambda p: (p.count("/"), len(p)))
    return candidates[0]


def _parse_skill_json_manifest(zip_path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            member = _find_skill_json_member(zf)
            if not member:
                return None
            raw_bytes = zf.read(member)
    except zipfile.BadZipFile:
        logger.warning("无效的 zip，跳过 skill.json 解析 path=%s", zip_path)
        return None
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        logger.warning("skill.json 非 UTF-8，跳过 path=%s err=%s", zip_path, e)
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("skill.json JSON 解析失败 path=%s err=%s", zip_path, e)
        return None
    if not isinstance(data, dict):
        logger.warning("skill.json 根类型不是对象，已忽略 path=%s", zip_path)
        return None
    return data


def _merge_manifest_into_fields(
    form_name: str,
    form_description: str | None,
    form_version: str,
    form_category: str | None,
    form_namespace: str | None,
    data: dict[str, Any],
) -> tuple[
    str,
    str | None,
    str,
    str | None,
    str | None,
    list[str] | None,
    str | None,
    str | None,
    dict[str, Any] | None,
]:
    name = form_name
    description = form_description
    version = form_version
    category = form_category
    namespace = form_namespace
    tags: list[str] | None = None
    homepage_url: str | None = None
    repository_url: str | None = None
    meta: dict[str, Any] = {}

    if "name" in data and data["name"] is not None:
        raw_name = str(data["name"]).strip()
        if "/" in raw_name:
            ns_part, rest = raw_name.split("/", 1)
            ns_part = ns_part.strip()
            rest = rest.strip()
            if ns_part:
                namespace = ns_part
            if rest:
                name = rest
        elif raw_name:
            name = raw_name

    if "description" in data:
        d = data.get("description")
        description = (str(d).strip() if d is not None else None) or None

    if "version" in data and data["version"] is not None:
        v = str(data["version"]).strip()
        if v:
            version = v

    if "tags" in data:
        t = data.get("tags")
        if isinstance(t, list):
            tags = [str(x) for x in t]
        elif t is not None:
            tags = [str(t)]

    if "category" in data and data["category"] is not None:
        c = str(data["category"]).strip()
        category = c if c else None

    if "homepage" in data and data["homepage"] is not None:
        h = str(data["homepage"]).strip()
        homepage_url = h if h else None

    if "repository" in data and data["repository"] is not None:
        r = str(data["repository"]).strip()
        repository_url = r if r else None

    for key in ("capabilities", "environmentVariables", "permissions", "dependencies"):
        if key in data:
            meta[key] = data[key]

    metadata_json = meta if meta else None
    return (
        name,
        description,
        version,
        category,
        namespace,
        tags,
        homepage_url,
        repository_url,
        metadata_json,
    )


def _norm_category_column():
    """lower(trim(coalesce(category, '')))"""
    trimmed = func.trim(func.coalesce(Skill.category, ""))
    return func.lower(trimmed)


def _category_filter_clause(cat_key: str):
    norm = _norm_category_column()
    if cat_key == "other":
        return or_(norm == "", ~norm.in_(_STANDARD_MARKET_CATEGORIES))
    return norm == cat_key


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
    author: Annotated[str | None, Query()] = None,
) -> PaginatedSkills:
    page_size = _clamp_page_size(page_size)
    if page < 1:
        page = 1

    effective_status = status_filter if status_filter is not None else "published"

    wheres = [Skill.status == effective_status]
    if category is not None and category.strip():
        cat_key = category.strip().lower()
        wheres.append(_category_filter_clause(cat_key))

    q = search.strip() if search and search.strip() else None
    if q:
        like = f"%{q}%"
        wheres.append(or_(Skill.name.ilike(like), Skill.description.ilike(like)))

    author_q = author.strip() if author and author.strip() else None
    if author_q:
        like_author = f"%{author_q}%"
        wheres.append(User.username.ilike(like_author))

    stmt = select(Skill)
    count_stmt = select(func.count()).select_from(Skill)
    if author_q:
        stmt = stmt.join(User, Skill.author_id == User.id)
        count_stmt = count_stmt.select_from(Skill).join(User, Skill.author_id == User.id)
    for w in wheres:
        stmt = stmt.where(w)
        count_stmt = count_stmt.where(w)

    sort_norm = sort.strip().lower() if sort else "newest"
    if sort_norm not in {"newest", "name", "popular", "install_count"}:
        sort_norm = "newest"
    if sort_norm in ("name", "popular"):
        stmt = stmt.order_by(Skill.name.asc(), Skill.created_at.desc())
    elif sort_norm == "install_count":
        # install_count 字段未就绪时按上架时间降序兜底
        stmt = stmt.order_by(Skill.created_at.desc())
    else:
        stmt = stmt.order_by(Skill.created_at.desc())

    total = int(await db.scalar(count_stmt) or 0)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.scalars(stmt)).all()
    items = [SkillResponse.model_validate(r) for r in rows]
    return PaginatedSkills(items=items, total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=SkillCategoriesResponse)
async def list_published_skill_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SkillCategoriesResponse:
    stmt = (
        select(Skill.category)
        .where(Skill.status == "published")
        .where(Skill.category.isnot(None))
        .where(func.trim(Skill.category) != "")
    )
    raw = list((await db.scalars(stmt)).all())
    seen_set: set[str] = set()
    items: list[str] = []
    for c in raw:
        t = (c or "").strip()
        if not t:
            continue
        key = t.casefold()
        if key in seen_set:
            continue
        seen_set.add(key)
        items.append(t)
    items.sort(key=str.casefold)
    return SkillCategoriesResponse(items=items)


@router.get("/admin/all", response_model=PaginatedAdminSkills)
async def list_skills_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    category: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    author: Annotated[str | None, Query()] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedAdminSkills:
    page_size = _clamp_page_size(page_size)
    if page < 1:
        page = 1

    wheres = []
    if status_filter is not None and status_filter.strip():
        wheres.append(Skill.status == status_filter.strip())

    if category is not None and category.strip():
        cat_key = category.strip().lower()
        wheres.append(_category_filter_clause(cat_key))

    q = search.strip() if search and search.strip() else None
    if q:
        like = f"%{q}%"
        wheres.append(or_(Skill.name.ilike(like), Skill.description.ilike(like)))

    author_q = author.strip() if author and author.strip() else None
    if author_q:
        like_author = f"%{author_q}%"
        wheres.append(User.username.ilike(like_author))

    stmt = select(Skill).options(selectinload(Skill.author))
    count_stmt = select(func.count()).select_from(Skill)
    if author_q:
        stmt = stmt.join(User, Skill.author_id == User.id)
        count_stmt = count_stmt.select_from(Skill).join(User, Skill.author_id == User.id)
    for w in wheres:
        stmt = stmt.where(w)
        count_stmt = count_stmt.where(w)

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
    namespace: Annotated[str | None, Form()] = None,
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

    fd, tmp_path = tempfile.mkstemp(prefix="skill_upload_", suffix=".zip")
    os.close(fd)
    Path(tmp_path).write_bytes(raw)

    manifest: dict[str, Any] | None = None
    try:
        manifest = _parse_skill_json_manifest(Path(tmp_path))
    except Exception:
        logger.warning("读取 skill.json 时发生未预期异常 path=%s", tmp_path, exc_info=True)
        manifest = None

    form_ns = _norm_optional_str(namespace)
    name_f = name.strip()
    ver_f = version.strip()
    desc_f = description
    cat_f = category

    if manifest:
        (
            name_f,
            desc_f,
            ver_f,
            cat_f,
            merged_ns,
            tags_f,
            home_f,
            repo_f,
            meta_f,
        ) = _merge_manifest_into_fields(name_f, desc_f, ver_f, cat_f, form_ns, manifest)
        form_ns = merged_ns
    else:
        tags_f = None
        home_f = None
        repo_f = None
        meta_f = None

    final_ns = _norm_optional_str(form_ns)
    if final_ns is not None and not _NAMESPACE_PATTERN.fullmatch(final_ns):
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "命名空间格式无效", "code": "INVALID_NAMESPACE"},
        )

    name_final = name_f.strip()
    if not name_final or not _NAMESPACE_PATTERN.fullmatch(name_final):
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "技能名称格式无效", "code": "INVALID_SKILL_NAME"},
        )
    name_f = name_final

    if not _SEMVER_PATTERN.fullmatch(ver_f):
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": "版本号格式不正确，请使用 SemVer 格式（如 1.0.0）",
                "code": "INVALID_VERSION",
            },
        )

    skill = Skill(
        name=name_f,
        description=desc_f,
        version=ver_f,
        author_id=current_user.id,
        status="scanning",
        category=cat_f,
        package_url=None,
        namespace=final_ns,
        tags=tags_f,
        homepage_url=home_f,
        repository_url=repo_f,
        metadata_json=meta_f,
    )
    db.add(skill)
    await db.flush()

    key = f"skills/{skill.id}/{ver_f}.zip"
    package_url = await upload_bytes(key, raw)
    skill.package_url = package_url

    db.add(
        SkillVersion(
            skill_id=skill.id,
            version=ver_f,
            package_url=package_url,
            changelog=None,
            created_by=str(current_user.id),
        )
    )
    await db.commit()
    await db.refresh(skill)

    background_tasks.add_task(_run_scan_job, str(skill.id), tmp_path)
    await log_action(
        db,
        user_id=str(current_user.id),
        action="upload",
        resource_type="skill",
        resource_id=str(skill.id),
        detail={"name": name_f, "version": ver_f},
    )
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
    await log_action(db, action="offline", resource_type="skill", resource_id=str(skill.id), detail={"comment": comment})
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
    await log_action(db, user_id=str(current_user.id), action="resubmit", resource_type="skill", resource_id=str(skill_id))
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
    await log_action(db, action="republish", resource_type="skill", resource_id=str(skill_id))
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
    await log_action(db, user_id=str(current_user.id), action="download", resource_type="skill", resource_id=str(skill_id))
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
    return InstallResponse(message="安装成功", path=path_str, npm_installed=False)


@router.post("/{skill_id}/install-npm", response_model=InstallResponse)
async def install_skill_npm_endpoint(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InstallResponse:
    _ = current_user
    skill = _require_published_package(await db.get(Skill, skill_id))
    try:
        path_str, npm_installed = await install_skill_with_npm_to_openclaw(skill)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(e), "code": "INSTALL_FAILED"},
        ) from e
    except Exception:
        logger.exception("npm 安装 Skill 失败 skill_id=%s", skill_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "安装失败", "code": "INSTALL_FAILED"},
        )
    msg = (
        "安装成功，已执行 npm install --production"
        if npm_installed
        else "安装成功（包内未检测到 package.json，未执行 npm）"
    )
    await log_action(db, user_id=str(current_user.id), action="install_npm", resource_type="skill", resource_id=str(skill_id), detail={"npm_installed": npm_installed})
    return InstallResponse(message=msg, path=path_str, npm_installed=npm_installed)


@router.get("/{skill_id}/versions", response_model=list[SkillVersionItem])
async def list_skill_versions(
    skill_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[SkillVersionItem]:
    _ = current_user
    skill = await db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "未找到", "code": "NOT_FOUND"},
        )
    stmt = (
        select(SkillVersion)
        .where(SkillVersion.skill_id == skill_id)
        .order_by(SkillVersion.created_at.desc())
    )
    rows = list((await db.scalars(stmt)).all())
    return [SkillVersionItem.model_validate(r) for r in rows]


@router.post("/{skill_id}/deprecate", response_model=ActionResponse)
async def deprecate_skill(
    skill_id: str,
    body: DeprecateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
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
            detail={"detail": "仅已上架技能可弃用", "code": "INVALID_STATE"},
        )
    skill.status = "deprecated"
    if body.message is not None and str(body.message).strip():
        skill.status_message = str(body.message).strip()
    else:
        skill.status_message = None
    skill.deprecated_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(
        db,
        user_id=str(admin.id),
        action="deprecate",
        resource_type="skill",
        resource_id=str(skill_id),
        detail={"message": skill.status_message},
    )
    return ActionResponse(message="已弃用", new_status="deprecated")


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
    detail = SkillDetailResponse.model_validate(skill)
    return detail.model_copy(update={"scans": scans})
