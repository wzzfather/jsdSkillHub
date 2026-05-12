from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.utils.minio_client import get_object_bytes

router = APIRouter(prefix="/avatars", tags=["avatars"])


@router.get("/{user_id}.webp")
async def get_user_avatar_webp(user_id: UUID) -> Response:
    """公开头像代理：从 MinIO 读取 `avatars/{user_id}.webp`，供浏览器 img src 使用（无需鉴权）。"""
    key = f"avatars/{user_id}.webp"
    data = await get_object_bytes(key)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "头像不存在", "code": "AVATAR_NOT_FOUND"},
        )
    return Response(
        content=data,
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=3600"},
    )
