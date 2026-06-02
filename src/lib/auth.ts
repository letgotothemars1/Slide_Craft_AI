const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "";

export interface AuthUser {
  id: string;
  email: string;
  isAdmin: boolean;
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

/**
 * Read the session from localStorage WITHOUT validating it server-side.
 * Used for fast initial render — the actual validation happens via restoreSession().
 */
export function getStoredSession(): AuthSession | null {
  if (!canUseStorage()) return null;
  const session = safeParseJson<AuthSession | null>(
    localStorage.getItem(AUTH_SESSION_KEY),
    null,
  );
  if (!session || !session.user?.email || !session.token) return null;
  return session;
}

/** Backend AuthResponse shape — kept here in one place. */
interface BackendAuthResponse {
  id: string;
  email: string;
  created_at: string;
  is_admin: boolean;
  token: string;
}

function sessionFromResponse(data: BackendAuthResponse): AuthSession {
  return {
    token: data.token,
    user: { id: data.id, email: data.email, isAdmin: data.is_admin },
    createdAt: data.created_at,
  };
}

async function apiAuth(
  path: string,
  email: string,
  password: string,
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

  const session = sessionFromResponse(data as BackendAuthResponse);
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

/**
 * Validate the stored token against the backend by calling /auth/me.
 *
 * Used on app start (in AuthProvider): if the token in localStorage is expired
 * or revoked, the user is silently logged out so they see a fresh login screen
 * instead of getting cryptic 401s on every later request.
 *
 * Returns the refreshed session (which may have an updated is_admin) or null
 * if the token is invalid.
 */
export async function restoreSession(): Promise<AuthSession | null> {
  const local = getStoredSession();
  if (!local) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: {
        Authorization: `Bearer ${local.token}`,
        Accept: "application/json",
        "ngrok-skip-browser-warning": "true",
      },
    });
    if (!res.ok) {
      // 401 = token expired or revoked → clear it and show fresh login
      persistSession(null);
      return null;
    }
    const data = (await res.json()) as BackendAuthResponse;
    const refreshed = sessionFromResponse(data);
    persistSession(refreshed);
    return refreshed;
  } catch {
    // Network error: trust the local copy rather than nuking it.
    return local;
  }
}

/**
 * Helper for API clients — returns the Authorization header value
 * for the current session, or an empty object if not logged in.
 */
export function authHeader(): Record<string, string> {
  const session = getStoredSession();
  if (!session) return {};
  return { Authorization: `Bearer ${session.token}` };
}

/**
 * Handle a 401 response from any protected endpoint: clear the local
 * session and bounce the browser to /auth. Used by API client helpers.
 *
 * Why redirect via location instead of useNavigate? These helpers run
 * outside React's component tree (in fetch callbacks), and we want to
 * force a clean reload so all stale state is dropped.
 */
export function handleUnauthorized(): void {
  persistSession(null);
  if (typeof window !== "undefined" && window.location.pathname !== "/auth") {
    window.location.href = "/auth";
  }
}
