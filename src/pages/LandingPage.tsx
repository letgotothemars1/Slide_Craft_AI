import React, { useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import AppHeader from "@/components/AppHeader";
import Reveal from "@/components/Reveal";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useTypewriter } from "@/hooks/useTypewriter";
import { track } from "@/lib/analytics";
import type { TranslationKey } from "@/lib/i18n";
import {
  Sparkles, Layers, Zap, FileText, Route, BarChart3, Type,
  ArrowRight, Briefcase, GraduationCap, Plane, Play, CheckCircle2, Download,
  Image as ImageIcon, Table2,
  type LucideIcon,
} from "lucide-react";

/* ─── data ─── */

interface CardItem {
  icon: LucideIcon;
  titleKey: TranslationKey;
  descKey: TranslationKey;
  /** Highlighted cards get a tinted panel; `tint` picks which brand hue. */
  tint?: "primary" | "accent";
}

// Ordered by how strongly each one differentiates us, not by implementation order.
const FEATURES: CardItem[] = [
  { icon: Route, titleKey: "features.routing.title", descKey: "features.routing.desc", tint: "primary" },
  { icon: BarChart3, titleKey: "features.charts.title", descKey: "features.charts.desc", tint: "accent" },
  { icon: Type, titleKey: "features.titles.title", descKey: "features.titles.desc", tint: "primary" },
  { icon: FileText, titleKey: "features.document.title", descKey: "features.document.desc" },
  { icon: Layers, titleKey: "features.formats.title", descKey: "features.formats.desc" },
  { icon: Zap, titleKey: "features.speed.title", descKey: "features.speed.desc" },
];

const USE_CASES: CardItem[] = [
  { icon: BarChart3, titleKey: "useCases.analytics.title", descKey: "useCases.analytics.desc" },
  { icon: Briefcase, titleKey: "useCases.pitch.title", descKey: "useCases.pitch.desc" },
  { icon: GraduationCap, titleKey: "useCases.education.title", descKey: "useCases.education.desc" },
  { icon: Plane, titleKey: "useCases.visual.title", descKey: "useCases.visual.desc" },
];

const STEPS: { step: string; titleKey: TranslationKey; descKey: TranslationKey }[] = [
  { step: "1", titleKey: "steps.1.title", descKey: "steps.1.desc" },
  { step: "2", titleKey: "steps.2.title", descKey: "steps.2.desc" },
  { step: "3", titleKey: "steps.3.title", descKey: "steps.3.desc" },
];

const CHIPS: { icon: LucideIcon; key: TranslationKey }[] = [
  { icon: Route, key: "hero.chips.structure" },
  { icon: Table2, key: "hero.chips.charts" },
  { icon: ImageIcon, key: "hero.chips.images" },
  { icon: FileText, key: "hero.chips.document" },
];

/* ─── hero product preview ─── */
/* Decorative: a scaled-down stand-in for real output. Hidden from assistive
   tech — the surrounding copy already says what the product produces. */

const CHART_BARS = [38, 55, 47, 72, 64, 88];

function HeroPreview() {
  const { t } = useLanguage();
  // Memoised: a fresh array each render would restart the typing loop forever.
  const topics = useMemo(
    () => [t("preview.topic1"), t("preview.topic2"), t("preview.topic3"), t("preview.topic4")],
    [t],
  );
  const { text, typing, animated } = useTypewriter(topics);

  return (
    <div className="relative mx-auto w-full max-w-4xl" aria-hidden="true">
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-elevated">
        {/* browser chrome */}
        <div className="flex items-center gap-1.5 border-b border-border bg-muted/40 px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-destructive/30" />
          <span className="h-2.5 w-2.5 rounded-full bg-warning/30" />
          <span className="h-2.5 w-2.5 rounded-full bg-success/30" />
          <div className="ml-3 flex h-6 flex-1 items-center rounded-md bg-muted/80 px-2.5">
            <span className="font-mono text-[11px] text-muted-foreground">slidecraft.org</span>
          </div>
        </div>

        {/* prompt bar — the input half of the story */}
        <div className="border-b border-border px-5 py-4 sm:px-7 sm:py-5">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {t("preview.promptLabel")}
          </p>
          <div className="flex items-center gap-3">
            <div className="flex h-10 flex-1 items-center overflow-hidden rounded-lg border border-border bg-background px-3 text-sm">
              <span className={animated && !typing ? "caret" : ""}>{text}</span>
            </div>
            <span className="hidden h-10 shrink-0 items-center gap-1.5 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground sm:inline-flex">
              <Sparkles className="h-3.5 w-3.5" />
              {t("preview.generate")}
            </span>
          </div>
        </div>

        {/* output half — the deck */}
        <div className="grid gap-3 p-5 sm:grid-cols-[1.6fr,1fr] sm:p-7">
          {/* main slide — 16:9, matches real output */}
          <div className="aspect-[16/9] rounded-lg border border-border bg-background p-4 sm:p-5">
            <div className="mb-3 h-1 w-10 rounded-full gradient-hero" />
            <p className="text-xs font-semibold leading-tight sm:text-sm">{t("preview.slideTitle")}</p>
            {/* Bars are direct flex children: a percentage height needs a parent
                with a resolved height, which `items-end` + fixed height gives. */}
            <div className="mt-4 flex h-[46%] items-end gap-2">
              {CHART_BARS.map((h, i) => (
                <div
                  key={i}
                  className="bar-grow flex-1 rounded-sm bg-primary"
                  style={{
                    height: `${h}%`,
                    opacity: 0.35 + i * 0.11,
                    transitionDelay: `${300 + i * 70}ms`,
                  }}
                />
              ))}
            </div>
            <div className="mt-2 flex gap-2">
              {["Q1", "Q2", "Q3", "Q4", "Q1", "Q2"].map((q, i) => (
                <span key={i} className="flex-1 text-center text-[10px] text-muted-foreground">
                  {q}
                </span>
              ))}
            </div>
          </div>

          {/* filmstrip — rest of the deck */}
          <div className="grid grid-cols-4 gap-2 sm:grid-cols-2">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="aspect-[16/9] rounded border border-border bg-background p-2">
                <div className="mb-1.5 h-0.5 w-4 rounded-full bg-primary/40" />
                <div className="space-y-1">
                  <div className="h-0.5 w-full rounded-full bg-muted-foreground/25" />
                  <div className="h-0.5 w-3/4 rounded-full bg-muted-foreground/15" />
                  {i % 2 === 0 && <div className="h-0.5 w-1/2 rounded-full bg-muted-foreground/15" />}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* status bar */}
        <div className="flex items-center gap-2 border-t border-border px-5 py-3 sm:px-7">
          <CheckCircle2 className="h-4 w-4 text-success-strong" />
          <span className="text-xs font-medium text-success-strong">{t("preview.ready")}</span>
          <span className="ml-auto flex items-center gap-1.5 rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
            <Download className="h-3 w-3" />
            {t("preview.meta")}
          </span>
        </div>
      </div>

      <div className="absolute -inset-8 -z-10 rounded-[2rem] bg-primary/[0.05] blur-3xl" />
    </div>
  );
}

/* ─── page ─── */

export default function LandingPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const ctaLink = user ? "/generate" : "/auth";

  useEffect(() => {
    track("page_view", { page: "landing", authed: Boolean(user) });
    // We intentionally fire page_view once per mount, not on auth changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCtaClick = (source: string) => {
    track("cta_click", { source, authed: Boolean(user) });
  };


  return (
    <div className="flex min-h-screen flex-col bg-background">
      <AppHeader onCtaClick={handleCtaClick} />

      <main className="flex-1">
        {/* ── Hero — centred, product visual below ── */}
        <section className="relative overflow-hidden px-4 pb-20 pt-16 sm:pt-24">
          {/* soft backdrop wash */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[520px] bg-gradient-to-b from-primary/[0.06] via-accent/[0.03] to-transparent"
          />

          <div className="container max-w-5xl">
            <Reveal className="mx-auto max-w-3xl space-y-7 text-center">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3.5 py-1.5 text-xs font-medium text-primary">
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                {t("hero.badge")}
              </div>

              <h1 className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl lg:text-[4.25rem]">
                {t("hero.titleLead")}{" "}
                <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  {t("hero.titleAccent")}
                </span>
              </h1>

              <p className="mx-auto max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
                {t("hero.subtitle")}
              </p>

              <div className="flex flex-wrap items-center justify-center gap-3">
                <Button size="lg" asChild className="h-[52px] rounded-full px-8 text-base shadow-elevated">
                  <Link to={ctaLink} onClick={() => handleCtaClick("hero")}>
                    <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
                    {t("hero.cta")}
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="h-[52px] rounded-full px-6 text-base">
                  <a href="#how-it-works">
                    <Play className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
                    {t("hero.secondary")}
                  </a>
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">{t("hero.note")}</p>

              {/* capability chips */}
              <ul className="flex flex-wrap items-center justify-center gap-2 pt-1">
                {CHIPS.map(({ icon: Icon, key }) => (
                  <li
                    key={key}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground shadow-card"
                  >
                    <Icon className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    {t(key)}
                  </li>
                ))}
              </ul>
            </Reveal>

            <Reveal delay={120} className="mt-14">
              <HeroPreview />
            </Reveal>
          </div>
        </section>

        {/* ── How it works ── */}
        <section id="how-it-works" className="scroll-mt-16 border-y border-border/60 bg-muted/30 py-20">
          <div className="container max-w-3xl space-y-10">
            <Reveal className="space-y-2 text-center">
              <h2 className="font-display text-2xl font-bold sm:text-3xl">{t("steps.title")}</h2>
              <p className="text-sm text-muted-foreground">{t("steps.subtitle")}</p>
            </Reveal>
            <ol className="flex flex-col items-stretch gap-3 md:flex-row md:gap-0">
              {STEPS.map((s, i) => (
                <React.Fragment key={s.step}>
                  <Reveal as="li" delay={i * 110} className="flex-1">
                    <div className="h-full space-y-2 rounded-xl border border-border bg-card p-5 text-center shadow-card">
                      <span className="inline-flex h-9 w-9 items-center justify-center rounded-full gradient-hero text-sm font-bold text-primary-foreground">
                        {s.step}
                      </span>
                      <h3 className="text-sm font-semibold">{t(s.titleKey)}</h3>
                      <p className="text-xs leading-relaxed text-muted-foreground">{t(s.descKey)}</p>
                    </div>
                  </Reveal>
                  {i < STEPS.length - 1 && (
                    <li aria-hidden="true" className="hidden w-8 shrink-0 items-center justify-center md:flex">
                      <ArrowRight className="h-4 w-4 text-muted-foreground/50" />
                    </li>
                  )}
                </React.Fragment>
              ))}
            </ol>
          </div>
        </section>

        {/* ── Features ── */}
        <section className="py-24">
          <div className="container max-w-5xl space-y-12">
            <Reveal className="space-y-3 text-center">
              <h2 className="font-display text-3xl font-bold sm:text-4xl">{t("features.title")}</h2>
              <p className="mx-auto max-w-xl text-sm text-muted-foreground sm:text-base">
                {t("features.subtitle")}
              </p>
            </Reveal>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((f, i) => {
                const Icon = f.icon;
                const panel =
                  f.tint === "primary"
                    ? "border-primary/20 bg-primary/[0.04] shadow-elevated"
                    : f.tint === "accent"
                      ? "border-accent/20 bg-accent/[0.04] shadow-elevated"
                      : "border-border bg-card shadow-card hover:shadow-elevated";
                return (
                  <Reveal as="article" key={f.titleKey} delay={i * 80} className="h-full">
                    <div
                      className={`h-full space-y-3 rounded-2xl border p-6 transition-shadow duration-200 ${panel}`}
                    >
                      <span
                        className={`inline-flex h-10 w-10 items-center justify-center rounded-xl ${
                          f.tint === "accent" ? "bg-accent/10" : f.tint ? "bg-primary/10" : "bg-muted"
                        }`}
                      >
                        <Icon
                          className={`h-5 w-5 ${f.tint === "accent" ? "text-accent" : "text-primary"}`}
                          aria-hidden="true"
                        />
                      </span>
                      <h3 className="text-base font-semibold">{t(f.titleKey)}</h3>
                      <p className="text-sm leading-relaxed text-muted-foreground">{t(f.descKey)}</p>
                    </div>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Use cases ── */}
        <section className="border-y border-border/60 bg-muted/30 py-20">
          <div className="container max-w-5xl space-y-10">
            <Reveal className="space-y-2 text-center">
              <h2 className="font-display text-2xl font-bold sm:text-3xl">{t("useCases.title")}</h2>
              <p className="text-sm text-muted-foreground">{t("useCases.subtitle")}</p>
            </Reveal>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {USE_CASES.map((u, i) => {
                const Icon = u.icon;
                return (
                  <Reveal as="article" key={u.titleKey} delay={i * 80} className="h-full">
                    <div className="h-full space-y-2.5 rounded-2xl border border-border bg-card p-5 shadow-card transition-shadow hover:shadow-elevated">
                      <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                        <Icon className="h-[18px] w-[18px] text-primary" aria-hidden="true" />
                      </span>
                      <h3 className="text-sm font-semibold">{t(u.titleKey)}</h3>
                      <p className="text-xs leading-relaxed text-muted-foreground">{t(u.descKey)}</p>
                    </div>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Final CTA ── */}
        <section className="py-24">
          <div className="container max-w-2xl">
            <Reveal>
              <div className="relative overflow-hidden rounded-3xl border border-primary/15 bg-primary/[0.03] p-12 text-center shadow-elevated">
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-accent/10 blur-3xl"
                />
                <div className="relative space-y-4">
                  <span className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-2xl gradient-hero text-primary-foreground">
                    <Sparkles className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <h2 className="font-display text-2xl font-bold sm:text-3xl">{t("cta.title")}</h2>
                  <p className="mx-auto max-w-sm text-sm text-muted-foreground">{t("cta.subtitle")}</p>
                  <div className="pt-2">
                    <Button size="lg" asChild className="h-[52px] rounded-full px-8 text-base shadow-elevated">
                      <Link to={ctaLink} onClick={() => handleCtaClick("footer")}>
                        <Sparkles className="mr-2 h-4 w-4" aria-hidden="true" />
                        {t("cta.button")}
                      </Link>
                    </Button>
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="mt-auto border-t border-border bg-card">
        <div className="container max-w-5xl py-10">
          <div className="flex flex-col items-center justify-between gap-6 sm:flex-row sm:items-start">
            <div className="space-y-2 text-center sm:text-left">
              <span className="flex items-center justify-center gap-2 font-display font-bold sm:justify-start">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
                SlideCraft AI
              </span>
              <p className="max-w-xs text-xs leading-relaxed text-muted-foreground">
                {t("footer.tagline")}
              </p>
            </div>

            <nav aria-label={t("footer.nav")}>
              <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
                <li>
                  <Link
                    to={ctaLink}
                    className="rounded text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {t("footer.create")}
                  </Link>
                </li>
                <li>
                  <Link
                    to="/history"
                    className="rounded text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {t("footer.history")}
                  </Link>
                </li>
                <li>
                  <a
                    href="#how-it-works"
                    className="rounded text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {t("footer.how")}
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          <div className="mt-8 border-t border-border pt-5 text-center text-xs text-muted-foreground sm:text-right">
            © {new Date().getFullYear()} SlideCraft AI
          </div>
        </div>
      </footer>
    </div>
  );
}
