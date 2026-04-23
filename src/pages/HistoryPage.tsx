import { useState, useEffect } from "react";
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Link } from "react-router-dom";
import { getHistory, type HistoryEntry } from "@/lib/history";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sparkles, ExternalLink, Trash2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const STATUS_BADGE: Record<string, string> = {
  queued: "bg-muted text-muted-foreground",
  running: "bg-primary/10 text-primary",
  done: "bg-success/10 text-success",
  error: "bg-destructive/10 text-destructive",
};

export default function HistoryPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setEntries(getHistory());
  }, []);

  const clearHistory = () => {
    localStorage.removeItem("ai-pres-history");
    setEntries([]);
  };

  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/", { replace: true });
  }, [logout, navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display font-bold text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
          <div className="flex items-center gap-3">
            <Button asChild>
              <Link to="/generate">Создать</Link>
            </Button>
            <Button variant="outline" onClick={handleLogout}>
              Выйти
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 container py-8 max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-display font-bold">История генераций</h1>
          {entries.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearHistory} className="gap-1 text-muted-foreground">
              <Trash2 className="h-4 w-4" />
              Очистить
            </Button>
          )}
        </div>

        {entries.length === 0 ? (
          <div className="rounded-xl border bg-card p-12 text-center space-y-4">
            <p className="text-muted-foreground">Пока нет генераций</p>
            <Button asChild>
              <Link to="/generate">Создать первую презентацию</Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((e) => (
              <Link
                key={e.job_id}
                to={`/jobs/${e.job_id}`}
                className="flex items-center justify-between rounded-lg border bg-card p-4 shadow-card hover:shadow-elevated transition-shadow group"
              >
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm font-medium truncate">{e.prompt_snippet || "Без описания"}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(e.created_at).toLocaleString("ru-RU")}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge variant="secondary" className={STATUS_BADGE[e.status] || ""}>
                    {e.status}
                  </Badge>
                  <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
