import type { Project } from "@/lib/project-api";

export const palettes: Record<Project["theme"], { background: string; foreground: string; muted: string; accent: string; panel: string }> = {
  clean_editorial: { background: "#fffcf7", foreground: "#111827", muted: "#57534e", accent: "#334155", panel: "#ffffff" },
  dark_tech_pitch: { background: "#0b1020", foreground: "#f8fafc", muted: "#a3b2c8", accent: "#22c55e", panel: "#162238" },
  infographic_bright: { background: "#f0f9ff", foreground: "#0f172a", muted: "#0369a1", accent: "#0ea5e9", panel: "#ffffff" },
};
