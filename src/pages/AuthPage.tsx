import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/context/AuthContext";

type AuthMode = "login" | "signup";

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, signup } = useAuth();

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: string } | undefined)?.from || "/generate";

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await signup(email, password);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || "Не удалось выполнить авторизацию");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
        </div>
      </header>

      <main className="flex-1 container py-12 flex items-center justify-center">
        <div className="w-full max-w-md rounded-xl border bg-card p-6 shadow-card space-y-6">
          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-display font-bold">
              {mode === "login" ? "Вход" : "Создание аккаунта"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {mode === "login"
                ? "Войдите, чтобы открыть генератор и историю."
                : "Зарегистрируйтесь, чтобы сохранить доступ к генерациям."}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 rounded-lg bg-secondary p-1">
            <Button
              type="button"
              variant={mode === "login" ? "default" : "ghost"}
              onClick={() => setMode("login")}
            >
              Login
            </Button>
            <Button
              type="button"
              variant={mode === "signup" ? "default" : "ghost"}
              onClick={() => setMode("signup")}
            >
              Sign up
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading
                ? "Подождите…"
                : mode === "login"
                  ? "Войти"
                  : "Создать аккаунт"}
            </Button>
          </form>
        </div>
      </main>
    </div>
  );
}
