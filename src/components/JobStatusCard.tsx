import type { JobStatus } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useLanguage } from "@/context/LanguageContext";
import { formatDateTime, type TranslationKey } from "@/lib/i18n";
import { Clock, Loader2, CheckCircle2, XCircle } from "lucide-react";

const STATUS_CONFIG: Record<string, { key: TranslationKey; icon: React.ReactNode; className: string }> = {
  queued: {
    key: "status.queued",
    icon: <Clock className="h-3.5 w-3.5" aria-hidden="true" />,
    className: "bg-muted text-muted-foreground",
  },
  running: {
    key: "status.running",
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />,
    className: "bg-primary/10 text-primary",
  },
  done: {
    key: "status.done",
    icon: <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />,
    className: "bg-success/10 text-success-strong",
  },
  error: {
    key: "status.error",
    icon: <XCircle className="h-3.5 w-3.5" aria-hidden="true" />,
    className: "bg-destructive/10 text-destructive",
  },
};

interface Props {
  job: JobStatus;
}

export default function JobStatusCard({ job }: Props) {
  const { t, language } = useLanguage();
  const cfg = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.queued;

  return (
    <div className="space-y-4 rounded-2xl border border-border bg-card p-6 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium text-muted-foreground">{t("job.task")}</h2>
        {/* aria-live: the badge changes on its own while polling, and a screen
            reader should hear "Done" without the user re-reading the page. */}
        <Badge variant="secondary" aria-live="polite" className={cfg.className + " gap-1"}>
          {cfg.icon}
          {t(cfg.key)}
        </Badge>
      </div>

      <p className="break-all font-mono text-xs text-muted-foreground">{job.job_id}</p>

      {job.progress != null && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{t("job.progress")}</span>
            <span className="tabular-nums">{job.progress}%</span>
          </div>
          <Progress value={job.progress} className="h-2" />
        </div>
      )}

      {job.message && <p className="text-sm text-muted-foreground">{job.message}</p>}

      <p className="text-xs text-muted-foreground">
        {t("job.created")}: {formatDateTime(job.created_at, language)}
      </p>
    </div>
  );
}
