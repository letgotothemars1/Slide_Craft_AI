import type { SystemMetrics } from "@/lib/infra-api";

interface Props {
  data: SystemMetrics;
}

function formatUptime(seconds: number | null): string {
  if (seconds === null || seconds < 0) return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}д ${h}ч ${m}м`;
  if (h > 0) return `${h}ч ${m}м`;
  return `${m}м`;
}

type AlertLevel = "ok" | "warn" | "crit";

function gaugeAlert(pct: number, warnAt = 70, critAt = 90): AlertLevel {
  if (pct >= critAt) return "crit";
  if (pct >= warnAt) return "warn";
  return "ok";
}

const GAUGE_COLORS: Record<AlertLevel, string> = {
  ok:   "#22c55e",
  warn: "#f59e0b",
  crit: "#ef4444",
};

const GAUGE_TEXT: Record<AlertLevel, string> = {
  ok:   "",
  warn: "text-amber-600",
  crit: "text-red-600",
};

const GAUGE_BADGE: Record<AlertLevel, string> = {
  ok:   "hidden",
  warn: "inline-flex bg-amber-100 text-amber-700 border border-amber-300",
  crit: "inline-flex bg-red-100 text-red-700 border border-red-300",
};

interface GaugeBarProps {
  label: string;
  pct: number | null;
  sub?: string;
  warnAt?: number;
  critAt?: number;
}

function GaugeBar({ label, pct, sub, warnAt = 70, critAt = 90 }: GaugeBarProps) {
  const value = pct ?? 0;
  const level = pct !== null ? gaugeAlert(value, warnAt, critAt) : "ok";
  const color = GAUGE_COLORS[level];

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <div className="flex items-center gap-1.5">
          {level !== "ok" && (
            <span className={`rounded px-1 py-0.5 text-[9px] font-bold uppercase tracking-wide ${GAUGE_BADGE[level]}`}>
              {level}
            </span>
          )}
          <span className={`font-mono font-medium ${GAUGE_TEXT[level]}`}>
            {pct !== null ? `${value.toFixed(1)}%` : "—"}
          </span>
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(100, value)}%`, background: color }}
        />
      </div>
      {sub && (
        <div className="mt-0.5 text-right text-[10px] text-muted-foreground">{sub}</div>
      )}
    </div>
  );
}

export default function SystemHealthCard({ data }: Props) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Системные ресурсы
      </h2>

      {data.error && (
        <p className="mt-2 text-xs text-destructive">⚠ {data.error}</p>
      )}

      <div className="mt-4 flex flex-col gap-4">
        <GaugeBar label="CPU" pct={data.cpu_pct} warnAt={70} critAt={90} />
        <GaugeBar
          label="RAM"
          pct={data.ram_used_pct}
          warnAt={80} critAt={95}
          sub={
            data.ram_used_mb !== null && data.ram_total_mb !== null
              ? `${Math.round(data.ram_used_mb / 1024 * 10) / 10} / ${Math.round(data.ram_total_mb / 1024 * 10) / 10} ГБ`
              : undefined
          }
        />
        <GaugeBar
          label="Диск"
          pct={data.disk_used_pct}
          warnAt={80} critAt={95}
          sub={
            data.disk_used_gb !== null && data.disk_total_gb !== null
              ? `${data.disk_used_gb} / ${data.disk_total_gb} ГБ`
              : undefined
          }
        />
      </div>

      <div className="mt-5 border-t pt-4">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Uptime сервера</span>
          <span className="font-mono font-medium">
            {formatUptime(data.server_uptime_seconds)}
          </span>
        </div>
      </div>
    </div>
  );
}
