import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { generateRequestSchema, type GenerateRequest, audienceValues, styleValues, languageValues, formatValues } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Sparkles, RotateCcw } from "lucide-react";

const AUDIENCE_LABELS: Record<string, string> = {
  executives: "Руководители",
  students: "Студенты",
  sales: "Продажи",
  investors: "Инвесторы",
  custom: "Другое",
};
const STYLE_LABELS: Record<string, string> = {
  business: "Бизнес",
  minimal: "Минимал",
  dark: "Тёмный",
  creative: "Креативный",
};

const PROMPT_EXAMPLES = [
  "Презентация о трендах AI в 2025 году для инвесторов",
  "Квартальный отчёт по продажам с графиками",
  "Обзор продукта для потенциальных клиентов",
];

interface Props {
  onSubmit: (data: GenerateRequest) => void;
  isLoading?: boolean;
}

export default function PromptForm({ onSubmit, isLoading }: Props) {
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

  const slides = form.watch("slides");

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {/* Prompt */}
      <div className="space-y-2">
        <Label htmlFor="prompt">Промпт</Label>
        <Textarea
          id="prompt"
          placeholder="Опишите тему и содержание презентации…"
          className="min-h-[120px] resize-none"
          {...form.register("prompt")}
        />
        {form.formState.errors.prompt && (
          <p className="text-sm text-destructive">{form.formState.errors.prompt.message}</p>
        )}
        <div className="flex flex-wrap gap-2">
          {PROMPT_EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => form.setValue("prompt", ex)}
              className="rounded-md bg-secondary px-2.5 py-1 text-xs text-secondary-foreground hover:bg-secondary/80 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Row: Audience + Style */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Аудитория</Label>
          <Select value={form.watch("audience")} onValueChange={(v) => form.setValue("audience", v as any)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {audienceValues.map((v) => (
                <SelectItem key={v} value={v}>{AUDIENCE_LABELS[v]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Стиль</Label>
          <Select value={form.watch("style")} onValueChange={(v) => form.setValue("style", v as any)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {styleValues.map((v) => (
                <SelectItem key={v} value={v}>{STYLE_LABELS[v]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Row: Language + Format */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Язык</Label>
          <Select value={form.watch("language")} onValueChange={(v) => form.setValue("language", v as any)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {languageValues.map((v) => (
                <SelectItem key={v} value={v}>{v === "ru" ? "Русский" : "English"}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Формат</Label>
          <Select value={form.watch("format")} onValueChange={(v) => form.setValue("format", v as any)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {formatValues.map((v) => (
                <SelectItem key={v} value={v}>{v === "both" ? "PPTX + PDF" : v.toUpperCase()}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Slides */}
      <div className="space-y-2">
        <Label>Слайдов: {slides}</Label>
        <Slider
          min={5}
          max={30}
          step={1}
          value={[slides]}
          onValueChange={([v]) => form.setValue("slides", v)}
        />
        {form.formState.errors.slides && (
          <p className="text-sm text-destructive">{form.formState.errors.slides.message}</p>
        )}
      </div>

      {/* Brand color */}
      <div className="space-y-2">
        <Label htmlFor="brandColor">Цвет бренда (опционально)</Label>
        <Input
          id="brandColor"
          type="color"
          className="h-10 w-20 cursor-pointer p-1"
          onChange={(e) => form.setValue("brandColor", e.target.value)}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isLoading} className="flex-1 gap-2">
          <Sparkles className="h-4 w-4" />
          {isLoading ? "Генерация…" : "Сгенерировать"}
        </Button>
        <Button type="button" variant="outline" onClick={() => form.reset()} disabled={isLoading}>
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
