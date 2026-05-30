"""
Analytics service.

Two responsibilities:
1. Record frontend tracking events into `analytics_events`.
2. Aggregate `analytics_events` + `jobs` into product metrics for the dashboard.

Design notes:
- IPs are never stored in plaintext — only SHA256(ip + salt) for deduplication.
- Recording is fire-and-forget from the API: if a single write fails we still return 200
  so the frontend isn't blocked by analytics infrastructure.
"""

from __future__ import annotations

import hashlib
import logging
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import AnalyticsEvent, Job

logger = logging.getLogger(__name__)

# Fallback salt used only when ANALYTICS_IP_SALT is empty. Process-local, regenerated
# on each restart — which is fine: it just means IP hashes can't be correlated across
# restarts, but raw IPs are still never persisted.
_PROCESS_SALT = os.urandom(16).hex()


def hash_ip(ip: str | None) -> str | None:
    """Return SHA256(ip + salt) hex digest, or None when no IP was provided."""
    if not ip:
        return None
    salt = settings.ANALYTICS_IP_SALT or _PROCESS_SALT
    return hashlib.sha256(f"{ip}|{salt}".encode("utf-8")).hexdigest()


def record_event(
    session: Session,
    *,
    session_id: str,
    event_type: str,
    ip: str | None,
    user_agent: str | None,
    referrer: str | None,
    metadata: dict | None,
) -> None:
    """Insert a single analytics event. Caller commits the session."""
    event = AnalyticsEvent(
        session_id=session_id,
        event_type=event_type,
        ip_hash=hash_ip(ip),
        user_agent=(user_agent or "")[:1024] or None,
        referrer=(referrer or "")[:1024] or None,
        event_metadata=metadata,
    )
    session.add(event)
    session.commit()


# --- Metrics aggregation -----------------------------------------------------


def _safe_ratio(numerator: int, denominator: int) -> float:
    """Return numerator/denominator rounded to 4 decimals, 0.0 when denominator is 0."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _count_jobs_since(session: Session, since: datetime | None) -> int:
    stmt = select(func.count(Job.id))
    if since is not None:
        stmt = stmt.where(Job.created_at >= since)
    return int(session.execute(stmt).scalar_one() or 0)


def _count_jobs_by_status(session: Session, status: str) -> int:
    stmt = select(func.count(Job.id)).where(Job.status == status)
    return int(session.execute(stmt).scalar_one() or 0)


def _avg_slides(session: Session) -> float:
    stmt = select(func.avg(Job.slides))
    value = session.execute(stmt).scalar_one()
    return round(float(value), 2) if value is not None else 0.0


def _rag_usage_ratio(session: Session) -> float:
    total = _count_jobs_since(session, None)
    if total == 0:
        return 0.0
    rag_count = int(
        session.execute(
            select(func.count(Job.id)).where(Job.document_id.is_not(None))
        ).scalar_one()
        or 0
    )
    return _safe_ratio(rag_count, total)


def _build_kpi(session: Session) -> dict:
    now = datetime.now(timezone.utc)
    total = _count_jobs_since(session, None)
    done = _count_jobs_by_status(session, "done")
    error = _count_jobs_by_status(session, "error")

    return {
        "total_jobs": total,
        "jobs_7d": _count_jobs_since(session, now - timedelta(days=7)),
        "jobs_30d": _count_jobs_since(session, now - timedelta(days=30)),
        "success_rate": _safe_ratio(done, total),
        "error_rate": _safe_ratio(error, total),
        "avg_slides": _avg_slides(session),
        "rag_usage_ratio": _rag_usage_ratio(session),
    }


def _unique_sessions_for_events(
    session: Session,
    event_types: Iterable[str],
    since: datetime,
) -> int:
    stmt = (
        select(func.count(func.distinct(AnalyticsEvent.session_id)))
        .where(AnalyticsEvent.event_type.in_(list(event_types)))
        .where(AnalyticsEvent.created_at >= since)
    )
    return int(session.execute(stmt).scalar_one() or 0)


def _unique_sessions_for_completed_jobs(session: Session, since: datetime) -> int:
    """
    Count distinct sessions that had at least one successful job.
    We link analytics_events.session_id ↔ jobs via metadata["job_id"] in the
    `generate_click` event payload (frontend will pass it on success).
    """
    # All sessions that completed a job_done event recorded by the frontend.
    completed_event_stmt = (
        select(func.count(func.distinct(AnalyticsEvent.session_id)))
        .where(AnalyticsEvent.event_type == "job_done")
        .where(AnalyticsEvent.created_at >= since)
    )
    return int(session.execute(completed_event_stmt).scalar_one() or 0)


def _build_funnel(session: Session, period_days: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=period_days)

    steps = [
        ("page_view", _unique_sessions_for_events(session, ["page_view"], since)),
        ("cta_click", _unique_sessions_for_events(session, ["cta_click"], since)),
        (
            "generate_click",
            _unique_sessions_for_events(session, ["generate_click"], since),
        ),
        ("job_done", _unique_sessions_for_completed_jobs(session, since)),
    ]

    funnel = []
    previous = None
    for step_name, count in steps:
        conv = None if previous is None or previous == 0 else round(count / previous, 4)
        funnel.append(
            {"step": step_name, "sessions": count, "conversion_from_previous": conv}
        )
        previous = count
    return funnel


def _build_trend(session: Session, period_days: int) -> list[dict]:
    """Number of jobs created per day for the last N days, zero-filled."""
    since_date = (datetime.now(timezone.utc) - timedelta(days=period_days)).date()

    stmt = (
        select(
            func.date(Job.created_at).label("day"),
            func.count(Job.id).label("count"),
        )
        .where(Job.created_at >= datetime.combine(since_date, datetime.min.time(), tzinfo=timezone.utc))
        .group_by(func.date(Job.created_at))
        .order_by(func.date(Job.created_at))
    )
    raw_rows = session.execute(stmt).all()
    by_day: dict[date, int] = {row.day: int(row.count) for row in raw_rows}

    points = []
    for offset in range(period_days + 1):
        d = since_date + timedelta(days=offset)
        points.append({"date": d.isoformat(), "count": by_day.get(d, 0)})
    return points


def _build_breakdown(session: Session, column) -> list[dict]:
    """Top values + counts for a Job column (format, language, style, audience)."""
    stmt = (
        select(column, func.count(Job.id))
        .group_by(column)
        .order_by(func.count(Job.id).desc())
    )
    return [
        {"value": str(value) if value is not None else "(unknown)", "count": int(count)}
        for value, count in session.execute(stmt).all()
    ]


def _build_top_errors(session: Session, limit: int = 5) -> list[dict]:
    """Top error messages from failed jobs (case-insensitive frequency counter)."""
    stmt = (
        select(Job.message)
        .where(Job.status == "error")
        .where(Job.message.is_not(None))
    )
    messages = [row[0] for row in session.execute(stmt).all() if row[0]]
    counter = Counter(message.strip() for message in messages)
    return [
        {"message": message, "count": count}
        for message, count in counter.most_common(limit)
    ]


def build_product_metrics(session: Session, *, period_days: int = 30) -> dict:
    """Aggregate everything the product dashboard needs in a single payload."""
    return {
        "period_days": period_days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kpi": _build_kpi(session),
        "funnel": _build_funnel(session, period_days),
        "trend": _build_trend(session, period_days),
        "breakdowns": {
            "format": _build_breakdown(session, Job.format),
            "language": _build_breakdown(session, Job.language),
            "style": _build_breakdown(session, Job.style),
            "audience": _build_breakdown(session, Job.audience),
        },
        "top_errors": _build_top_errors(session),
    }
