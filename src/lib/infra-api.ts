/**
 * Technical dashboard data-fetching layer.
 * Talks to GET /metrics/infra — returns system health, service state,
 * API performance metrics, and generation job stats.
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";

// ── types (mirror app/schemas.py) ──────────────────────────────────────────

export interface SystemMetrics {
  cpu_pct: number | null;
  ram_used_pct: number | null;
  ram_used_mb: number | null;
  ram_total_mb: number | null;
  disk_used_pct: number | null;
  disk_used_gb: number | null;
  disk_total_gb: number | null;
  server_uptime_seconds: number | null;
  error?: string;
}

export interface ServiceInfo {
  status: string; // "active" | "failed" | "unknown"
  sub_state: string;
  restarts_total: number;
  service_uptime_seconds: number | null;
}

export interface NginxInfo {
  active_connections: number;
}

export interface LatencyPercentiles {
  p50: number | null;
  p95: number | null;
  p99: number | null;
}

export interface EndpointStat {
  endpoint: string;
  count: number;
  p50_ms: number | null;
  p95_ms: number | null;
  p99_ms: number | null;
}

export interface HourlyPoint {
  hour: string; // "2025-05-31T14:00"
  count: number;
}

export interface StatusCodeCount {
  status_code: number;
  count: number;
}

export interface RecentErrorEntry {
  endpoint: string;
  method: string;
  status_code: number;
  ts: string;
}

export interface ApiMetrics {
  window_hours: number;
  total_requests: number;
  rps_1h: number | null;
  rps_24h: number | null;
  error_rate_4xx: number;
  error_rate_5xx: number;
  latency: LatencyPercentiles;
  slowest_endpoints: EndpointStat[];
  hourly_trend: HourlyPoint[];
  status_breakdown: StatusCodeCount[];
  recent_errors: RecentErrorEntry[];
}

export interface GenerationPerf {
  avg_duration_s: number | null;
  p95_duration_s: number | null;
  p99_duration_s: number | null;
  sample_count: number;
  queue_depth: number;
}

export interface InfraMetrics {
  generated_at: string;
  system: SystemMetrics;
  service: ServiceInfo;
  nginx: NginxInfo | null;
  api: ApiMetrics;
  generation: GenerationPerf;
}

// ── fetcher ────────────────────────────────────────────────────────────────

const CACHE_TTL_MS = 15_000;
let cache: { ts: number; data: InfraMetrics } | null = null;

export async function fetchInfraMetrics(): Promise<InfraMetrics> {
  const now = Date.now();
  if (cache && now - cache.ts < CACHE_TTL_MS) return cache.data;

  const res = await fetch(`${API_BASE}/metrics/infra`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Infra API ${res.status}: ${text || res.statusText}`);
  }
  const data = (await res.json()) as InfraMetrics;
  cache = { ts: Date.now(), data };
  return data;
}

export function invalidateInfraCache(): void {
  cache = null;
}
