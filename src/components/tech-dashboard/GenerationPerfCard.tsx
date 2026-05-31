import type { GenerationPerf } from "@/lib/infra-api";

interface Props {
  data: GenerationPerf;
}

function formatSec(s: number | null): string {
  if (s === null) return "—";
  if (s >= 60) return `${Math.floor(s / 60)}м ${Math.round(s % 60)}с`;
  return `${s.toFixed(1)}с`;
}

interface StatProps {
  label: string;
  value: string;
  warn?: boolean;
}

function Stat({ label, value, warn }: StatProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <span
        className={`font-mono text-xl font-bold leading-none ${
          warn ? "text-amber-500" : ""
        }`}
      >
        {value}
      </span>
    </div>
  );
}

export default function GenerationPerfCard({ data }: Props) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Генерация — производительность
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Время с момента создания джоба до завершения ·{" "}
        {data.sample_count.toLocaleString("ru-RU")} завершённых джобов
      </p>

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Среднее" value={formatSec(data.avg_duration_s)} />
        <Stat label="p95" value={formatSec(data.p95_duration_s)} />
        <Stat label="p99" value={formatSec(data.p99_duration_s)} />
        <Stat
          label="Очередь"
          value={String(data.queue_depth)}
          warn={data.queue_depth > 5}
        />
      </div>
    </div>
  );
}
