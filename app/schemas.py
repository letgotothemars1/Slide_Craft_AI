from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Audience = Literal["executives", "students", "sales", "investors", "custom"]
Style = Literal["business", "minimal", "dark", "creative"]
Language = Literal["ru", "en"]
OutputFormat = Literal["pptx", "pdf", "both"]
JobStatus = Literal["queued", "running", "done", "error"]


class GenerateRequest(BaseModel):
    """Request model for POST /generate (strictly aligned with frontend schema)."""

    prompt: str = Field(min_length=1, max_length=2000)
    audience: Audience
    style: Style
    language: Language
    slides: int = Field(ge=5, le=30)
    format: OutputFormat
    document_id: str | None = None
    brandColor: str | None = None
    logoUrl: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt must not be empty")
        return cleaned


class GenerateResponse(BaseModel):
    job_id: str


class AuthCredentialsRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=256)

    model_config = ConfigDict(extra="forbid")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("email must not be empty")
        return cleaned


class AuthResponse(BaseModel):
    id: str
    email: str
    created_at: str
    is_admin: bool = False
    # JWT access token. Frontend stores it in localStorage and sends as
    # `Authorization: Bearer <token>` on protected requests.
    token: str


class DocumentUploadResponse(BaseModel):
    document_id: str


class JobResult(BaseModel):
    pptx_url: str | None
    pdf_url: str | None
    preview_images: list[str] | None


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float | None
    message: str | None
    result: JobResult | None
    created_at: str


class HealthResponse(BaseModel):
    ok: bool


# --- Analytics ---

class TrackEventRequest(BaseModel):
    """Payload from frontend tracker. Kept open-ended for future events."""

    session_id: str = Field(min_length=8, max_length=64)
    event_type: str = Field(min_length=1, max_length=64)
    metadata: dict | None = None

    model_config = ConfigDict(extra="forbid")


class TrackEventResponse(BaseModel):
    ok: bool


class FunnelStep(BaseModel):
    step: str
    sessions: int
    conversion_from_previous: float | None  # null for the first step


class TrendPoint(BaseModel):
    date: str  # ISO date "YYYY-MM-DD"
    count: int


class BreakdownItem(BaseModel):
    value: str
    count: int


class ErrorRow(BaseModel):
    message: str
    count: int


class ProductMetricsKpi(BaseModel):
    total_jobs: int
    jobs_7d: int
    jobs_30d: int
    success_rate: float
    error_rate: float
    avg_slides: float
    rag_usage_ratio: float


class ProductMetricsResponse(BaseModel):
    period_days: int
    generated_at: str
    kpi: ProductMetricsKpi
    funnel: list[FunnelStep]
    trend: list[TrendPoint]
    breakdowns: dict[str, list[BreakdownItem]]
    top_errors: list[ErrorRow]


# --- Infrastructure / Tech dashboard ---

class SystemMetrics(BaseModel):
    cpu_pct: float | None = None
    ram_used_pct: float | None = None
    ram_used_mb: int | None = None
    ram_total_mb: int | None = None
    disk_used_pct: float | None = None
    disk_used_gb: float | None = None
    disk_total_gb: float | None = None
    server_uptime_seconds: int | None = None
    error: str | None = None


class ServiceInfo(BaseModel):
    status: str  # "active" | "failed" | "unknown"
    sub_state: str
    restarts_total: int
    service_uptime_seconds: int | None = None


class NginxInfo(BaseModel):
    active_connections: int


class LatencyPercentiles(BaseModel):
    p50: float | None
    p95: float | None
    p99: float | None


class EndpointStat(BaseModel):
    endpoint: str
    count: int
    p50_ms: float | None
    p95_ms: float | None
    p99_ms: float | None


class HourlyPoint(BaseModel):
    hour: str   # "2025-05-31T14:00"
    count: int


class StatusCodeCount(BaseModel):
    status_code: int
    count: int


class RecentErrorEntry(BaseModel):
    endpoint: str
    method: str
    status_code: int
    ts: str


class ApiMetrics(BaseModel):
    window_hours: int
    total_requests: int
    rps_1h: float | None
    rps_24h: float | None
    error_rate_4xx: float
    error_rate_5xx: float
    latency: LatencyPercentiles
    slowest_endpoints: list[EndpointStat]
    hourly_trend: list[HourlyPoint]
    status_breakdown: list[StatusCodeCount]
    recent_errors: list[RecentErrorEntry]


class GenerationPerf(BaseModel):
    avg_duration_s: float | None
    p95_duration_s: float | None
    p99_duration_s: float | None
    sample_count: int
    queue_depth: int


class SparklinePoint(BaseModel):
    label: str   # "-0м", "-1м", ... "-14м"
    count: int


class LiveMetricsResponse(BaseModel):
    ts: str
    generate_last_1m: int
    generate_last_5m: int
    generate_last_15m: int
    generate_last_60m: int
    running_jobs: int
    queued_jobs: int
    sparkline_15m: list[SparklinePoint]


class InfraMetricsResponse(BaseModel):
    generated_at: str
    system: SystemMetrics
    service: ServiceInfo
    nginx: NginxInfo | None = None
    api: ApiMetrics
    generation: GenerationPerf
