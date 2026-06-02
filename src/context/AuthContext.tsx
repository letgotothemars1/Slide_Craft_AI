import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  type AuthSession,
  type AuthUser,
  login as loginWithPassword,
  logout as logoutFromStorage,
  restoreSession,
  signup as signupWithPassword,
} from "@/lib/auth";

interface AuthContextValue {
  session: AuthSession | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: re-validate the token in localStorage by hitting /auth/me.
  // This catches expired/revoked tokens at boot rather than letting the user
  // hit a wall of 401s on protected pages.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const refreshed = await restoreSession();
      if (cancelled) return;
      setSession(refreshed);
      setIsLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const nextSession = await loginWithPassword(email, password);
    setSession(nextSession);
  }, []);

  const signup = useCallback(async (email: string, password: string) => {
    const nextSession = await signupWithPassword(email, password);
    setSession(nextSession);
  }, []);

  const logout = useCallback(async () => {
    await logoutFromStorage();
    setSession(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      isAuthenticated: !!session,
      isAdmin: !!session?.user?.isAdmin,
      isLoading,
      login,
      signup,
      logout,
    }),
    [session, isLoading, login, signup, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
