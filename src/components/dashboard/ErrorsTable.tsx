import type { ErrorRow } from "@/lib/dashboard-api";

interface Props {
  rows: ErrorRow[];
}

/**
 * Heuristic categorizer based on substring matches.
 * Keeps the dashboard self-contained; backend doesn't need to know about UI labels.
 */
function categorize(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("llm") || lower.includes("spec.generate") || lower.includes("rate limit"))
    return "LLM";
  if (lower.includes("document") || lower.includes("rag") || lower.includes("indexing"))
    return "RAG";
  if (lower.includes("render") || lower.includes("playwright") || lower.includes("pdf"))
    return "RENDER";
  if (lower.includes("storage") || lower.includes("upload") || lower.includes("supabase"))
    return "STORAGE";
  return "OTHER";
}

export default function ErrorsTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="rounded-md bg-secondary/40 px-4 py-8 text-center text-sm text-muted-foreground">
        Ошибок за выбранный период нет
      </div>
    );
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr>
          <th className="border-b py-2.5 px-3 text-left text-[11px] uppercase tracking-wider text-muted-foreground font-medium w-14">
            #
          </th>
          <th className="border-b py-2.5 px-3 text-left text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
            Сообщение
          </th>
          <th className="border-b py-2.5 px-3 text-right text-[11px] uppercase tracking-wider text-muted-foreground font-medium w-24">
            Кол-во
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const category = categorize(row.message);
          return (
            <tr key={i}>
              <td className="border-b py-2.5 px-3 text-muted-foreground">{i + 1}</td>
              <td className="border-b py-2.5 px-3">
                <span className="mr-2 inline-block rounded bg-destructive/15 px-2 py-0.5 text-[11px] font-medium text-destructive">
                  {category}
                </span>
                {row.message}
              </td>
              <td className="border-b py-2.5 px-3 text-right font-semibold tabular-nums">
                {row.count}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
