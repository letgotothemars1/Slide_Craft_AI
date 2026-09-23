import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import AppHeader from "@/components/AppHeader";
import { useLanguage } from "@/context/LanguageContext";
import { formatRelativeSeconds, type TranslationKey } from "@/lib/i18n";
import { fetchProductMetrics, invalidateMetricsCache } from "@/lib/dashboard-api";
import KpiCard from "@/components/dashboard/KpiCard";
import TrendChart from "@/components/dashboard/TrendChart";
import FunnelView from "@/components/dashboard/FunnelView";
import DonutBreakdown from "@/components/dashboard/DonutBreakdown";
import ErrorsTable from "@/components/dashboard/ErrorsTable";

const POLL_MS = 30_000;
const PERIODS: { key: TranslationKey; value: number }[] = [
  { key: "dash.period7", value: 7 },
  { key: "dash.period30", value: 30 },
  { key: "dash.period90", value: 90 },
];

function formatPercent(v: number): string {
  return `${Math.round(v * 100)}%`;
}

export default function DashboardPage() {
  const { t, language } = useLanguage();
  const [periodDays, setPeriodDays] = useState<number>(30);
  const [now, setNow] = useState<Date>(new Date());

  const query = useQuery({
    queryKey: ["product-metrics", periodDays],
    queryFn: () => fetchProductMetrics(periodDays),
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: true,
    staleTime: POLL_MS - 1_000,
  });

  // Tick a clock once per second so "обновлено N сек назад" stays live.
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const lastUpdatedAt = useMemo(() => {
    if (!query.dataUpdatedAt) return null;
    return new Date(query.dataUpdatedAt);
  }, [query.dataUpdatedAt]);

  const handleRefresh = () => {
    invalidateMetricsCache();
    query.refetch();
  };

  const data = query.data;

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />

      <main className="container mx-auto max-w-[1280px] py-8">
        {/* Title + controls */}
        <div className="mb-7 flex items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight">
              {t("dash.productTitle")}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">{t("dash.productSubtitle")}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-1.5 text-xs text-muted-foreground">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
              </span>
              <span>
                {t("dash.autoRefresh30")} ·{" "}
                <b className="text-foreground">
                  {lastUpdatedAt
                    ? `${t("dash.updated")} ${formatRelativeSeconds(
                        (now.getTime() - lastUpdatedAt.getTime()) / 1000,
                        language,
                      )}`
                    : t("dash.loading")}
                </b>
              </span>
            </div>

            <div className="flex rounded-lg border bg-card p-0.5">
              {PERIODS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPeriodDays(p.value)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    periodDays === p.value
                      ? "bg-foreground text-background"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t(p.key)}
                </button>
              ))}
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

        {/* Loading state */}
        {!data && !query.isError && (
          <div className="grid grid-cols-5 gap-4">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="h-[110px] animate-pulse rounded-xl border bg-card" />
            ))}
          </div>
        )}

        {data && (
          <>
            {/* KPI row */}
            <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
              <KpiCard
                label="Всего презентаций"
                value={data.kpi.total_jobs.toLocaleString("ru-RU")}
                sub={`+${data.kpi.jobs_7d} за 7 дней · +${data.kpi.jobs_30d} за 30 дней`}
                helpText="За всё время. Подписи снизу — за скользящие окна 7 / 30 дней."
              />
              <KpiCard
                label="Success rate"
                value={formatPercent(data.kpi.success_rate)}
                helpText="Процент джобов со статусом 'done' от общего количества."
              />
              <KpiCard
                label="Error rate"
                value={formatPercent(data.kpi.error_rate)}
                helpText="Процент джобов со статусом 'error' от общего количества."
              />
              <KpiCard
                label="Среднее слайдов"
                value={data.kpi.avg_slides.toFixed(1)}
                sub="на одну презентацию"
              />
              <KpiCard
                label="RAG режим"
                value={formatPercent(data.kpi.rag_usage_ratio)}
                sub="с прикреплённым PDF"
              />
            </div>

            {/* Trend + Funnel */}
            <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[2fr_1fr]">
              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold tracking-tight">Презентации по дням</h2>
                <p className="mt-1 mb-4 text-xs text-muted-foreground">
                  Скользящее окно · последние {data.period_days} дней · создано джобов в сутки
                </p>
                <TrendChart data={data.trend} />
              </div>
              <div className="rounded-xl border bg-card p-6">
                <h2 className="text-base font-semibold tracking-tight">Воронка</h2>
                <p className="mt-1 mb-4 text-xs text-muted-foreground">
                  Уникальных сессий за {data.period_days} дней · процент = конверсия с прошлого шага
                </p>
                <FunnelView steps={data.funnel} />
              </div>
            </div>

            {/* Breakdowns */}
            <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <DonutBreakdown title="Формат" hint="PDF / PPTX / Both" items={data.breakdowns.format} />
              <DonutBreakdown title="Язык" hint="ru / en" items={data.breakdowns.language} />
              <DonutBreakdown
                title="Стиль"
                hint="business / minimal / dark / creative"
                items={data.breakdowns.style}
              />
              <DonutBreakdown
                title="Аудитория"
                hint="executives / students / sales / investors / custom"
                items={data.breakdowns.audience}
              />
            </div>

            {/* Top errors */}
            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-base font-semibold tracking-tight">Топ ошибок</h2>
              <p className="mt-1 mb-4 text-xs text-muted-foreground">
                Самые частые причины падения за {data.period_days} дней
              </p>
              <ErrorsTable rows={data.top_errors} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
