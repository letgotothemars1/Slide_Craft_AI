/**
 * Lightweight client-side analytics: anonymous session id + fire-and-forget event tracker.
 *
 * - session_id lives in localStorage; same browser = same session across visits/tabs
 * - track() never throws and never blocks the UI on network errors
 * - in production the API base is "" (same origin), so requests go through Nginx → backend
 */

const SESSION_KEY = "slidecraft-session-id";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";

/**
 * Backend listens on POST /events/track. Frontend sends:
 *   { session_id, event_type, metadata? }
 * Server enriches with IP hash, user-agent and referer from request headers.
 */
function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  try {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing && existing.length >= 8) return existing;
    const fresh = generateSessionId();
    localStorage.setItem(SESSION_KEY, fresh);
    return fresh;
  } catch {
    // Private mode / disabled storage → return ephemeral id (not persisted).
    return generateSessionId();
  }
}

function generateSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback (old browsers): 16 bytes of random hex.
  const arr = new Uint8Array(16);
  if (typeof crypto !== "undefined" && "getRandomValues" in crypto) {
    crypto.getRandomValues(arr);
  } else {
    for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function getSessionId(): string {
  return getOrCreateSessionId();
}

export type TrackableEvent =
  | "page_view"
  | "cta_click"
  | "generate_click"
  | "job_done";

/**
 * Fire-and-forget event tracker.
 * - Uses navigator.sendBeacon when available (works during page unload).
 * - Falls back to fetch with keepalive.
 * - All network/serialization errors are swallowed: analytics must never break the UI.
 */
export function track(event: TrackableEvent, metadata?: Record<string, unknown>): void {
  if (typeof window === "undefined") return;

  const payload = {
    session_id: getOrCreateSessionId(),
    event_type: event,
    metadata: metadata ?? null,
  };

  const url = `${API_BASE}/events/track`;
  const body = JSON.stringify(payload);

  try {
    if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
      const blob = new Blob([body], { type: "application/json" });
      const ok = navigator.sendBeacon(url, blob);
      if (ok) return;
    }
    // Fallback: regular fetch, kept alive so it can fly during navigations.
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => {
      // Ignored on purpose — analytics never breaks the UI.
    });
  } catch {
    // Ignored on purpose.
  }
}
