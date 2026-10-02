import { z } from "zod";

const sourceRefSchema = z.object({
  document_id: z.string(),
  filename: z.string(),
  page_number: z.number().int().positive(),
  excerpt: z.string(),
});

const blockSchema = z.object({
  text: z.string(),
  status: z.enum(["ready", "generating", "error"]),
  revision: z.number().int().nonnegative(),
  error: z.string().nullable().optional(),
});

export const projectSchema = z.object({
  id: z.string(),
  language: z.literal("en"),
  phase: z.enum(["intake", "designing", "drafting", "outline_draft", "outline_approved", "building", "ready", "error"]),
  revision: z.number().int().nonnegative(),
  assignment_text: z.string(),
  context_pack_text: z.string(),
  source_document_id: z.string().nullable(),
  source_filename: z.string().nullable(),
  theme: z.enum(["clean_editorial", "dark_tech_pitch", "infographic_bright"]),
  build_mode: z.enum(["template", "model"]).default("template"),
  outline: z.array(z.object({
    id: z.string(),
    order: z.number().int().positive(),
    purpose: z.string(),
    title: z.string(),
    key_message: z.string(),
    evidence_refs: z.array(sourceRefSchema),
    suggested_refs: z.array(sourceRefSchema).default([]),
    layout_type: z.enum(["title", "content", "comparison"]),
  })),
  slides: z.array(z.object({
    id: z.string(),
    status: z.enum(["queued", "generating", "ready", "error"]),
    revision: z.number().int().nonnegative(),
    design: z.object({layout:z.enum(['hero','editorial','chart','process','comparison','statement']),emphasis:z.enum(['quiet','accent','inverse']),rationale:z.string(),arrangement:z.enum(['columns','rows']).optional(),visual:z.object({kind:z.enum(['none','process','bars']),labels:z.array(z.string()),values:z.array(z.number()),unit:z.string()}).nullable().optional()}).nullable().optional(),
    design_status: z.enum(['none','queued','generating','ready','error']).optional(),
    design_error: z.string().nullable().optional(),
    sections: z.array(z.object({id:z.string(),heading:z.string(),text:z.string()})).optional(),
    sections_status:z.enum(['none','generating','ready','error']).optional(),
    sections_error:z.string().nullable().optional(),
    design_stage:z.enum(['none','composing','checking','refining','complete']).optional(),
    quality_issues:z.array(z.string()).optional(),
    quality_attempts:z.number().optional(),
    scene: z.array(z.object({kind:z.enum(['text','rect']),x:z.number(),y:z.number(),w:z.number(),h:z.number(),text:z.string(),color:z.string(),size:z.number(),bold:z.boolean(),font:z.enum(['Arial','Georgia']),block_key:z.enum(['title','body','source_label']).nullable(),column:z.number().nullable(),section_id:z.string().nullable().optional(),section_field:z.enum(['heading','text']).nullable().optional()})).optional(),
    show_source: z.boolean().optional(),
    revision_instruction: z.string().optional(),
    visual: z.object({kind: z.enum(["none","process","bars"]), labels: z.array(z.string()), values: z.array(z.number()), unit: z.string()}).nullable().optional(),
    blocks: z.object({ title: blockSchema, body: blockSchema, source_label: blockSchema }),
  })),
});

export type Project = z.infer<typeof projectSchema>;
export type OutlineItem = Project["outline"][number];
export type SourceRef = OutlineItem["evidence_refs"][number];

export const projectCreateSchema = z.object({
  assignment_text: z.string().trim().min(1, "Add the assignment"),
  context_pack_text: z.string().trim().min(1, "Add a Context Pack"),
  source_document_id: z.string().nullable(),
  theme: projectSchema.shape.theme,
  language: z.literal("en"),
});

export type ProjectCreate = z.infer<typeof projectCreateSchema>;

const demoMaterialsSchema = z.object({
  assignment_text: z.string().min(1),
  context_pack_text: z.string().min(1),
  source_filename: z.string().min(1),
});

export async function getDemoMaterials(): Promise<z.infer<typeof demoMaterialsSchema>> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects/demo/materials`);
  if (!response.ok) throw new Error(`Demo materials could not be loaded (${response.status})`);
  return demoMaterialsSchema.parse(await response.json());
}

export async function getDemoPdf(): Promise<Blob> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects/demo/source.pdf`);
  if (!response.ok) throw new Error(`Demo PDF could not be loaded (${response.status})`);
  return response.blob();
}

export async function createProject(input: ProjectCreate): Promise<Project> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(projectCreateSchema.parse(input)),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(typeof detail?.detail === "string" ? detail.detail : `Project could not be saved (${response.status})`);
  }
  return projectSchema.parse(await response.json());
}

export async function getProject(projectId: string): Promise<Project> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects/${encodeURIComponent(projectId)}`);
  if (!response.ok) throw new Error(`Project request failed: ${response.status}`);
  return projectSchema.parse(await response.json());
}

async function projectRequest(projectId: string, path: string, method: string, body: unknown): Promise<Project> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects/${encodeURIComponent(projectId)}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : typeof detail?.message === "string" ? detail.message : `Project request failed: ${response.status}`);
  }
  return projectSchema.parse(await response.json());
}

export function createStarterOutline(project: Project): Promise<Project> {
  return projectRequest(project.id, "/outline/generate", "POST", { expected_revision: project.revision, mode: "template" });
}

export function createModelOutline(project: Project): Promise<Project> {
  return projectRequest(project.id, "/outline/generate", "POST", { expected_revision: project.revision, mode: "model" });
}

export function saveOutline(project: Project, outline: OutlineItem[]): Promise<Project> {
  return projectRequest(project.id, "/outline", "PUT", { expected_revision: project.revision, outline });
}

export function approveOutline(project: Project, theme: Project["theme"]): Promise<Project> {
  return projectRequest(project.id, "/outline/approve", "POST", { expected_revision: project.revision, theme });
}

export function buildProject(project: Project, mode: "template" | "model" = "template"): Promise<Project> {
  return projectRequest(project.id, "/build", "POST", { expected_revision: project.revision, mode });
}

export function editSlideBlock(project: Project, slideId: string, blockKey: "title" | "body" | "source_label", text: string): Promise<Project> {
  return projectRequest(project.id, `/slides/${encodeURIComponent(slideId)}/blocks/${blockKey}`, "PATCH", {
    expected_revision: project.revision, text,
  });
}

export function resetBlockFromOutline(project: Project, slideId: string, blockKey: "title" | "body"): Promise<Project> {
  return projectRequest(project.id, `/slides/${encodeURIComponent(slideId)}/blocks/${blockKey}/reset-from-outline`, "POST", {
    expected_revision: project.revision,
  });
}

export function regenerateBlock(project: Project, slideId: string, blockKey: "title" | "body"): Promise<Project> {
  return projectRequest(project.id, `/slides/${encodeURIComponent(slideId)}/blocks/${blockKey}/regenerate`, "POST", {
    expected_revision: project.revision,
  });
}

export function retrySlide(project: Project, slideId: string): Promise<Project> {
  return projectRequest(project.id, `/slides/${encodeURIComponent(slideId)}/retry`, "POST", {
    expected_revision: project.revision,
  });
}

export function exportPptxUrl(projectId: string): string {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  return `${apiBase}/projects/${encodeURIComponent(projectId)}/export.pptx`;
}

export async function getSourceCandidates(projectId: string): Promise<SourceRef[]> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string) || "";
  const response = await fetch(`${apiBase}/projects/${encodeURIComponent(projectId)}/source-candidates`);
  if (!response.ok) throw new Error(`Source request failed: ${response.status}`);
  return z.array(sourceRefSchema).parse(await response.json());
}

export async function downloadProjectPptx(projectId: string): Promise<void> {
  const response = await fetch(exportPptxUrl(projectId));
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(typeof data?.detail === "string" ? data.detail : "PPTX could not be downloaded. Try again.");
  }
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `slidecraft-${projectId}.pptx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function startLiveDraft(project: Project, mode: "model" | "template"): Promise<Project> {
  return projectRequest(project.id, "/draft/start", "POST", {expected_revision: project.revision, mode});
}
export function retryDraftSlide(project: Project, slideId: string): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/retry`, "POST", {expected_revision: project.revision});
}

export function hideSlideVisual(project: Project, slideId: string): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/visual`, "DELETE", {expected_revision: project.revision});
}

export function changeSlideComposition(project: Project, slideId: string, layout_type: OutlineItem["layout_type"]): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/composition`, "PATCH", {expected_revision: project.revision, layout_type});
}

export function confirmDraftSource(project: Project, slideId: string, source_ref: SourceRef): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/source`, "POST", {expected_revision: project.revision, source_ref});
}

export function setSlideSourceVisibility(project: Project, slideId: string, show_source: boolean): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/source-visibility`, 'PATCH', {expected_revision: project.revision, show_source});
}
export function regenerateWholeSlide(project: Project, slideId: string, instruction: string): Promise<Project> {
  return projectRequest(project.id, `/draft/slides/${encodeURIComponent(slideId)}/regenerate`, 'POST', {expected_revision: project.revision, instruction});
}

export function startAIDesign(project: Project, theme: Project['theme']): Promise<Project> {
  return projectRequest(project.id,'/design/start','POST',{expected_revision:project.revision,theme});
}
export function retryAIDesign(project: Project, slideId: string): Promise<Project> {
  return projectRequest(project.id,`/design/slides/${encodeURIComponent(slideId)}/retry`,'POST',{expected_revision:project.revision});
}


export async function prepareSlideSections(project:Project,slideId:string):Promise<Project>{
  return projectRequest(project.id,`/slides/${encodeURIComponent(slideId)}/sections/prepare`, 'POST', {expected_revision:project.revision});
}
export async function saveSlideSections(project:Project,slideId:string,sections:NonNullable<Project['slides'][number]['sections']>):Promise<Project>{
  return projectRequest(project.id,`/slides/${encodeURIComponent(slideId)}/sections`, 'PATCH', {expected_revision:project.revision,sections});
}

export function prepareAllSections(project:Project):Promise<Project>{
  return projectRequest(project.id,'/sections/prepare','POST',{expected_revision:project.revision});
}
