import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  approveOutline, createModelOutline, createStarterOutline, getSourceCandidates, saveOutline,
  type OutlineItem, type Project, type SourceRef,
} from "@/lib/project-api";

const themes: { value: Project["theme"]; label: string }[] = [
  { value: "clean_editorial", label: "Clean editorial" },
  { value: "dark_tech_pitch", label: "Dark tech" },
  { value: "infographic_bright", label: "Bright infographic" },
];

export default function OutlineEditor({ project, onChange }: { project: Project; onChange: (project: Project) => void }) {
  const [outline, setOutline] = useState<OutlineItem[]>(project.outline);
  const [candidates, setCandidates] = useState<SourceRef[]>([]);
  const [theme, setTheme] = useState<Project["theme"]>(project.theme);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setOutline([...project.outline].sort((a, b) => a.order - b.order));
    setTheme(project.theme);
    setDirty(false);
  }, [project]);

  useEffect(() => {
    if (!project.source_document_id) return;
    getSourceCandidates(project.id).then(setCandidates).catch(() => setCandidates([]));
  }, [project.id, project.source_document_id]);

  const run = async (action: () => Promise<Project>, success: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      onChange(await action());
      setNotice(success);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Request failed. Refresh the project and try again.");
    } finally {
      setBusy(false);
    }
  };

  const replace = (index: number, patch: Partial<OutlineItem>) => {
    setOutline((current) => current.map((item, i) => i === index ? { ...item, ...patch } : item));
    setDirty(true);
  };

  const move = (index: number, offset: number) => {
    const next = [...outline];
    const other = index + offset;
    if (other < 0 || other >= next.length) return;
    [next[index], next[other]] = [next[other], next[index]];
    setOutline(next.map((item, i) => ({ ...item, order: i + 1 })));
    setDirty(true);
  };

  const attach = (index: number, candidateIndex: number) => {
    const candidate = candidates[candidateIndex];
    if (!candidate) return;
    const item = outline[index];
    if (item.evidence_refs.some((ref) => ref.page_number === candidate.page_number && ref.excerpt === candidate.excerpt)) return;
    replace(index, { evidence_refs: [...item.evidence_refs, candidate] });
  };

  const approved = !["intake", "outline_draft"].includes(project.phase);
  return (
    <section className="space-y-5" aria-label="Slide outline">
      <div className="rounded-xl border bg-white p-5 text-slate-900">
        <h2 className="text-xl font-semibold">Five-slide outline</h2>
        <p className="mt-2 text-sm text-slate-600">Create an AI draft with your configured provider, or use the key-free template. Check either draft against the assignment and Context Pack. Only PDF excerpts you select appear as source references.</p>
        {project.phase === "intake" && <div className="mt-4 flex flex-wrap gap-2"><Button disabled={busy} onClick={() => void run(() => createModelOutline(project), "AI outline created. Check every claim and select PDF evidence before approval.")}>{busy ? "Generating outline…" : "Generate AI outline"}</Button><Button variant="outline" disabled={busy} onClick={() => void run(() => createStarterOutline(project), "Template outline created. Review every slide before approval.")}>Use key-free template</Button></div>}
      </div>

      {outline.map((item, index) => <article key={item.id} className="rounded-xl border border-slate-300 bg-white p-5 text-slate-900 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Slide {index + 1} · {item.layout_type}</p><p className="mt-1 text-sm text-slate-600">{item.purpose}</p></div>
          {!approved && <div className="flex gap-2"><Button type="button" size="sm" variant="outline" disabled={index === 0 || busy} onClick={() => move(index, -1)} aria-label={`Move slide ${index + 1} up`}>↑</Button><Button type="button" size="sm" variant="outline" disabled={index === outline.length - 1 || busy} onClick={() => move(index, 1)} aria-label={`Move slide ${index + 1} down`}>↓</Button></div>}
        </div>
        <label className="mt-4 block text-sm font-medium" htmlFor={`title-${item.id}`}>Title</label>
        <Input id={`title-${item.id}`} value={item.title} maxLength={200} disabled={approved || busy} onChange={(event) => replace(index, { title: event.target.value })} className="mt-1" />
        <label className="mt-4 block text-sm font-medium" htmlFor={`message-${item.id}`}>Key message</label>
        <Textarea id={`message-${item.id}`} value={item.key_message} maxLength={500} disabled={approved || busy} onChange={(event) => replace(index, { key_message: event.target.value })} className="mt-1" rows={3} />
        <div className="mt-4 border-t pt-3 text-sm">
          <p className="font-medium">PDF evidence</p>
          {item.evidence_refs.length === 0 && <p className="mt-1 text-amber-700">Source needed</p>}
          {item.evidence_refs.map((ref, refIndex) => <div key={`${ref.page_number}-${refIndex}`} className="mt-2 rounded bg-slate-100 p-2"><p className="font-medium">{ref.filename}, p. {ref.page_number}</p><p className="mt-1 line-clamp-3 text-slate-600">{ref.excerpt}</p>{!approved && <button type="button" className="mt-1 text-red-700 underline" onClick={() => replace(index, { evidence_refs: item.evidence_refs.filter((_, i) => i !== refIndex) })}>Remove excerpt</button>}</div>)}
          {!approved && candidates.length > 0 && <select aria-label={`Add PDF excerpt to slide ${index + 1}`} className="mt-3 h-10 w-full rounded-md border bg-white px-2" value="" onChange={(event) => attach(index, Number(event.target.value))}><option value="">Select a PDF excerpt…</option>{candidates.map((ref, candidateIndex) => <option key={candidateIndex} value={candidateIndex}>p. {ref.page_number} · {ref.excerpt.slice(0, 95)}</option>)}</select>}
        </div>
      </article>)}

      {outline.length === 5 && !approved && <div className="rounded-xl border bg-card p-5">
        <p className="text-sm text-muted-foreground">Review assignment requirements manually before approval. PDF excerpts are candidates; confirm that each one really supports its slide.</p>
        <Button className="mt-4" disabled={busy || !dirty} onClick={() => void run(() => saveOutline(project, outline), "Outline saved.")}>Save outline edits</Button>
        <div className="mt-5 border-t pt-4"><label htmlFor="approval-theme" className="block text-sm font-medium">Confirm visual theme</label><select id="approval-theme" className="mt-2 h-10 w-full rounded-md border bg-background px-3 text-sm" value={theme} onChange={(event) => setTheme(event.target.value as Project["theme"])}>{themes.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><Button className="mt-4" variant="outline" disabled={busy || dirty} onClick={() => void run(() => approveOutline(project, theme), "Outline approved. Slide building is the next module.")}>Approve outline and theme</Button>{dirty && <p className="mt-2 text-sm text-muted-foreground">Save edits before approval.</p>}</div>
      </div>}
      {approved && <p className="rounded-xl border bg-card p-5 text-sm">Outline approved. The selected order and theme are saved for slide building.</p>}
      {notice && <p role="status" className="text-sm text-green-700">{notice}</p>}
      {error && <p role="alert" className="text-sm text-destructive">{error} <button type="button" className="underline" onClick={() => window.location.reload()}>Refresh project</button></p>}
    </section>
  );
}
