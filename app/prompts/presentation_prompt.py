from __future__ import annotations

# Presentation categories the orchestrator routes to. Each gets its own
# "director" block on top of the shared mechanics — different topics want very
# different decks (a travel listicle vs a financial report).
PRESENTATION_CATEGORIES = ("travel_visual", "business_data", "general")


def _common_rules() -> str:
    """Schema mechanics + universal principles + per-layout formatting (category-agnostic)."""
    return (
        "You are producing a JSON presentation spec. "
        "Output a single JSON object with fields: title, subtitle, theme_variant, image_density, audience, language, "
        "style, slides. Each slide includes: id, type, layout_type, title, subtitle, visual_density, bullets, body, "
        "visual_hint, section, key_message, image_prompt, image_url, chart, table, columns, source, speaker_notes. "
        "MECHANICS: "
        "1) slides length MUST equal the requested count. "
        "2) Use the requested language for all content. "
        "3) For empty fields return null; image_url is always null; columns is [] when unused; chart/table are null unless used. "
        "4) Never output any text before or after the JSON. "
        "5) NEVER create a quote slide: do not use layout_type=quote_focus or type=quote under any circumstances. "
        "PRINCIPLES: one idea per slide; the slide titles read in sequence must convey the whole story, so on "
        "content/analysis slides the title is a complete-sentence takeaway (~6-16 words, not a topic label) and the "
        "short topic word goes in 'section'; keep bullets few, short and parallel (3-5); every slide earns its place. "
        "LAYOUT MECHANICS (how to fill each layout when you choose it): "
        "comparison_split — bullets as 'left | right' (pipe); section as 'Left Title/Right Title'; both sides compare the "
        "same dimension; no 'Option A'/'Слева' prefixes. "
        "agenda_clean — bullets are the presentation's SECTIONS (4-6), not content items. "
        "kpi_cards — every bullet starts with a numeric metric then ':' or '—' then a short label; never use it without real numbers. "
        "chart_focus — fill 'chart' with real numbers: single series via 'points' (3-6 label+value) OR grouped via "
        "'categories'+'series' (2-3 named series aligned to categories); chart_type bar=compare, line=trend, pie=share; "
        "set 'unit'; leave 'points' empty when using series and vice versa. "
        "data_table — fill 'table' (3-5 headers, first column is the row label; 3-7 rows of short string cells). "
        "process_flow — each stage a bullet (3-6), optionally 'Label — short detail'; a left-to-right pipeline. "
        "multi_column — fill 'columns' with 3-5 {header, items} (2-5 short items each). "
        "timeline_process — chronological steps as bullets. "
        "source — a short citation (e.g. 'Источник: …') on slides with figures or factual claims; null otherwise. "
    )


# ── Category directors ─────────────────────────────────────────────────────────

_TRAVEL = (
    "DECK STYLE — VISUAL TRAVEL / LISTICLE. This deck is carried by imagery and atmosphere, not data. "
    "Set image_density='rich' and theme_variant='clean_editorial'. "
    "STRUCTURE: hero opener (hero_minimal, with image_prompt) -> optional short agenda -> ONE slide per "
    "destination/item -> a short closing. "
    "Every destination/item slide uses layout_type=content_two_column and MUST have: a set image_prompt (a vivid "
    "English description of that specific place; render ALL images in ONE consistent warm editorial-ILLUSTRATION "
    "style, NOT photorealistic — end every image_prompt with 'warm flat editorial illustration, cohesive style, soft "
    "warm palette'), a 'section' tag "
    "(e.g. 'Направление 1'), an action-title, a short evocative 'subtitle', a 1-2 sentence 'body' paragraph, and 3 "
    "short 'bullets' of concrete highlights. Keep subtitle AND body AND bullets — do NOT null the subtitle here. "
    "Use the SAME content_two_column layout for ALL destinations — consistency beats variety for a listicle. "
    "Do NOT use kpi_cards, chart_focus or process_flow. At most ONE optional data_table or comparison_split near the "
    "end, only if it genuinely helps. "
    "NEVER use ** highlighting — this is an informational deck, no emphasis markup and no persuasion. "
)

_BUSINESS = (
    "DECK STYLE — BUSINESS / DATA / ANALYTICAL. Lead with data, structure and takeaways. "
    "Set image_density='minimal' (image_prompt only on the hero and at most one other slide) and theme_variant "
    "'dark_tech_pitch' or 'clean_editorial'. "
    "Use chart_focus and data_table for real numbers, kpi_cards for headline metrics, comparison_split, process_flow, "
    "multi_column and infographic_visual to structure arguments. Maximize layout variety (use at least 4 distinct "
    "layout_types; never repeat a layout on consecutive slides); content_two_column is a fallback for at most ~1/3 of "
    "slides. On these slides set 'subtitle' to null (the action-title replaces it). "
    "You MAY highlight the single most important number/term per key bullet with **double asterisks** (accent color) — "
    "sparingly, at most one per line, never a whole sentence. "
)

_GENERAL = (
    "DECK STYLE — GENERAL INFORMATIONAL / EDUCATIONAL. Balance clear text with visuals. "
    "Set image_density='moderate'. Pick the layout that best fits each slide's meaning (content_two_column, "
    "infographic_visual, timeline_process, comparison_split, multi_column; charts/tables only for real data). Favor "
    "clarity and some layout variety; on content slides set 'subtitle' to null (the action-title replaces it). "
    "Put image_prompt on the hero and a few key slides. Do NOT use ** highlighting unless the topic is clearly persuasive. "
)

_CATEGORY_DIRECTIVES = {
    "travel_visual": _TRAVEL,
    "business_data": _BUSINESS,
    "general": _GENERAL,
}


def build_presentation_prompt_parts(
    *,
    prompt: str,
    audience: str,
    style: str,
    language: str,
    slides: int,
    retrieved_chunks: list[str] | None = None,
    category: str = "general",
) -> tuple[str, str, str]:
    """Builds (system, developer, user) prompt parts for the given deck category."""

    system_instruction = (
        "You are an expert presentation architect. "
        "Return only valid JSON that exactly follows the required schema. "
        "Do not include markdown fences, prose, or explanations."
    )

    directive = _CATEGORY_DIRECTIVES.get(category, _GENERAL)
    developer_instruction = _common_rules() + directive

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
