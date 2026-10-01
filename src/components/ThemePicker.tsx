import { useId } from "react";
import { useLanguage } from "@/context/LanguageContext";
import type { Project } from "@/lib/project-api";
import { palettes } from "@/lib/slide-themes";

const options = [
  { value: "clean_editorial", title: "project.theme.clean", description: "project.theme.cleanHint" },
  { value: "dark_tech_pitch", title: "project.theme.dark", description: "project.theme.darkHint" },
  { value: "infographic_bright", title: "project.theme.bright", description: "project.theme.brightHint" },
] as const;

export default function ThemePicker({ value, onChange, disabled = false }: {
  value: Project["theme"];
  onChange: (theme: Project["theme"]) => void;
  disabled?: boolean;
}) {
  const name = useId();
  const { t } = useLanguage();
  return <fieldset disabled={disabled}>
    <legend className="sr-only">{t("project.theme.label")}</legend>
    <div className="grid gap-3 sm:grid-cols-3">
      {options.map((option) => {
        const palette = palettes[option.value];
        const selected = option.value === value;
        return <label key={option.value} className="block cursor-pointer has-[:disabled]:cursor-not-allowed">
          <input type="radio" name={name} value={option.value} checked={selected}
            onChange={() => onChange(option.value)} aria-label={t(option.title)} className="peer sr-only" />
          <div className="grid h-full grid-cols-2 items-center gap-3 rounded-xl border border-border p-3 transition-colors hover:border-primary/60 peer-checked:border-primary peer-checked:bg-primary/5 peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 peer-disabled:opacity-60 sm:flex sm:flex-col sm:items-stretch">
            <div aria-hidden="true" className="flex aspect-video w-full flex-col rounded-md p-3" style={{ backgroundColor: palette.background, color: palette.foreground }}>
              <p className="font-display text-[10px] font-bold leading-tight">{t("project.theme.sampleTitle")}</p>
              <div className="my-auto grid grid-cols-2 gap-1 text-[7px] leading-tight">
                <div className="min-w-0 truncate rounded p-1.5" style={{ backgroundColor: palette.panel }}>{t("project.theme.sampleLeft")}</div>
                <div className="min-w-0 truncate rounded p-1.5" style={{ backgroundColor: palette.panel }}>{t("project.theme.sampleRight")}</div>
              </div>
              <p className="border-t pt-1 text-[6px]" style={{ borderColor: palette.accent, color: palette.muted }}>{t("project.theme.sampleSource")}</p>
            </div>
            <div className="min-w-0 sm:flex sm:flex-1 sm:flex-col">
              <p className="text-sm font-semibold">{t(option.title)}</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{t(option.description)}</p>
              <p className={`pt-3 text-xs font-semibold sm:mt-auto ${selected ? "text-primary" : "text-muted-foreground"}`}>{selected ? t("project.theme.selected") : t("project.theme.choose")}</p>
            </div>
          </div>
        </label>;
      })}
    </div>
  </fieldset>;
}
