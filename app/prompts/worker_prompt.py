from __future__ import annotations

import json


def build_worker_slide_prompt(*, payload: dict) -> tuple[str, str]:
    """Build (system, user) prompt for a Worker LLM that renders one slide as HTML.

    The payload includes:
    - canvas_w, canvas_h: pixel dimensions (1280x720)
    - theme: full color dict from THEME_VARS
    - layout_type: layout name (e.g. "content_two_column")
    - layout_blocks: list of block dicts with x/y/w/h/type coords
    - slide: full slide spec dict (title, subtitle, bullets, body, ...)
    """
    w = payload.get("canvas_w", 1280)
    h = payload.get("canvas_h", 720)

    system = (
        "You are an expert slide HTML renderer. "
        f"Produce a COMPLETE, STANDALONE HTML document for exactly ONE {w}×{h}px slide. "
        "Strict rules:\n"
        f"1. Canvas size is {w}×{h}px. "
        f"Set <html>, <body>, and .slide div to exactly width:{w}px; height:{h}px; overflow:hidden.\n"
        "2. Use position:absolute for ALL content blocks inside .slide. "
        "Use the x/y/w/h coords from layout_blocks as left/top/width/height in pixels.\n"
        "3. ONLY inline CSS — no <style> tags, no class stylesheets, no external CSS.\n"
        "4. Include Inter font in <head>: "
        "<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap\" rel=\"stylesheet\">.\n"
        "5. Use the colors from theme palette EXACTLY — do not invent colors outside the palette. "
        "You may use theme colors creatively (gradients, transparency) but stay within palette.\n"
        "6. Render ALL content from the slide spec: title, subtitle, bullets, body, key_message, section. "
        "Never omit content fields that have values.\n"
        "7. Bullets: render each as a row with an accent dash '—' prefix in theme.accent color.\n"
        "8. .slide background must equal theme.page_bg. "
        "The root content div must have class='slide'.\n"
        "9. font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif on all text.\n"
        "10. Return ONLY the HTML document — no markdown fences, no explanation, no extra text."
    )

    user = (
        "Render the following slide into a complete standalone HTML document:\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )

    return system, user
