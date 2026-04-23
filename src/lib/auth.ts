const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export interface AuthUser {
  id: string;
  email: string;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
  createdAt: string;
}

const AUTH_SESSION_KEY = "slidecraft-auth-session";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof localStorage !== "undefined";
}

function safeParseJson<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function persistSession(session: AuthSession | null): void {
  if (!canUseStorage()) return;
  if (session) {
    localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(AUTH_SESSION_KEY);
  }
}

export function getStoredSession(): AuthSession | null {
  if (!canUseStorage()) return null;
  const session = safeParseJson<AuthSession | null>(
    localStorage.getItem(AUTH_SESSION_KEY),
    null
  );
  if (!session || !session.user?.email || !session.token) return null;
  return session;
}

async function apiAuth(
  path: string,
  email: string,
  password: string
): Promise<AuthSession> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const detail = (data as { detail?: string }).detail;
    throw new Error(detail ?? `Auth error ${res.status}`);
  }

  // Backend returns { id, email, created_at }
  const { id, email: userEmail, created_at } = data as {
    id: string;
    email: string;
    created_at: string;
  };

  const session: AuthSession = {
    token: `session-${id}-${Date.now()}`,
    user: { id, email: userEmail },
    createdAt: created_at,
  };

  persistSession(session);
  return session;
}

export async function signup(email: string, password: string): Promise<AuthSession> {
  return apiAuth("/auth/signup", email, password);
}

export async function login(email: string, password: string): Promise<AuthSession> {
  return apiAuth("/auth/login", email, password);
}

export async function logout(): Promise<void> {
  persistSession(null);
}
