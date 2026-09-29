import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  buildProject, editSlideBlock, exportPptxUrl, getProject, resetBlockFromOutline, retrySlide, type Project,
} from "@/lib/project-api";

type BlockKey = "title" | "body" | "source_label";
const blockLabels: Record<BlockKey, string> = { title: "Title", body: "Body", source_label: "Source label" };

const palettes: Record<Project["theme"], { background: string; foreground: string; muted: string; accent: string; panel: string }> = {
  clean_editorial: { background: "#fffcf7", foreground: "#111827", muted: "#57534e", accent: "#334155", panel: "#ffffff" },
  dark_tech_pitch: { background: "#0b1020", foreground: "#f8fafc", muted: "#a3b2c8", accent: "#22c55e", panel: "#162238" },
  infographic_bright: { background: "#f0f9ff", foreground: "#0f172a", muted: "#0369a1", accent: "#0ea5e9", panel: "#ffffff" },
};

function SlidePreview({ project, slideId }: { project: Project; slideId: string }) {
  const slide = project.slides.find((item) => item.id === slideId);
  const item = project.outline.find((entry) => entry.id === slideId);
  if (!slide || !item) return null;
  const palette = palettes[project.theme];
  const title = slide.blocks.title.text;
  const body = slide.blocks.body.text;
  const source = slide.blocks.source_label.text;
  const [left, right] = body.split("|", 2).map((part) => part?.trim());

  return <div className="aspect-video w-full overflow-hidden rounded-xl border p-[5%] shadow-sm" style={{ backgroundColor: palette.background, color: palette.foreground }} aria-label={`Slide ${item.order} preview`}>
    <div className="flex h-full flex-col">
      <div className="mb-auto" style={{ borderLeft: item.layout_type === "title" ? `6px solid ${palette.accent}` : undefined, paddingLeft: item.layout_type === "title" ? "4%" : undefined }}>
        <p className="text-[7px] font-semibold uppercase tracking-wide sm:text-xs sm:tracking-widest" style={{ color: palette.accent }}>Slide {item.order} · {item.purpose}</p>
        <h3 className={`mt-1 font-display font-bold leading-tight sm:mt-3 ${item.layout_type === "title" ? "text-sm sm:text-4xl" : "text-xs sm:text-3xl"}`}>{title}</h3>
      </div>
      {item.layout_type === "comparison" ? <div className="grid grid-cols-2 gap-1 text-[7px] sm:gap-3 sm:text-base"><div className="min-h-10 rounded p-1 sm:min-h-16 sm:rounded-lg sm:p-3" style={{ backgroundColor: palette.panel }}>{left || "First point needed"}</div><div className="min-h-10 rounded p-1 sm:min-h-16 sm:rounded-lg sm:p-3" style={{ backgroundColor: palette.panel }}>{right || "Second point needed"}</div></div> : <p className="mb-auto max-w-[85%] text-[8px] leading-snug sm:text-xl" style={{ color: palette.muted }}>{body}</p>}
      <p className="mt-1 border-t pt-1 text-[6px] sm:mt-4 sm:pt-2 sm:text-xs" style={{ borderColor: palette.accent, color: palette.muted }}>{source}</p>
    </div>
  </div>;
}

export default function SlideWorkspace({ project, onChange }: { project: Project; onChange: (project: Project) => void }) {
  const [selectedId, setSelectedId] = useState(project.outline[0]?.id ?? "");
  const [drafts, setDrafts] = useState<Record<BlockKey, string>>({ title: "", body: "", source_label: "" });
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const slide = project.slides.find((item) => item.id === selectedId);
  const selectedLayout = project.outline.find((item) => item.id === selectedId)?.layout_type;

  useEffect(() => {
    if (slide) setDrafts({
      title: slide.blocks.title.text,
      body: slide.blocks.body.text,
      source_label: slide.blocks.source_label.text,
    });
  }, [selectedId, slide?.revision]);

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

  if (project.phase === "outline_approved") return <section className="rounded-xl border bg-card p-5"><h2 className="text-xl font-semibold">Build slides</h2><p className="mt-2 text-sm text-muted-foreground">The local build copies the approved outline into editable slides, one at a time. It does not use an AI model.</p><Button className="mt-4" disabled={Boolean(busy)} onClick={() => void run("build", () => buildProject(project))}>Build five slides from outline</Button>{error && <p role="alert" className="mt-3 text-destructive">{error}</p>}</section>;

  const readyCount = project.slides.filter((item) => item.status === "ready").length;
  return <section className="space-y-5" aria-label="Slide workspace">
    <div className="rounded-xl border bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-semibold">Slides</h2><p className="mt-1 text-sm text-muted-foreground">{readyCount} of {project.slides.length} ready · {project.phase === "building" ? "Building" : project.phase === "ready" ? "Ready" : "Needs attention"}</p></div>{project.phase === "ready" && <a className="inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground" href={exportPptxUrl(project.id)} download>Download draft PPTX</a>}</div>
      <div className="mt-4 flex gap-2 overflow-x-auto pb-2 sm:grid sm:grid-cols-5 sm:overflow-visible sm:pb-0">{project.outline.map((item) => { const status = project.slides.find((slide) => slide.id === item.id)?.status ?? "queued"; return <button type="button" key={item.id} className={`min-w-28 flex-1 rounded-md border p-2 text-left text-xs sm:min-w-0 ${selectedId === item.id ? "border-primary ring-2 ring-primary/30" : ""}`} onClick={() => setSelectedId(item.id)}><span className="block font-semibold">{item.order}. {item.title}</span><span className="mt-1 block capitalize text-muted-foreground">{status}</span></button>; })}</div>
    </div>
    {slide && <><div className="rounded-xl border bg-card p-4 sm:p-5"><SlidePreview project={project} slideId={selectedId} /></div>
      {slide.status === "ready" ? <div className="space-y-4 rounded-xl border bg-card p-5"><h3 className="font-semibold">Edit slide {project.outline.find((item) => item.id === selectedId)?.order}</h3>{(["title", "body", "source_label"] as BlockKey[]).map((key) => <div key={key}><label htmlFor={`block-${key}`} className="block text-sm font-medium">{key === "body" && selectedLayout === "comparison" ? "Comparison points" : blockLabels[key]}</label>{key === "body" && selectedLayout === "comparison" ? <div className="mt-2 grid gap-3 sm:grid-cols-2">{([0, 1] as const).map((partIndex) => <div key={partIndex}><label className="text-xs text-muted-foreground" htmlFor={`comparison-${partIndex}`}>{partIndex === 0 ? "First point" : "Second point"}</label><Textarea id={`comparison-${partIndex}`} rows={3} value={drafts.body.split("|", 2)[partIndex]?.trim() ?? ""} disabled={busy === key} onChange={(event) => { const parts = drafts.body.split("|", 2); parts[partIndex] = event.target.value; setDrafts({ ...drafts, body: `${parts[0] ?? ""} | ${parts[1] ?? ""}` }); }} /></div>)}</div> : key === "body" ? <Textarea id={`block-${key}`} className="mt-1" rows={3} value={drafts[key]} disabled={busy === key} onChange={(event) => setDrafts({ ...drafts, [key]: event.target.value })} /> : <Input id={`block-${key}`} className="mt-1" value={drafts[key]} disabled={busy === key} onChange={(event) => setDrafts({ ...drafts, [key]: event.target.value })} />}<Button className="mt-2" size="sm" variant="outline" disabled={busy === key || !drafts[key].trim() || drafts[key] === slide.blocks[key].text || (key === "body" && selectedLayout === "comparison" && !drafts.body.split("|", 2)[1]?.trim())} onClick={() => void run(key, () => editSlideBlock(project, selectedId, key, drafts[key]))}>Save {blockLabels[key].toLowerCase()}</Button>{key !== "source_label" && <Button className="ml-2 mt-2" size="sm" variant="ghost" disabled={busy === key || slide.blocks[key].text === (key === "title" ? project.outline.find((item) => item.id === selectedId)?.title : project.outline.find((item) => item.id === selectedId)?.key_message)} onClick={() => void run(key, () => resetBlockFromOutline(project, selectedId, key))}>Reset from outline</Button>}</div>)}<p className="text-xs text-muted-foreground">This is a draft from the approved outline. Review every slide and source before presenting. Source labels can be edited manually.</p></div> : <div className="rounded-xl border bg-card p-5 text-sm">{slide.status === "error" ? <><p>Slide build failed.</p><Button className="mt-3" disabled={Boolean(busy)} onClick={() => void run("retry", () => retrySlide(project, selectedId))}>Retry this slide</Button></> : <p>{slide.status === "generating" ? "Building this slide…" : "This slide is queued."}</p>}</div>}</>}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
  </section>;
}
