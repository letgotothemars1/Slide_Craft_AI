import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { type JobStatus, getJobStatus } from "@/lib/api";
import { updateHistoryStatus } from "@/lib/history";
import { track } from "@/lib/analytics";
import JobStatusCard from "@/components/JobStatusCard";
import PreviewGallery from "@/components/PreviewGallery";
import DownloadButtons from "@/components/DownloadButtons";
import ShareLink from "@/components/ShareLink";
import { Sparkles, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function JobPage() {
  const { jobId } = useParams<{ jobId: string }>();
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
        setError(err.message || "Не удалось получить статус задачи");
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    };

    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, 2500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId]);

  if (!jobId) {
    return <NotFoundState />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/history" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              История
            </Link>
            <Button asChild variant="outline" size="sm">
              <Link to="/generate">
                <ArrowLeft className="h-4 w-4 mr-1" />
                Новая
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 container py-8 max-w-3xl mx-auto space-y-6">
        {error ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center space-y-3">
            <p className="text-destructive font-medium">{error}</p>
            <Button asChild variant="outline">
              <Link to="/generate">Вернуться</Link>
            </Button>
          </div>
        ) : !job ? (
          <div className="space-y-4">
            <Skeleton className="h-32 rounded-lg" />
            <Skeleton className="h-8 w-48" />
          </div>
        ) : (
          <>
            <JobStatusCard job={job} />
            <ShareLink jobId={job.job_id} />

            {job.status === "done" && job.result && (
              <>
                <DownloadButtons pptxUrl={job.result.pptx_url} pdfUrl={job.result.pdf_url} />
                {job.result.preview_images && job.result.preview_images.length > 0 && (
                  <PreviewGallery images={job.result.preview_images} />
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function NotFoundState() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-display font-bold">Задача не найдена</h1>
        <p className="text-muted-foreground">Проверьте ссылку или создайте новую презентацию</p>
        <Button asChild>
          <Link to="/generate">Создать</Link>
        </Button>
      </div>
    </div>
  );
}
