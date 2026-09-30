import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppHeader from "@/components/AppHeader";
import OutlineEditor from "@/components/OutlineEditor";
import SlideWorkspace from "@/components/SlideWorkspace";
import { getProject, type Project } from "@/lib/project-api";

export default function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState("");
  const acceptProject = (fresh: Project) => setProject((current) =>
    current && fresh.id === current.id && fresh.revision < current.revision ? current : fresh
  );
  const working = project?.phase === "building" || project?.slides.some((slide) =>
    Object.values(slide.blocks).some((block) => block.status === "generating")
  );

  useEffect(() => {
    if (!projectId) return;
    getProject(projectId).then(setProject).catch((reason) => {
      setError(reason instanceof Error ? reason.message : "Project could not be loaded.");
    });
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !working) return;
    const timer = window.setInterval(() => {
      getProject(projectId).then((fresh) => setProject((current) =>
        current && fresh.revision <= current.revision ? current : fresh
      )).catch(() => undefined);
    }, 600);
    return () => window.clearInterval(timer);
  }, [projectId, working]);

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="container max-w-3xl py-10 sm:py-14">
        <Link to="/projects/new" className="text-sm text-muted-foreground hover:text-foreground">← New project</Link>
        <p className="mt-8 text-xs font-semibold uppercase tracking-widest text-primary">Academic MVP · Saved inputs</p>
        <h1 className="mt-2 font-display text-3xl font-bold">Presentation project</h1>
        {error && <p role="alert" className="mt-6 text-destructive">{error}</p>}
        {!project && !error && <p className="mt-6">Loading project…</p>}
        {project && <div className="mt-8 space-y-5">
          <p className="text-sm text-muted-foreground">Phase: {project.phase} · Theme: {project.theme.replace(/_/g, " ")}</p>
          <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Assignment</h2><p className="mt-3 whitespace-pre-wrap text-sm">{project.assignment_text}</p></section>
          <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Context Pack</h2><p className="mt-3 whitespace-pre-wrap text-sm">{project.context_pack_text}</p></section>
          <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Source PDF</h2><p className="mt-3 text-sm">{project.source_filename ? `${project.source_filename} · indexed` : "No PDF attached yet"}</p></section>
          {project.phase === "intake" || project.phase === "outline_draft"
            ? <OutlineEditor project={project} onChange={acceptProject} />
            : <details className="rounded-xl border bg-card p-5"><summary className="cursor-pointer font-semibold">Approved outline</summary><div className="mt-4"><OutlineEditor project={project} onChange={acceptProject} /></div></details>}
          {!["intake", "outline_draft"].includes(project.phase) && <SlideWorkspace project={project} onChange={acceptProject} />}
        </div>}
      </main>
    </div>
  );
}
