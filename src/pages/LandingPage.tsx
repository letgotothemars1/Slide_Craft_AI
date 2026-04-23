import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import {
  Sparkles, Layers, Clock, Zap, Globe, Palette, FileText,
  MessageSquare, ArrowRight, Briefcase, GraduationCap, BarChart3,
  Download, Languages, ShoppingBag, CheckCircle2, Play,
} from "lucide-react";

/* ─── data ─── */

const FEATURES = [
  { icon: <FileText className="h-5 w-5 text-primary" />, title: "Генерация по документу", desc: "Загрузите PDF — AI извлечёт ключевые идеи и превратит в презентацию", highlight: true },
  { icon: <Layers className="h-5 w-5 text-primary" />, title: "PPTX и PDF", desc: "Скачивайте в нужном формате или сразу в обоих", highlight: true },
  { icon: <Zap className="h-5 w-5 text-primary" />, title: "Мгновенная генерация", desc: "Готовая презентация за считанные минуты", highlight: true },
  { icon: <Palette className="h-5 w-5 text-primary" />, title: "Стили на выбор", desc: "Бизнес, минимал, тёмный и креативный — под любую аудиторию" },
  { icon: <Globe className="h-5 w-5 text-primary" />, title: "Мультиязычность", desc: "Генерация на русском и английском языках" },
  { icon: <Clock className="h-5 w-5 text-primary" />, title: "История задач", desc: "Все генерации сохраняются для быстрого доступа" },
];

const STEPS = [
  { step: "1", title: "Опишите тему", desc: "Промпт или PDF-документ" },
  { step: "2", title: "Настройте", desc: "Стиль, язык, число слайдов" },
  { step: "3", title: "Скачайте", desc: "PPTX или PDF за минуты" },
];

const USE_CASES = [
  { icon: <Briefcase className="h-5 w-5" />, title: "Executive summaries", desc: "Квартальные отчёты и презентации для руководства" },
  { icon: <GraduationCap className="h-5 w-5" />, title: "Лекции и конспекты", desc: "Учебные презентации по PDF-материалам и темам" },
  { icon: <BarChart3 className="h-5 w-5" />, title: "Питч-деки", desc: "Инвестиционные деки и market overviews" },
  { icon: <ShoppingBag className="h-5 w-5" />, title: "Sales decks", desc: "Клиентские предложения и продуктовые презентации" },
];

const VALUE_PILLS = [
  { icon: <Download className="h-3.5 w-3.5" />, label: "Экспорт в PPTX и PDF" },
  { icon: <MessageSquare className="h-3.5 w-3.5" />, label: "Для учебы, бизнеса и продаж" },
  { icon: <Languages className="h-3.5 w-3.5" />, label: "Русский и английский" },
  { icon: <Zap className="h-3.5 w-3.5" />, label: "Результат за минуты" },
];

/* ─── hero product preview ─── */

const MOCK_SLIDES = [
  {
    title: "Обзор рынка",
    sub: "Q4 2025 · Ключевые тренды",
    bars: [85, 62, 45],
  },
  {
    title: "Метрики роста",
    sub: "MRR, retention, unit economics",
    bars: [70, 90, 55],
  },
  {
    title: "Roadmap",
    sub: "Продуктовый план на 2026",
    bars: [40, 75, 95],
  },
];

function HeroPreview() {
  return (
    <div className="relative mx-auto max-w-[640px]">
      {/* browser frame */}
      <div className="rounded-2xl border border-border bg-card shadow-elevated overflow-hidden">
        {/* toolbar */}
        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-border bg-muted/40">
          <span className="h-2 w-2 rounded-full bg-destructive/30" />
          <span className="h-2 w-2 rounded-full bg-warning/30" />
          <span className="h-2 w-2 rounded-full bg-success/30" />
          <div className="ml-3 flex-1 h-5 rounded-md bg-muted/80 flex items-center px-2">
            <span className="text-[10px] text-muted-foreground/60 font-mono">slidecraft.ai/generate</span>
          </div>
        </div>

        {/* slides grid */}
        <div className="p-4 grid grid-cols-3 gap-2.5">
          {MOCK_SLIDES.map((s, i) => (
            <div
              key={i}
              className="aspect-[16/10] rounded-lg border border-border bg-background p-2.5 flex flex-col justify-between group hover:border-primary/30 hover:shadow-elevated transition-all duration-200"
            >
              <div>
                <div className="h-0.5 w-6 rounded-full gradient-hero mb-1.5" />
                <p className="text-[11px] font-semibold leading-tight">{s.title}</p>
                <p className="text-[9px] text-muted-foreground mt-0.5 leading-tight">{s.sub}</p>
              </div>
              {/* mini chart bars */}
              <div className="flex items-end gap-0.5 h-3 mt-auto">
                {s.bars.map((h, j) => (
                  <div
                    key={j}
                    className="flex-1 rounded-sm bg-primary/15 group-hover:bg-primary/25 transition-colors"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* status bar */}
        <div className="px-4 pb-3 flex items-center gap-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-success" />
          <span className="text-[11px] font-medium text-success">Готово</span>
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-[10px] text-muted-foreground">3 слайда · PPTX · 1.2 MB</span>
            <div className="h-5 px-2 rounded-md bg-primary/10 text-primary text-[10px] font-medium flex items-center gap-1">
              <Download className="h-2.5 w-2.5" />
              Скачать
            </div>
          </div>
        </div>
      </div>

      {/* glow */}
      <div className="absolute -inset-6 -z-10 rounded-3xl bg-primary/[0.04] blur-3xl" />
    </div>
  );
}

/* ─── page ─── */

export default function LandingPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const ctaLink = user ? "/generate" : "/auth";

  const handleLogout = async () => {
    await logout();
    navigate("/", { replace: true });
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* ── Header ── */}
      <header className="border-b border-border/60 bg-card/70 backdrop-blur-md sticky top-0 z-50">
        <div className="container flex h-14 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-display text-lg font-bold">
            <Sparkles className="h-5 w-5 text-primary" />
            SlideCraft AI
          </Link>
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <Button size="sm" asChild>
                  <Link to="/generate">Создать презентацию</Link>
                </Button>
                <Button size="sm" variant="outline" onClick={handleLogout}>
                  Выйти
                </Button>
              </>
            ) : (
              <>
                <Link to="/auth" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5">
                  Войти
                </Link>
                <Button size="sm" asChild>
                  <Link to="/auth">Начать бесплатно</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="pt-12 pb-10 px-4">
        <div className="container max-w-5xl">
          <div className="grid lg:grid-cols-[1fr,1.1fr] gap-8 lg:gap-12 items-center">
            {/* left — copy */}
            <div className="space-y-5 text-center lg:text-left">
              {/* badge */}
              <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
                <Sparkles className="h-3 w-3" />
                AI-генератор презентаций
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold leading-[1.1] tracking-tight">
                Презентации, которые{" "}
                <span className="relative inline-block">
                  <span className="relative z-10 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">впечатляют</span>
                </span>
              </h1>

              <p className="text-base text-muted-foreground leading-relaxed max-w-md mx-auto lg:mx-0">
                Опишите тему или загрузите документ — AI создаст структурированную презентацию с&nbsp;дизайном и&nbsp;контентом за&nbsp;минуты.
              </p>

              {/* value strip */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
                {VALUE_PILLS.map((p) => (
                  <span key={p.label} className="inline-flex items-center gap-1">
                    {p.icon}
                    {p.label}
                  </span>
                ))}
              </div>

              {/* CTA */}
              <div className="flex flex-wrap items-center gap-3 justify-center lg:justify-start pt-1">
                <Button size="lg" asChild className="shadow-elevated text-sm px-7 h-11">
                  <Link to={ctaLink}>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Сгенерировать презентацию
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="text-sm px-5 h-11">
                  <a href="#how-it-works">
                    <Play className="mr-1.5 h-3.5 w-3.5" />
                    Как это работает
                  </a>
                </Button>
              </div>
            </div>

            {/* right — preview */}
            <div className="lg:mt-0 mt-2">
              <HeroPreview />
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how-it-works" className="py-10 bg-muted/30">
        <div className="container max-w-3xl space-y-6">
          <div className="text-center space-y-1">
            <h2 className="text-xl font-bold">Как это работает</h2>
            <p className="text-sm text-muted-foreground">Три шага до готовой презентации</p>
          </div>
          <div className="flex flex-col md:flex-row items-stretch gap-0">
            {STEPS.map((s, i) => (
              <React.Fragment key={s.step}>
                <div className="flex-1 rounded-xl border border-border bg-card p-4 text-center space-y-1.5 shadow-card">
                  <div className="inline-flex items-center justify-center h-8 w-8 rounded-full gradient-hero text-primary-foreground font-bold text-xs">
                    {s.step}
                  </div>
                  <h3 className="text-sm font-semibold">{s.title}</h3>
                  <p className="text-xs text-muted-foreground">{s.desc}</p>
                </div>
                {i < STEPS.length - 1 && (
                  <div className="hidden md:flex items-center justify-center w-6 shrink-0">
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/40" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-10">
        <div className="container max-w-4xl space-y-6">
          <div className="text-center space-y-1">
            <h2 className="text-xl font-bold">Почему SlideCraft AI?</h2>
            <p className="text-sm text-muted-foreground">Всё, что нужно для быстрой генерации презентаций</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className={`rounded-xl border p-4 space-y-1.5 transition-all duration-200 ${
                  f.highlight
                    ? "border-primary/25 bg-primary/[0.02] shadow-elevated hover:border-primary/40"
                    : "border-border bg-card shadow-card hover:shadow-elevated"
                }`}
              >
                <div className={`inline-flex items-center justify-center h-8 w-8 rounded-lg ${f.highlight ? "bg-primary/10" : "bg-muted"}`}>
                  {f.icon}
                </div>
                <h3 className="text-sm font-semibold">{f.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Use cases ── */}
      <section className="py-10 bg-muted/30">
        <div className="container max-w-4xl space-y-6">
          <div className="text-center space-y-1">
            <h2 className="text-xl font-bold">Подходит для</h2>
            <p className="text-sm text-muted-foreground">Реальные сценарии, в которых SlideCraft AI экономит часы</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {USE_CASES.map((u) => (
              <div key={u.title} className="rounded-xl border border-border bg-card p-4 shadow-card space-y-1.5 hover:shadow-elevated transition-shadow">
                <div className="inline-flex items-center justify-center h-8 w-8 rounded-lg bg-primary/10 text-primary">
                  {u.icon}
                </div>
                <h3 className="text-sm font-semibold">{u.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{u.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="py-10">
        <div className="container max-w-lg">
          <div className="rounded-2xl border border-primary/15 bg-primary/[0.02] p-8 text-center space-y-3 shadow-elevated">
            <div className="inline-flex items-center justify-center h-10 w-10 rounded-full gradient-hero text-primary-foreground mx-auto">
              <Sparkles className="h-5 w-5" />
            </div>
            <h2 className="text-xl font-bold">Готовы создать презентацию?</h2>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Опишите тему или загрузите документ — результат будет готов за минуты
            </p>
            <div className="pt-1">
              <Button size="lg" asChild className="shadow-elevated text-sm px-7 h-11">
                <Link to={ctaLink}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Начать бесплатно
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="mt-auto bg-[hsl(222_47%_8%)]">
        {/* top divider */}
        <div className="border-t border-[hsl(220_20%_14%)]" />

        <div className="container max-w-6xl py-14 px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10">
            {/* Продукт */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[hsl(0_0%_96%)] tracking-wide">Продукт</h4>
              <ul className="space-y-2.5 text-sm text-[hsl(220_15%_55%)]">
                <li>Цены</li>
                <li>Вдохновение</li>
                <li>Образование</li>
                <li>Гид по промптам</li>
                <li>Инсайты</li>
                <li>Шаблоны</li>
                <li>Обзор</li>
                <li>Интеграции</li>
                <li>Доступность</li>
              </ul>
            </div>

            {/* Компания */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[hsl(0_0%_96%)] tracking-wide">Компания</h4>
              <ul className="space-y-2.5 text-sm text-[hsl(220_15%_55%)]">
                <li>О нас</li>
                <li>Карьера</li>
                <li>Команда</li>
                <li>Помощь</li>
                <li>Сообщество</li>
                <li>Документация для разработчиков</li>
                <li>Бренд</li>
                <li>Связаться с нами</li>
              </ul>
            </div>

            {/* Соцсети */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[hsl(0_0%_96%)] tracking-wide">Соцсети</h4>
              <ul className="space-y-2.5 text-sm text-[hsl(220_15%_55%)]">
                <li>Instagram</li>
                <li>LinkedIn</li>
                <li>TikTok</li>
                <li>X</li>
                <li>YouTube</li>
              </ul>
            </div>

            {/* Правовая информация */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold text-[hsl(0_0%_96%)] tracking-wide">Правовая информация</h4>
              <ul className="space-y-2.5 text-sm text-[hsl(220_15%_55%)]">
                <li>Политика допустимого использования</li>
                <li>Уведомление о cookie</li>
                <li>Настройки cookie</li>
                <li>Дополнение по обработке данных</li>
                <li>Политика конфиденциальности</li>
                <li>Субобработчики</li>
                <li>Условия использования</li>
                <li>Условия третьих сторон</li>
              </ul>
            </div>
          </div>

          {/* copyright */}
          <div className="mt-12 pt-6 border-t border-[hsl(220_20%_14%)] flex justify-end">
            <span className="text-xs text-[hsl(220_15%_40%)]">© {new Date().getFullYear()} SlideCraft AI. Все права защищены.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
