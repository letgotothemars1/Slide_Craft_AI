import { ReactNode } from "react";

interface Props {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  delta?: { value: string; positive?: boolean };
  helpText?: string;
}

export default function KpiCard({ label, value, sub, delta, helpText }: Props) {
  return (
    <div className="relative rounded-xl border bg-card p-5">
      {helpText && (
        <span
          title={helpText}
          className="absolute right-3 top-3 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full bg-secondary text-[10px] font-semibold text-muted-foreground hover:bg-secondary/70"
        >
          ?
        </span>
      )}
      <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-2 text-3xl font-bold leading-none tracking-tight">{value}</div>
      {delta && (
        <div
          className={`mt-2 text-xs font-medium ${
            delta.positive ? "text-success" : "text-destructive"
          }`}
        >
          {delta.value}
        </div>
      )}
      {sub && <div className="mt-2 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}
