from __future__ import annotations

import threading

from app.services.orchestrator import run_generation_pipeline


def run_generation_job(job_id: str) -> None:
    """Backward-compatible entrypoint used by background worker."""
    run_generation_pipeline(job_id)


def start_generation_job(job_id: str) -> None:
    """Starts generation in daemon thread so POST /generate returns immediately."""
    worker = threading.Thread(target=run_generation_job, args=(job_id,), daemon=True)
    worker.start()


def start_finalize_job(job_id: str) -> None:
    """Resume a reviewed job: images, render and upload, off the request thread."""
    from app.services.orchestrator import run_finalize_pipeline

    worker = threading.Thread(target=run_finalize_pipeline, args=(job_id,), daemon=True)
    worker.start()
