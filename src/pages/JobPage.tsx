import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { type JobStatus, getJobStatus } from "@/lib/api";
import { updateHistoryStatus } from "@/lib/history";
import { track } from "@/lib/analytics";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import JobStatusCard from "@/components/JobStatusCard";
import PreviewGallery from "@/components/PreviewGallery";
import DownloadButtons from "@/components/DownloadButtons";
import ShareLink from "@/components/ShareLink";
import { useLanguage } from "@/context/LanguageContext";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function JobPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { t } = useLanguage();
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Ensures we fire `job_done` exactly once per page visit, even if polling races.
  const reportedRef = useRef<boolean>(false);

  useEffect(() => {
    if (!jobId) return;
    reportedRef.current = false;

    const fetchStatus = async () => {
      try {
        const status = await getJobStatus(jobId);
        setJob(status);
        updateHistoryStatus(jobId, status.status);

        if (status.status === "done" || status.status === "error") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          if (!reportedRef.current) {
            reportedRef.current = true;
            // Final funnel step — used to compute end-to-end conversion in the dashboard.
            track("job_done", { job_id: jobId, status: status.status });
          }
        }
      } catch (err: any) {
        setError(err.message || t("job.statusError"));
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    };

    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, 2500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // `t` is intentionally omitted: switching language mid-poll should not
    // restart the interval, and the message is only read on failure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  if (!jobId) return <NotFoundState />;

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex-1 px-4 py-12 sm:py-16">
        <div className="container max-w-3xl space-y-6">
          {error ? (
            <div className="space-y-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-8 text-center">
              <p role="alert" className="font-medium text-destructive">
                {error}
              </p>
              <Button asChild variant="outline" className="h-11 rounded-full px-6">
                <Link to="/generate">{t("job.back")}</Link>
              </Button>
            </div>
          ) : !job ? (
            <div className="space-y-4">
              <Skeleton className="h-40 rounded-2xl" />
              <Skeleton className="h-8 w-48 rounded-full" />
            </div>
          ) : (
            <>
              <Reveal>
                <JobStatusCard job={job} />
              </Reveal>
              <Reveal delay={80}>
                <ShareLink jobId={job.job_id} />
              </Reveal>

              {job.status === "done" && job.result && (
                <>
                  <Reveal delay={140}>
                    <DownloadButtons pptxUrl={job.result.pptx_url} pdfUrl={job.result.pdf_url} />
                  </Reveal>
                  {job.result.preview_images && job.result.preview_images.length > 0 && (
                    <Reveal delay={200}>
                      <PreviewGallery images={job.result.preview_images} />
                    </Reveal>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function NotFoundState() {
  const { t } = useLanguage();
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />
      <main className="flex flex-1 items-center justify-center px-4">
        <div className="space-y-4 text-center">
          <h1 className="font-display text-2xl font-bold">{t("job.notFound")}</h1>
          <p className="text-sm text-muted-foreground">{t("job.notFoundHint")}</p>
          <Button asChild className="h-11 rounded-full px-6">
            <Link to="/generate">{t("history.emptyCta")}</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
