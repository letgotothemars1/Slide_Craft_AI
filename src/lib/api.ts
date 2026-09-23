import { z } from "zod";

// In production the frontend and backend are served from the same origin,
// so relative paths work without CORS issues. VITE_API_BASE_URL can still
// be set for local development with a different backend host (e.g. ngrok).
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";

// --- Schemas ---

export const audienceValues = ["executives", "students", "sales", "investors", "custom"] as const;
export const styleValues = ["business", "minimal", "dark", "creative"] as const;
export const languageValues = ["ru", "en"] as const;
export const formatValues = ["pdf", "pptx", "both"] as const;
export const statusValues = ["queued", "running", "done", "error"] as const;

export const generateRequestSchema = z.object({
  prompt: z.string().trim().min(1, "Введите промпт").max(2000, "Макс. 2000 символов"),
  audience: z.enum(audienceValues),
  style: z.enum(styleValues),
  language: z.enum(languageValues),
  slides: z.number().int().min(5, "Минимум 5 слайдов").max(30, "Максимум 30 слайдов"),
  format: z.enum(formatValues),
  document_id: z.string().nullable().optional(),
  brandColor: z.string().nullable(),
  logoUrl: z.string().nullable(),
});

export type GenerateRequest = z.infer<typeof generateRequestSchema>;

export const generateResponseSchema = z.object({
  job_id: z.string(),
});

export const documentUploadResponseSchema = z.object({
  document_id: z.string(),
});

export const jobResultSchema = z.object({
  pptx_url: z.string().nullable(),
  pdf_url: z.string().nullable(),
  preview_images: z.array(z.string()).nullable(),
});

export const jobStatusSchema = z.object({
  job_id: z.string(),
  status: z.enum(statusValues),
  progress: z.number().nullable(),
  message: z.string().nullable(),
  result: jobResultSchema.nullable(),
  created_at: z.string(),
});

export type JobStatus = z.infer<typeof jobStatusSchema>;

// --- API client ---

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  const hasFormDataBody = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!hasFormDataBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  // Bypass ngrok browser interstitial page for API requests
  headers.set("ngrok-skip-browser-warning", "true");

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export async function generatePresentation(data: GenerateRequest): Promise<string> {
  const body = generateRequestSchema.parse(data);
  const res = await request<{ job_id: string }>("/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return generateResponseSchema.parse(res).job_id;
}

export async function uploadDocument(file: File): Promise<{ document_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await request<{ document_id: string }>("/documents/upload", {
    method: "POST",
    body: formData,
  });

  return documentUploadResponseSchema.parse(res);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await request<JobStatus>(`/status/${encodeURIComponent(jobId)}`);
  return jobStatusSchema.parse(res);
}
