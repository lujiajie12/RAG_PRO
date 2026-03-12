from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="ContextPilot", alias="APP_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=5001, alias="APP_PORT")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/contextpilot",
        alias="DATABASE_URL",
    )
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="knowledge-files", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(default="replace-me", alias="OPENAI_API_KEY")
    chat_model: str = Field(default="gpt-4.1-mini", alias="CHAT_MODEL")
    embedding_model: str = Field(default="text-embedding-3-large", alias="EMBEDDING_MODEL")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")

    default_user_id: str = Field(default="demo-user", alias="DEFAULT_USER_ID")
    default_top_k: int = Field(default=8, alias="DEFAULT_TOP_K")
    chunk_parent_size: int = Field(default=1000, alias="CHUNK_PARENT_SIZE")
    chunk_child_size: int = Field(default=220, alias="CHUNK_CHILD_SIZE")
    context_token_budget: int = Field(default=2400, alias="CONTEXT_TOKEN_BUDGET")

    def to_flask_config(self) -> dict[str, object]:
        return {
            "APP_NAME": self.app_name,
            "APP_HOST": self.app_host,
            "APP_PORT": self.app_port,
            "DEBUG": self.app_env == "development",
            "SECRET_KEY": self.secret_key,
            "API_PREFIX": self.api_prefix,
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "CORS_ORIGINS": [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()],
            "MINIO_ENDPOINT": self.minio_endpoint,
            "MINIO_ACCESS_KEY": self.minio_access_key,
            "MINIO_SECRET_KEY": self.minio_secret_key,
            "MINIO_BUCKET": self.minio_bucket,
            "MINIO_SECURE": self.minio_secure,
            "OPENAI_BASE_URL": self.openai_base_url,
            "OPENAI_API_KEY": self.openai_api_key,
            "CHAT_MODEL": self.chat_model,
            "EMBEDDING_MODEL": self.embedding_model,
            "RERANKER_MODEL": self.reranker_model,
            "DEFAULT_USER_ID": self.default_user_id,
            "DEFAULT_TOP_K": self.default_top_k,
            "CHUNK_PARENT_SIZE": self.chunk_parent_size,
            "CHUNK_CHILD_SIZE": self.chunk_child_size,
            "CONTEXT_TOKEN_BUDGET": self.context_token_budget,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
