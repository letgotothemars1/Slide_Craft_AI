import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useLanguage } from "@/context/LanguageContext";
import {
  approveJob,
  getJobSpec,
  regenerateJob,
  saveJobSpec,
  slidePreviewUrl,
  type PresentationSpec,
  type SpecSlide,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Check, Loader2, Plus, RefreshCw, Sparkles, Trash2 } from "lucide-react";

interface Props {
  jobId: string;
  /** Called once the deck has been approved, so the page can resume polling. */
  onApproved: () => void;
}

/** Bumped per slide so only the edited preview is refetched. */
type Versions = Record<number, number>;

export default function SlideReviewWorkspace({ jobId, onApproved }: Props) {
  const { t } = useLanguage();
  const [spec, setSpec] = useState<PresentationSpec | null>(null);
  const [selected, setSelected] = useState(0);
  const [versions, setVersions] = useState<Versions>({});
  const [saving, setSaving] = useState(false);
  // One busy flag: approving and regenerating must not run together.
  const [busy, setBusy] = useState<"approve" | "regenerate" | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Holds the latest spec for the debounced save, so a rapid second edit does
  // not persist the state captured when the first timer was scheduled.
  const latest = useRef<PresentationSpec | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    getJobSpec(jobId)
      .then((loaded) => {
        setSpec(loaded);
        latest.current = loaded;
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [jobId]);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const persist = useCallback(
    (index: number) => {
      if (timer.current) clearTimeout(timer.current);
      // Saves on a pause rather than per keystroke: every save re-renders the
      // slide server-side, which is far too expensive to run per character.
      timer.current = setTimeout(async () => {
        const payload = latest.current;
        if (!payload) return;
        setSaving(true);
        setError(null);
        try {
          await saveJobSpec(jobId, payload);
          setVersions((current) => ({ ...current, [index]: (current[index] ?? 0) + 1 }));
        } catch (reason) {
          setError(reason instanceof Error ? reason.message : t("review.saveFailed"));
        } finally {
          setSaving(false);
        }
      }, 800);
    },
    [jobId, t],
  );

  const edit = useCallback(
    (change: Partial<SpecSlide>) => {
      setSpec((current) => {
        if (!current) return current;
        const slides = current.slides.map((slide, i) =>
          i === selected ? { ...slide, ...change } : slide,
        );
        const next = { ...current, slides };
        latest.current = next;
        return next;
      });
      persist(selected);
    },
    [persist, selected],
  );

  const handleApprove = async () => {
    if (timer.current) clearTimeout(timer.current);
    setBusy("approve");
    setError(null);
    try {
      // Flush the pending edit first, or the deck would be built from the last
      // saved version and silently lose the final keystrokes.
      if (latest.current) await saveJobSpec(jobId, latest.current);
      await approveJob(jobId);
      onApproved();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      setBusy(null);
    }
  };

  const handleRegenerate = async () => {
    if (timer.current) clearTimeout(timer.current);
    setBusy("regenerate");
    setError(null);
    try {
      await regenerateJob(jobId);
      onApproved();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      setBusy(null);
    }
  };

  if (error && !spec) {
    return (
      <p role="alert" className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
        {error}
      </p>
    );
  }
  if (!spec) return <p className="text-sm text-muted-foreground">{t("dash.loading")}</p>;

  const slide = spec.slides[selected];

  return (
    <div className="space-y-5">
      {/* ── header ── */}
      <header className="flex flex-wrap items-center justify-between gap-4 border-b pb-5">
        <div className="space-y-1">
          <h1 className="font-display text-2xl font-bold">{t("review.draftTitle")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("review.subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            {saving ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                {t("review.saving")}
              </>
            ) : (
              <>
                <Check className="h-3 w-3 text-success-strong" aria-hidden="true" />
                {t("review.saved")}
              </>
            )}
          </span>

          <Button
            variant="outline"
            onClick={handleRegenerate}
            disabled={busy !== null}
            title={t("review.regenerateHint")}
            className="h-10 gap-2"
          >
            {busy === "regenerate" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            )}
            {busy === "regenerate" ? t("review.regenerating") : t("review.regenerate")}
          </Button>

          <Button
            onClick={handleApprove}
            disabled={busy !== null}
            title={t("review.approveHint")}
            className="h-10 gap-2"
          >
            {busy === "approve" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Sparkles className="h-4 w-4" aria-hidden="true" />
            )}
            {busy === "approve" ? t("review.approving") : t("review.approve")}
          </Button>
        </div>
      </header>

      {/* Same three-column shell as the modular draft editor: a 180px rail, a
          fluid slide, and a 340px inspector. The CSS lives in index.css and is
          shared, so the two editors cannot drift apart. */}
      <div className="draft-editor-grid">
        {/* ── thumbnail rail ── */}
        <nav aria-label={t("review.draftTitle")} className="draft-thumbnails">
          <ul className="contents">
            {spec.slides.map((item, index) => (
              <li key={item.id || index} className="draft-thumbnail-row">
                <button
                  type="button"
                  onClick={() => setSelected(index)}
                  aria-current={index === selected}
                  className={cn("draft-thumbnail cursor-pointer space-y-1.5",
                    index === selected && "is-selected")}
                >
                  <img
                    src={slidePreviewUrl(jobId, index, versions[index] ?? 0)}
                    alt=""
                    className="aspect-video w-full rounded bg-muted object-cover"
                    loading="lazy"
                  />
                  <span className="block truncate px-1 pb-0.5 text-[11px] leading-tight text-muted-foreground">
                    {index + 1}. {item.title || t("review.untitled")}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* ── selected slide ── */}
        <div className="min-w-0 space-y-2">
          <p className="text-xs text-muted-foreground">
            {t("review.slide")} {selected + 1} / {spec.slides.length}
          </p>
          {/* The same renderer that produces the final file, so this is the
              slide itself rather than an approximation of it. */}
          <img
            key={`${selected}-${versions[selected] ?? 0}`}
            src={slidePreviewUrl(jobId, selected, versions[selected] ?? 0)}
            alt={`${t("review.slide")} ${selected + 1}`}
            className="aspect-video w-full rounded-xl border border-border bg-muted object-cover"
          />
        </div>

        {/* ── element editor ── */}
        <aside className="draft-inspector space-y-5">
          <div className="space-y-1">
            <h2 className="text-sm font-semibold">{t("review.settings")}</h2>
            <p className="text-xs text-muted-foreground">{t("review.element")}</p>
          </div>

          {/* Everything on the slide, in reading order. Tabs hid most of the
              panel behind a click and made a slide with four editable parts
              look like it had one. */}
          <Section label={t("review.fieldTitle")}>
            <Textarea
              spellCheck={false}
              aria-label={t("review.fieldTitle")}
              value={slide.title ?? ""}
              onChange={(e) => edit({ title: e.target.value })}
              className="min-h-[72px] resize-none"
            />
          </Section>

          {slide.subtitle != null && (
            <Section label={t("review.fieldSubtitle")}>
              <Textarea
                spellCheck={false}
                aria-label={t("review.fieldSubtitle")}
                value={slide.subtitle ?? ""}
                onChange={(e) => edit({ subtitle: e.target.value })}
                className="min-h-[56px] resize-none"
              />
            </Section>
          )}

          {slide.body != null && (
            <Section label={t("review.fieldBody")}>
              <Textarea
                spellCheck={false}
                aria-label={t("review.fieldBody")}
                value={slide.body ?? ""}
                onChange={(e) => edit({ body: e.target.value })}
                className="min-h-[110px] resize-none"
              />
            </Section>
          )}

          {slide.bullets?.length > 0 && (
            <Section label={`${t("review.fieldBullets")} · ${slide.bullets.length}`}>
              <div className="space-y-2">
                {slide.bullets.map((bullet, i) => (
                  <div key={i} className="flex gap-1.5">
                    <Textarea
                      spellCheck={false}
                      aria-label={`${t("review.fieldBullets")} ${i + 1}`}
                      value={bullet}
                      onChange={(e) => {
                        const bullets = [...slide.bullets];
                        bullets[i] = e.target.value;
                        edit({ bullets });
                      }}
                      className="min-h-[56px] resize-none text-sm"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={t("review.removeBullet")}
                      className="h-9 w-9 shrink-0 text-muted-foreground"
                      onClick={() => edit({ bullets: slide.bullets.filter((_, j) => j !== i) })}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-9 w-full gap-1.5"
                  onClick={() => edit({ bullets: [...slide.bullets, ""] })}
                >
                  <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("review.addBullet")}
                </Button>
              </div>
            </Section>
          )}

          {slide.chart?.points?.length ? (
            <Section label={t("review.chart")}>
              <div className="space-y-2">
                {slide.chart.points.map((point, i) => (
                  <div key={i} className="flex gap-1.5">
                    <Input
                      spellCheck={false}
                      aria-label={t("review.chartLabel")}
                      value={point.label}
                      onChange={(e) => {
                        const points = slide.chart!.points.map((pt, j) =>
                          j === i ? { ...pt, label: e.target.value } : pt,
                        );
                        edit({ chart: { ...slide.chart!, points } });
                      }}
                      className="h-9 text-sm"
                    />
                    <Input
                      spellCheck={false}
                      type="number"
                      aria-label={t("review.chartValue")}
                      value={point.value}
                      onChange={(e) => {
                        const points = slide.chart!.points.map((pt, j) =>
                          j === i ? { ...pt, value: Number(e.target.value) } : pt,
                        );
                        edit({ chart: { ...slide.chart!, points } });
                      }}
                      className="h-9 w-20 shrink-0 text-sm tabular-nums"
                    />
                  </div>
                ))}
              </div>
            </Section>
          ) : null}

          {slide.key_message != null && (
            <Section label={t("review.fieldKeyMessage")}>
              <Input
                spellCheck={false}
                aria-label={t("review.fieldKeyMessage")}
                value={slide.key_message ?? ""}
                onChange={(e) => edit({ key_message: e.target.value })}
                className="h-10"
              />
            </Section>
          )}

          {slide.source != null && (
            <Section label={t("review.fieldSource")}>
              <Input
                spellCheck={false}
                aria-label={t("review.fieldSource")}
                value={slide.source ?? ""}
                onChange={(e) => edit({ source: e.target.value })}
                className="h-10"
              />
            </Section>
          )}

          {error && (
            <p role="alert" className="text-xs text-destructive">
              {error}
            </p>
          )}
        </aside>
      </div>

    </div>
  );
}

/** One labelled block in the inspector. Sections stack in reading order, so a
 *  slide with four editable parts looks like it has four. */
function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5 border-t border-border pt-4 first-of-type:border-t-0 first-of-type:pt-0">
      <Label className="text-xs uppercase tracking-wide text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}
