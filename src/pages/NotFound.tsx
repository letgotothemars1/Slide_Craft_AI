import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import AppHeader from "@/components/AppHeader";
import { useLanguage } from "@/context/LanguageContext";
import { Compass } from "lucide-react";

export default function NotFound() {
  const location = useLocation();
  const { t } = useLanguage();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader />

      <main className="flex flex-1 items-center justify-center px-4 py-16">
        <div className="max-w-md space-y-5 text-center">
          <span className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
            <Compass className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
          </span>
          <p className="font-display text-5xl font-extrabold tracking-tight text-muted-foreground/40">404</p>
          <h1 className="font-display text-2xl font-bold">{t("notFound.title")}</h1>
          <p className="text-sm leading-relaxed text-muted-foreground">{t("notFound.desc")}</p>
          {/* A router Link, not a bare <a>: the old one reloaded the whole app. */}
          <Button asChild className="h-11 rounded-full px-6">
            <Link to="/">{t("notFound.home")}</Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
