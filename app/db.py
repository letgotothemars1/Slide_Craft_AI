from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
import logging

from sqlalchemy import Boolean, JSON, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Minimal users table for email/password authentication."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    # Profile fields — all nullable on purpose: accounts created before this
    # iteration have none, and login still happens by email, not username.
    username: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Admin flag — gates access to /metrics/* endpoints and dashboard routes.
    # Flipped automatically on login when email matches settings.ADMIN_EMAIL,
    # or can be set manually via SQL.
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Job(Base):
    """Main generation job table."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(String(32), nullable=False)
    style: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    slides: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    brand_color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    artifacts: Mapped[list["JobArtifact"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    specs: Mapped[list["JobSpec"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Document(Base):
    """Uploaded source document for optional RAG pipeline."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    """Chunked text + embedding used for retrieval."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    # MVP: JSON vector for compatibility. TODO: migrate to pgvector for DB-side similarity search.
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class Project(Base):
    """Persisted intake and editable state for the modular student journey."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="intake")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignment_text: Mapped[str] = mapped_column(Text, nullable=False)
    context_pack_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    theme: Mapped[str] = mapped_column(String(32), nullable=False)
    build_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="template")
    outline_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    slides_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JobArtifact(Base):
    """Stores generated files uploaded to object storage."""

    __tablename__ = "job_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    job: Mapped[Job] = relationship(back_populates="artifacts")


class AnalyticsEvent(Base):
    """
    Lightweight analytics event log.
    One row per tracked frontend event (page_view, cta_click, generate_click, ...).
    """

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class RequestLog(Base):
    """
    HTTP request log for API performance monitoring.

    Written by RequestLoggingMiddleware on every non-health, non-metrics request.
    Auto-pruned to 7 days by infra_service to keep the table small.
    """

    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class JobSpec(Base):
    """Stores generation spec payload per job for reproducibility."""

    __tablename__ = "job_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    spec_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    job: Mapped[Job] = relationship(back_populates="specs")


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """Simple initialization for MVP. In production, use Alembic migrations."""
    Base.metadata.create_all(bind=engine)
    _run_startup_migrations()


def _run_startup_migrations() -> None:
    """
    Lightweight startup migrations for evolving MVP schema.
    Keeps old local databases usable without a full Alembic setup.
    """
    with engine.begin() as conn:
        dialect = conn.dialect.name
        try:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS build_mode VARCHAR(16) NOT NULL DEFAULT 'template'"))
                conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER"))
                conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS document_id VARCHAR(64)"))
                # Keep email uniqueness guaranteed even on old environments.
                conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)")
                )
                # Admin flag for users — added in JWT-auth iteration.
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE")
                )
                # Profile fields — added in the account iteration.
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(80)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(80)"))
                # Postgres allows many NULLs under a unique index, so existing
                # accounts without a username do not collide with each other.
                conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username ON users (username)")
                )
            elif dialect == "sqlite":
                project_rows = conn.execute(text("PRAGMA table_info(projects)")).fetchall()
                if "build_mode" not in {row[1] for row in project_rows}:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN build_mode VARCHAR(16) NOT NULL DEFAULT 'template'"))
                chunk_rows = conn.execute(text("PRAGMA table_info(document_chunks)")).fetchall()
                if "page_number" not in {row[1] for row in chunk_rows}:
                    conn.execute(text("ALTER TABLE document_chunks ADD COLUMN page_number INTEGER"))
                rows = conn.execute(text("PRAGMA table_info(jobs)")).fetchall()
                existing_columns = {row[1] for row in rows}
                if "document_id" not in existing_columns:
                    conn.execute(text("ALTER TABLE jobs ADD COLUMN document_id VARCHAR(64)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)"))
                user_rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                user_columns = {row[1] for row in user_rows}
                if "is_admin" not in user_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
                for column, ddl in (
                    ("username", "ALTER TABLE users ADD COLUMN username VARCHAR(64)"),
                    ("first_name", "ALTER TABLE users ADD COLUMN first_name VARCHAR(80)"),
                    ("last_name", "ALTER TABLE users ADD COLUMN last_name VARCHAR(80)"),
                ):
                    if column not in user_columns:
                        conn.execute(text(ddl))
                conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username ON users (username)")
                )
        except Exception:
            logger.exception("db.migration.failed migration=startup")


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
