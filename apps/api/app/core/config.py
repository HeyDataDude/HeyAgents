"""Centralized, typed application configuration.

All configuration flows through environment variables (see `.env.example`). No secrets are ever
hardcoded. `Settings` is cached so the whole process shares one instance.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderMode = Literal["mock", "live"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    # ── General ──────────────────────────────────────────────────────────────
    env: str = Field(default="development", alias="COUNCIL_ENV")
    provider_mode: ProviderMode = Field(default="mock", alias="COUNCIL_PROVIDER_MODE")
    log_level: str = Field(default="INFO", alias="COUNCIL_LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="COUNCIL_API_HOST")
    api_port: int = Field(default=8000, alias="COUNCIL_API_PORT")
    cors_origins: str = Field(default="http://localhost:3000", alias="COUNCIL_CORS_ORIGINS")

    demo_user_email: str = Field(default="you@example.com", alias="COUNCIL_DEMO_USER_EMAIL")

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://council:council@localhost:5432/council",
        alias="COUNCIL_DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg://council:council@localhost:5432/council",
        alias="COUNCIL_DATABASE_URL_SYNC",
    )

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # ── Storage ──────────────────────────────────────────────────────────────
    storage_backend: Literal["local", "s3"] = Field(
        default="local", alias="COUNCIL_STORAGE_BACKEND"
    )
    storage_local_dir: str = Field(default="./data/storage", alias="COUNCIL_STORAGE_LOCAL_DIR")
    s3_endpoint_url: str | None = Field(default=None, alias="COUNCIL_S3_ENDPOINT_URL")
    s3_bucket: str = Field(default="council", alias="COUNCIL_S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="COUNCIL_S3_REGION")

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = Field(default="mock", alias="COUNCIL_LLM_PROVIDER")
    llm_default_model: str = Field(default="gpt-4o-mini", alias="COUNCIL_LLM_DEFAULT_MODEL")
    llm_fast_model: str = Field(default="gpt-4o-mini", alias="COUNCIL_LLM_FAST_MODEL")
    llm_deep_model: str = Field(default="gpt-4o", alias="COUNCIL_LLM_DEEP_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_provider: str = Field(default="mock", alias="COUNCIL_EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="COUNCIL_EMBEDDING_MODEL")
    embedding_dim: int = Field(default=1536, alias="COUNCIL_EMBEDDING_DIM")

    # ── STT / TTS ────────────────────────────────────────────────────────────
    stt_provider: str = Field(default="mock", alias="COUNCIL_STT_PROVIDER")
    stt_model: str = Field(default="base", alias="COUNCIL_STT_MODEL")
    stt_device: str = Field(default="cpu", alias="COUNCIL_STT_DEVICE")
    tts_provider: str = Field(default="mock", alias="COUNCIL_TTS_PROVIDER")
    tts_voice: str = Field(default="calm", alias="COUNCIL_TTS_VOICE")

    # ── Research ─────────────────────────────────────────────────────────────
    research_provider: str = Field(default="mock", alias="COUNCIL_RESEARCH_PROVIDER")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    serper_api_key: str | None = Field(default=None, alias="SERPER_API_KEY")

    # ── Agent memory (Letta) ─────────────────────────────────────────────────
    agent_memory_provider: str = Field(default="mock", alias="COUNCIL_AGENT_MEMORY_PROVIDER")
    letta_base_url: str = Field(default="http://localhost:8283", alias="LETTA_BASE_URL")
    letta_api_key: str | None = Field(default=None, alias="LETTA_API_KEY")

    # ── Realtime voice (LiveKit) ─────────────────────────────────────────────
    realtime_provider: str = Field(default="mock", alias="COUNCIL_REALTIME_PROVIDER")
    livekit_url: str | None = Field(default=None, alias="LIVEKIT_URL")
    livekit_api_key: str | None = Field(default=None, alias="LIVEKIT_API_KEY")
    livekit_api_secret: str | None = Field(default=None, alias="LIVEKIT_API_SECRET")

    # ── Reports ──────────────────────────────────────────────────────────────
    enable_morning_brief: bool = Field(default=True, alias="COUNCIL_ENABLE_MORNING_BRIEF")
    enable_daily_brief: bool = Field(default=True, alias="COUNCIL_ENABLE_DAILY_BRIEF")
    enable_weekly_synthesis: bool = Field(default=True, alias="COUNCIL_ENABLE_WEEKLY_SYNTHESIS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_mock(self) -> bool:
        return self.provider_mode == "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
