import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { cn } from "@/lib/utils";

type AuthMode = "login" | "signup";

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, signup } = useAuth();
  const { t } = useLanguage();

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: string } | undefined)?.from || "/generate";
  const isLogin = mode === "login";

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await signup(email, password);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || t("auth.error"));
    } finally {
      setLoading(false);
    }
  };

  const tabClass = (active: boolean) =>
    cn(
      "inline-flex h-10 flex-1 cursor-pointer items-center justify-center rounded-md text-sm font-medium transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
      active ? "bg-card text-foreground shadow-card" : "text-muted-foreground hover:text-foreground",
    );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader minimal />

      <main className="flex flex-1 items-center justify-center px-4 py-14">
        <Reveal className="w-full max-w-md">
          <div className="space-y-6 rounded-2xl border border-border bg-card p-8 shadow-elevated">
            <div className="space-y-2 text-center">
              <h1 className="font-display text-2xl font-bold">
                {isLogin ? t("auth.loginTitle") : t("auth.signupTitle")}
              </h1>
              <p className="text-sm text-muted-foreground">
                {isLogin ? t("auth.loginSubtitle") : t("auth.signupSubtitle")}
              </p>
            </div>

            {/* Tabs as buttons with aria-pressed: two options, both always visible. */}
            <div role="group" aria-label={t("auth.loginTitle")} className="flex gap-1 rounded-lg bg-muted p-1">
              <button
                type="button"
                aria-pressed={isLogin}
                onClick={() => setMode("login")}
                className={tabClass(isLogin)}
              >
                {t("auth.tabLogin")}
              </button>
              <button
                type="button"
                aria-pressed={!isLogin}
                onClick={() => setMode("signup")}
                className={tabClass(!isLogin)}
              >
                {t("auth.tabSignup")}
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">{t("auth.email")}</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.password")}</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  className="h-11"
                />
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}

              <Button type="submit" className="h-11 w-full rounded-full" disabled={loading}>
                {loading ? t("auth.pending") : isLogin ? t("auth.submitLogin") : t("auth.submitSignup")}
              </Button>
            </form>
          </div>
        </Reveal>
      </main>
    </div>
  );
}
