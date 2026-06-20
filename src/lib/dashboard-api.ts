/**
 * Dashboard data fetching layer.
 *
 * - Talks to GET /metrics/product
 * - Tiny in-memory cache with TTL so repeated mounts (e.g. tab switching) don't
 *   spam the backend. React Query handles auto-refresh; this cache covers the
 *   pre-RQ initial render path.
 */

import { authHeader, handleUnauthorized } from "@/lib/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";

export interface FunnelStep {
  step: string;
  sessions: number;
  conversion_from_previous: number | null;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface BreakdownItem {
  value: string;
  count: number;
}

export interface ErrorRow {
  message: string;
  count: number;
}

export interface ProductMetricsKpi {
  total_jobs: number;
  jobs_7d: number;
  jobs_30d: number;
  success_rate: number;
  error_rate: number;
  avg_slides: number;
  rag_usage_ratio: number;
}

export interface ProductMetrics {
  period_days: number;
  generated_at: string;
  kpi: ProductMetricsKpi;
  funnel: FunnelStep[];
  trend: TrendPoint[];
  breakdowns: {
    format: BreakdownItem[];
    language: BreakdownItem[];
    style: BreakdownItem[];
    audience: BreakdownItem[];
  };
  top_errors: ErrorRow[];
}

const CACHE_TTL_MS = 15_000;
let cache: { key: string; ts: number; data: ProductMetrics } | null = null;

export async function fetchProductMetrics(periodDays: number): Promise<ProductMetrics> {
  const key = `period=${periodDays}`;
  const now = Date.now();
  if (cache && cache.key === key && now - cache.ts < CACHE_TTL_MS) {
    return cache.data;
  }

  const url = `${API_BASE}/metrics/product?period_days=${periodDays}`;
  const res = await fetch(url, {
    headers: { Accept: "application/json", ...authHeader() },
  });
  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Сессия истекла");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Metrics API ${res.status}: ${text || res.statusText}`);
  }
  const data = (await res.json()) as ProductMetrics;
  cache = { key, ts: Date.now(), data };
  return data;
}

export function invalidateMetricsCache(): void {
  cache = null;
}
