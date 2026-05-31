import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Server, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchInfraMetrics, invalidateInfraCache } from "@/lib/infra-api";
import SystemHealthCard from "@/components/tech-dashboard/SystemHealthCard";
import ServiceStatusCard from "@/components/tech-dashboard/ServiceStatusCard";
import HourlyChart from "@/components/tech-dashboard/HourlyChart";
import LatencyTable from "@/components/tech-dashboard/LatencyTable";
import GenerationPerfCard from "@/components/tech-dashboard/GenerationPerfCard";
import RecentErrorsTable from "@/components/tech-dashboard/RecentErrorsTable";
import LiveActivityWidget from "@/components/tech-dashboard/LiveActivityWidget";

const POLL_MS = 30_000;

function formatPercent(v: number): string {
  return `${Math.round(v * 100)}%`;
}

function formatRps(rps: number | null): string {
  if (rps === null) return "—";
  if (rps < 0.001) return "< 0.001 req/s";
  return `${rps.toFixed(3)} req/s`;
}

function formatRelative(date: Date): string {
  const diff = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (diff < 5) return "только что";
  if (diff < 60) return `${diff} сек назад`;
  const min = Math.floor(diff / 60);
  if (min < 60) return `${min} мин назад`;
  return `${Math.floor(min / 60)} ч назад`;
}

type AlertLevel = "ok" | "warn" | "crit";

function alertLevel(value: number, warnThreshold: number, critThreshold: number): AlertLevel {
  if (value >= critThreshold) return "crit";
  if (value >= warnThreshold) return "warn";
  return "ok";
}

interface KpiProps {
  label: string;
  value: React.ReactNode;
  sub?: string;
  alert?: AlertLevel;
  badge?: string; // short label shown top-right: "WARN" / "CRIT"
}

function KpiTile({ label, value, sub, alert = "ok", badge }: KpiProps) {
  const styles: Record<AlertLevel, { card: string; value: string; badge: string }> = {
    ok:   { card: "border-border bg-card",                         value: "",                   badge: "" },
    warn: { card: "border-amber-400 bg-amber-50/60",               value: "text-amber-600",     badge: "bg-amber-100 text-amber-700 border-amber-300" },
    crit: { card: "border-red-400 bg-red-50/60",                   value: "text-red-600",       badge: "bg-red-100 text-red-700 border-red-300" },
  };
  const s = styles[alert];

  return (
    <div className={`relative rounded-xl border p-5 transition-colors duration-300 ${s.card}`}>
      {alert !== "ok" && (
        <span className={`absolute right-3 top-3 rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${s.badge}`}>
          {badge ?? (alert === "crit" ? "CRIT" : "WARN")}
        </span>
      )}
      <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className={`mt-2 text-3xl font-bold leading-none tracking-tight ${s.value}`}>
        {value}
      </div>
      {sub && <div className="mt-2 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export default function TechDashboardPage() {
  const [now, setNow] = useState(new Date());

  const query = useQuery({
    queryKey: ["infra-metrics"],
    queryFn: fetchInfraMetrics,
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: true,
    staleTime: POLL_MS - 1_000,
  });

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const lastUpdated = useMemo(
    () => (query.dataUpdatedAt ? new Date(query.dataUpdatedAt) : null),
    [query.dataUpdatedAt],
  );

  const handleRefresh = () => {
    invalidateInfraCache();
    query.refetch();
  };

  const data = query.data;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-card/80 backdrop-blur-sm">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-lg">
            <Server className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Product
            </Link>
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
              На главную
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-[1280px] py-8">
        {/* Title row */}
        <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-display font-bold tracking-tight">
              SlideCraft AI — Technical Dashboard
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Системные ресурсы, API производительность, статус сервиса
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-1.5 text-xs text-muted-foreground">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
              </span>
              Auto-refresh 30 сек ·{" "}
              <b className="text-foreground">
                {lastUpdated ? formatRelative(lastUpdated) : "загрузка…"}
              </b>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={query.isFetching}
            >
              <RefreshCw
                className={`mr-1.5 h-3.5 w-3.5 ${query.isFetching ? "animate-spin" : ""}`}
              />
              Сейчас
            </Button>
          </div>
        </div>

        {/* Error state */}
        {query.isError && (
          <div className="mb-6 rounded-xl border border-destructive/40 bg-destructive/5 p-6 text-sm text-destructive">
            Ошибка загрузки метрик: {String((query.error as Error)?.message || "unknown")}
          </div>
        )}

        {/* Skeleton */}
        {!data && !query.isError && (
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="h-[180px] animate-pulse rounded-xl border bg-card" />
            ))}
          </div>
        )}

        {/* ── Live widget (always shown, independent of main data) ── */}
        <div className="mb-6">
          <LiveActivityWidget />
        </div>

        {data && (
          <>
            {/* ── Row 1: System + Service + API KPIs ── */}
            <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* System card spans 1 col */}
              <SystemHealthCard data={data.system} />
              <ServiceStatusCard service={data.service} nginx={data.nginx} />
              <KpiTile
                label="Запросов за 24ч"
                value={data.api.total_requests.toLocaleString("ru-RU")}
                sub={`RPS 1ч: ${formatRps(data.api.rps_1h)} · 24ч: ${formatRps(data.api.rps_24h)}`}
              />
              <KpiTile
                label="Error rate 5xx"
                value={formatPercent(data.api.error_rate_5xx)}
                sub={`4xx: ${formatPercent(data.api.error_rate_4xx)}`}
                alert={alertLevel(data.api.error_rate_5xx, 0.02, 0.10)}
              />
            </div>

            {/* ── Row 2: Latency KPIs ── */}
            <div className="mb-6 grid grid-cols-3 gap-4">
              <KpiTile
                label="Latency p50"
                value={
                  data.api.latency.p50 !== null
                    ? `${Math.round(data.api.latency.p50)}ms`
                    : "—"
                }
                sub="медиана API ответов"
                alert={alertLevel(data.api.latency.p50 ?? 0, 500, 2000)}
              />
              <KpiTile
                label="Latency p95"
                value={
                  data.api.latency.p95 !== null
                    ? `${Math.round(data.api.latency.p95)}ms`
                    : "—"
                }
                sub="95-й перцентиль"
                alert={alertLevel(data.api.latency.p95 ?? 0, 1000, 5000)}
              />
              <KpiTile
                label="Latency p99"
                value={
                  data.api.latency.p99 !== null
                    ? `${Math.round(data.api.latency.p99)}ms`
                    : "—"
                }
                sub="99-й перцентиль"
                alert={alertLevel(data.api.latency.p99 ?? 0, 2000, 10000)}
              />
            </div>

            {/* ── Row 3: Hourly chart + Slowest endpoints ── */}
            <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr]">
              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold tracking-tight">
                  Запросы по часам
                </h2>
                <p className="mt-1 mb-4 text-xs text-muted-foreground">
                  Последние 24 часа · все API эндпоинты
                </p>
                <HourlyChart data={data.api.hourly_trend} />
              </div>

              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold tracking-tight">
                  Самые медленные эндпоинты
                </h2>
                <p className="mt-1 mb-4 text-xs text-muted-foreground">
                  По p95 latency за 24 часа
                </p>
                <LatencyTable endpoints={data.api.slowest_endpoints} />
              </div>
            </div>

            {/* ── Row 4: Generation perf ── */}
            <div className="mb-6">
              <GenerationPerfCard data={data.generation} />
            </div>

            {/* ── Row 5: Status breakdown + Recent errors ── */}
            <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[200px_1fr]">
              {/* Status code breakdown */}
              <div className="rounded-xl border bg-card p-5">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                  HTTP статусы
                </h2>
                <div className="flex flex-col gap-2">
                  {data.api.status_breakdown.length === 0 ? (
                    <p className="text-xs text-muted-foreground">Нет данных</p>
                  ) : (
                    data.api.status_breakdown.map((s) => (
                      <div key={s.status_code} className="flex items-center justify-between text-xs">
                        <span
                          className={`font-mono font-semibold ${
                            s.status_code >= 500
                              ? "text-destructive"
                              : s.status_code >= 400
                              ? "text-amber-500"
                              : "text-success"
                          }`}
                        >
                          {s.status_code}
                        </span>
                        <span className="text-muted-foreground">
                          {s.count.toLocaleString("ru-RU")}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold tracking-tight">
                  Последние ошибки
                </h2>
                <p className="mt-1 mb-4 text-xs text-muted-foreground">
                  HTTP 4xx / 5xx за 24 часа · последние 20
                </p>
                <RecentErrorsTable errors={data.api.recent_errors} />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
