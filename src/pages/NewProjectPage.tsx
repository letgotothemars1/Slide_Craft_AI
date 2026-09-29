import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppHeader from "@/components/AppHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { uploadDocument } from "@/lib/api";
import { createProject, getDemoMaterials, getDemoPdf, type ProjectCreate } from "@/lib/project-api";

const contextInstruction = `You are helping me prepare an academic presentation. Based only on our conversation and the materials already available to you, return a structured Context Pack in English with these headings:
Purpose and audience
Thesis
Key claims
Evidence for each claim (source title and page if known)
Assignment constraints and exact wording to preserve
Unresolved questions
Distinguish verified information from assumptions. Do not invent sources or page numbers. Keep the answer concise so I can paste and edit it in SlideCraft AI.`;

const themes = [
  { value: "clean_editorial", label: "Clean editorial" },
  { value: "dark_tech_pitch", label: "Dark tech" },
  { value: "infographic_bright", label: "Bright infographic" },
] as const;

export default function NewProjectPage() {
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState("");
  const [contextPack, setContextPack] = useState("");
  const [theme, setTheme] = useState<ProjectCreate["theme"]>("clean_editorial");
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

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
    setSourceId(null);
    setFilename(null);
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
    setError("");
    setNotice("");
    try {
      const [materials, pdf] = await Promise.all([getDemoMaterials(), getDemoPdf()]);
      setAssignment(materials.assignment_text);
      setContextPack(materials.context_pack_text);
      const attached = await attachPdf(new File([pdf], materials.source_filename, { type: "application/pdf" }));
      if (attached) setNotice("Synthetic example loaded with its two-page PDF. Review the inputs, then save the project.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Demo example could not be loaded.");
    } finally {
      setLoadingDemo(false);
    }
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (!assignment.trim() || !contextPack.trim()) {
      setError("Add both the assignment and Context Pack before saving.");
      return;
    }
    if (uploading) return;
    setSaving(true);
    try {
      const project = await createProject({
        assignment_text: assignment,
        context_pack_text: contextPack,
        source_document_id: sourceId,
        theme,
        language: "en",
      });
      navigate(`/projects/${project.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Project could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="container max-w-3xl py-10 sm:py-14">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">← Home</Link>
        <p className="mt-8 text-xs font-semibold uppercase tracking-widest text-primary">Academic MVP · Step 1</p>
        <h1 className="mt-2 font-display text-3xl font-bold">Create a presentation project</h1>
        <p className="mt-3 text-muted-foreground">Bring in your assignment and the thinking you have already done. Review the inputs, approve an outline, and build editable slides.</p>

        <div className="mt-6 rounded-xl border border-primary/30 bg-primary/5 p-5">
          <p className="font-semibold">Try the full workflow without API keys</p>
          <p className="mt-1 text-sm text-muted-foreground">Load a fictional campus case, including a two-page PDF. All figures are synthetic.</p>
          <Button type="button" variant="outline" className="mt-3" disabled={loadingDemo || uploading || saving} onClick={() => void loadDemo()}>{loadingDemo ? "Loading example…" : "Load synthetic demo example"}</Button>
          <a className="ml-4 inline-block text-sm underline" href="/projects/demo/source.pdf" download>Download the sample PDF</a>
        </div>

        <form onSubmit={save} className="mt-8 space-y-7">
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
            <h2 className="text-lg font-semibold">3. Source PDF</h2>
            <p className="mt-1 text-sm text-muted-foreground">Use one public, synthetic or team-authored PDF for this course demo. Source text keeps its page numbers.</p>
            <label htmlFor="source-pdf" className="mt-4 block text-sm font-medium">Attach one PDF</label>
            <Input id="source-pdf" type="file" accept=".pdf,application/pdf" className="mt-2" disabled={uploading} onChange={(event) => void attachPdf(event.target.files?.[0])} />
            <p className="mt-2 text-sm text-muted-foreground" aria-live="polite">{uploading ? "Indexing PDF…" : filename ? `Attached: ${filename}` : "You can save without a PDF. Adding one later is not yet available."}</p>
          </section>

          <section className="rounded-xl border bg-card p-5 sm:p-6">
            <h2 className="text-lg font-semibold">4. Theme</h2>
            <p className="mt-1 text-sm text-muted-foreground">This choice is stored now and will be confirmed when you approve the outline.</p>
            <label htmlFor="project-theme" className="mt-4 block text-sm font-medium">Visual theme</label>
            <select id="project-theme" className="mt-2 h-10 w-full rounded-md border bg-background px-3 text-sm" value={theme} onChange={(event) => setTheme(event.target.value as ProjectCreate["theme"])}>
              {themes.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </section>

          {notice && <p role="status" className="text-sm text-success-strong">{notice}</p>}
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <Button type="submit" size="lg" disabled={saving || uploading || loadingDemo}>{saving ? "Saving project…" : "Save project"}</Button>
        </form>
      </main>
    </div>
  );
}
