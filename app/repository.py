from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db import Document, DocumentChunk, Job, JobArtifact, JobSpec, User
from app.schemas import GenerateRequest, JobResult, JobStatusResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def create_job(session: Session, job_id: str, payload: GenerateRequest) -> Job:
    """Insert a new job with initial queued status."""
    now = _utc_now()
    job = Job(
        job_id=job_id,
        prompt=payload.prompt,
        audience=payload.audience,
        style=payload.style,
        language=payload.language,
        slides=payload.slides,
        format=payload.format,
        document_id=payload.document_id,
        brand_color=payload.brandColor,
        logo_url=payload.logoUrl,
        status="queued",
        progress=0,
        message=None,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def save_job_spec(session: Session, job_id: str, spec_json: dict) -> JobSpec:
    """Persist generated LLM presentation spec for a job."""
    spec = JobSpec(job_id=job_id, spec_json=spec_json)
    session.add(spec)
    session.commit()
    session.refresh(spec)
    return spec


def get_user_by_email(session: Session, email: str) -> User | None:
    """Find user by normalized email."""
    return session.query(User).filter(User.email == email).one_or_none()


def get_user_by_id(session: Session, user_id: str) -> User | None:
    """Find user by primary key (used by JWT-authenticated endpoints)."""
    return session.query(User).filter(User.id == user_id).one_or_none()


def create_user(session: Session, *, email: str, password_hash: str) -> User:
    """Create user with pre-hashed password."""
    now = _utc_now()
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_document(
    session: Session,
    *,
    document_id: str,
    filename: str,
    storage_key: str,
    file_url: str,
    mime_type: str,
    status: str = "uploaded",
    user_id: str | None = None,
) -> Document:
    doc = Document(
        id=document_id,
        user_id=user_id,
        filename=filename,
        storage_key=storage_key,
        file_url=file_url,
        mime_type=mime_type,
        status=status,
        created_at=_utc_now(),
        updated_at=_utc_now(),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document(session: Session, document_id: str) -> Document | None:
    return session.query(Document).filter(Document.id == document_id).one_or_none()


def update_document_status(session: Session, document_id: str, status: str) -> Document | None:
    doc = get_document(session, document_id)
    if not doc:
        return None
    doc.status = status
    doc.updated_at = _utc_now()
    session.commit()
    session.refresh(doc)
    return doc


def replace_document_chunks(
    session: Session,
    *,
    document_id: str,
    chunks: list[tuple[int, str, list[float]]],
) -> None:
    session.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    for chunk_index, chunk_text, embedding in chunks:
        session.add(
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                embedding=embedding,
            )
        )
    session.commit()


def list_document_chunks(session: Session, document_id: str) -> list[DocumentChunk]:
    return (
        session.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def get_latest_job_spec(session: Session, job_id: str) -> JobSpec | None:
    """Returns the most recent saved spec for a job."""
    return (
        session.query(JobSpec)
        .filter(JobSpec.job_id == job_id)
        .order_by(JobSpec.created_at.desc(), JobSpec.id.desc())
        .first()
    )


def get_job(session: Session, job_id: str) -> Job | None:
    return session.query(Job).filter(Job.job_id == job_id).one_or_none()


def update_job_state(
    session: Session,
    job_id: str,
    *,
    status: str,
    progress: int | None,
    message: str | None,
) -> Job | None:
    """Update status/progress/message for a job."""
    job = get_job(session, job_id)
    if not job:
        return None

    job.status = status
    job.progress = progress
    job.message = message
    job.updated_at = _utc_now()
    session.commit()
    session.refresh(job)
    return job


def complete_job(session: Session, job_id: str, message: str = "Done.") -> Job | None:
    """Mark job as done. Artifact URLs are stored in job_artifacts table."""
    job = get_job(session, job_id)
    if not job:
        return None

    job.status = "done"
    job.progress = 100
    job.message = message
    job.updated_at = _utc_now()
    session.commit()
    session.refresh(job)
    return job


def fail_job(session: Session, job_id: str, message: str) -> Job | None:
    job = get_job(session, job_id)
    if not job:
        return None

    job.status = "error"
    job.message = message
    job.progress = None
    job.updated_at = _utc_now()
    session.commit()
    session.refresh(job)
    return job


def add_job_artifact(
    session: Session,
    *,
    job_id: str,
    artifact_type: str,
    storage_key: str,
    public_url: str,
    mime_type: str,
) -> JobArtifact:
    artifact = JobArtifact(
        job_id=job_id,
        artifact_type=artifact_type,
        storage_key=storage_key,
        public_url=public_url,
        mime_type=mime_type,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def _latest_artifact_url(session: Session, job_id: str, artifact_type: str) -> str | None:
    artifact = (
        session.query(JobArtifact)
        .filter(JobArtifact.job_id == job_id, JobArtifact.artifact_type == artifact_type)
        .order_by(JobArtifact.created_at.desc(), JobArtifact.id.desc())
        .first()
    )
    return artifact.public_url if artifact else None


def _preview_urls(session: Session, job_id: str) -> list[str] | None:
    previews = (
        session.query(JobArtifact)
        .filter(JobArtifact.job_id == job_id, JobArtifact.artifact_type == "preview")
        .order_by(JobArtifact.created_at.asc(), JobArtifact.id.asc())
        .all()
    )
    if not previews:
        return None
    return [item.public_url for item in previews]


def to_status_response(session: Session, job: Job) -> JobStatusResponse:
    # Frontend expects result=null while the job is not finished.
    result: JobResult | None = None

    if job.status in {"done", "error"}:
        result = JobResult(
            pptx_url=_latest_artifact_url(session, job.job_id, "pptx"),
            pdf_url=_latest_artifact_url(session, job.job_id, "pdf"),
            preview_images=_preview_urls(session, job.job_id),
        )

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        result=result,
        created_at=_to_iso(job.created_at),
    )
