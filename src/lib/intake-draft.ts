import { z } from 'zod';
import { projectSchema } from '@/lib/project-api';

export const intakeStorageKey = `slidecraft.intake.v1:${import.meta.env.VITE_API_BASE_URL || 'same-origin'}`;
const intakeSchema = z.object({
  assignment: z.string(),
  contextPack: z.string(),
  theme: projectSchema.shape.theme,
  sourceId: z.string().nullable(),
  filename: z.string().nullable(),
});
export type IntakeDraft = z.infer<typeof intakeSchema>;
export const emptyIntakeDraft: IntakeDraft = {assignment: '', contextPack: '', theme: 'clean_editorial', sourceId: null, filename: null};

export function restoreIntakeDraft(): IntakeDraft {
  try {
    const raw = localStorage.getItem(intakeStorageKey);
    return raw ? intakeSchema.parse(JSON.parse(raw)) : {...emptyIntakeDraft};
  } catch { return {...emptyIntakeDraft}; }
}

export function storeIntakeDraft(draft: IntakeDraft): boolean {
  try { localStorage.setItem(intakeStorageKey, JSON.stringify(draft)); return true; }
  catch { return false; }
}
