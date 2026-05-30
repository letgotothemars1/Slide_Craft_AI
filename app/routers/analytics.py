"""
HTTP endpoints for analytics: client-side event tracking and dashboard metrics.

`POST /events/track` is intentionally tolerant of failures — analytics must never
block the user-facing UI.

`GET /metrics/product` aggregates everything the product dashboard needs in one shot.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import (
    ProductMetricsResponse,
    TrackEventRequest,
    TrackEventResponse,
)
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])


def _extract_client_ip(request: Request) -> str | None:
    """Pull the real client IP through proxies (Nginx) when available."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Pick the leftmost IP — that's the original client.
        return forwarded.split(",")[0].strip() or None
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None
    return request.client.host if request.client else None


@router.post("/events/track", response_model=TrackEventResponse)
def track_event(
    payload: TrackEventRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> TrackEventResponse:
    try:
        analytics_service.record_event(
            session,
            session_id=payload.session_id,
            event_type=payload.event_type,
            ip=_extract_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            metadata=payload.metadata,
        )
    except Exception:
        # Analytics writes never break the UX. Log and swallow.
        logger.exception(
            "analytics.event.write.failed event_type=%s session_id=%s",
            payload.event_type,
            payload.session_id,
        )
        return TrackEventResponse(ok=False)
    return TrackEventResponse(ok=True)


@router.get("/metrics/product", response_model=ProductMetricsResponse)
def product_metrics(
    period_days: int = Query(default=30, ge=1, le=365),
    session: Session = Depends(get_session),
) -> ProductMetricsResponse:
    data = analytics_service.build_product_metrics(session, period_days=period_days)
    return ProductMetricsResponse(**data)
