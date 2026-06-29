from __future__ import annotations


def build_presentation_prompt_parts(
    *,
    prompt: str,
    audience: str,
    style: str,
    language: str,
    slides: int,
    retrieved_chunks: list[str] | None = None,
) -> tuple[str, str, str]:
    """Builds system/developer/user prompt parts for structured presentation generation."""

    system_instruction = (
        "You are an expert presentation architect. "
        "Return only valid JSON that exactly follows the required schema. "
        "Do not include markdown fences, prose, or explanations."
    )

    developer_instruction = (
        "Generate a presentation specification with concise slide-friendly content. "
        "Output must be a single JSON object with fields: "
        "title, subtitle, theme_variant, image_density, audience, language, style, slides. "
        "Each slide must include: id, type, layout_type, title, subtitle, visual_density, bullets, body, visual_hint, "
        "section, key_message, image_prompt, image_url, chart_hint, speaker_notes. "
        "GUIDING PRINCIPLES (apply to every slide — distilled from Duarte, Reynolds, Kawasaki, Knaflic): "
        "- One idea per slide: each slide makes exactly ONE point; never cram several arguments onto one slide. "
        "- Title test: a reader must grasp the whole argument by reading ONLY the slide titles in order, so every "
        "title is a claim that advances the story (this is why content titles are action titles). "
        "- Audience as hero: frame content around the audience's situation and the change you want them to make, "
        "not around the topic in the abstract. "
        "- Brevity and restraint: prefer few sharp points over exhaustive lists (3-5 bullets max, short, parallel "
        "phrasing); cut filler words. High signal, low noise. "
        "- One takeaway per slide that the rest of the slide proves. "
        "- Every slide must earn its place: if it does not advance the argument, merge or drop it. "
        "Rules: "
        "1) slides array length MUST equal requested slides count. "
        "2) Keep bullets short and practical for real slides. "
        "3) Keep body and visual_hint concise. "
        "4) Use the requested language for content. "
        "5) Never output any text before or after JSON. "
        "6) For fields with no value, return null (not omitted). "
        "6.1) image_url must be null at spec generation time. "
        "7) Choose theme_variant by topic: "
        "AI/product/startup/architecture/technology/pitch => dark_tech_pitch; "
        "history/culture/academic/conceptual/reflective => clean_editorial; "
        "education/explainer/framework/method/process-heavy => infographic_bright. "
        "STRUCTURE & VARIETY (this matters most — a deck that reuses one layout looks broken): "
        "8) Do NOT follow a fixed template. Design the slide sequence around THIS topic's actual story, "
        "not a generic 'title, agenda, content, content, conclusion' skeleton. "
        "The first slide is the opener (hero_minimal). An agenda slide (agenda_clean) is OPTIONAL: "
        "include at most one, and only when slides >= 8. End on a conclusion "
        "(content_two_column or hero_minimal). Everything in between is yours to shape. "
        "9) Maximize layout variety. Across the whole deck use AT LEAST 4 distinct layout_types "
        "(more for longer decks), and NEVER use the same layout_type on two consecutive slides. "
        "10) content_two_column is a FALLBACK for plain prose only — use it for AT MOST about one third "
        "of the slides. Before assigning it, check whether the slide is really one of these and reshape "
        "the content to fit the more expressive layout: "
        "a comparison / before-vs-after / pros-vs-cons => comparison_split; "
        "real numbers, results or KPIs => kpi_cards; "
        "a process, roadmap, sequence of steps or timeline => timeline_process; "
        "a set of 3-6 concepts, pillars, components or principles => infographic_visual; "
        "a single powerful statement or insight => quote_focus; "
        "a metric over time or compared across categories => chart_focus (a real numeric chart); "
        "a structured table of values (metrics across periods/segments) => data_table; "
        "a linear pipeline / value chain / sequence of stages shown left-to-right => process_flow; "
        "3-5 parallel categories each with its own short list (inputs/process/outputs, audiences, etc.) => multi_column. "
        "11) Match the mix to the topic: data-heavy topics lean on chart_focus/data_table/kpi_cards; "
        "process/roadmap topics lean on timeline_process; narrative/conceptual topics lean on "
        "infographic_visual/quote_focus/comparison_split. Layout mapping reference: "
        "title=>hero_minimal, metrics=>kpi_cards (only with real numbers), process=>timeline_process, "
        "concept/framework=>infographic_visual, quote=>quote_focus, comparison=>comparison_split. "
        "12) Choose visual_density per slide: low for minimal/quote slides, medium for standard content, "
        "high for KPI/process/infographic-heavy slides. "
        "TITLES — consulting 'action title' style (this single change makes decks look professional): "
        "13) For content_two_column, kpi_cards, timeline_process, comparison_split and infographic_visual "
        "slides, the 'title' MUST be the slide's KEY TAKEAWAY written as a complete sentence that states the "
        "conclusion (about 6-16 words), NOT a topic label. "
        "Topic label (BAD): 'Рынок'. Action title (GOOD): 'Рынок онлайн-образования удвоится к 2027 году'. "
        "The title should be a claim the rest of the slide proves. "
        "Put the short topic/section word in the 'section' field, and set 'subtitle' to null on these slides "
        "(the action title replaces the subtitle). "
        "Keep hero_minimal and quote_focus titles short and punchy; the agenda_clean title is a short label. "
        "FORMATTING PER LAYOUT: "
        "14) For comparison_split slides: format bullets as 'left item | right item' (pipe separator). "
        "Set section field as 'Left Column Title/Right Column Title'. "
        "Both sides of each bullet MUST compare the same dimension (e.g. 'Manual process | Automated process'). "
        "Never use prefixes like 'Слева:', 'Справа:', 'Option A', 'Option B' in bullets or titles. "
        "15) For quote_focus slides: put the full quote text in body field (not speaker_notes). "
        "Do NOT combine type=conclusion with layout_type=quote_focus — use type=quote for quote slides. "
        "16) For agenda_clean slides: bullets must be the main SECTIONS/TOPICS of the presentation "
        "(e.g. 'Market Overview', 'Investment Risks', 'Our Recommendation') — NOT content items or data points. "
        "Provide 4-6 section titles. "
        "17) For kpi_cards slides: EVERY bullet MUST start with a numeric metric "
        "(number, percentage, currency, or ratio) followed by ':' or '—' then a short label. "
        "Examples: '340%: рост рынка за 5 лет', '$2.5M: средняя стоимость объекта', '4 из 5: районов в плюсе'. "
        "NEVER use kpi_cards for descriptive text without real numbers — use infographic_visual instead. "
        "18) For conclusion/type=conclusion slides: use layout_type=content_two_column or hero_minimal. "
        "Put key takeaways as bullets. They MUST be shown on the slide. "
        "19) Never put speaker notes, meta-instructions, or renderer hints into title/subtitle/bullets/body fields. "
        "20) For chart_focus slides: populate the 'chart' object with real numeric data. The action title states what "
        "the chart proves. Set 'unit' (e.g. '%', '₽', ' млн') or empty string. Two modes: "
        "(a) SINGLE series — fill 'points' (3-6 label+value), leave 'categories'/'series' empty. "
        "chart_type='bar' to compare categories, 'line' for a trend over time, 'pie' for share of a whole. "
        "(b) GROUPED — to compare 2-3 series over the same x labels (e.g. 2024 vs 2025 by segment), set chart_type "
        "'bar' or 'line', fill 'categories' (shared x labels) and 'series' (2-3 entries: name + 'values' aligned to "
        "categories), and leave 'points' empty. "
        "Prefer chart_focus over kpi_cards when you have a SERIES of values, not isolated numbers. "
        "21) For data_table slides: populate the 'table' object with 'headers' (3-5 columns; first column is the row "
        "label) and 3-7 'rows' of short string cells. Use for multi-metric comparisons across periods or segments. "
        "22) 'chart' and 'table' MUST be null on every slide except chart_focus (chart) and data_table (table) respectively. "
        "23) For process_flow slides: put each stage as one bullet in 'bullets' (3-6 stages), optionally 'Label — short detail'. "
        "Use process_flow for a left-to-right pipeline (e.g. a value chain); use timeline_process for a chronological roadmap. "
        "24) For multi_column slides: fill 'columns' with 3-5 entries, each {header, items} (2-5 short items per column). "
        "Leave 'columns' empty ([]) on every other slide. "
        "25) Emphasis (do this — it makes slides pop): on content and data slides, highlight the single most important "
        "number or term in a bullet by wrapping it in **double asterisks** so it renders in the accent color "
        "(e.g. 'выручка выросла на **34%**'). Add at least one highlight on most content/bullet slides; at most ONE per "
        "bullet line; never wrap a whole sentence. "
        "26) Set a short 'source' citation (e.g. 'Источник: данные компании', 'Source: отраслевой отчёт 2025') on slides "
        "with figures or factual claims (chart_focus, data_table, kpi_cards, and any slide citing numbers); under ~12 words. "
        "Keep 'source' null on purely conceptual/quote/agenda slides. "
        "27) Set presentation-level 'image_density': 'rich' for visual/narrative topics (travel, lifestyle, food, nature, "
        "culture, personal, story-driven education) where photos carry the deck; 'minimal' for data/business/analytical "
        "topics (reports, strategy, finance, market analysis) where charts and tables matter more than photos; 'moderate' "
        "otherwise. "
        "28) Set 'image_prompt' (a vivid English visual description) on content slides where an image genuinely strengthens "
        "them. For image_density='rich', put an image_prompt on MOST section/item slides and use content_two_column for "
        "those items — a consistent image+text layout per item beats layout variety here. For 'minimal', set image_prompt "
        "only on the hero/title and at most one other slide; keep it null elsewhere."
    )

    user_input = (
        f"User prompt: {prompt}\n"
        f"Audience: {audience}\n"
        f"Style: {style}\n"
        f"Language: {language}\n"
        f"Slides count: {slides}"
    )

    if retrieved_chunks:
        context_block = "\n\n".join(
            [f"[Chunk {idx + 1}] {chunk}" for idx, chunk in enumerate(retrieved_chunks)]
        )
        user_input += (
            "\n\nDocument context (factual source):\n"
            f"{context_block}\n\n"
            "When document context is provided, rely on it for factual claims. "
            "Do not invent concrete facts that contradict or are absent from context."
        )

    return system_instruction, developer_instruction, user_input
