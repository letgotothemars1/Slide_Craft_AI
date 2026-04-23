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
        "title, subtitle, theme_variant, audience, language, style, slides. "
        "Each slide must include: id, type, layout_type, title, subtitle, visual_density, bullets, body, visual_hint, "
        "section, key_message, image_prompt, image_url, chart_hint, speaker_notes. "
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
        "8) Choose layout_type by slide meaning: "
        "title => hero_minimal; "
        "agenda => agenda_clean; "
        "content/explanation/analysis => content_two_column; "
        "metrics/results/KPI => kpi_cards (ONLY if you have real numbers); "
        "process/roadmap/timeline => timeline_process; "
        "concept/framework => infographic_visual; "
        "quote slide => quote_focus; "
        "comparison/pros-vs-cons/before-vs-after => comparison_split. "
        "9) Do not use the same layout_type for all content slides; mix layouts by semantics. "
        "10) If topic is data-heavy, prefer kpi_cards/infographic_visual more often. "
        "11) If topic is narrative/conceptual, prefer hero_minimal/quote_focus/comparison_split more often. "
        "12) If topic is process/roadmap, prefer timeline_process more often. "
        "13) Choose visual_density per slide: low for minimal/quote slides, medium for standard content, "
        "high for KPI/process/infographic-heavy slides. "
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
        "19) Never put speaker notes, meta-instructions, or renderer hints into title/subtitle/bullets/body fields."
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
