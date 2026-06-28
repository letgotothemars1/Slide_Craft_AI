from __future__ import annotations

import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    BASE_URL: str = "http://localhost:8000"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/slidecraft"

    # Local folder for final files in local mode and static file serving.
    STORAGE_PATH: Path = Path("storage")
    # Temporary folder for files before upload.
    STORAGE_TEMP_PATH: Path = Path("storage_tmp")

    # Supabase Storage configuration (optional for local development).
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str | None = None

    # OpenAI LLM configuration.
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-5.4-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # Worker LLM: per-slide HTML rendering agent.
    # Set WORKER_LLM_ENABLED=true to activate; uses OPENAI_WORKER_MODEL if set, else OPENAI_MODEL.
    WORKER_LLM_ENABLED: bool = False
    OPENAI_WORKER_MODEL: str | None = None
    # Critic LLM: quality-review agent that fixes spec before rendering.
    # Set CRITIC_LLM_ENABLED=true to activate; uses OPENAI_CRITIC_MODEL if set, else OPENAI_MODEL.
    CRITIC_LLM_ENABLED: bool = False
    OPENAI_CRITIC_MODEL: str | None = None
    # OpenAI image generation configuration (optional; reserved for future use).
    OPENAI_IMAGE_MODEL: str | None = None
    OPENAI_IMAGE_SIZE: str | None = None
    OPENAI_IMAGE_QUALITY: str | None = None
    OPENAI_IMAGE_BACKGROUND: str | None = None

    # ── LLM provider for text generation (presentation spec / worker / critic) ──
    # "anthropic" → Claude (ANTHROPIC_MODEL); "openai" → OPENAI_MODEL.
    # NOTE: embeddings (RAG) and image generation have no Anthropic equivalent
    # and always use OpenAI regardless of this setting — keep OPENAI_API_KEY set
    # if you use document upload (RAG) or image generation.
    LLM_PROVIDER: str = "anthropic"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-opus-4-8"

    CORS_ORIGINS: list[str] = DEFAULT_CORS_ORIGINS.copy()
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    # Session config
    SESSION_TTL_HOURS: int = 3

    # Public URLs (used for ngrok / production deployments)
    FRONTEND_ORIGIN: str | None = None
    BACKEND_PUBLIC_URL: str | None = None

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str | None = None

    # Salt for hashing client IPs in analytics_events (we never store raw IPs).
    # Set to a random string in production via env. If empty, a process-local fallback is used.
    ANALYTICS_IP_SALT: str = ""

    # ── JWT authentication ───────────────────────────────────────────────
    # Secret key used to sign access tokens. MUST be set in production via env
    # to a long random string (64+ chars). If empty, a process-local random
    # fallback is generated — tokens won't survive a server restart.
    JWT_SECRET_KEY: str = ""
    # Signing algorithm. HS256 = HMAC-SHA256, symmetric (same key signs & verifies).
    # Correct choice when one service both issues and validates tokens.
    JWT_ALGORITHM: str = "HS256"
    # How long an issued access token remains valid. 30 days is a sensible
    # default for a personal admin tool — long enough that we don't re-login
    # constantly, short enough to limit damage if a token leaks.
    JWT_EXPIRE_DAYS: int = 30

    # Email of the account that should be auto-granted admin rights on login.
    # When a user logs in with this email, the backend will flip their is_admin
    # flag to TRUE in the database and embed is_admin=true into their JWT.
    # Leave empty to disable auto-admin (admin flag must then be set manually).
    ADMIN_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Allows JSON array or comma-separated CORS_ORIGINS env format."""
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return DEFAULT_CORS_ORIGINS.copy()
            if raw.startswith("["):
                return json.loads(raw)
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    @property
    def supabase_storage_enabled(self) -> bool:
        """Supabase storage is enabled only when all required env vars are set."""
        return all(
            [
                self.SUPABASE_URL,
                self.SUPABASE_SERVICE_ROLE_KEY,
                self.SUPABASE_STORAGE_BUCKET,
            ]
        )

    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def openai_image_enabled(self) -> bool:
        """Image generation is enabled only when key + image model are provided."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_IMAGE_MODEL)

    @property
    def anthropic_enabled(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)


settings = Settings()
settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
settings.STORAGE_TEMP_PATH.mkdir(parents=True, exist_ok=True)
