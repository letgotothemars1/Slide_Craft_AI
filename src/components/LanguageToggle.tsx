import { LANGUAGES, type Language } from "@/lib/i18n";
import { useLanguage } from "@/context/LanguageContext";
import { cn } from "@/lib/utils";

const LABELS: Record<Language, string> = { ru: "RU", en: "EN" };

/**
 * Two-position switch for the interface language. Rendered as a pair of
 * buttons with `aria-pressed` rather than a select: only two options, and the
 * inactive one stays visible so the choice is obvious at a glance.
 */
export default function LanguageToggle({ className }: { className?: string }) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div
      role="group"
      aria-label={t("nav.language")}
      className={cn(
        "inline-flex items-center rounded-md border border-border bg-muted/50 p-0.5",
        className,
      )}
    >
      {LANGUAGES.map((code) => {
        const isActive = code === language;
        return (
          <button
            key={code}
            type="button"
            onClick={() => setLanguage(code)}
            aria-pressed={isActive}
            // 44px wide on phones per the touch-target rule, compact from sm up.
            className={cn(
              "inline-flex h-11 w-11 cursor-pointer items-center justify-center rounded text-xs font-semibold transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
              "sm:h-7 sm:w-8",
              isActive
                ? "bg-card text-foreground shadow-card"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {LABELS[code]}
          </button>
        );
      })}
    </div>
  );
}
