from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from app import repository
from app.config import settings
from app.db import Job, SessionLocal
from app.services.image_service import get_image_service
from app.services.llm_service import PresentationSpec, get_llm_service
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.render_service import (
    build_artifact_filename,
    build_storage_key,
    render_placeholder_pdf,
    render_placeholder_pptx,
    render_pptx_from_spec,
    resolve_layout_type,
    sanitize_job_id_for_paths,
)
from app.services.html_render_service import render_pdf_html
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)
SAFE_SLIDE_ID_PATTERN = re.compile(r"[^A-Za-z0-9_-]")
IMAGE_ELIGIBLE_LAYOUTS = {
    "hero_minimal",
    "content_two_column",
    "comparison_split",
    "infographic_visual",
}
# Per-deck image budget driven by spec.image_density (topic-aware regulation):
# visual/narrative topics (travel, lifestyle) get many images; data/business few.
IMAGE_BUDGET = {"rich": 6, "moderate": 3, "minimal": 2}
DEFAULT_IMAGE_BUDGET = 2


@dataclass
class JobContext:
    """Input data required by pipeline steps."""

    job_id: str
    prompt: str
    audience: str
    style: str
    language: str
    slides: int
    output_format: str
    document_id: str | None


@dataclass
class UploadedArtifact:
    """Uploaded file metadata that will be persisted into job_artifacts."""

    artifact_type: str
    storage_key: str
    public_url: str
    mime_type: str


def _sanitize_slide_id(slide_id: str) -> str:
    cleaned = SAFE_SLIDE_ID_PATTERN.sub("_", slide_id).strip("_")
    return cleaned or "slide"


def _set_running_state(job_id: str, progress: int, message: str) -> None:
    """Small helper to keep status updates readable inside pipeline."""
    with SessionLocal() as session:
        repository.update_job_state(
            session,
            job_id,
            status="running",
            progress=progress,
            message=message,
        )


def _load_saved_spec(job: JobContext) -> dict | None:
    """Load previously saved spec to avoid repeated LLM call for same job."""
    with SessionLocal() as session:
        latest_spec = repository.get_latest_job_spec(session, job.job_id)

    if latest_spec is None:
        return None

    try:
        spec = PresentationSpec.model_validate(latest_spec.spec_json)
    except Exception:
        logger.exception(
            "orchestrator.spec.loaded.invalid job_id=%s reason=validation_failed",
            job.job_id,
        )
        return None

    if len(spec.slides) != job.slides:
        logger.warning(
            "orchestrator.spec.loaded.invalid job_id=%s reason=slides_mismatch have=%s expected=%s",
            job.job_id,
            len(spec.slides),
            job.slides,
        )
        return None

    logger.debug("orchestrator.spec.loaded job_id=%s source=db slides=%s", job.job_id, len(spec.slides))
    return spec.model_dump()


def load_job_context(job_id: str) -> JobContext:
    """Step 1: load job from DB and build orchestration context."""
    with SessionLocal() as session:
        job: Job | None = repository.get_job(session, job_id)

    if job is None:
        raise LookupError(f"Job not found: {job_id}")

    context = JobContext(
        job_id=job.job_id,
        prompt=job.prompt,
        audience=job.audience,
        style=job.style,
        language=job.language,
        slides=job.slides,
        output_format=job.format,
        document_id=job.document_id,
    )

    logger.debug(
        "orchestrator.job.loaded job_id=%s format=%s slides=%s",
        context.job_id,
        context.output_format,
        context.slides,
    )
    return context


def generate_spec(job: JobContext) -> dict:
    """Step 2: call LLM and return validated presentation spec."""
    logger.debug("orchestrator.spec.generating job_id=%s", job.job_id)

    retrieved_chunks: list[str] | None = None
    if job.document_id:
        logger.debug("rag.enabled job_id=%s document_id=%s", job.job_id, job.document_id)
        retrieved_chunks = retrieve_relevant_chunks(
            prompt=job.prompt,
            document_id=job.document_id,
            top_k=5,
        )
    else:
        logger.debug("rag.skipped job_id=%s reason=no_document_id", job.job_id)

    llm_service = get_llm_service()
    spec_json = llm_service.generate_presentation_spec(
        prompt=job.prompt,
        audience=job.audience,
        style=job.style,
        language=job.language,
        slides=job.slides,
        retrieved_chunks=retrieved_chunks,
    )

    spec = PresentationSpec.model_validate(spec_json)
    return spec.model_dump()


def save_spec(job_id: str, spec: dict) -> None:
    """Step 3: persist generated/validated spec in job_specs."""
    with SessionLocal() as session:
        repository.save_job_spec(session, job_id=job_id, spec_json=spec)

    logger.debug("orchestrator.spec.saved job_id=%s", job_id)


def _select_image_candidates(spec: PresentationSpec) -> list[tuple[int, int, str]]:
    """
    Select slides for image generation (budget from spec.image_density) with priority:
    1) hero/title, 2) key content, 3) comparison/infographic.
    """
    ranked: list[tuple[int, int, str]] = []

    for idx, slide in enumerate(spec.slides):
        if not slide.image_prompt:
            continue

        layout = resolve_layout_type(slide)
        if layout not in IMAGE_ELIGIBLE_LAYOUTS:
            continue

        if layout == "hero_minimal" or slide.type == "title":
            priority = 0
        elif layout == "content_two_column":
            priority = 1
        elif layout in {"comparison_split", "infographic_visual"}:
            priority = 2
        else:
            priority = 3

        ranked.append((priority, idx, slide.id))

    ranked.sort(key=lambda item: (item[0], item[1]))
    cap = IMAGE_BUDGET.get(spec.image_density, DEFAULT_IMAGE_BUDGET)
    return ranked[:cap]


def _run_critic(spec_json: dict) -> dict:
    """Run Critic LLM quality review. Always returns a spec — original on failure."""
    try:
        from app.services.critic_llm_service import CriticLLMService
        critic = CriticLLMService()
        return critic.review_and_fix(spec_json)
    except Exception:
        logger.exception("orchestrator.critic.error — keeping original spec")
        return spec_json


def generate_assets(job_id: str, spec_json: dict, temp_dir: Path) -> tuple[dict, list[UploadedArtifact]]:
    """
    Optional image generation step.
    Never breaks the pipeline: on failure returns original spec + empty artifact list.
    """
    try:
        spec = PresentationSpec.model_validate(spec_json)
    except Exception:
        logger.exception("image.error job_id=%s reason=invalid_spec", job_id)
        return spec_json, []

    if not settings.openai_image_enabled:
        return spec.model_dump(), []

    try:
        image_service = get_image_service()
    except Exception:
        logger.exception("image.error job_id=%s reason=service_init_failed", job_id)
        return spec.model_dump(), []

    storage = get_storage_service()
    safe_job_id = sanitize_job_id_for_paths(job_id)
    uploaded_artifacts: list[UploadedArtifact] = []

    from concurrent.futures import ThreadPoolExecutor

    candidates = []
    for _, _, slide_id in _select_image_candidates(spec):
        slide = next((item for item in spec.slides if item.id == slide_id), None)
        if slide is not None and slide.image_prompt:
            candidates.append(slide)

    def _generate_and_upload(slide) -> UploadedArtifact | None:
        """Best-effort image generation + upload for one slide (runs in a worker thread)."""
        try:
            image_bytes = image_service.generate_slide_image(
                slide.image_prompt,
                job_id=job_id,
                slide_id=slide.id,
            )
            if image_bytes is None:
                return None

            safe_slide_id = _sanitize_slide_id(slide.id)
            image_local_path = temp_dir / f"{safe_slide_id}.png"
            image_local_path.write_bytes(image_bytes)

            storage_key = f"jobs/{safe_job_id}/images/{safe_slide_id}.png"
            public_url = storage.upload_file(image_local_path, storage_key, "image/png")
            slide.image_url = public_url

            logger.debug("image.saved job_id=%s slide_id=%s public_url=%s", job_id, slide.id, public_url)
            return UploadedArtifact(
                artifact_type="image",
                storage_key=storage_key,
                public_url=public_url,
                mime_type="image/png",
            )
        except Exception:
            # Image path is best-effort only; we keep the pipeline alive on any per-slide failure.
            logger.exception("image.error job_id=%s slide_id=%s stage=generate_or_upload", job_id, slide.id)
            return None

    # Generate all slide images concurrently — sequential generation was the main latency cost.
    if candidates:
        with ThreadPoolExecutor(max_workers=min(6, len(candidates))) as pool:
            for artifact in pool.map(_generate_and_upload, candidates):
                if artifact is not None:
                    uploaded_artifacts.append(artifact)

    updated_spec = spec.model_dump()
    if uploaded_artifacts:
        save_spec(job_id, updated_spec)
        logger.debug(
            "orchestrator.spec.saved job_id=%s source=image_assets count=%s",
            job_id,
            len(uploaded_artifacts),
        )

    return updated_spec, uploaded_artifacts


def render_pdf(spec: dict | None, job_id: str, temp_dir: Path, prompt: str) -> Path:
    """Step 4a: render PDF from spec, fallback to placeholder if spec is missing."""
    pdf_path = temp_dir / build_artifact_filename(job_id, "pdf")

    logger.debug("orchestrator.pdf.render.started job_id=%s", job_id)
    if spec is None:
        render_placeholder_pdf(pdf_path, job_id, prompt)
    else:
        render_pdf_html(pdf_path, spec)
    logger.debug("orchestrator.pdf.render.finished job_id=%s path=%s", job_id, pdf_path)

    return pdf_path


def render_pptx(spec: dict | None, job_id: str, temp_dir: Path, prompt: str) -> Path:
    """Step 4b: render PPTX from spec, fallback to placeholder if spec is missing."""
    pptx_path = temp_dir / build_artifact_filename(job_id, "pptx")

    logger.debug("orchestrator.pptx.render.started job_id=%s", job_id)
    if spec is None:
        # TODO: remove fallback once LLM/spec becomes hard requirement for every job.
        render_placeholder_pptx(pptx_path, job_id, prompt)
    else:
        render_pptx_from_spec(pptx_path, spec)
    logger.debug("orchestrator.pptx.render.finished job_id=%s path=%s", job_id, pptx_path)

    return pptx_path


def upload_artifacts(
    job_id: str,
    local_pdf_path: Path | None,
    local_pptx_path: Path | None,
) -> list[UploadedArtifact]:
    """Step 5: upload generated files to storage and return their URLs."""
    logger.debug("orchestrator.artifacts.upload.started job_id=%s", job_id)

    storage = get_storage_service()
    uploaded: list[UploadedArtifact] = []

    if local_pdf_path is not None:
        pdf_key = build_storage_key(job_id, "pdf")
        pdf_url = storage.upload_file(local_pdf_path, pdf_key, "application/pdf")
        uploaded.append(
            UploadedArtifact(
                artifact_type="pdf",
                storage_key=pdf_key,
                public_url=pdf_url,
                mime_type="application/pdf",
            )
        )

    if local_pptx_path is not None:
        pptx_key = build_storage_key(job_id, "pptx")
        pptx_url = storage.upload_file(
            local_pptx_path,
            pptx_key,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        uploaded.append(
            UploadedArtifact(
                artifact_type="pptx",
                storage_key=pptx_key,
                public_url=pptx_url,
                mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        )

    logger.debug("orchestrator.artifacts.upload.finished job_id=%s count=%s", job_id, len(uploaded))
    return uploaded


def finalize_job(job_id: str, artifact_urls: list[UploadedArtifact]) -> None:
    """Step 6: persist artifacts and mark job as done."""
    with SessionLocal() as session:
        for artifact in artifact_urls:
            repository.add_job_artifact(
                session,
                job_id=job_id,
                artifact_type=artifact.artifact_type,
                storage_key=artifact.storage_key,
                public_url=artifact.public_url,
                mime_type=artifact.mime_type,
            )

        repository.complete_job(session, job_id)

    logger.debug("orchestrator.job.completed job_id=%s artifacts=%s", job_id, len(artifact_urls))


def fail_job(job_id: str, error: Exception, step: str) -> None:
    """Step 7: move job to error and keep readable failure context for status endpoint."""
    logger.exception("orchestrator.job.failed job_id=%s step=%s", job_id, step)

    with SessionLocal() as session:
        repository.fail_job(session, job_id, f"Generation failed at {step}: {error}")


def run_generation_pipeline(job_id: str) -> None:
    """Top-level pipeline for a single generation job."""
    temp_dir = settings.STORAGE_TEMP_PATH / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    current_step = "load_job_context"
    try:
        job = load_job_context(job_id)

        _set_running_state(job_id, 10, "Preparing structure...")

        current_step = "spec.load"
        spec_json: dict | None = _load_saved_spec(job)

        if spec_json is None:
            _set_running_state(job_id, 25, "Generating presentation spec...")

            current_step = "spec.generate"
            try:
                spec_json = generate_spec(job)

                current_step = "spec.save"
                save_spec(job_id, spec_json)
            except Exception:
                if job.document_id:
                    # For RAG mode we fail fast, because ignoring document retrieval would be misleading.
                    raise
                # Keep current product behavior: render placeholders when spec generation fails.
                # TODO: make spec generation mandatory and fail fast once frontend UX is ready.
                logger.exception(
                    "orchestrator.spec.generation.failed job_id=%s fallback=placeholder",
                    job_id,
                )
                spec_json = None

        if spec_json is not None and settings.CRITIC_LLM_ENABLED:
            _set_running_state(job_id, 35, "Reviewing presentation quality...")
            current_step = "spec.critic"
            spec_json = _run_critic(spec_json)

        image_artifacts: list[UploadedArtifact] = []
        if spec_json is not None:
            _set_running_state(job_id, 40, "Generating slide visuals...")
            current_step = "assets.generate"
            spec_json, image_artifacts = generate_assets(job_id, spec_json, temp_dir)

        pdf_path: Path | None = None
        pptx_path: Path | None = None

        if job.output_format in {"pdf", "both"}:
            _set_running_state(job_id, 55, "Rendering PDF...")
            current_step = "pdf.render"
            pdf_path = render_pdf(spec_json, job_id, temp_dir, job.prompt)

        if job.output_format in {"pptx", "both"}:
            _set_running_state(job_id, 75, "Rendering PPTX...")
            current_step = "pptx.render"
            pptx_path = render_pptx(spec_json, job_id, temp_dir, job.prompt)

        _set_running_state(job_id, 95, "Uploading artifacts...")

        current_step = "artifacts.upload"
        artifacts = image_artifacts + upload_artifacts(job_id, pdf_path, pptx_path)

        current_step = "job.finalize"
        finalize_job(job_id, artifacts)

    except LookupError:
        # Job record does not exist, nothing to finalize.
        logger.warning("orchestrator.job.failed job_id=%s step=%s reason=job_not_found", job_id, current_step)
    except Exception as exc:  # noqa: BLE001
        fail_job(job_id, exc, current_step)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
