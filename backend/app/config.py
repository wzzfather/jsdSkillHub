from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    debug: bool = False
    api_version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://appstore:appstore@localhost:5432/appstore"
    sqlalchemy_echo: bool = False

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    minio_endpoint_url: str = "http://localhost:9000"
    # 返回给浏览器/公网的预签名 URL 使用的 endpoint（容器内可用 http://minio:9000 时仍应设为宿主机可访问地址）
    minio_external_url: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "app-store"

    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_use_ssl: bool = False

    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_api_key: str = ""
    qwen_model: str = "qwen-flash"

    clamav_host: str = "localhost"
    clamav_port: int = 3310

    semgrep_timeout_seconds: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
