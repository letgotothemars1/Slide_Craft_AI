import { useEffect, useRef, useState } from "react";
import { authHeader, handleUnauthorized } from "@/lib/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";
const POLL_MS = 5_000;

interface SparklinePoint {
  label: string;
  count: number;
}

interface LiveMetrics {
  ts: string;
  generate_last_1m: number;
  generate_last_5m: number;
  generate_last_15m: number;
  generate_last_60m: number;
  running_jobs: number;
  queued_jobs: number;
  sparkline_15m: SparklinePoint[];
}

function Sparkline({ data }: { data: SparklinePoint[] }) {
  const maxVal = Math.max(1, ...data.map((d) => d.count));
  const H = 40;

  return (
    <svg viewBox={`0 0 ${data.length * 12} ${H}`} className="h-10 w-full" preserveAspectRatio="none">
      {data.map((d, i) => {
        const barH = Math.max(2, (d.count / maxVal) * (H - 4));
        const x = i * 12 + 1;
        const y = H - barH;
        const active = d.count > 0;
        return (
          <rect
            key={i}
            x={x} y={y}
            width={10} height={barH}
            rx={2}
            fill={active ? "#2563EB" : "#E2E8F0"}
            opacity={active ? 0.85 : 1}
          />
        );
      })}
    </svg>
  );
}

export default function LiveActivityWidget() {
  const [data, setData] = useState<LiveMetrics | null>(null);
  const [blink, setBlink] = useState(false);
  const prevCount = useRef<number>(0);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/metrics/live`, {
          headers: { Accept: "application/json", ...authHeader() },
        });
        if (res.status === 401) {
          handleUnauthorized();
          return;
        }
        if (!res.ok) throw new Error(`${res.status}`);
        const json = (await res.json()) as LiveMetrics;
        if (!alive) return;

        // Blink if new request came in since last poll
        if (json.generate_last_1m > prevCount.current) {
          setBlink(true);
          setTimeout(() => setBlink(false), 600);
        }
        prevCount.current = json.generate_last_1m;
        setData(json);
        setError(false);
      } catch {
        if (alive) setError(true);
      }
    };

    poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const isActive = data
    ? data.running_jobs > 0 || data.queued_jobs > 0 || data.generate_last_5m > 0
    : false;

  return (
    <div
      className={`rounded-xl border bg-card p-5 transition-colors duration-300 ${
        blink ? "border-primary/60 bg-primary/5" : ""
      }`}
    >
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            {isActive && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
            )}
            <span
              className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                isActive ? "bg-primary" : "bg-muted-foreground/40"
              }`}
            />
          </span>
          <span className="text-sm font-semibold">Live — запросы генерации</span>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {error ? "⚠ нет связи" : "обновление каждые 5с"}
        </span>
      </div>

      {/* Big counter + windows */}
      <div className="mb-4 flex items-end gap-6">
        <div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            сейчас / мин
          </div>
          <div
            className={`mt-1 font-mono text-4xl font-bold leading-none transition-colors duration-300 ${
              blink ? "text-primary" : ""
            }`}
          >
            {data ? data.generate_last_1m : "—"}
          </div>
        </div>

        <div className="flex flex-col gap-1 pb-1">
          <div className="flex items-center justify-between gap-8 text-xs">
            <span className="text-muted-foreground">за 5 мин</span>
            <span className="font-mono font-semibold">{data?.generate_last_5m ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between gap-8 text-xs">
            <span className="text-muted-foreground">за 15 мин</span>
            <span className="font-mono font-semibold">{data?.generate_last_15m ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between gap-8 text-xs">
            <span className="text-muted-foreground">за 60 мин</span>
            <span className="font-mono font-semibold">{data?.generate_last_60m ?? "—"}</span>
          </div>
        </div>

        {/* Queue */}
        <div className="ml-auto flex flex-col gap-1 pb-1 text-right">
          <div className="flex items-center justify-between gap-6 text-xs">
            <span className="text-muted-foreground">выполняется</span>
            <span
              className={`font-mono font-bold ${
                (data?.running_jobs ?? 0) > 0 ? "text-primary" : ""
              }`}
            >
              {data?.running_jobs ?? "—"}
            </span>
          </div>
          <div className="flex items-center justify-between gap-6 text-xs">
            <span className="text-muted-foreground">в очереди</span>
            <span
              className={`font-mono font-bold ${
                (data?.queued_jobs ?? 0) > 0 ? "text-amber-500" : ""
              }`}
            >
              {data?.queued_jobs ?? "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Sparkline */}
      {data && (
        <div>
          <div className="mb-1 flex justify-between text-[10px] text-muted-foreground">
            <span>−14м</span>
            <span>последние 15 минут (1 бар = 1 минута)</span>
            <span>сейчас</span>
          </div>
          <Sparkline data={data.sparkline_15m} />
        </div>
      )}

      {/* Skeleton while loading */}
      {!data && !error && (
        <div className="h-10 animate-pulse rounded bg-secondary" />
      )}
    </div>
  );
}
