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

export const projectCreateSchema = z.object({
  assignment_text: z.string().trim().min(1, "Add the assignment"),
  context_pack_text: z.string().trim().min(1, "Add a Context Pack"),
  source_document_id: z.string().nullable(),
  theme: projectSchema.shape.theme,
  language: z.literal("en"),
});

export type ProjectCreate = z.infer<typeof projectCreateSchema>;

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
