import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import ThemePicker from "@/components/ThemePicker";
import { useLanguage } from "@/context/LanguageContext";
import AppHeader from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { uploadDocument } from "@/lib/api";
import { createProject, startLiveDraft, getProject, getDemoMaterials, getDemoPdf, type ProjectCreate, type Project } from "@/lib/project-api";

import { restoreIntakeDraft, storeIntakeDraft, emptyIntakeDraft } from "@/lib/intake-draft";

const contextInstruction = `You are helping me prepare an academic presentation. Based only on our conversation and the materials already available to you, return a structured Context Pack in English with these headings:
Purpose and audience
Thesis
Key claims
Evidence for each claim (source title and page if known)
Assignment constraints and exact wording to preserve
Unresolved questions
Distinguish verified information from assumptions. Do not invent sources or page numbers. Keep the answer concise so I can paste and edit it in SlideCraft AI.`;

export default function NewProjectPage() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const tr = (en: string, ru: string) => language === "ru" ? ru : en;
  const [initialDraft] = useState(restoreIntakeDraft);
  const [assignment, setAssignment] = useState(initialDraft.assignment);
  const [contextPack, setContextPack] = useState(initialDraft.contextPack);
  const [theme, setTheme] = useState<ProjectCreate["theme"]>(initialDraft.theme);
  const [sourceId, setSourceId] = useState<string | null>(initialDraft.sourceId);
  const [filename, setFilename] = useState<string | null>(initialDraft.filename);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [demoError, setDemoError] = useState("");
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [locallySaved, setLocallySaved] = useState<boolean | null>(null);
  const requestedMode = useRef<"model" | "template">("model");
  const createdProject = useRef<{ signature: string; project: Project } | null>(null);
  useEffect(() => {
    setLocallySaved(storeIntakeDraft({assignment, contextPack, theme, sourceId, filename}));
  }, [assignment, contextPack, theme, sourceId, filename]);

  const startFresh = () => {
    setAssignment(''); setContextPack(''); setTheme(emptyIntakeDraft.theme);
    setSourceId(null); setFilename(null); createdProject.current=null;
    setError(''); setDemoError('');
    setNotice(tr('Started a blank project. Previously created projects are kept.', 'Начат пустой проект. Созданные ранее проекты сохранены.'));
    setLocallySaved(storeIntakeDraft({...emptyIntakeDraft}));
  };

  const copyInstruction = async () => {
    try {
      await navigator.clipboard.writeText(contextInstruction);
      setNotice("Instruction copied. Paste it into the AI chat where you discussed your topic, then paste its answer below.");
      setError("");
    } catch {
      setError("Copy failed. Select the instruction below and copy it manually.");
    }
  };

  const attachPdf = async (file?: File): Promise<boolean> => {
    if (!file) return false;
    setError("");
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setError("Choose a PDF file.");
      return false;
    }
    setUploading(true);
    try {
      const result = await uploadDocument(file);
      setSourceId(result.document_id);
      setFilename(file.name);
      setNotice("PDF indexed and ready to use as a source.");
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "PDF indexing failed. Try another file.");
      return false;
    } finally {
      setUploading(false);
    }
  };

  const loadDemo = async () => {
    setLoadingDemo(true);
    setDemoError("");
    setError("");
    setNotice("");
    try {
      const [materials, pdf] = await Promise.all([getDemoMaterials(), getDemoPdf()]);
      setAssignment(materials.assignment_text);
      setContextPack(materials.context_pack_text);
      const attached = await attachPdf(new File([pdf], materials.source_filename, { type: "application/pdf" }));
      if (attached) setNotice("Synthetic example loaded with its two-page PDF. Review the inputs, then choose how to generate your draft.");
    } catch (reason) {
      setDemoError(reason instanceof TypeError ? t("project.demo.unavailable") : reason instanceof Error ? reason.message : t("project.demo.unavailable"));
    } finally {
      setLoadingDemo(false);
    }
  };

  const generate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const mode = requestedMode.current;
    requestedMode.current = "model";
    setError("");
    if (!assignment.trim() || !contextPack.trim()) {
      setError("Add both the assignment and Context Pack before generating.");
      return;
    }
    if (saving || uploading || loadingDemo) return;
    setSaving(true);
    try {
      const input: ProjectCreate = {
        assignment_text: assignment,
        context_pack_text: contextPack,
        source_document_id: sourceId,
        theme,
        language: "en",
      };
      const signature = JSON.stringify(input);
      let project: Project;
      if (createdProject.current?.signature === signature) {
        project = await getProject(createdProject.current.project.id);
      } else {
        project = await createProject(input);
        createdProject.current = {signature, project};
      }
      if (project.phase === "intake" || (project.phase === "error" && !project.outline.length)) {
        await startLiveDraft(project, mode);
      }
      navigate(`/projects/${project.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : tr("Generation could not be started. Your inputs are kept; try again or use the key-free draft.", "Не удалось запустить генерацию. Данные сохранены; повторите или выберите черновик без API."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="container max-w-3xl py-10 sm:py-14">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">← Home</Link>
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4"><h1 className="font-display text-3xl font-bold">Create a presentation project</h1><Button type="button" variant="outline" disabled={saving || uploading || loadingDemo} onClick={startFresh}>{tr('Start from scratch', 'Начать с нуля')}</Button></div>
        <p className="mt-3 text-muted-foreground">Bring in your assignment and the thinking you have already done. Review the inputs and choose how to generate your live draft.</p>

        <div className="mt-6 rounded-xl border border-primary/30 bg-primary/5 p-5">
          <p className="font-semibold">Try the full workflow without API keys</p>
          <p className="mt-1 text-sm text-muted-foreground">Load a fictional campus case, including a two-page PDF. All figures are synthetic.</p>
          <Button type="button" variant="outline" className="mt-3" disabled={loadingDemo || uploading || saving} onClick={() => void loadDemo()}>{loadingDemo ? "Loading example…" : "Load synthetic demo example"}</Button>
          <a className="ml-4 inline-block text-sm underline" href={`${(import.meta.env.VITE_API_BASE_URL as string) || ""}/projects/demo/source.pdf`} download>Download the sample PDF</a>
          {demoError && <p role="alert" className="mt-3 text-sm text-destructive">{demoError}</p>}
        </div>

        <form onSubmit={generate} className="mt-8">
          <fieldset disabled={saving} className="space-y-7">
          <legend className="sr-only">{tr('Presentation inputs', 'Материалы презентации')}</legend>
          <p role={locallySaved === false ? 'status' : undefined} className="text-sm text-muted-foreground">{locallySaved === true ? tr('Inputs are saved automatically in this browser, including your theme and uploaded PDF reference.', 'Введённые данные, тема и ссылка на загруженный PDF автоматически сохраняются в этом браузере.') : locallySaved === false ? tr('Browser storage is unavailable. Keep this page open to retain your inputs.', 'Хранилище браузера недоступно. Не закрывайте страницу, чтобы сохранить введённые данные.') : ''}</p>
          <section className="rounded-xl border bg-card p-5 sm:p-6">
            <h2 className="text-lg font-semibold">1. Assignment</h2>
            <p className="mt-1 text-sm text-muted-foreground">Paste the brief and any requirements that slides must follow. This is a constraint, not evidence.</p>
            <label htmlFor="assignment" className="mt-4 block text-sm font-medium">Assignment brief</label>
            <Textarea id="assignment" value={assignment} onChange={(event) => setAssignment(event.target.value)} rows={7} className="mt-2" placeholder="Paste your assignment here" required />
          </section>

          <section className="rounded-xl border bg-card p-5 sm:p-6">
            <h2 className="text-lg font-semibold">2. Context Pack</h2>
            <p className="mt-1 text-sm text-muted-foreground">Copy this instruction into the AI chat where you developed your ideas. Paste its answer below and edit it as needed. SlideCraft does not access that chat.</p>
            <Button type="button" variant="outline" onClick={copyInstruction} className="mt-4">Copy instruction for your AI chat</Button>
            <details className="mt-3 text-sm text-muted-foreground"><summary className="cursor-pointer">Show the instruction</summary><pre className="mt-2 whitespace-pre-wrap rounded-md bg-muted p-3 font-sans">{contextInstruction}</pre></details>
            <label htmlFor="context-pack" className="mt-4 block text-sm font-medium">Context Pack</label>
            <Textarea id="context-pack" value={contextPack} onChange={(event) => setContextPack(event.target.value)} rows={9} className="mt-2" placeholder="Paste and review the structured response" required />
          </section>

          <section className="rounded-xl border bg-card p-5 sm:p-6">
            <h2 className="text-lg font-semibold">{t("project.pdf.title")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t("project.pdf.help")}</p>
            <p className="mt-2 text-sm text-muted-foreground">{t("project.pdf.example")}</p>
            <label htmlFor="source-pdf" className="mt-4 block text-sm font-medium">{t("project.pdf.attach")}</label>
            <Input key={sourceId ?? "empty"} id="source-pdf" type="file" accept=".pdf,application/pdf" className="mt-2" disabled={uploading} onChange={(event) => void attachPdf(event.target.files?.[0])} />
            <p className="mt-2 text-sm text-muted-foreground" aria-live="polite">{uploading ? t("project.pdf.indexing") : filename ? t("project.pdf.attached", { filename }) : t("project.pdf.empty")}</p>
            {sourceId && <Button type="button" size="sm" variant="ghost" className="mt-2" disabled={uploading} onClick={() => {setSourceId(null); setFilename(null);}}>{tr('Remove PDF', 'Убрать PDF')}</Button>}
          </section>

          <section className="rounded-xl border bg-card p-5 sm:p-6">
            <h2 className="text-lg font-semibold">{t("project.theme.intake")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t("project.theme.hint")}</p>
            <div className="mt-4"><ThemePicker value={theme} onChange={setTheme} disabled={saving} /></div>
          </section>

          {notice && <p role="status" className="text-sm text-success-strong">{notice}</p>}
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{tr('AI writes slide content progressively. The key-free draft uses your existing inputs without a model call.', 'AI постепенно создаёт содержание слайдов. Черновик без API использует введённые материалы без вызова модели.')}</p>
            <div className="flex flex-wrap gap-3">
              <Button type="submit" name="mode" value="model" onClick={() => {requestedMode.current = "model";}} size="lg" disabled={saving || uploading || loadingDemo}>{saving ? tr('Starting generation…', 'Запускаем генерацию…') : tr('Generate with AI', 'Создать с AI')}</Button>
              <Button type="submit" name="mode" value="template" onClick={() => {requestedMode.current = "template";}} variant="outline" size="lg" disabled={saving || uploading || loadingDemo}>{tr('Generate without API', 'Создать без API')}</Button>
            </div>
          </div>
          </fieldset>
        </form>
      </main>
    </div>
  );
}
