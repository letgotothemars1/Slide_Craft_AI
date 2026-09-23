import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { clearHistory, getHistory, type HistoryEntry } from "@/lib/history";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import { useLanguage } from "@/context/LanguageContext";
import { formatDateTime, type TranslationKey } from "@/lib/i18n";
import { ExternalLink, Trash2, FileStack } from "lucide-react";

const STATUS_BADGE: Record<string, string> = {
  queued: "bg-muted text-muted-foreground",
  running: "bg-primary/10 text-primary",
  done: "bg-success/10 text-success-strong",
  error: "bg-destructive/10 text-destructive",
};

const STATUS_KEY: Record<string, TranslationKey> = {
  queued: "status.queued",
  running: "status.running",
  done: "status.done",
  error: "status.error",
};

export default function HistoryPage() {
  const { t, language } = useLanguage();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setEntries(getHistory());
  }, []);

  const handleClear = () => {
    clearHistory();
    setEntries([]);
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex-1 px-4 py-12 sm:py-16">
        <div className="container max-w-3xl">
          <Reveal className="mb-8 flex items-center justify-between gap-4">
            <h1 className="font-display text-2xl font-bold sm:text-3xl">{t("history.title")}</h1>
            {entries.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClear}
                className="h-11 gap-1.5 text-muted-foreground sm:h-9"
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                {t("history.clear")}
              </Button>
            )}
          </Reveal>

          {entries.length === 0 ? (
            <Reveal>
              <div className="space-y-4 rounded-2xl border border-border bg-card p-12 text-center shadow-card">
                <span className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-muted">
                  <FileStack className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
                </span>
                <p className="text-sm text-muted-foreground">{t("history.empty")}</p>
                <Button asChild className="h-11 rounded-full px-6">
                  <Link to="/generate">{t("history.emptyCta")}</Link>
                </Button>
              </div>
            </Reveal>
          ) : (
            <ul className="space-y-3">
              {entries.map((e, i) => (
                <Reveal as="li" key={e.job_id} delay={Math.min(i, 6) * 60}>
                  <Link
                    to={`/jobs/${e.job_id}`}
                    className="group flex items-center justify-between gap-4 rounded-xl border border-border bg-card p-4 shadow-card transition-shadow hover:shadow-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {e.prompt_snippet || t("history.noDescription")}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDateTime(e.created_at, language)}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <Badge variant="secondary" className={STATUS_BADGE[e.status] || ""}>
                        {STATUS_KEY[e.status] ? t(STATUS_KEY[e.status]) : e.status}
                      </Badge>
                      <ExternalLink
                        className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
                        aria-hidden="true"
                      />
                    </div>
                  </Link>
                </Reveal>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
