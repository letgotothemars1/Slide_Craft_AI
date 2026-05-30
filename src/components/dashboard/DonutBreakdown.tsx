import { useMemo } from "react";
import type { BreakdownItem } from "@/lib/dashboard-api";

interface Props {
  title: string;
  hint?: string;
  items: BreakdownItem[];
}

const PALETTE = ["#2563EB", "#7C3AED", "#0EA5E9", "#F59E0B", "#16A34A"];

export default function DonutBreakdown({ title, hint, items }: Props) {
  const total = useMemo(() => items.reduce((a, b) => a + b.count, 0), [items]);

  const segments = useMemo(() => {
    if (total === 0) return [];
    const cx = 70, cy = 70, r = 55, thickness = 20;
    let startAngle = -Math.PI / 2;
    return items.map((item, i) => {
      const fraction = item.count / total;
      const angle = fraction * Math.PI * 2;
      const endAngle = startAngle + angle;
      const largeArc = angle > Math.PI ? 1 : 0;
      const x1 = cx + r * Math.cos(startAngle);
      const y1 = cy + r * Math.sin(startAngle);
      const x2 = cx + r * Math.cos(endAngle);
      const y2 = cy + r * Math.sin(endAngle);
      const d = `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${largeArc} 1 ${x2.toFixed(
        2
      )} ${y2.toFixed(2)}`;
      startAngle = endAngle;
      return {
        d,
        color: PALETTE[i % PALETTE.length],
        thickness,
        label: item.value,
        count: item.count,
        pct: Math.round(fraction * 100),
      };
    });
  }, [items, total]);

  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="text-base font-semibold tracking-tight">{title}</h3>
      {hint && <p className="mt-1 mb-4 text-xs text-muted-foreground">{hint}</p>}

      <div className="flex flex-col items-center">
        <svg viewBox="0 0 140 140" className="h-[140px] w-[140px]">
          {total === 0 ? (
            <circle cx="70" cy="70" r="55" fill="none" stroke="hsl(var(--border))" strokeWidth="20" />
          ) : (
            segments.map((seg, i) => (
              <path
                key={i}
                d={seg.d}
                stroke={seg.color}
                strokeWidth={seg.thickness}
                fill="none"
                strokeLinecap="butt"
              />
            ))
          )}
          <text
            x="70"
            y="68"
            textAnchor="middle"
            className="fill-foreground text-[20px] font-bold"
          >
            {total}
          </text>
          <text
            x="70"
            y="84"
            textAnchor="middle"
            className="fill-muted-foreground text-[10px] uppercase tracking-wider"
          >
            всего
          </text>
        </svg>

        <div className="mt-4 w-full space-y-1.5">
          {segments.length === 0 ? (
            <div className="text-center text-xs text-muted-foreground">Нет данных</div>
          ) : (
            segments.map((seg, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-sm"
                    style={{ background: seg.color }}
                  />
                  <span className="text-foreground">{seg.label}</span>
                </div>
                <span className="tabular-nums text-muted-foreground">{seg.pct}%</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
