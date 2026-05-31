import type { RecentErrorEntry } from "@/lib/infra-api";

interface Props {
  errors: RecentErrorEntry[];
}

function statusColor(code: number): string {
  if (code >= 500) return "text-destructive";
  if (code >= 400) return "text-amber-500";
  return "text-muted-foreground";
}

function formatTs(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("ru-RU", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function RecentErrorsTable({ errors }: Props) {
  if (errors.length === 0) {
    return (
      <p className="py-6 text-center text-xs text-muted-foreground">
        Ошибок нет 🎉
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="pb-2 pr-4 font-medium">Время</th>
            <th className="pb-2 pr-4 font-medium">Метод</th>
            <th className="pb-2 pr-4 font-medium">Эндпоинт</th>
            <th className="pb-2 font-medium">Код</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((e, i) => (
            <tr
              key={i}
              className="border-b border-border/50 last:border-0 hover:bg-secondary/30"
            >
              <td className="py-1.5 pr-4 font-mono text-muted-foreground">
                {formatTs(e.ts)}
              </td>
              <td className="py-1.5 pr-4 font-mono uppercase text-muted-foreground">
                {e.method}
              </td>
              <td className="max-w-[260px] truncate py-1.5 pr-4 font-mono" title={e.endpoint}>
                {e.endpoint}
              </td>
              <td className={`py-1.5 font-mono font-bold ${statusColor(e.status_code)}`}>
                {e.status_code}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
