import { useMemo } from "react";
import type { HourlyPoint } from "@/lib/infra-api";

interface Props {
  data: HourlyPoint[];
}

/**
 * Pure-SVG bar chart showing request count per hour over the last 24h.
 * Mirrors the style of TrendChart but uses bars instead of a line.
 */
export default function HourlyChart({ data }: Props) {
  const view = useMemo(() => {
    const W = 600;
    const H = 200;
    const padL = 36;
    const padR = 8;
    const padT = 12;
    const padB = 24;
    const innerW = W - padL - padR;
    const innerH = H - padT - padB;

    const counts = data.map((d) => d.count);
    const maxRaw = Math.max(1, ...counts);
    const maxV = maxRaw * 1.2;

    const n = data.length;
    const barW = Math.max(2, (innerW / n) * 0.65);
    const gap = innerW / n;

    const bars = data.map((d, i) => {
      const barH = (d.count / maxV) * innerH;
      const x = padL + i * gap + (gap - barW) / 2;
      const y = padT + innerH - barH;
      return { x, y, w: barW, h: barH, count: d.count, hour: d.hour };
    });

    const yTicks = Array.from({ length: 4 }, (_, i) => {
      const value = (maxV * (i + 1)) / 4;
      const y = padT + innerH - (value / maxV) * innerH;
      return { value: Math.round(value), y };
    });

    // x-axis labels: every 4 hours
    const xLabels = data
      .map((d, i) => ({ i, label: d.hour.slice(11, 16) }))
      .filter((_, i) => i % 4 === 0);

    return { W, H, padL, padT, padB, innerH, bars, yTicks, xLabels };
  }, [data]);

  return (
    <svg
      viewBox={`0 0 ${view.W} ${view.H}`}
      preserveAspectRatio="none"
      className="h-[200px] w-full"
    >
      {/* Grid lines */}
      {view.yTicks.map((t, i) => (
        <g key={i}>
          <line
            x1={view.padL}
            y1={t.y}
            x2={view.W - 8}
            y2={t.y}
            stroke="hsl(var(--border))"
            strokeWidth={1}
          />
          <text
            x={view.padL - 4}
            y={t.y + 3}
            textAnchor="end"
            fontSize={9}
            fill="hsl(var(--muted-foreground))"
          >
            {t.value}
          </text>
        </g>
      ))}

      {/* Bars */}
      {view.bars.map((b, i) => (
        <rect
          key={i}
          x={b.x}
          y={b.y}
          width={b.w}
          height={Math.max(1, b.h)}
          rx={2}
          fill="hsl(var(--primary))"
          opacity={b.count === 0 ? 0.15 : 0.75}
        />
      ))}

      {/* X-axis labels */}
      {view.xLabels.map((t, i) => (
        <text
          key={i}
          x={view.padL + t.i * (view.W - view.padL - 8) / view.bars.length + (view.W - view.padL - 8) / view.bars.length / 2}
          y={view.H - 6}
          textAnchor="middle"
          fontSize={9}
          fill="hsl(var(--muted-foreground))"
        >
          {t.label}
        </text>
      ))}
    </svg>
  );
}
