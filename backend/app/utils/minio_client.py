import asyncio

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.config import get_settings


def _client(*, endpoint_url: str | None = None) -> BaseClient:
    """创建 S3 客户端。endpoint_url 省略时使用 MINIO_ENDPOINT_URL（服务间/容器内访问）。"""
    s = get_settings()
    base = (endpoint_url if endpoint_url is not None else s.minio_endpoint_url).rstrip("/")
    return boto3.client(
        "s3",
        endpoint_url=base,
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


def http_object_url(key: str, *, external: bool = False) -> str:
    """拼接桶对象的 HTTP 路径式 URL；浏览器访问应使用 external=True（MINIO_EXTERNAL_URL）。"""
    s = get_settings()
    base = (s.minio_external_url if external else s.minio_endpoint_url).rstrip("/")
    return f"{base}/{s.minio_bucket}/{key}"


def generate_download_url(key: str, expires: int = 3600) -> str:
    """使用 boto3 / S3 API 生成临时 GET 预签名 URL（默认 3600 秒）。

    必须使用 MINIO_EXTERNAL_URL 对应的 endpoint 创建客户端并签名，否则 Host 与 SigV4
    不一致时 MinIO 会校验失败；浏览器也应使用该外部地址访问对象。
    """
    s = get_settings()
    client = _client(endpoint_url=s.minio_external_url)
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


async def get_object_bytes(key: str) -> bytes | None:
    """从 MinIO 读取对象正文。不存在时返回 None（S3/MinIO 报告 NoSuchKey 或 404）。"""
    s = get_settings()
    client = _client()

    def _read() -> bytes | None:
        try:
            resp = client.get_object(Bucket=s.minio_bucket, Key=key)
            return resp["Body"].read()
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                return None
            raise

    return await asyncio.to_thread(_read)
