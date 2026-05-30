import { useMemo } from "react";
import type { TrendPoint } from "@/lib/dashboard-api";

interface Props {
  data: TrendPoint[];
}

/**
 * Pure-SVG line chart with filled area gradient and lightweight axes.
 * No external chart library — keeps the bundle small and works offline.
 */
export default function TrendChart({ data }: Props) {
  const view = useMemo(() => {
    const W = 600;
    const H = 280;
    const padL = 36, padR = 12, padT = 18, padB = 26;
    const innerW = W - padL - padR;
    const innerH = H - padT - padB;
    const counts = data.map((d) => d.count);
    const maxRaw = Math.max(1, ...counts);
    const maxV = maxRaw * 1.15;
    const xFor = (i: number) =>
      padL + (data.length <= 1 ? innerW / 2 : (i / (data.length - 1)) * innerW);
    const yFor = (v: number) => padT + innerH - (v / maxV) * innerH;

    const linePath = data
      .map((d, i) => `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(1)} ${yFor(d.count).toFixed(1)}`)
      .join(" ");
    const areaPath =
      data.length > 0
        ? `${linePath} L ${xFor(data.length - 1).toFixed(1)} ${padT + innerH} L ${padL} ${
            padT + innerH
          } Z`
        : "";

    const yTicks = Array.from({ length: 5 }, (_, i) => {
      const value = (maxV * i) / 4;
      const y = padT + innerH - (value / maxV) * innerH;
      return { value: Math.round(value), y };
    });

    const xTickStep = Math.max(1, Math.ceil(data.length / 6));
    const xTicks = data
      .map((d, i) => ({ x: xFor(i), label: d.date.slice(5), i }))
      .filter((_, i) => i % xTickStep === 0);

    return { W, H, padL, padR, padT, padB, linePath, areaPath, yTicks, xTicks };
  }, [data]);

  return (
    <svg
      viewBox={`0 0 ${view.W} ${view.H}`}
      preserveAspectRatio="none"
      className="h-[280px] w-full"
    >
      <defs>
        <linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="hsl(var(--primary))" stopOpacity={0.25} />
          <stop offset="1" stopColor="hsl(var(--primary))" stopOpacity={0} />
        </linearGradient>
      </defs>
      {view.yTicks.map((t, i) => (
        <g key={i}>
          <line
            x1={view.padL}
            y1={t.y}
            x2={view.W - view.padR}
            y2={t.y}
            stroke="hsl(var(--border))"
            strokeWidth={1}
          />
          <text
            x={view.padL - 6}
            y={t.y + 3}
            textAnchor="end"
            fontSize={10}
            fill="hsl(var(--muted-foreground))"
          >
            {t.value}
          </text>
        </g>
      ))}
      {view.areaPath && <path d={view.areaPath} fill="url(#trendArea)" />}
      {view.linePath && (
        <path
          d={view.linePath}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      )}
      {view.xTicks.map((t, i) => (
        <text
          key={i}
          x={t.x}
          y={view.H - 8}
          textAnchor="middle"
          fontSize={10}
          fill="hsl(var(--muted-foreground))"
        >
          {t.label}
        </text>
      ))}
    </svg>
  );
}
