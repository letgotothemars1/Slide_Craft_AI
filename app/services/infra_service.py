"""
Infrastructure / technical metrics service.

Provides three data sources combined into one payload for GET /metrics/infra:
  1. system  — CPU, RAM, Disk via psutil (graceful fallback if unavailable)
  2. service — systemd unit state via `systemctl show` (fallback on dev/macOS)
  3. nginx   — active connections via stub_status (optional, None if not configured)
  4. api     — request latency / error-rate from the request_logs table (7-day rolling)
  5. generation — job duration p50/p95/p99 from the jobs table

Design notes:
- psutil.cpu_percent(interval=0.1) blocks 100 ms — acceptable for a metrics endpoint.
- systemctl calls use a 5-second timeout and fail silently outside systemd.
- request_logs is pruned to 7 days by _maybe_cleanup(); cleanup runs at most once/hour.
- All functions are synchronous (called from a sync FastAPI dependency).
"""

from __future__ import annotations

import logging
import subprocess
import time as _time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.orm import Session

from app.db import Job, RequestLog

logger = logging.getLogger(__name__)

# ─── cleanup state ───────────────────────────────────────────────────────────
_last_cleanup_mono: float = 0.0
_CLEANUP_INTERVAL_S = 3600.0   # run at most once per hour
_KEEP_DAYS = 7


def _maybe_cleanup_request_logs(session: Session) -> None:
    """Delete request_logs older than KEEP_DAYS. Runs at most once per hour."""
    global _last_cleanup_mono
    now = _time.monotonic()
    if now - _last_cleanup_mono < _CLEANUP_INTERVAL_S:
        return
    _last_cleanup_mono = now
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=_KEEP_DAYS)
        session.execute(sa_delete(RequestLog).where(RequestLog.created_at < cutoff))
        session.commit()
        logger.debug("infra.cleanup.done keep_days=%d", _KEEP_DAYS)
    except Exception:
        logger.exception("infra.cleanup.failed")


# ─── system metrics ───────────────────────────────────────────────────────────

def get_system_metrics() -> dict:
    """Return CPU / RAM / Disk stats via psutil. Returns error key on failure."""
    try:
        import psutil  # lazy import — soft dependency

        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_ts = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
        uptime_s = int((datetime.now(timezone.utc) - boot_ts).total_seconds())

        # Use (total - available) consistently for both the number and the percent.
        # psutil's mem.used on macOS counts only wired+active (misses inactive/compressed),
        # while mem.percent uses (total - available) — those two disagree. We pick
        # total-available as the single source of truth so the gauge and the label match.
        ram_used_bytes = mem.total - mem.available

        return {
            "cpu_pct": round(cpu_pct, 1),
            "ram_used_pct": round(ram_used_bytes / mem.total * 100, 1),
            "ram_used_mb": round(ram_used_bytes / 1024 / 1024),
            "ram_total_mb": round(mem.total / 1024 / 1024),
            "disk_used_pct": round(disk.percent, 1),
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "server_uptime_seconds": uptime_s,
        }
    except ImportError:
        return {
            "cpu_pct": None,
            "ram_used_pct": None,
            "ram_used_mb": None,
            "ram_total_mb": None,
            "disk_used_pct": None,
            "disk_used_gb": None,
            "disk_total_gb": None,
            "server_uptime_seconds": None,
            "error": "psutil not installed",
        }
    except Exception as exc:
        logger.exception("infra.system_metrics.failed")
        return {
            "cpu_pct": None,
            "ram_used_pct": None,
            "ram_used_mb": None,
            "ram_total_mb": None,
            "disk_used_pct": None,
            "disk_used_gb": None,
            "disk_total_gb": None,
            "server_uptime_seconds": None,
            "error": str(exc),
        }


# ─── systemd service info ─────────────────────────────────────────────────────

def get_service_info() -> dict:
    """
    Query systemd for the slidecraft.service unit state.
    Returns safe defaults when not running under systemd (e.g. macOS dev).
    """
    _default = {
        "status": "unknown",
        "sub_state": "unknown",
        "restarts_total": 0,
        "service_uptime_seconds": None,
    }
    try:
        result = subprocess.run(
            [
                "systemctl",
                "show",
                "slidecraft",
                "--property=ActiveState,SubState,ActiveEnterTimestamp,NRestarts",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        props: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                props[k] = v

        service_uptime_s: int | None = None
        ts_str = props.get("ActiveEnterTimestamp", "")
        if ts_str and ts_str not in ("", "n/a"):
            try:
                # Format: "Mon 2025-05-31 10:23:45 UTC"
                parts = ts_str.split()
                if len(parts) >= 3:
                    dt = datetime.strptime(
                        f"{parts[1]} {parts[2]}", "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                    service_uptime_s = int(
                        (datetime.now(timezone.utc) - dt).total_seconds()
                    )
            except Exception:
                pass

        return {
            "status": props.get("ActiveState", "unknown"),
            "sub_state": props.get("SubState", "unknown"),
            "restarts_total": int(props.get("NRestarts", 0) or 0),
            "service_uptime_seconds": service_uptime_s,
        }
    except FileNotFoundError:
        # systemctl not available (macOS, Docker without systemd, etc.)
        return _default
    except Exception:
        logger.exception("infra.service_info.failed")
        return _default


# ─── nginx stub_status ────────────────────────────────────────────────────────

def get_nginx_info() -> dict | None:
    """
    Fetch active connections from nginx stub_status module.
    Returns None when the location is not configured (graceful degradation).

    Server-side prerequisite — add to nginx config:
        location = /nginx-status {
            stub_status;
            allow 127.0.0.1;
            deny all;
        }
    """
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1/nginx-status", timeout=2
        ) as resp:
            body = resp.read().decode()
        # Line 1: "Active connections: 42"
        first_line = body.strip().splitlines()[0]
        active = int(first_line.split(":")[1].strip())
        return {"active_connections": active}
    except Exception:
        return None


# ─── latency helpers ──────────────────────────────────────────────────────────

def _percentiles(values_ms: list[float]) -> dict:
    if not values_ms:
        return {"p50": None, "p95": None, "p99": None}
    s = sorted(values_ms)
    n = len(s)

    def pct(p: float) -> float:
        idx = max(0, min(n - 1, int(n * p / 100)))
        return round(s[idx], 1)

    return {"p50": pct(50), "p95": pct(95), "p99": pct(99)}


# ─── API metrics from request_logs ───────────────────────────────────────────

def build_api_metrics(session: Session, *, window_hours: int = 24) -> dict:
    """
    Aggregate request_logs for the last `window_hours`.
    Also triggers periodic cleanup of old rows.
    """
    _maybe_cleanup_request_logs(session)

    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    logs = session.execute(
        select(RequestLog).where(RequestLog.created_at >= since)
    ).scalars().all()

    total = len(logs)
    now_utc = datetime.now(timezone.utc)

    # Error counts
    n_4xx = sum(1 for lg in logs if 400 <= lg.status_code < 500)
    n_5xx = sum(1 for lg in logs if lg.status_code >= 500)

    # RPS
    rps_1h: float | None = None
    rps_24h: float | None = None
    if total > 0:
        since_1h = now_utc - timedelta(hours=1)
        count_1h = sum(1 for lg in logs if lg.created_at >= since_1h)
        rps_1h = round(count_1h / 3600, 4)
        rps_24h = round(total / (window_hours * 3600), 4)

    # Global latency percentiles
    all_durations = [lg.duration_ms for lg in logs]
    global_pct = _percentiles(all_durations)

    # Per-endpoint stats — sort by p95 desc for "slowest endpoints" view
    ep_durations: dict[str, list[float]] = defaultdict(list)
    for lg in logs:
        ep_durations[lg.endpoint].append(lg.duration_ms)

    slowest: list[dict] = []
    for ep, durations in sorted(ep_durations.items(), key=lambda x: -len(x[1])):
        p = _percentiles(durations)
        slowest.append(
            {
                "endpoint": ep,
                "count": len(durations),
                "p50_ms": p["p50"],
                "p95_ms": p["p95"],
                "p99_ms": p["p99"],
            }
        )
    # Sort by p95 descending
    slowest.sort(key=lambda x: x["p95_ms"] or 0.0, reverse=True)
    slowest = slowest[:10]

    # Hourly request trend — fill every hour in the window
    hour_counts: Counter[str] = Counter()
    for lg in logs:
        hour_counts[lg.created_at.strftime("%Y-%m-%dT%H:00")] += 1

    hourly_trend = []
    for h in range(window_hours, 0, -1):
        dt = now_utc - timedelta(hours=h)
        key = dt.strftime("%Y-%m-%dT%H:00")
        hourly_trend.append({"hour": key, "count": hour_counts.get(key, 0)})

    # Status code breakdown
    status_counts: Counter[int] = Counter(lg.status_code for lg in logs)
    status_breakdown = [
        {"status_code": k, "count": v}
        for k, v in sorted(status_counts.items())
    ]

    # Recent errors (4xx / 5xx), newest first
    recent_errors = [
        {
            "endpoint": lg.endpoint,
            "method": lg.method,
            "status_code": lg.status_code,
            "ts": lg.created_at.isoformat(),
        }
        for lg in sorted(
            [lg for lg in logs if lg.status_code >= 400],
            key=lambda x: x.created_at,
            reverse=True,
        )[:20]
    ]

    return {
        "window_hours": window_hours,
        "total_requests": total,
        "rps_1h": rps_1h,
        "rps_24h": rps_24h,
        "error_rate_4xx": round(n_4xx / total, 4) if total else 0.0,
        "error_rate_5xx": round(n_5xx / total, 4) if total else 0.0,
        "latency": global_pct,
        "slowest_endpoints": slowest,
        "hourly_trend": hourly_trend,
        "status_breakdown": status_breakdown,
        "recent_errors": recent_errors,
    }


# ─── generation job performance ───────────────────────────────────────────────

def build_generation_perf(session: Session) -> dict:
    """
    Compute duration stats for completed jobs (done + error).
    Duration = updated_at − created_at (i.e. end-to-end wall time).
    """
    rows = session.execute(
        select(Job.created_at, Job.updated_at, Job.status).where(
            Job.status.in_(["done", "error"])
        )
    ).all()

    durations_s = [
        (r.updated_at - r.created_at).total_seconds()
        for r in rows
        if r.updated_at and r.created_at and r.updated_at > r.created_at
    ]

    queue_depth = int(
        session.execute(
            select(func.count(Job.id)).where(Job.status.in_(["queued", "running"]))
        ).scalar_one()
        or 0
    )

    if not durations_s:
        return {
            "avg_duration_s": None,
            "p95_duration_s": None,
            "p99_duration_s": None,
            "sample_count": 0,
            "queue_depth": queue_depth,
        }

    pct = _percentiles([d * 1000 for d in durations_s])  # to ms for _percentiles

    return {
        "avg_duration_s": round(sum(durations_s) / len(durations_s), 1),
        "p95_duration_s": round((pct["p95"] or 0) / 1000, 1),
        "p99_duration_s": round((pct["p99"] or 0) / 1000, 1),
        "sample_count": len(durations_s),
        "queue_depth": queue_depth,
    }


# ─── combined payload ─────────────────────────────────────────────────────────

def build_live_metrics(session: Session) -> dict:
    """
    Lightweight live activity snapshot — intended to be polled every 5 seconds.
    Single query for /generate hits in the last 60 minutes, then bucketed in Python.
    Two extra count queries for job queue state.
    """
    now = datetime.now(timezone.utc)
    since_60m = now - timedelta(minutes=60)

    # ── All /generate hits in the last 60 minutes ───────────────────────────
    gen_rows = session.execute(
        select(RequestLog.created_at, RequestLog.status_code)
        .where(RequestLog.endpoint == "/generate")
        .where(RequestLog.created_at >= since_60m)
    ).all()

    def _count_recent(minutes: int) -> int:
        cutoff = now - timedelta(minutes=minutes)
        return sum(1 for r in gen_rows if r.created_at >= cutoff)

    # 1-minute sparkline buckets for the last 15 minutes
    # bucket 0 = current minute, bucket 14 = 15 minutes ago
    sparkline: list[dict] = []
    for m in range(14, -1, -1):
        bucket_start = now - timedelta(minutes=m + 1)
        bucket_end = now - timedelta(minutes=m)
        count = sum(
            1 for r in gen_rows
            if bucket_start <= r.created_at < bucket_end
        )
        sparkline.append({"label": f"-{m}м", "count": count})

    # ── Job queue state ──────────────────────────────────────────────────────
    running_jobs = int(
        session.execute(
            select(func.count(Job.id)).where(Job.status == "running")
        ).scalar_one()
        or 0
    )
    queued_jobs = int(
        session.execute(
            select(func.count(Job.id)).where(Job.status == "queued")
        ).scalar_one()
        or 0
    )

    return {
        "ts": now.isoformat(),
        "generate_last_1m": _count_recent(1),
        "generate_last_5m": _count_recent(5),
        "generate_last_15m": _count_recent(15),
        "generate_last_60m": _count_recent(60),
        "running_jobs": running_jobs,
        "queued_jobs": queued_jobs,
        "sparkline_15m": sparkline,
    }


def build_infra_metrics(session: Session) -> dict:
    """Single call that assembles the full technical dashboard payload."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": get_system_metrics(),
        "service": get_service_info(),
        "nginx": get_nginx_info(),
        "api": build_api_metrics(session),
        "generation": build_generation_perf(session),
    }
