import { useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  generateRequestSchema,
  type GenerateRequest,
  audienceValues,
  styleValues,
  languageValues,
  formatValues,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useLanguage } from "@/context/LanguageContext";
import type { TranslationKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Sparkles, Paperclip, FileText, X, Minus, Plus, Loader2 } from "lucide-react";

const MAX_PROMPT = 2000;
const MIN_SLIDES = 5;
const MAX_SLIDES = 30;

const AUDIENCE_KEYS: Record<string, TranslationKey> = {
  executives: "gen.audience.executives",
  students: "gen.audience.students",
  sales: "gen.audience.sales",
  investors: "gen.audience.investors",
  custom: "gen.audience.custom",
};
const STYLE_KEYS: Record<string, TranslationKey> = {
  business: "gen.style.business",
  minimal: "gen.style.minimal",
  dark: "gen.style.dark",
  creative: "gen.style.creative",
};
const LANG_KEYS: Record<string, TranslationKey> = {
  ru: "gen.lang.ru",
  en: "gen.lang.en",
};

/** Pill-shaped trigger so the controls read as chips under the text field. */
const triggerClass =
  "h-11 w-auto gap-1.5 rounded-full border-border bg-background px-3.5 text-xs font-medium " +
  "focus:ring-2 focus:ring-ring focus:ring-offset-1 sm:h-9";

interface Props {
  onSubmit: (data: GenerateRequest) => void;
  isLoading?: boolean;
  /** Document attachment lives in the parent so the page owns the upload call. */
  attachedFileName: string | null;
  isUploading: boolean;
  onUpload: (file: File) => void | Promise<void>;
  onClearFile: () => void;
}

export default function PromptForm({
  onSubmit,
  isLoading,
  attachedFileName,
  isUploading,
  onUpload,
  onClearFile,
}: Props) {
  const { t } = useLanguage();
  const fileInput = useRef<HTMLInputElement>(null);

  const form = useForm<GenerateRequest>({
    resolver: zodResolver(generateRequestSchema),
    defaultValues: {
      prompt: "",
      audience: "executives",
      style: "business",
      language: "ru",
      slides: 10,
      format: "pdf",
      brandColor: null,
      logoUrl: null,
    },
  });

  const prompt = form.watch("prompt");
  const slides = form.watch("slides");
  const busy = Boolean(isLoading) || isUploading;

  // The zod messages live in the shared API schema and are Russian-only, so the
  // localized text is derived from the value instead of read off the error.
  const promptError = form.formState.errors.prompt
    ? prompt.trim().length === 0
      ? t("gen.error.promptRequired")
      : t("gen.error.promptLong")
    : null;

  const nudgeSlides = (delta: number) =>
    form.setValue("slides", Math.min(MAX_SLIDES, Math.max(MIN_SLIDES, slides + delta)), {
      shouldValidate: true,
    });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <div
        className={cn(
          "overflow-hidden rounded-2xl border bg-card shadow-elevated transition-colors",
          promptError ? "border-destructive/50" : "border-border",
        )}
      >
        {/* prompt */}
        <div className="p-4 sm:p-5">
          <Textarea
            id="prompt"
            aria-label={t("gen.title")}
            placeholder={t("gen.placeholder")}
            maxLength={MAX_PROMPT}
            className="min-h-[132px] resize-none border-0 bg-transparent p-0 text-base shadow-none focus-visible:ring-0"
            {...form.register("prompt")}
          />

          {attachedFileName && (
            <div className="mt-3 inline-flex max-w-full items-center gap-2 rounded-full border border-border bg-muted/50 py-1.5 pl-3 pr-1.5 text-xs">
              <FileText className="h-3.5 w-3.5 shrink-0 text-primary" aria-hidden="true" />
              <span className="truncate font-medium">{attachedFileName}</span>
              <button
                type="button"
                onClick={onClearFile}
                disabled={busy}
                aria-label={t("gen.removeFile")}
                className="inline-flex h-6 w-6 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-background hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* controls */}
        <div className="flex flex-wrap items-center gap-2 border-t border-border bg-muted/30 p-3 sm:p-4">
          <input
            ref={fileInput}
            type="file"
            accept="application/pdf,.pdf"
            className="sr-only"
            tabIndex={-1}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void onUpload(file);
              // Let the same file be picked again after clearing.
              event.currentTarget.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={busy}
            className="inline-flex h-11 cursor-pointer items-center gap-1.5 rounded-full border border-border bg-background px-3.5 text-xs font-medium transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:opacity-50 sm:h-9"
          >
            {isUploading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Paperclip className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {isUploading ? t("gen.uploading") : t("gen.attach")}
          </button>

          <Select
            value={form.watch("audience")}
            onValueChange={(v) => form.setValue("audience", v as GenerateRequest["audience"])}
          >
            <SelectTrigger aria-label={t("gen.audience")} className={triggerClass}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {audienceValues.map((v) => (
                <SelectItem key={v} value={v}>{t(AUDIENCE_KEYS[v])}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={form.watch("style")}
            onValueChange={(v) => form.setValue("style", v as GenerateRequest["style"])}
          >
            <SelectTrigger aria-label={t("gen.style")} className={triggerClass}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {styleValues.map((v) => (
                <SelectItem key={v} value={v}>{t(STYLE_KEYS[v])}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={form.watch("language")}
            onValueChange={(v) => form.setValue("language", v as GenerateRequest["language"])}
          >
            <SelectTrigger aria-label={t("gen.language")} className={triggerClass}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {languageValues.map((v) => (
                <SelectItem key={v} value={v}>{t(LANG_KEYS[v])}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={form.watch("format")}
            onValueChange={(v) => form.setValue("format", v as GenerateRequest["format"])}
          >
            <SelectTrigger aria-label={t("gen.format")} className={triggerClass}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {formatValues.map((v) => (
                <SelectItem key={v} value={v}>{v === "both" ? "PDF + PPTX" : v.toUpperCase()}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* slide count — a stepper keeps the full 5..30 range in one chip */}
          <div
            role="group"
            aria-label={t("gen.slides")}
            className="inline-flex h-11 items-center gap-0.5 rounded-full border border-border bg-background px-1 sm:h-9"
          >
            <button
              type="button"
              onClick={() => nudgeSlides(-1)}
              disabled={busy || slides <= MIN_SLIDES}
              aria-label={t("gen.fewer")}
              className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-40 sm:h-7 sm:w-7"
            >
              <Minus className="h-3.5 w-3.5" />
            </button>
            <span className="min-w-[4.5rem] text-center text-xs font-medium tabular-nums">
              {slides} · {t("gen.slides").toLowerCase()}
            </span>
            <button
              type="button"
              onClick={() => nudgeSlides(1)}
              disabled={busy || slides >= MAX_SLIDES}
              aria-label={t("gen.more")}
              className="inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-40 sm:h-7 sm:w-7"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* counter + submit pinned right */}
          <div className="ml-auto flex items-center gap-3">
            <span
              className={cn(
                "hidden text-xs tabular-nums sm:inline",
                prompt.length > MAX_PROMPT * 0.9 ? "text-warning-strong" : "text-muted-foreground",
              )}
            >
              {prompt.length}/{MAX_PROMPT}
            </span>
            <Button type="submit" disabled={busy} className="h-11 rounded-full px-5 sm:h-9">
              {busy ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
              )}
              {busy ? t("gen.submitting") : t("gen.submit")}
            </Button>
          </div>
        </div>
      </div>

      {promptError && (
        <p role="alert" className="mt-2 px-1 text-sm text-destructive">
          {promptError}
        </p>
      )}

      {/* examples */}
      <div className="mt-6 space-y-2.5">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {t("gen.examples")}
        </p>
        <ul className="flex flex-wrap gap-2">
          {(["gen.example1", "gen.example2", "gen.example3"] as TranslationKey[]).map((key) => (
            <li key={key}>
              <button
                type="button"
                onClick={() => form.setValue("prompt", t(key), { shouldValidate: true })}
                className="inline-flex min-h-11 cursor-pointer items-center rounded-full border border-border bg-card px-3.5 text-xs text-muted-foreground shadow-card transition-colors hover:border-primary/30 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 sm:min-h-9"
              >
                {t(key)}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </form>
  );
}
