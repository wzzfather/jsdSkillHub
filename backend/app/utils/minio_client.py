import asyncio

import boto3
from botocore.client import BaseClient

from app.config import get_settings


def _client() -> BaseClient:
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.minio_endpoint_url,
        aws_access_key_id=s.minio_access_key,
        aws_secret_access_key=s.minio_secret_key,
        region_name="us-east-1",
    )


async def ensure_bucket() -> None:
    s = get_settings()
    client = _client()

    def _ensure() -> None:
        existing = client.list_buckets().get("Buckets", [])
        names = {b["Name"] for b in existing}
        if s.minio_bucket not in names:
            client.create_bucket(Bucket=s.minio_bucket)

    await asyncio.to_thread(_ensure)


async def upload_bytes(key: str, data: bytes, content_type: str = "application/zip") -> str:
    s = get_settings()
    client = _client()

    def _upload() -> None:
        client.put_object(Bucket=s.minio_bucket, Key=key, Body=data, ContentType=content_type)

    await asyncio.to_thread(_upload)
    base = s.minio_endpoint_url.rstrip("/")
    return f"{base}/{s.minio_bucket}/{key}"


def generate_download_url(key: str, expires: int = 3600) -> str:
    """使用 boto3 / S3 API 生成临时 GET 预签名 URL（默认 3600 秒）。"""
    s = get_settings()
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": s.minio_bucket, "Key": key},
        ExpiresIn=expires,
    )


async def download_object_to_file(key: str, dest_path: str) -> None:
    """从 MinIO 桶下载对象到本地路径（在线程中执行同步 boto3 调用）。"""
    s = get_settings()
    client = _client()

    def _download() -> None:
        client.download_file(s.minio_bucket, key, dest_path)

    await asyncio.to_thread(_download)
