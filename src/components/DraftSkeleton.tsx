import { Skeleton } from "@/components/ui/skeleton";
import { useLanguage } from "@/context/LanguageContext";

/**
 * Shown while the text is still being written.
 *
 * Deliberately the same three-pane shape as the review workspace that replaces
 * it: the layout does not jump when the draft arrives, and the wait reads as
 * "the deck is being built here" rather than as a progress bar on a blank page.
 */
export default function DraftSkeleton({ message }: { message?: string | null }) {
  const { t } = useLanguage();

  return (
    <div className="space-y-5">
      <header className="space-y-1.5 border-b pb-5">
        <h1 className="font-display text-2xl font-bold">{t("review.draftTitle")}</h1>
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {message || t("review.planning")}
        </p>
      </header>

      <div className="draft-editor-grid" aria-busy="true">
        <div className="draft-thumbnails">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="aspect-video w-full rounded-lg" />
          ))}
        </div>

        <div className="min-w-0 space-y-3">
          <Skeleton className="h-4 w-28 rounded-full" />
          <div className="aspect-video w-full rounded-xl border border-border bg-card p-8">
            <div className="space-y-4">
              <Skeleton className="h-6 w-2/3 rounded-full" />
              <Skeleton className="h-5 w-1/2 rounded-full" />
              <div className="space-y-2.5 pt-6">
                <Skeleton className="h-3.5 w-full rounded-full" />
                <Skeleton className="h-3.5 w-11/12 rounded-full" />
                <Skeleton className="h-3.5 w-4/5 rounded-full" />
              </div>
            </div>
          </div>
        </div>

        <div className="draft-inspector space-y-4">
          <Skeleton className="h-4 w-32 rounded-full" />
          <Skeleton className="h-10 w-full rounded-lg" />
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-10 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
