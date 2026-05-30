import type { FunnelStep } from "@/lib/dashboard-api";

interface Props {
  steps: FunnelStep[];
}

const STEP_LABELS: Record<string, string> = {
  page_view: "Зашли на сайт",
  cta_click: "Нажали «Попробовать»",
  generate_click: "Нажали «Сгенерировать»",
  job_done: "Презентация готова",
};

function fmt(value: number): string {
  return value.toLocaleString("ru-RU").replace(",", " ");
}

export default function FunnelView({ steps }: Props) {
  const top = steps[0]?.sessions ?? 0;
  const last = steps.length > 0 ? steps[steps.length - 1].sessions : 0;
  const overall = top > 0 ? (last / top) * 100 : 0;

  const drops: string[] = [];
  for (let i = 1; i < steps.length; i++) {
    const prev = steps[i - 1].sessions;
    const cur = steps[i].sessions;
    const drop = prev > 0 ? Math.round(((cur - prev) / prev) * 100) : 0;
    drops.push(`${drop}%`);
  }

  return (
    <div className="space-y-3">
      {steps.map((s, idx) => {
        const widthPct = top > 0 ? (s.sessions / top) * 100 : 0;
        const conv = s.conversion_from_previous;
        return (
          <div
            key={s.step}
            className="grid grid-cols-[150px_1fr_70px] items-center gap-3"
          >
            <div className="text-sm font-medium">{STEP_LABELS[s.step] ?? s.step}</div>
            <div className="relative h-8 overflow-hidden rounded-md bg-secondary">
              <div
                className="flex h-full min-w-[40px] items-center px-3 text-xs font-semibold text-primary-foreground"
                style={{
                  width: `${Math.max(widthPct, 4)}%`,
                  background:
                    "linear-gradient(90deg, hsl(var(--primary)) 0%, hsl(var(--accent)) 100%)",
                }}
              >
                {fmt(s.sessions)}
              </div>
            </div>
            <div
              className={`text-right text-sm font-semibold ${
                idx === 0 ? "text-muted-foreground font-normal" : "text-success"
              }`}
            >
              {idx === 0 ? "—" : `${Math.round((conv ?? 0) * 100)}%`}
            </div>
          </div>
        );
      })}

      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-dashed pt-4">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground">
            Общая конверсия (от посетителей)
          </div>
          <div className="mt-1 text-xl font-bold tracking-tight">{overall.toFixed(1)}%</div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">
            {fmt(top)} посетителей → {fmt(last)} готовых презентаций
          </div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted-foreground">
            Дроп между шагами
          </div>
          <div className="mt-1 text-xl font-bold tracking-tight">
            {drops.length > 0 ? drops.join(" / ") : "—"}
          </div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">
            от шага к шагу
          </div>
        </div>
      </div>
    </div>
  );
}
