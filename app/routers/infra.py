"""
HTTP endpoint for infrastructure / technical dashboard.

GET /metrics/infra — returns system health, service state, API performance,
                      and generation job stats in one payload.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import InfraMetricsResponse, LiveMetricsResponse
from app.services import infra_service
from app.services.auth_service import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["infra"])


@router.get("/metrics/infra", response_model=InfraMetricsResponse)
def infra_metrics(
    session: Session = Depends(get_session),
    _admin = Depends(require_admin),
) -> InfraMetricsResponse:
    data = infra_service.build_infra_metrics(session)
    return InfraMetricsResponse(**data)


@router.get("/metrics/live", response_model=LiveMetricsResponse)
def live_metrics(
    session: Session = Depends(get_session),
    _admin = Depends(require_admin),
) -> LiveMetricsResponse:
    """
    Lightweight live snapshot of /generate traffic.
    Designed to be polled every 5 seconds — 3 small DB queries total.
    """
    data = infra_service.build_live_metrics(session)
    return LiveMetricsResponse(**data)
