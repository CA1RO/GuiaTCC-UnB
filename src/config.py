"""Configurações centralizadas do GuiaOrientador-UnB."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── PostgreSQL ──
    database_url: str = "postgresql+asyncpg://guia_orientador:changeme_pg_password@localhost:5432/guia_orientador_db"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── MinIO ──
    minio_endpoint: str = "localhost:8333"
    minio_root_user: str = "minio_admin"
    minio_root_password: str = "changeme_minio_password"
    minio_bucket_bronze: str = "bronze"
    minio_bucket_silver: str = "silver"
    minio_secure: bool = False

    # ── OpenAI ──
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"

    # ── App ──
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "changeme_secret_key"

    # ── RAG ──
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64
    rag_top_k: int = 5
    embedding_dimension: int = 1536

    # ── Fonte pública CAPES ──
    capes_docentes_url: str = (
        "https://dadosabertos.capes.gov.br/dataset/"
        "0be9cfba-56e8-4da1-b3cc-0a05412eba3d/resource/"
        "4b256d1c-9448-4598-bf1d-9d8d8df633de/download/"
        "br-capes-colsucup-docente-2024-2025-12-01.csv"
    )
    capes_sigla_instituicao: str = "UNB"

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


settings = Settings()
