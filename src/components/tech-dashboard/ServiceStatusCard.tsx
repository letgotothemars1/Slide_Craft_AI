import type { ServiceInfo, NginxInfo } from "@/lib/infra-api";

interface Props {
  service: ServiceInfo;
  nginx: NginxInfo | null;
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

function StatusBadge({ status }: { status: string }) {
  const isActive = status === "active";
  const isFailed = status === "failed";
  const color = isActive
    ? "bg-success/15 text-success border-success/30"
    : isFailed
    ? "bg-destructive/15 text-destructive border-destructive/30"
    : "bg-secondary text-muted-foreground border-border";
  const dot = isActive
    ? "bg-success"
    : isFailed
    ? "bg-destructive"
    : "bg-muted-foreground";
  const label = isActive ? "active" : isFailed ? "failed" : status;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${color}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot} ${isActive ? "animate-pulse" : ""}`} />
      {label}
    </span>
  );
}

interface RowProps {
  label: string;
  value: React.ReactNode;
}

function Row({ label, value }: RowProps) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </div>
  );
}

export default function ServiceStatusCard({ service, nginx }: Props) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Сервис
      </h2>

      <div className="mt-4 flex items-center justify-between">
        <StatusBadge status={service.status} />
        <span className="text-xs text-muted-foreground">{service.sub_state}</span>
      </div>

      <div className="mt-4 flex flex-col gap-3 border-t pt-4">
        <Row
          label="Uptime сервиса"
          value={formatUptime(service.service_uptime_seconds)}
        />
        <Row
          label="Рестарты"
          value={
            <span
              className={service.restarts_total > 0 ? "text-amber-500" : ""}
            >
              {service.restarts_total}
            </span>
          }
        />
        {nginx !== null && (
          <Row
            label="Nginx подключений"
            value={nginx.active_connections}
          />
        )}
      </div>
    </div>
  );
}
