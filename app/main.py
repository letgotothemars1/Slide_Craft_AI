from __future__ import annotations

import logging
import shutil
from datetime import timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import repository
from app.config import settings
from app.db import get_session, init_db
from app.schemas import (
    AuthCredentialsRequest,
    AuthResponse,
    DocumentUploadResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    JobStatusResponse,
)
from app.routers import analytics as analytics_router
from app.services.document_service import index_document
from app.services.auth_service import hash_password, verify_password
from app.services.generator import start_generation_job
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

app = FastAPI(title="SlideCraft MVP Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router.router)

# Local storage mode serves files from /files/...
app.mount("/files", StaticFiles(directory=str(settings.STORAGE_PATH)), name="files")


@app.on_event("startup")
def on_startup() -> None:
    # For MVP: create tables automatically.
    # Production recommendation: switch to Alembic migrations.
    init_db()


@app.post("/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: AuthCredentialsRequest, session: Session = Depends(get_session)) -> AuthResponse:
    existing_user = repository.get_user_by_email(session, payload.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user = repository.create_user(
        session,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    return AuthResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at.astimezone(timezone.utc).isoformat(),
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthCredentialsRequest, session: Session = Depends(get_session)) -> AuthResponse:
    user = repository.get_user_by_email(session, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at.astimezone(timezone.utc).isoformat(),
    )


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, session: Session = Depends(get_session)) -> GenerateResponse:
    job_id = str(uuid4())

    repository.create_job(session, job_id=job_id, payload=payload)
    start_generation_job(job_id)

    return GenerateResponse(job_id=job_id)


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> DocumentUploadResponse:
    filename = file.filename or "document.pdf"
    content_type = file.content_type or "application/pdf"
    if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    document_id = str(uuid4())
    logger.debug("document.upload.started document_id=%s filename=%s", document_id, filename)

    temp_dir = settings.STORAGE_TEMP_PATH / "documents" / document_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / f"{document_id}.pdf"

    try:
        data = await file.read()
        temp_file.write_bytes(data)

        storage = get_storage_service()
        storage_key = f"documents/{document_id}/{document_id}.pdf"
        file_url = storage.upload_file(temp_file, storage_key, "application/pdf")

        repository.create_document(
            session,
            document_id=document_id,
            filename=filename,
            storage_key=storage_key,
            file_url=file_url,
            mime_type="application/pdf",
            status="uploaded",
        )
        repository.update_document_status(session, document_id, "indexing")

        try:
            indexed_chunks = index_document(document_id, temp_file)
            repository.update_document_status(session, document_id, "ready")
            logger.debug(
                "document.upload.completed document_id=%s status=ready chunks=%s",
                document_id,
                indexed_chunks,
            )
        except Exception as exc:  # noqa: BLE001
            repository.update_document_status(session, document_id, "error")
            logger.exception("document.upload.completed document_id=%s status=error", document_id)
            raise HTTPException(status_code=500, detail=f"Document indexing failed: {exc}") from exc

        return DocumentUploadResponse(document_id=document_id)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def status(job_id: str, session: Session = Depends(get_session)) -> JobStatusResponse:
    job = repository.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return repository.to_status_response(session, job)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)
