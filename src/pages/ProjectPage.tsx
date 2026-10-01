import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppHeader from "@/components/AppHeader";
import LiveDraftEditor from "@/components/LiveDraftEditor";
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
  const working = project?.phase === "designing" || project?.phase === "drafting" || project?.phase === "building" || project?.slides.some((slide) =>
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
    }, 300);
    return () => window.clearInterval(timer);
  }, [projectId, working]);

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="container max-w-[1500px] py-5 sm:py-6">
        <Link to="/projects/new" className="text-sm text-muted-foreground hover:text-foreground">← New project</Link>
        {error && <p role="alert" className="mt-6 text-destructive">{error}</p>}
        {!project && !error && <p className="mt-6">Loading project…</p>}
        {project && <div className="mt-4 space-y-4">
          <details className="border-b pb-4"><summary className="cursor-pointer text-sm text-muted-foreground">Assignment, Context Pack & shared PDF</summary><div className="mt-4 grid gap-5 md:grid-cols-2"><section><h2 className="font-semibold">Assignment</h2><p className="mt-2 whitespace-pre-wrap text-sm">{project.assignment_text}</p></section><section><h2 className="font-semibold">Context Pack</h2><p className="mt-2 whitespace-pre-wrap text-sm">{project.context_pack_text}</p></section></div><p className="mt-4 text-sm">{project.source_filename || "No PDF uploaded"}</p></details>
          {(["intake", "designing", "drafting", "outline_draft", "ready"].includes(project.phase) || (project.phase === "error" && !project.outline.length)) && (project.phase !== "outline_draft" || project.slides.length > 0) ? <LiveDraftEditor project={project} onChange={acceptProject}/> : <>
          {project.phase === "intake" || project.phase === "outline_draft"
            ? <OutlineEditor project={project} onChange={acceptProject} />
            : <details className="rounded-xl border bg-card p-5"><summary className="cursor-pointer font-semibold">Approved outline</summary><div className="mt-4"><OutlineEditor project={project} onChange={acceptProject} /></div></details>}
          {!["intake", "outline_draft"].includes(project.phase) && <SlideWorkspace project={project} onChange={acceptProject} />}
          </>}
        </div>}
      </main>
    </div>
  );
}
