export const LANGUAGES = ["ru", "en"] as const;
export type Language = (typeof LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "ru";
export const LANGUAGE_STORAGE_KEY = "slidecraft.language";

export function isLanguage(value: unknown): value is Language {
  return typeof value === "string" && (LANGUAGES as readonly string[]).includes(value);
}

/**
 * Every entry must carry all languages. The `satisfies` clause below is what
 * enforces it: adding a key with only `ru` fails the type check instead of
 * silently shipping a missing translation.
 */
const dictionary = {
  // ── header / nav ──
  "nav.login": { ru: "Войти", en: "Log in" },
  "nav.signup": { ru: "Начать бесплатно", en: "Get started" },
  "nav.signupShort": { ru: "Начать", en: "Start" },
  "nav.create": { ru: "Создать презентацию", en: "Create presentation" },
  "nav.createShort": { ru: "Создать", en: "Create" },
  "nav.logout": { ru: "Выйти", en: "Log out" },
  "nav.language": { ru: "Язык интерфейса", en: "Interface language" },

  // ── hero ──
  "hero.badge": { ru: "Генератор презентаций", en: "Presentation generator" },
  "hero.titleLead": { ru: "Презентация целиком,", en: "A finished deck," },
  "hero.titleAccent": { ru: "а не текст для слайдов", en: "not text for slides" },
  "hero.subtitle": {
    ru: "Опишите тему — и получите готовый файл: со структурой, заголовками-выводами, графиками по реальным цифрам и свёрстанными слайдами.",
    en: "Describe a topic and get a finished file: structure, conclusion-led titles, charts built from real numbers, and laid-out slides.",
  },
  "hero.cta": { ru: "Сгенерировать презентацию", en: "Generate a presentation" },
  "hero.secondary": { ru: "Как это работает", en: "How it works" },
  "hero.note": {
    ru: "Бесплатно · Русский и английский · PDF и PPTX",
    en: "Free · Russian and English · PDF and PPTX",
  },

  "hero.chips.structure": { ru: "Структура под тему", en: "Topic-matched structure" },
  "hero.chips.charts": { ru: "Графики и таблицы", en: "Charts and tables" },
  "hero.chips.images": { ru: "Иллюстрации", en: "Illustrations" },
  "hero.chips.document": { ru: "Генерация по PDF", en: "Generate from a PDF" },

  // ── hero preview (decorative) ──
  "preview.promptLabel": { ru: "Тема презентации", en: "Presentation topic" },
  // Four topics that between them cover the three routing categories, so the
  // rotation quietly demonstrates the feature the page is claiming.
  "preview.topic1": {
    ru: "Квартальный отчёт по выручке за 2026 год",
    en: "Quarterly revenue report for 2026",
  },
  "preview.topic2": {
    ru: "Пять городов Европы, которые стоит увидеть",
    en: "Five European cities worth seeing",
  },
  "preview.topic3": {
    ru: "Введение в машинное обучение для студентов",
    en: "Intro to machine learning for students",
  },
  "preview.topic4": {
    ru: "Питч для инвесторов: рынок доставки еды",
    en: "Investor pitch: the food delivery market",
  },
  "preview.generate": { ru: "Создать", en: "Generate" },
  "preview.slideTitle": {
    ru: "Выручка выросла на 40% за счёт корпоративного сегмента",
    en: "Revenue grew 40%, driven by the enterprise segment",
  },
  "preview.ready": { ru: "Готово", en: "Done" },
  "preview.meta": { ru: "12 слайдов · PDF", en: "12 slides · PDF" },

  // ── how it works ──
  "steps.title": { ru: "Как это работает", en: "How it works" },
  "steps.subtitle": {
    ru: "Три шага до готовой презентации",
    en: "Three steps to a finished deck",
  },
  "steps.1.title": { ru: "Опишите тему", en: "Describe the topic" },
  "steps.1.desc": { ru: "Свободным текстом или загрузите PDF", en: "In plain words, or upload a PDF" },
  "steps.2.title": { ru: "Выберите параметры", en: "Set the options" },
  "steps.2.desc": { ru: "Язык, аудитория, число слайдов", en: "Language, audience, slide count" },
  "steps.3.title": { ru: "Скачайте результат", en: "Download the result" },
  "steps.3.desc": { ru: "Готовый PDF за пару минут", en: "A finished PDF in a couple of minutes" },

  // ── features ──
  "features.title": { ru: "Чем это отличается", en: "What makes it different" },
  "features.subtitle": {
    ru: "Обычный чат выдаёт текст, который ещё нужно разложить по слайдам. Здесь вёрстка, графика и структура — часть результата.",
    en: "A regular chat hands you text you still have to arrange into slides. Here the layout, the graphics and the structure are part of the output.",
  },
  "features.routing.title": { ru: "Структура под тип темы", en: "Structure matched to the topic" },
  "features.routing.desc": {
    ru: "Сервис распознаёт, что за презентация нужна, и собирает её по сценарию именно этого типа — а не по одному шаблону на все случаи",
    en: "The service works out what kind of deck you need and builds it to that type's own plan, instead of one template for everything",
  },
  "features.charts.title": { ru: "Настоящие графики и таблицы", en: "Real charts and tables" },
  "features.charts.desc": {
    ru: "Столбчатые, линейные и круговые диаграммы рисуются как векторная графика, с легендами и подписями — не картинкой",
    en: "Bar, line and pie charts are drawn as vector graphics with legends and labels — not pasted in as images",
  },
  "features.titles.title": { ru: "Заголовки-выводы", en: "Conclusion-led titles" },
  "features.titles.desc": {
    ru: "Каждый слайд озаглавлен мыслью, а не темой: «Выручка выросла на 40%» вместо «Выручка»",
    en: "Every slide is titled with a point, not a subject: “Revenue grew 40%” instead of “Revenue”",
  },
  "features.document.title": { ru: "Генерация по документу", en: "Generate from a document" },
  "features.document.desc": {
    ru: "Загрузите PDF — ключевые идеи из него лягут в основу презентации",
    en: "Upload a PDF and its key ideas become the backbone of the deck",
  },
  "features.formats.title": { ru: "PDF и PPTX", en: "PDF and PPTX" },
  "features.formats.desc": {
    ru: "Готовый PDF по умолчанию или редактируемый PPTX, если нужно доработать вручную",
    en: "A finished PDF by default, or an editable PPTX if you want to tweak it by hand",
  },
  "features.speed.title": { ru: "Минуты вместо вечера", en: "Minutes instead of an evening" },
  "features.speed.desc": {
    ru: "Структура, текст, иллюстрации и вёрстка собираются за один проход",
    en: "Structure, copy, illustrations and layout all come together in one pass",
  },

  // ── use cases ──
  "useCases.title": { ru: "Подходит для", en: "Built for" },
  "useCases.subtitle": {
    ru: "Под каждый тип сервис собирает свою структуру",
    en: "Each type gets its own structure",
  },
  "useCases.analytics.title": { ru: "Отчёты и аналитика", en: "Reports and analysis" },
  "useCases.analytics.desc": {
    ru: "Квартальные итоги, метрики, разборы рынка — с графиками по реальным цифрам",
    en: "Quarterly results, metrics and market reviews, charted from real numbers",
  },
  "useCases.pitch.title": { ru: "Питчи и коммерческие", en: "Pitches and proposals" },
  "useCases.pitch.desc": {
    ru: "Инвестиционные деки и клиентские предложения",
    en: "Investor decks and client proposals",
  },
  "useCases.education.title": { ru: "Учебные материалы", en: "Teaching material" },
  "useCases.education.desc": {
    ru: "Лекции, семинары и конспекты по теме или по PDF",
    en: "Lectures, seminars and summaries from a topic or a PDF",
  },
  "useCases.visual.title": { ru: "Визуальные подборки", en: "Visual round-ups" },
  "useCases.visual.desc": {
    ru: "Travel-деки и обзоры, где всё держится на иллюстрациях",
    en: "Travel decks and round-ups carried by imagery",
  },

  // ── final cta ──
  "cta.title": { ru: "Готовы попробовать?", en: "Ready to try it?" },
  "cta.subtitle": {
    ru: "Опишите тему или загрузите документ — результат будет готов за минуты",
    en: "Describe a topic or upload a document — the result is ready in minutes",
  },
  "cta.button": { ru: "Начать бесплатно", en: "Get started" },

  // ── generate page / composer ──
  "gen.title": { ru: "О чём презентация?", en: "What is the deck about?" },
  "gen.subtitle": {
    ru: "Опишите тему своими словами. Остальное подберётся само — структуру, графику и вёрстку сервис соберёт под ваш запрос.",
    en: "Describe the topic in your own words. The rest follows — structure, graphics and layout are built around your request.",
  },
  "gen.placeholder": {
    ru: "Например: квартальный отчёт по выручке с разбивкой по сегментам и прогнозом на следующий квартал",
    en: "For example: a quarterly revenue report broken down by segment, with next-quarter guidance",
  },
  "gen.submit": { ru: "Создать презентацию", en: "Create presentation" },
  "gen.submitting": { ru: "Генерируем…", en: "Generating…" },
  "gen.examples": { ru: "Примеры запросов", en: "Example prompts" },
  "gen.example1": {
    ru: "Квартальный отчёт по продажам с графиками",
    en: "Quarterly sales report with charts",
  },
  "gen.example2": {
    ru: "Пять направлений для отпуска этой осенью",
    en: "Five places to travel this autumn",
  },
  "gen.example3": {
    ru: "Обзор продукта для потенциальных клиентов",
    en: "Product overview for prospective clients",
  },

  // composer controls
  "gen.attach": { ru: "Прикрепить PDF", en: "Attach a PDF" },
  "gen.attachShort": { ru: "PDF", en: "PDF" },
  "gen.uploading": { ru: "Загружаем…", en: "Uploading…" },
  "gen.removeFile": { ru: "Убрать файл", en: "Remove file" },
  "gen.audience": { ru: "Аудитория", en: "Audience" },
  "gen.style": { ru: "Стиль", en: "Style" },
  "gen.language": { ru: "Язык деки", en: "Deck language" },
  "gen.format": { ru: "Формат", en: "Format" },
  "gen.slides": { ru: "Слайдов", en: "Slides" },
  "gen.fewer": { ru: "Меньше слайдов", en: "Fewer slides" },
  "gen.more": { ru: "Больше слайдов", en: "More slides" },

  "gen.audience.executives": { ru: "Руководители", en: "Executives" },
  "gen.audience.students": { ru: "Студенты", en: "Students" },
  "gen.audience.sales": { ru: "Продажи", en: "Sales" },
  "gen.audience.investors": { ru: "Инвесторы", en: "Investors" },
  "gen.audience.custom": { ru: "Другое", en: "Other" },
  "gen.style.business": { ru: "Бизнес", en: "Business" },
  "gen.style.minimal": { ru: "Минимал", en: "Minimal" },
  "gen.style.dark": { ru: "Тёмный", en: "Dark" },
  "gen.style.creative": { ru: "Креативный", en: "Creative" },
  "gen.lang.ru": { ru: "Русский", en: "Russian" },
  "gen.lang.en": { ru: "Английский", en: "English" },

  // messages
  "gen.error.promptRequired": { ru: "Опишите тему презентации", en: "Describe the deck topic" },
  "gen.error.promptLong": { ru: "Слишком длинно — максимум 2000 символов", en: "Too long — 2000 characters max" },
  "gen.error.pdfOnly": { ru: "Можно загрузить только PDF-файл", en: "Only PDF files can be uploaded" },
  "gen.error.upload": { ru: "Не удалось загрузить документ", en: "Could not upload the document" },
  "gen.error.generate": { ru: "Ошибка при запуске генерации", en: "Could not start generation" },
  "gen.ok.attached": { ru: "Документ прикреплён", en: "Document attached" },

  // ── auth ──
  "auth.loginTitle": { ru: "Вход", en: "Log in" },
  "auth.signupTitle": { ru: "Создание аккаунта", en: "Create an account" },
  "auth.loginSubtitle": {
    ru: "Войдите, чтобы открыть генератор и историю",
    en: "Log in to reach the generator and your history",
  },
  "auth.signupSubtitle": {
    ru: "Зарегистрируйтесь, чтобы сохранять свои генерации",
    en: "Sign up to keep your generations",
  },
  "auth.tabLogin": { ru: "Вход", en: "Log in" },
  "auth.tabSignup": { ru: "Регистрация", en: "Sign up" },
  "auth.email": { ru: "Электронная почта", en: "Email" },
  "auth.password": { ru: "Пароль", en: "Password" },
  "auth.submitLogin": { ru: "Войти", en: "Log in" },
  "auth.submitSignup": { ru: "Создать аккаунт", en: "Create account" },
  "auth.pending": { ru: "Подождите…", en: "One moment…" },
  "auth.error": { ru: "Не удалось выполнить авторизацию", en: "Could not sign you in" },

  // ── history ──
  "history.title": { ru: "История генераций", en: "Generation history" },
  "history.clear": { ru: "Очистить", en: "Clear" },
  "history.empty": { ru: "Пока нет генераций", en: "Nothing generated yet" },
  "history.emptyCta": { ru: "Создать первую презентацию", en: "Create your first deck" },
  "history.noDescription": { ru: "Без описания", en: "No description" },

  // ── job ──
  "job.task": { ru: "Задача", en: "Job" },
  "job.progress": { ru: "Прогресс", en: "Progress" },
  "job.created": { ru: "Создано", en: "Created" },
  "job.share": { ru: "Поделиться", en: "Share" },
  "job.copyLink": { ru: "Скопировать ссылку", en: "Copy link" },
  "job.copied": { ru: "Ссылка скопирована", en: "Link copied" },
  "job.previews": { ru: "Превью слайдов", en: "Slide previews" },
  "job.slideAlt": { ru: "Слайд", en: "Slide" },
  "job.downloadPdf": { ru: "Скачать PDF", en: "Download PDF" },
  "job.downloadPptx": { ru: "Скачать PPTX", en: "Download PPTX" },
  "job.newDeck": { ru: "Новая", en: "New" },
  "job.notFound": { ru: "Задача не найдена", en: "Job not found" },
  "job.notFoundHint": {
    ru: "Проверьте ссылку или создайте новую презентацию",
    en: "Check the link, or start a new deck",
  },
  "job.statusError": { ru: "Не удалось получить статус задачи", en: "Could not fetch job status" },
  "job.back": { ru: "Вернуться", en: "Go back" },

  "status.queued": { ru: "В очереди", en: "Queued" },
  "status.running": { ru: "Генерация", en: "Generating" },
  "status.done": { ru: "Готово", en: "Done" },
  "status.error": { ru: "Ошибка", en: "Failed" },

  // ── 404 ──
  "notFound.title": { ru: "Страница не найдена", en: "Page not found" },
  "notFound.desc": {
    ru: "Такой страницы нет. Возможно, ссылка устарела или в адресе опечатка.",
    en: "There is no such page. The link may be out of date, or the address mistyped.",
  },
  "notFound.home": { ru: "На главную", en: "Back home" },

  // ── dashboards (admin) ──
  "dash.productTitle": { ru: "Продуктовые метрики", en: "Product metrics" },
  "dash.productSubtitle": {
    ru: "Воронка, конверсии и распределения по презентациям",
    en: "Funnel, conversion and deck breakdowns",
  },
  "dash.techTitle": { ru: "Состояние системы", en: "System health" },
  "dash.techSubtitle": {
    ru: "Системные ресурсы, производительность API, статус сервиса",
    en: "System resources, API performance, service status",
  },
  "dash.autoRefresh30": { ru: "Обновление каждые 30 с", en: "Refreshes every 30s" },
  "nav.home": { ru: "На главную", en: "Home" },

  "dash.period7": { ru: "7 дней", en: "7 days" },
  "dash.period30": { ru: "30 дней", en: "30 days" },
  "dash.period90": { ru: "90 дней", en: "90 days" },
  "dash.justNow": { ru: "только что", en: "just now" },
  "dash.updated": { ru: "обновлено", en: "updated" },
  "dash.loading": { ru: "загрузка…", en: "loading…" },
  "dash.offline": { ru: "нет связи", en: "no connection" },
  "dash.refreshRate": { ru: "обновление каждые 5 с", en: "refreshes every 5s" },

  "dash.totalDecks": { ru: "Всего презентаций", en: "Decks in total" },
  "dash.allTimeNote": {
    ru: "За всё время. Подписи снизу — за скользящие окна 7 / 30 дней.",
    en: "All time. The figures below cover rolling 7- and 30-day windows.",
  },
  "dash.successNote": {
    ru: "Доля задач со статусом «готово» от общего числа.",
    en: "Share of jobs that finished with status “done”.",
  },
  "dash.errorNote": {
    ru: "Доля задач со статусом «ошибка» от общего числа.",
    en: "Share of jobs that ended with status “error”.",
  },
  "dash.avgSlides": { ru: "Среднее слайдов", en: "Average slides" },
  "dash.perDeck": { ru: "на одну презентацию", en: "per deck" },
  "dash.withPdf": { ru: "с прикреплённым PDF", en: "with a PDF attached" },
  "dash.ragMode": { ru: "Режим RAG", en: "RAG mode" },

  "dash.funnel.visited": { ru: "Зашли на сайт", en: "Visited the site" },
  "dash.funnel.tried": { ru: "Нажали «Попробовать»", en: "Clicked “Try it”" },
  "dash.funnel.generated": { ru: "Нажали «Сгенерировать»", en: "Clicked “Generate”" },
  "dash.funnel.ready": { ru: "Презентация готова", en: "Deck ready" },

  "dash.breakdown.audience": { ru: "Аудитория", en: "Audience" },
  "dash.breakdown.style": { ru: "Стиль", en: "Style" },
  "dash.breakdown.format": { ru: "Формат", en: "Format" },
  "dash.breakdown.language": { ru: "Язык", en: "Language" },

  "dash.uptime": { ru: "Аптайм сервиса", en: "Service uptime" },
  "dash.requests24h": { ru: "Запросов за 24 ч", en: "Requests in 24h" },
  "dash.nginxConns": { ru: "Соединений nginx", en: "Nginx connections" },
  "dash.restarts": { ru: "Рестарты", en: "Restarts" },
  "dash.disk": { ru: "Диск", en: "Disk" },
  "dash.queue": { ru: "Очередь", en: "Queue" },
  "dash.medianApi": { ru: "медиана ответа API", en: "median API response" },
  "dash.p95": { ru: "95-й перцентиль", en: "95th percentile" },
  "dash.p99": { ru: "99-й перцентиль", en: "99th percentile" },
  "dash.average": { ru: "Среднее", en: "Average" },

  // ── footer ──
  "footer.tagline": {
    ru: "Превращает текстовый запрос в готовую презентацию со структурой, графикой и вёрсткой.",
    en: "Turns a written request into a finished presentation with structure, graphics and layout.",
  },
  "footer.nav": { ru: "Разделы сайта", en: "Site sections" },
  "footer.create": { ru: "Создать", en: "Create" },
  "footer.history": { ru: "История", en: "History" },
  "footer.how": { ru: "Как это работает", en: "How it works" },
} satisfies Record<string, Record<Language, string>>;

export type TranslationKey = keyof typeof dictionary;

export function translate(key: TranslationKey, language: Language): string {
  return dictionary[key][language];
}

/**
 * Formats a timestamp for the active interface language.
 *
 * Dates used to be hardcoded to `ru-RU` in four places, which meant an English
 * interface still printed Russian month order and a 24-hour clock.
 */
export function formatDateTime(iso: string, language: Language): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat(language === "ru" ? "ru-RU" : "en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/**
 * "5 сек назад" / "5 sec ago", in the active language.
 *
 * `Intl.RelativeTimeFormat` handles plural forms and word order per locale,
 * which hand-built strings like `${n} сек назад` got wrong the moment the
 * interface could be English.
 */
export function formatRelativeSeconds(seconds: number, language: Language): string {
  const rtf = new Intl.RelativeTimeFormat(language === "ru" ? "ru-RU" : "en-GB", {
    numeric: "auto",
    style: "narrow",
  });
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return rtf.format(-s, "second");
  const minutes = Math.floor(s / 60);
  if (minutes < 60) return rtf.format(-minutes, "minute");
  return rtf.format(-Math.floor(minutes / 60), "hour");
}

/** Picks the initial language: stored choice first, then the browser's. */
export function detectInitialLanguage(): Language {
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (isLanguage(stored)) return stored;
  } catch {
    // Private mode or blocked storage — fall through to the browser hint.
  }

  const browser = typeof navigator === "undefined" ? "" : navigator.language.toLowerCase();
  return browser.startsWith("ru") ? "ru" : browser ? "en" : DEFAULT_LANGUAGE;
}
