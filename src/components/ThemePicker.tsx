import DraftCanvas from "./DraftCanvas";
import { useId } from "react";
import { useLanguage } from "@/context/LanguageContext";
import type { Project } from "@/lib/project-api";
import { palettes } from "@/lib/slide-themes";

const options = [
  { value: "clean_editorial", title: "project.theme.clean", description: "project.theme.cleanHint" },
  { value: "dark_tech_pitch", title: "project.theme.dark", description: "project.theme.darkHint" },
  { value: "infographic_bright", title: "project.theme.bright", description: "project.theme.brightHint" },
] as const;

export default function ThemePicker({ value, onChange, disabled = false, project, slideId }: {
  value: Project["theme"];
  onChange: (theme: Project["theme"]) => void;
  disabled?: boolean;
  project?: Project;
  slideId?: string;
}) {
  const name = useId();
  const { t } = useLanguage();
  return <fieldset disabled={disabled}>
    <legend className="sr-only">{t("project.theme.label")}</legend>
    <div className="grid gap-3 sm:grid-cols-3">
      {options.map((option) => {
        const palette = palettes[option.value];
        const selected = option.value === value;
        const original = project ? palettes[project.theme] : null;
        const recolor = (color: string) => {
          if (!original) return color;
          const key = (Object.keys(original) as (keyof typeof original)[]).find(key => original[key] === color.toLowerCase());
          return key ? palette[key] : color;
        };
        const preview = project && slideId ? {...project, theme: option.value, slides: project.slides.map(slide => ({...slide, scene: slide.scene?.map(element => ({...element, color: recolor(element.color)}))}))} : null;
        return <label key={option.value} className="block cursor-pointer has-[:disabled]:cursor-not-allowed">
          <input type="radio" name={name} value={option.value} checked={selected}
            onChange={() => onChange(option.value)} aria-label={t(option.title)} className="peer sr-only" />
          <div className="grid h-full grid-cols-2 items-center gap-3 rounded-xl border border-border p-3 transition-colors hover:border-primary/60 peer-checked:border-primary peer-checked:bg-primary/5 peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 peer-disabled:opacity-60 sm:flex sm:flex-col sm:items-stretch">
            {preview && slideId ? <div aria-hidden="true"><DraftCanvas project={preview} slideId={slideId} grayscale={false}/></div> : <div aria-hidden="true" className="flex aspect-video w-full flex-col rounded-md p-3" style={{ backgroundColor: palette.background, color: palette.foreground }}>
              <p className="font-display text-[10px] font-bold leading-tight">{t("project.theme.sampleTitle")}</p>
              <div className="my-auto grid grid-cols-2 gap-1 text-[7px] leading-tight">
                <div className="min-w-0 truncate rounded p-1.5" style={{ backgroundColor: palette.panel }}>{t("project.theme.sampleLeft")}</div>
                <div className="min-w-0 truncate rounded p-1.5" style={{ backgroundColor: palette.panel }}>{t("project.theme.sampleRight")}</div>
              </div>
              <p className="border-t pt-1 text-[6px]" style={{ borderColor: palette.accent, color: palette.muted }}>{t("project.theme.sampleSource")}</p>
            </div>}
            <div className="min-w-0 sm:flex sm:flex-1 sm:flex-col">
              <p className="text-sm font-semibold">{t(option.title)}</p>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{t(option.description)}</p>
            </div>
          </div>
        </label>;
      })}
    </div>
  </fieldset>;
}
