import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  buildProject, editSlideBlock, downloadProjectPptx, getProject, regenerateBlock, resetBlockFromOutline, retrySlide, type Project,
} from "@/lib/project-api";

import { palettes } from "@/lib/slide-themes";

type BlockKey = "title" | "body" | "source_label";
const blockLabels: Record<BlockKey, string> = { title: "Title", body: "Body", source_label: "Source label" };



function SlidePreview({ project, slideId }: { project: Project; slideId: string }) {
  const slide = project.slides.find((item) => item.id === slideId);
  const item = project.outline.find((entry) => entry.id === slideId);
  if (!slide || !item) return null;
  const palette = palettes[project.theme];
  const title = slide.blocks.title.text;
  const body = slide.blocks.body.text;
  const source = slide.blocks.source_label.text;
  const bodySize = body.length > 260 ? "text-[7px] sm:text-base" : body.length > 150 ? "text-[8px] sm:text-lg" : "text-[8px] sm:text-xl";
  const [left, right] = body.split("|", 2).map((part) => part?.trim());

  return <div className="aspect-video w-full overflow-hidden rounded-xl border p-[5%] shadow-sm" style={{ backgroundColor: palette.background, color: palette.foreground }} aria-label={`Slide ${item.order} preview`}>
    <div className="flex h-full flex-col">
      <div className="mb-auto" style={{ borderLeft: item.layout_type === "title" ? `6px solid ${palette.accent}` : undefined, paddingLeft: item.layout_type === "title" ? "4%" : undefined }}>
        <p className="text-[7px] font-semibold uppercase tracking-wide sm:text-xs sm:tracking-widest" style={{ color: palette.accent }}>Slide {item.order} · {item.purpose}</p>
        <h3 className={`mt-1 font-display font-bold leading-tight sm:mt-3 ${item.layout_type === "title" ? "text-sm sm:text-4xl" : "text-xs sm:text-3xl"}`}>{title}</h3>
      </div>
      {item.layout_type === "comparison" ? <div className="grid grid-cols-2 gap-1 text-[7px] sm:gap-3 sm:text-base"><div className="min-h-10 rounded p-1 sm:min-h-16 sm:rounded-lg sm:p-3" style={{ backgroundColor: palette.panel }}>{left || "First point needed"}</div><div className="min-h-10 rounded p-1 sm:min-h-16 sm:rounded-lg sm:p-3" style={{ backgroundColor: palette.panel }}>{right || "Second point needed"}</div></div> : <p className={`mb-auto max-w-[85%] leading-snug ${bodySize}`} style={{ color: palette.muted }}>{body}</p>}
      <p className="mt-1 border-t pt-1 text-[6px] sm:mt-4 sm:pt-2 sm:text-xs" style={{ borderColor: palette.accent, color: palette.muted }}>{source}</p>
    </div>
  </div>;
}

export function BlockEditor({ project, slideId, blockKey, onChange, roomy = false }: {
  project: Project; slideId: string; blockKey: BlockKey; roomy?: boolean; onChange: (project: Project) => void;
}) {
  const slide = project.slides.find((row) => row.id === slideId)!;
  const outline = project.outline.find((row) => row.id === slideId)!;
  const block = slide.blocks[blockKey];
  const [draft, setDraft] = useState(block.text);
  const savedText = useRef(block.text);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const generating = block.status === "generating";
  const disabled = pending || generating;
  const dirty = draft !== block.text;
  const comparison = blockKey === "body" && outline.layout_type === "comparison";
  const parts = draft.split("|");
  const valid = Boolean(draft.trim()) && (!comparison || (parts.length === 2 && parts.every((part) => part.trim())));
  const label = comparison ? "Comparison points" : blockLabels[blockKey];

  useEffect(() => {
    const previous = savedText.current;
    setDraft((current) => current === previous ? block.text : current);
    savedText.current = block.text;
  }, [block.text]);

  const run = async (action: () => Promise<Project>) => {
    setPending(true);
    setError("");
    try { onChange(await action()); }
    catch (reason) {
      const message = reason instanceof Error ? reason.message : "Request failed. Try again.";
      setError(message);
      if (message.includes("Refresh")) {
        try { onChange(await getProject(project.id)); } catch { /* Keep the local draft. */ }
      }
    } finally { setPending(false); }
  };

  return <fieldset className="space-y-2" aria-busy={generating}>
    <legend className="text-sm font-medium">{label}</legend>
    {comparison ? <div className={roomy ? "grid gap-4" : "grid gap-3 sm:grid-cols-2"}>{([0, 1] as const).map((index) =>
      <div key={index}><label className="text-xs text-muted-foreground" htmlFor={`comparison-${index}`}>{index === 0 ? "First point" : "Second point"}</label>
        <Textarea id={`comparison-${index}`} rows={roomy ? 6 : 3} maxLength={240} value={parts[index]?.trim() ?? ""} disabled={disabled}
          onChange={(event) => { const updated = [...parts]; updated[index] = event.target.value; setDraft(`${updated[0] ?? ""} | ${updated[1] ?? ""}`); }} />
      </div>)}</div>
      : blockKey === "body" ? <Textarea aria-label={label} id={`block-${blockKey}`} rows={roomy ? 12 : 4} value={draft} maxLength={500} disabled={disabled} onChange={(event) => setDraft(event.target.value)} />
      : <Input aria-label={label} id={`block-${blockKey}`} value={draft} maxLength={200} disabled={disabled} onChange={(event) => setDraft(event.target.value)} />}
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="outline" disabled={disabled || !dirty || !valid}
        onClick={() => void run(() => editSlideBlock(project, slideId, blockKey, draft))}>Save {blockLabels[blockKey].toLowerCase()}</Button>
      {blockKey !== "source_label" && <>
        <Button size="sm" variant="outline" disabled={disabled || dirty || slide.status !== "ready"}
          onClick={() => void run(() => regenerateBlock(project, slideId, blockKey))}>
          {generating ? `Regenerating ${blockKey}…` : block.status === "error" ? `Retry ${blockKey} with AI` : `Regenerate ${blockKey} with AI`}
        </Button>
        <Button size="sm" variant="ghost" disabled={disabled || dirty || slide.status !== "ready" || block.text === (blockKey === "title" ? outline.title : outline.key_message)}
          onClick={() => void run(() => resetBlockFromOutline(project, slideId, blockKey))}>Reset from outline</Button>
      </>}
      {dirty && <Button size="sm" variant="ghost" disabled={disabled} onClick={() => { setDraft(block.text); setError(""); }}>Discard unsaved {blockKey === "source_label" ? "source label" : blockKey}</Button>}
    </div>
    {dirty && <p className="text-xs text-muted-foreground">Unsaved changes. Save or discard them before regenerating this block.</p>}
    {generating && <p role="status" className="text-sm text-muted-foreground">AI is rewriting this {blockKey}. Other blocks remain editable.</p>}
    {(error || block.error) && <p role="alert" className="text-sm text-destructive">{error || block.error}</p>}
  </fieldset>;
}

export default function SlideWorkspace({ project, onChange }: { project: Project; onChange: (project: Project) => void }) {
  const [selectedId, setSelectedId] = useState(project.outline[0]?.id ?? "");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const slide = project.slides.find((item) => item.id === selectedId);
  const regenerating = project.slides.some((item) => Object.values(item.blocks).some((block) => block.status === "generating"));

  const run = async (key: string, action: () => Promise<Project>) => {
    setBusy(key);
    setError("");
    try { onChange(await action()); }
    catch (reason) {
      const message = reason instanceof Error ? reason.message : "Request failed";
      setError(message);
      if (message.includes("Refresh")) getProject(project.id).then(onChange).catch(() => undefined);
    } finally { setBusy(""); }
  };

  if (project.phase === "outline_approved") return <section className="rounded-xl border bg-card p-5"><h2 className="text-xl font-semibold">Build slides</h2><p className="mt-2 text-sm text-muted-foreground">Generate slide bodies one at a time with your configured AI provider, or copy the approved outline into editable slides without a key. Approved titles and selected PDF source labels stay attached to their slides.</p><div className="mt-4 flex flex-wrap gap-2"><Button disabled={Boolean(busy)} onClick={() => void run("build", () => buildProject(project, "model"))}>Build with AI</Button><Button variant="outline" disabled={Boolean(busy)} onClick={() => void run("build", () => buildProject(project, "template"))}>Use key-free outline</Button></div>{error && <p role="alert" className="mt-3 text-destructive">{error}</p>}</section>;

  const download = async () => {
    setBusy("export");
    setError("");
    try { await downloadProjectPptx(project.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "PPTX could not be downloaded. Try again."); }
    finally { setBusy(""); }
  };

  const readyCount = project.slides.filter((item) => item.status === "ready").length;
  return <section className="space-y-5" aria-label="Slide workspace">
    <div className="rounded-xl border bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">Slides</h2><p className="mt-1 text-sm text-muted-foreground" aria-live="polite">{readyCount} of {project.slides.length} ready · {project.phase === "building" ? "Building" : project.phase === "ready" ? "Ready" : "Needs attention"}</p></div>{project.phase === "ready" && (regenerating ? <Button disabled>Wait for regeneration to export</Button> : <Button disabled={busy === "export"} onClick={() => void download()}>{busy === "export" ? "Preparing PPTX…" : "Download draft PPTX"}</Button>)}</div>
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2 sm:grid sm:grid-cols-5 sm:overflow-visible sm:pb-0">{project.outline.map((item) => { const builtSlide = project.slides.find((row) => row.id === item.id); const status = builtSlide?.status ?? "queued"; const title = status === "ready" ? builtSlide?.blocks.title.text : item.title; return <button type="button" key={item.id} aria-pressed={selectedId === item.id} className={`min-w-28 flex-1 rounded-md border p-2 text-left text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:min-w-0 ${selectedId === item.id ? "border-primary ring-2 ring-primary/30" : ""}`} onClick={() => setSelectedId(item.id)}><span className="block font-semibold">{item.order}. {title}</span><span className="mt-1 block capitalize text-muted-foreground">{status}</span></button>; })}</div>
    </div>
    {slide && <><div className="rounded-xl border bg-card p-4 sm:p-5"><SlidePreview project={project} slideId={selectedId} /></div>
      {slide.status === "ready" ? <div className="space-y-5 rounded-xl border bg-card p-5"><h3 className="font-semibold">Edit slide {project.outline.find((item) => item.id === selectedId)?.order}</h3>
        {(["title", "body", "source_label"] as BlockKey[]).map((key) => <BlockEditor key={`${selectedId}-${key}`} project={project} slideId={selectedId} blockKey={key} onChange={onChange} />)}
        <p className="text-xs text-muted-foreground">Review every slide and source before presenting. Regenerate with AI rewrites only the selected block; source labels can be edited manually.</p>
      </div> : <div className="rounded-xl border bg-card p-5 text-sm">{slide.status === "error" ? <><p>Slide build failed.</p><Button className="mt-3" disabled={Boolean(busy)} onClick={() => void run("retry", () => retrySlide(project, selectedId))}>Retry this slide</Button></> : <p>{slide.status === "generating" ? "Building this slide…" : "This slide is queued."}</p>}</div>}</>}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
  </section>;
}
