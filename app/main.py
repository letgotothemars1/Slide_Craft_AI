from __future__ import annotations

import logging
import shutil
import threading
import time
from datetime import timezone
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session

from app import repository
from app.config import settings
from app.db import RequestLog, SessionLocal, get_session, init_db
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
from app.routers import infra as infra_router
from app.services.document_service import index_document
from app.services.auth_service import (
    CurrentUser,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.services.generator import start_generation_job
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)

# ─── request logging middleware ───────────────────────────────────────────────

# Paths we do NOT want to log (high-frequency or recursive)
_SKIP_LOG_PREFIXES = ("/files/", "/metrics/", "/events/")
_SKIP_LOG_EXACT = frozenset({"/health"})


def _should_log_path(path: str) -> bool:
    if path in _SKIP_LOG_EXACT:
        return False
    for prefix in _SKIP_LOG_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


def _write_request_log(path: str, method: str, status_code: int, duration_ms: float) -> None:
    """Insert a RequestLog row. Runs in a daemon thread — never throws to caller."""
    try:
        db = SessionLocal()
        try:
            db.add(
                RequestLog(
                    endpoint=path[:256],
                    method=method[:10],
                    status_code=status_code,
                    duration_ms=round(duration_ms, 2),
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # analytics writes must never break request handling


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Captures wall-clock duration and HTTP status for every API request.
    The DB write is dispatched to a daemon thread so it adds zero latency
    to the response path.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if not _should_log_path(request.url.path):
            return await call_next(request)

        start = time.monotonic()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            threading.Thread(
                target=_write_request_log,
                args=(request.url.path, request.method, status_code, duration_ms),
                daemon=True,
            ).start()


# ─── app setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="SlideCraft MVP Backend", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(analytics_router.router)
app.include_router(infra_router.router)

# Local storage mode serves files from /files/...
app.mount("/files", StaticFiles(directory=str(settings.STORAGE_PATH)), name="files")


@app.on_event("startup")
def on_startup() -> None:
    # For MVP: create tables automatically.
    # Production recommendation: switch to Alembic migrations.
    init_db()


def _ensure_admin_flag(session: Session, user) -> bool:
    """
    If ADMIN_EMAIL is configured and matches this user, flip is_admin=True
    in the database (only if not already true). Returns the effective flag.

    This is the auto-bootstrap mechanism — we don't need to manually run SQL
    to mark the admin user: the first time they log in with the right email,
    they're granted access.
    """
    admin_email = (settings.ADMIN_EMAIL or "").strip().lower()
    if admin_email and user.email.lower() == admin_email and not user.is_admin:
        user.is_admin = True
        session.commit()
        logger.info("auth.admin.granted email=%s", user.email)
    return bool(user.is_admin)


def _build_auth_response(user) -> AuthResponse:
    """Common builder — creates the JWT and assembles the response payload."""
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        is_admin=user.is_admin,
    )
    return AuthResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at.astimezone(timezone.utc).isoformat(),
        is_admin=user.is_admin,
        token=token,
    )


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
    # Even on signup we may want to auto-grant admin (covers the case where the
    # admin signs up for the first time on a fresh deployment).
    _ensure_admin_flag(session, user)
    return _build_auth_response(user)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthCredentialsRequest, session: Session = Depends(get_session)) -> AuthResponse:
    user = repository.get_user_by_email(session, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _ensure_admin_flag(session, user)
    return _build_auth_response(user)


@app.get("/auth/me", response_model=AuthResponse)
def me(
    session: Session = Depends(get_session),
    current: CurrentUser = Depends(get_current_user),
) -> AuthResponse:
    """
    Return the current user based on the JWT in Authorization header.

    Frontend calls this on app start to validate that the stored token is still
    good — if /auth/me returns 401, the token is expired/invalid and the user
    should be redirected to the login page.

    We re-read from the DB (rather than just trusting the JWT) so a freshly
    revoked admin flag takes effect immediately on the next page load.
    """
    user = repository.get_user_by_id(session, current.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return _build_auth_response(user)


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


# Accepts both GET and HEAD — UptimeRobot's free plan uses HEAD requests
# for HTTP monitoring, so this endpoint needs to handle both methods.
@app.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)
