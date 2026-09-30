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
});

export const projectSchema = z.object({
  id: z.string(),
  language: z.literal("en"),
  phase: z.enum(["intake", "outline_draft", "outline_approved", "building", "ready", "error"]),
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
    layout_type: z.enum(["title", "content", "comparison"]),
  })),
  slides: z.array(z.object({
    id: z.string(),
    status: z.enum(["queued", "generating", "ready", "error"]),
    revision: z.number().int().nonnegative(),
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
  return projectRequest(project.id, "/outline/generate", "POST", { expected_revision: project.revision });
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
