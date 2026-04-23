import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  type AuthSession,
  type AuthUser,
  getStoredSession,
  login as loginWithPassword,
  logout as logoutFromStorage,
  signup as signupWithPassword,
} from "@/lib/auth";

interface AuthContextValue {
  session: AuthSession | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedSession = getStoredSession();
    setSession(storedSession);
    setIsLoading(false);
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
