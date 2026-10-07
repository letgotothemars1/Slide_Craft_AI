import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { type JobStatus, getJobStatus } from "@/lib/api";
import { updateHistoryStatus } from "@/lib/history";
import { track } from "@/lib/analytics";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import JobStatusCard from "@/components/JobStatusCard";
import SlideReviewWorkspace from "@/components/SlideReviewWorkspace";
import DraftSkeleton from "@/components/DraftSkeleton";
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
  // Bumped on approval to restart polling, which stops while the deck is being
  // edited — the status cannot change until the student approves.
  const [pollCycle, setPollCycle] = useState(0);

  useEffect(() => {
    if (!jobId) return;
    reportedRef.current = false;

    const fetchStatus = async () => {
      try {
        const status = await getJobStatus(jobId);
        setJob(status);
        updateHistoryStatus(jobId, status.status);

        if (status.status === "draft") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          return;
        }

        if (status.status === "done" || status.status === "error") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          if (!reportedRef.current) {
            reportedRef.current = true;
            // Final funnel step — used to compute end-to-end conversion in the dashboard.
            track("job_done", { job_id: jobId, status: status.status });
          }
        }
      } catch (err: unknown) {
        setError((err instanceof Error && err.message) || t("job.statusError"));
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
  }, [jobId, pollCycle]);

  if (!jobId) return <NotFoundState />;

  // The slide workspace — waiting, editing or finished — is the full-width
  // layout. Only the states that show a single card (loading, failure) read
  // better narrow, so the deck is never boxed into a column.
  const boxed = !!error || !job || job.status === "error";

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex-1 px-4 py-12 sm:py-16">
        <div className={`container space-y-6 ${boxed ? "max-w-3xl" : "max-w-[1500px]"}`}>
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
              {job.status === "queued" || job.status === "running" ? (
                <DraftSkeleton message={job.message} />
              ) : job.status === "draft" ? (
                <SlideReviewWorkspace
                  jobId={job.job_id}
                  // Approval restarts the pipeline, so polling has to resume.
                  onApproved={() => {
                    setJob({ ...job, status: "running" });
                    setPollCycle((cycle) => cycle + 1);
                  }}
                />
              ) : job.status === "done" ? (
                <SlideReviewWorkspace
                  jobId={job.job_id}
                  mode="final"
                  actions={
                    <DownloadButtons
                      pptxUrl={job.result?.pptx_url ?? null}
                      pdfUrl={job.result?.pdf_url ?? null}
                    />
                  }
                />
              ) : (
              <Reveal>
                <JobStatusCard job={job} />
              </Reveal>
              )}
              {job.status === "done" && (
                <Reveal delay={80}>
                  {/* Kept to a readable width: a link field stretched across the
                      full deck layout reads as an input box, not as a link. */}
                  <div className="max-w-xl">
                    <ShareLink jobId={job.job_id} />
                  </div>
                </Reveal>
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
