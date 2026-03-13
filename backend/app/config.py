from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

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

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="contextpilot", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="knowledge-files", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    openai_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_api_key: str = Field(default="replace-me", alias="OPENAI_API_KEY")
    chat_model: str = Field(default="qwen-plus", alias="CHAT_MODEL")
    chat_execution_mode: str = Field(default="rag_llm", alias="CHAT_EXECUTION_MODE")
    embedding_model: str = Field(default="text-embedding-v4", alias="EMBEDDING_MODEL")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")

    default_user_id: str = Field(default="demo-user", alias="DEFAULT_USER_ID")
    default_top_k: int = Field(default=8, alias="DEFAULT_TOP_K")
    recall_top_k: int = Field(default=40, alias="RECALL_TOP_K")
    rerank_top_k: int = Field(default=16, alias="RERANK_TOP_K")
    mmr_lambda: float = Field(default=0.72, alias="MMR_LAMBDA")
    chunk_parent_size: int = Field(default=1000, alias="CHUNK_PARENT_SIZE")
    chunk_child_size: int = Field(default=220, alias="CHUNK_CHILD_SIZE")
    chunk_parent_tokens: int = Field(default=800, alias="CHUNK_PARENT_TOKENS")
    chunk_child_tokens: int = Field(default=180, alias="CHUNK_CHILD_TOKENS")
    chunk_parent_overlap_tokens: int = Field(default=120, alias="CHUNK_PARENT_OVERLAP_TOKENS")
    chunk_child_overlap_tokens: int = Field(default=40, alias="CHUNK_CHILD_OVERLAP_TOKENS")
    context_token_budget: int = Field(default=2400, alias="CONTEXT_TOKEN_BUDGET")

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        auth = quote_plus(self.postgres_user)
        if self.postgres_password:
            auth = f"{auth}:{quote_plus(self.postgres_password)}"

        return (
            f"postgresql+psycopg://{auth}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def to_flask_config(self) -> dict[str, object]:
        return {
            "APP_NAME": self.app_name,
            "APP_HOST": self.app_host,
            "APP_PORT": self.app_port,
            "DEBUG": self.app_env == "development",
            "SECRET_KEY": self.secret_key,
            "API_PREFIX": self.api_prefix,
            "SQLALCHEMY_DATABASE_URI": self.get_database_url(),
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
            "CHAT_EXECUTION_MODE": self.chat_execution_mode,
            "EMBEDDING_MODEL": self.embedding_model,
            "RERANKER_MODEL": self.reranker_model,
            "DEFAULT_USER_ID": self.default_user_id,
            "DEFAULT_TOP_K": self.default_top_k,
            "RECALL_TOP_K": self.recall_top_k,
            "RERANK_TOP_K": self.rerank_top_k,
            "MMR_LAMBDA": self.mmr_lambda,
            "CHUNK_PARENT_SIZE": self.chunk_parent_size,
            "CHUNK_CHILD_SIZE": self.chunk_child_size,
            "CHUNK_PARENT_TOKENS": self.chunk_parent_tokens,
            "CHUNK_CHILD_TOKENS": self.chunk_child_tokens,
            "CHUNK_PARENT_OVERLAP_TOKENS": self.chunk_parent_overlap_tokens,
            "CHUNK_CHILD_OVERLAP_TOKENS": self.chunk_child_overlap_tokens,
            "CONTEXT_TOKEN_BUDGET": self.context_token_budget,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
