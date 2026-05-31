import type { EndpointStat } from "@/lib/infra-api";

interface Props {
  endpoints: EndpointStat[];
}

function msLabel(ms: number | null): string {
  if (ms === null) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

function latencyColor(ms: number | null): string {
  if (ms === null) return "bg-secondary";
  if (ms < 200) return "bg-success/60";
  if (ms < 1000) return "bg-amber-400/60";
  return "bg-destructive/60";
}

export default function LatencyTable({ endpoints }: Props) {
  if (endpoints.length === 0) {
    return (
      <p className="py-4 text-center text-xs text-muted-foreground">
        Нет данных — запросы появятся после первых обращений к API
      </p>
    );
  }

  const maxP95 = Math.max(1, ...endpoints.map((e) => e.p95_ms ?? 0));

  return (
    <div className="flex flex-col gap-2">
      {endpoints.map((ep, i) => (
        <div key={i} className="group flex items-center gap-3">
          {/* Endpoint name */}
          <span
            className="w-44 shrink-0 truncate text-xs text-muted-foreground group-hover:text-foreground"
            title={ep.endpoint}
          >
            {ep.endpoint}
          </span>

          {/* Bar (p95) */}
          <div className="relative h-5 flex-1 overflow-hidden rounded bg-secondary">
            <div
              className={`h-full rounded transition-all duration-500 ${latencyColor(ep.p95_ms)}`}
              style={{
                width: `${((ep.p95_ms ?? 0) / maxP95) * 100}%`,
              }}
            />
            <span className="absolute inset-0 flex items-center px-2 text-[10px] font-mono font-semibold">
              p95 {msLabel(ep.p95_ms)}
            </span>
          </div>

          {/* Count + p50 */}
          <div className="w-28 shrink-0 text-right text-[10px] text-muted-foreground">
            <span className="font-mono">{ep.count.toLocaleString("ru-RU")}</span> req ·{" "}
            <span className="font-mono">p50 {msLabel(ep.p50_ms)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
