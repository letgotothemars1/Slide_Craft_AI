import type { JobStatus } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Clock, Loader2, CheckCircle2, XCircle } from "lucide-react";

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactNode; className: string }> = {
  queued: { label: "В очереди", icon: <Clock className="h-3.5 w-3.5" />, className: "bg-muted text-muted-foreground" },
  running: { label: "Генерация", icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />, className: "bg-primary/10 text-primary" },
  done: { label: "Готово", icon: <CheckCircle2 className="h-3.5 w-3.5" />, className: "bg-success/10 text-success" },
  error: { label: "Ошибка", icon: <XCircle className="h-3.5 w-3.5" />, className: "bg-destructive/10 text-destructive" },
};

interface Props {
  job: JobStatus;
}

export default function JobStatusCard({ job }: Props) {
  const cfg = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.queued;

  return (
    <div className="rounded-lg border bg-card p-5 shadow-card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Задача</h3>
        <Badge variant="secondary" className={cfg.className + " gap-1"}>
          {cfg.icon}
          {cfg.label}
        </Badge>
      </div>

      <p className="font-mono text-xs text-muted-foreground break-all">{job.job_id}</p>

      {job.progress != null && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Прогресс</span>
            <span>{job.progress}%</span>
          </div>
          <Progress value={job.progress} className="h-2" />
        </div>
      )}

      {job.message && (
        <p className="text-sm text-muted-foreground italic">{job.message}</p>
      )}

      <p className="text-xs text-muted-foreground">
        Создано: {new Date(job.created_at).toLocaleString("ru-RU")}
      </p>
    </div>
  );
}
