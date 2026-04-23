"""
Slide renderer: HTML → per-slide PNG screenshots → combined PDF
Canvas: 1280 × 720 px (16:9), device_scale_factor=2 → effective 2560 × 1440
Inspired by block-based absolute positioning approach.
"""
from __future__ import annotations

import asyncio
import io
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape
from pathlib import Path

from app.config import settings
from app.services.llm_service import PresentationSpec, SlideSpec, ThemeVariant

logger = logging.getLogger(__name__)

# ── Canvas dimensions ─────────────────────────────────────────────────────────
W, H = 1280, 720

# ── Theme palette ─────────────────────────────────────────────────────────────
THEME_VARS: dict[str, dict[str, str]] = {
    "dark_tech_pitch": {
        "page_bg":        "#0B1020",
        "accent":         "#22C55E",
        "accent_soft":    "rgba(34,197,94,0.12)",
        "panel_bg":       "rgba(255,255,255,0.07)",
        "panel_alt":      "rgba(255,255,255,0.04)",
        "border":         "rgba(255,255,255,0.12)",
        "text_primary":   "#F8FAFC",
        "text_secondary": "#94A3B8",
        "quote_bg":       "#0D1829",
    },
    "clean_editorial": {
        "page_bg":        "#FFFCF7",
        "accent":         "#334155",
        "accent_soft":    "#ECE7DD",
        "panel_bg":       "#FFFFFF",
        "panel_alt":      "#F8FAFC",
        "border":         "#D6D3D1",
        "text_primary":   "#111827",
        "text_secondary": "#57534E",
        "quote_bg":       "#F4F1EB",
    },
    "infographic_bright": {
        "page_bg":        "#F0F9FF",
        "accent":         "#0EA5E9",
        "accent_soft":    "#D1FAE5",
        "panel_bg":       "#FFFFFF",
        "panel_alt":      "#ECFEFF",
        "border":         "#7DD3FC",
        "text_primary":   "#0F172A",
        "text_secondary": "#0369A1",
        "quote_bg":       "#E0F2FE",
    },
}

# ── Block layout definitions (pixel coords on 1280×720 canvas) ────────────────
LAYOUTS: dict[str, list[dict]] = {
    "hero_minimal": [
        {"type": "accent_bar",   "x": 0,   "y": 0,   "w": 5,   "h": 720},
        {"type": "tag",          "x": 72,  "y": 52,  "w": 300, "h": 36},
        {"type": "title",        "x": 72,  "y": 100, "w": 720, "h": 240, "fontSize": 68, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "subtitle",     "x": 72,  "y": 352, "w": 680, "h": 72,  "fontSize": 24, "fontWeight": 400},
        {"type": "bullets",      "x": 72,  "y": 436, "w": 640, "h": 218, "fontSize": 17, "fontWeight": 500},
        {"type": "key_message",  "x": 72,  "y": 672, "w": 680, "h": 28,  "fontSize": 14},
        {"type": "image_right",  "x": 808, "y": 0,   "w": 472, "h": 720},
    ],
    "agenda_clean": [
        {"type": "title",        "x": 64,  "y": 52,  "w": 1160, "h": 90,  "fontSize": 52, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "subtitle",     "x": 64,  "y": 152, "w": 800,  "h": 36,  "fontSize": 18, "fontWeight": 400},
        {"type": "agenda_list",  "x": 64,  "y": 202, "w": 1152, "h": 478},
    ],
    "content_two_column": [
        {"type": "tag",          "x": 64,  "y": 44,  "w": 260,  "h": 36},
        {"type": "title",        "x": 64,  "y": 92,  "w": 740,  "h": 122, "fontSize": 52, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "accent_sub",   "x": 64,  "y": 222, "w": 720,  "h": 46,  "fontSize": 22, "fontWeight": 700},
        {"type": "body",         "x": 64,  "y": 276, "w": 700,  "h": 76,  "fontSize": 18, "fontWeight": 400},
        {"type": "bullets",      "x": 64,  "y": 360, "w": 700,  "h": 298, "fontSize": 17, "fontWeight": 500},
        {"type": "key_message",  "x": 64,  "y": 676, "w": 700,  "h": 26,  "fontSize": 14},
        {"type": "image",        "x": 824, "y": 44,  "w": 400,  "h": 614, "radius": 22},
    ],
    "kpi_cards": [
        {"type": "title",        "x": 64,  "y": 52,  "w": 1160, "h": 90,  "fontSize": 48, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "subtitle",     "x": 64,  "y": 150, "w": 900,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "kpi_grid",     "x": 64,  "y": 202, "w": 1152, "h": 474},
    ],
    "timeline_process": [
        {"type": "title",           "x": 64,  "y": 52,  "w": 1160, "h": 80,  "fontSize": 48, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "subtitle",        "x": 64,  "y": 140, "w": 800,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "timeline_steps",  "x": 64,  "y": 190, "w": 1152, "h": 490},
    ],
    "quote_focus": [
        {"type": "quote_content",   "x": 0,   "y": 0,   "w": 1280, "h": 720},
    ],
    "comparison_split": [
        {"type": "title",           "x": 64,  "y": 52,  "w": 1160, "h": 80,  "fontSize": 48, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "comparison_cols", "x": 64,  "y": 148, "w": 1152, "h": 532},
    ],
    "infographic_visual": [
        {"type": "title",              "x": 64,  "y": 52,  "w": 1160, "h": 80,  "fontSize": 48, "fontWeight": 800, "lineHeight": 1.06},
        {"type": "subtitle",           "x": 64,  "y": 140, "w": 800,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "infographic_nodes",  "x": 64,  "y": 190, "w": 1152, "h": 490},
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_layout(slide: SlideSpec) -> str:
    if slide.layout_type and slide.layout_type in LAYOUTS:
        return slide.layout_type
    return {
        "title":      "hero_minimal",
        "agenda":     "agenda_clean",
        "quote":      "quote_focus",
        "conclusion": "hero_minimal",
        "content":    "content_two_column",
    }.get(slide.type, "content_two_column")


def _resolve_theme(spec: PresentationSpec) -> dict[str, str]:
    key: ThemeVariant = spec.theme_variant or "clean_editorial"
    return THEME_VARS.get(key, THEME_VARS["clean_editorial"])


def _extract_quote(slide: SlideSpec) -> str:
    return slide.body or slide.key_message or (slide.bullets[0] if slide.bullets else slide.subtitle or "")


def _extract_kpi_cards(slide: SlideSpec) -> list[tuple[str, str]]:
    cards = []
    for idx, item in enumerate(slide.bullets[:4], 1):
        has_number = bool(re.search(r"\d", item))
        if has_number:
            m = re.match(r"^(.{1,30}?)\s*[:—–]\s*(.+)$", item)
            if m:
                cards.append((m.group(1).strip(), m.group(2).strip()))
                continue
        parts = re.split(r"\s+[—–-]\s+", item, maxsplit=1)
        if len(parts) == 2 and len(parts[0]) <= 30:
            cards.append((parts[0].strip(), parts[1].strip()))
            continue
        cards.append((f"#{idx}", item))
    return cards or [(f"#{i}", f"Metric {i}") for i in range(1, 5)]


def _extract_comparison(slide: SlideSpec) -> tuple[str, list[str], str, list[str]]:
    left_title, right_title = "До", "После"
    if slide.section and "/" in slide.section:
        parts = slide.section.split("/", 1)
        left_title, right_title = parts[0].strip(), parts[1].strip()
    left_items: list[str] = []
    right_items: list[str] = []
    for item in slide.bullets:
        if "|" in item:
            l, r = item.split("|", 1)
            left_items.append(l.strip())
            right_items.append(r.strip())
        else:
            (left_items if len(left_items) <= len(right_items) else right_items).append(item)
    return left_title, left_items[:5], right_title, right_items[:5]


# ── Block renderer ────────────────────────────────────────────────────────────

def _pos(b: dict) -> str:
    return f"position:absolute;left:{b['x']}px;top:{b['y']}px;width:{b['w']}px;height:{b['h']}px;overflow:hidden;"


def _render_block(b: dict, slide: SlideSpec, t: dict) -> str:  # noqa: C901
    btype = b["type"]
    p = _pos(b)

    if btype == "accent_bar":
        return f'<div style="{p}background:{t["accent"]};"></div>'

    if btype == "tag":
        if not slide.section:
            return ""
        return (
            f'<div style="{p}display:flex;align-items:center;">'
            f'<span style="display:inline-block;background:{t["accent_soft"]};color:{t["accent"]};'
            f'font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            f'padding:5px 14px;border-radius:20px;border:1px solid {t["accent"]};">'
            f'{escape(slide.section)}</span></div>'
        )

    if btype == "title":
        fs = b.get("fontSize", 48)
        fw = b.get("fontWeight", 800)
        lh = b.get("lineHeight", 1.08)
        return (
            f'<div style="{p}font-size:{fs}px;font-weight:{fw};line-height:{lh};'
            f'letter-spacing:-.025em;color:{t["text_primary"]};">'
            f'{escape(slide.title or "")}</div>'
        )

    if btype == "accent_sub":
        if not slide.subtitle:
            return ""
        fs = b.get("fontSize", 22)
        fw = b.get("fontWeight", 700)
        return (
            f'<div style="{p}font-size:{fs}px;font-weight:{fw};color:{t["accent"]};'
            f'letter-spacing:-.01em;display:flex;align-items:center;">'
            f'{escape(slide.subtitle)}</div>'
        )

    if btype == "subtitle":
        if not slide.subtitle:
            return ""
        fs = b.get("fontSize", 18)
        fw = b.get("fontWeight", 400)
        return (
            f'<div style="{p}font-size:{fs}px;font-weight:{fw};'
            f'color:{t["text_secondary"]};line-height:1.5;display:flex;align-items:center;">'
            f'{escape(slide.subtitle)}</div>'
        )

    if btype == "body":
        if not slide.body or slide.bullets:
            return ""
        fs = b.get("fontSize", 18)
        return (
            f'<div style="{p}font-size:{fs}px;color:{t["text_secondary"]};line-height:1.6;">'
            f'{escape(slide.body)}</div>'
        )

    if btype == "bullets":
        bullets = slide.bullets[:8]
        if not bullets:
            return ""
        fs = b.get("fontSize", 17)
        fw = b.get("fontWeight", 500)
        rows = []
        for i, item in enumerate(bullets):
            border = f"border-bottom:1px solid {t['border']};" if i < len(bullets) - 1 else ""
            rows.append(
                f'<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;{border}">'
                f'<span style="color:{t["accent"]};font-weight:700;font-size:{fs+1}px;flex-shrink:0;line-height:1.5;">—</span>'
                f'<span style="font-size:{fs}px;font-weight:{fw};line-height:1.5;color:{t["text_primary"]};">{escape(item)}</span>'
                f'</div>'
            )
        return (
            f'<div style="{p}background:{t["panel_bg"]};border:1px solid {t["border"]};'
            f'border-radius:20px;padding:20px 28px;display:flex;flex-direction:column;justify-content:space-evenly;">'
            + "".join(rows) + "</div>"
        )

    if btype == "key_message":
        if not slide.key_message:
            return ""
        fs = b.get("fontSize", 14)
        return (
            f'<div style="{p}font-size:{fs}px;color:{t["text_secondary"]};'
            f'display:flex;align-items:center;">{escape(slide.key_message)}</div>'
        )

    if btype == "image_right":
        if not slide.image_url:
            return ""
        return (
            f'<div style="{p}">'
            f'<img src="{slide.image_url}" style="width:100%;height:100%;object-fit:cover;border-radius:24px 0 0 24px;"/>'
            f'</div>'
        )

    if btype == "image":
        radius = b.get("radius", 22)
        if slide.image_url:
            return (
                f'<div style="{p}border-radius:{radius}px;overflow:hidden;">'
                f'<img src="{slide.image_url}" style="width:100%;height:100%;object-fit:cover;"/>'
                f'</div>'
            )
        hint = slide.visual_hint or ""
        return (
            f'<div style="{p}border-radius:{radius}px;background:{t["panel_alt"]};'
            f'border:1px solid {t["border"]};display:flex;align-items:center;justify-content:center;">'
            + (f'<div style="font-size:13px;color:{t["text_secondary"]};text-align:center;padding:24px;opacity:.4;line-height:1.5;">{escape(hint)}</div>' if hint else "")
            + "</div>"
        )

    if btype == "agenda_list":
        bullets = slide.bullets[:8]
        items = "".join(
            f'<div style="display:flex;align-items:center;gap:16px;background:{t["panel_bg"]};'
            f'border:1px solid {t["border"]};border-radius:12px;padding:14px 24px;">'
            f'<div style="width:34px;height:34px;border-radius:9px;background:{t["accent_soft"]};'
            f'border:1.5px solid {t["accent"]};display:flex;align-items:center;justify-content:center;'
            f'font-size:14px;font-weight:700;color:{t["accent"]};flex-shrink:0;">{i + 1}</div>'
            f'<div style="font-size:18px;font-weight:500;color:{t["text_primary"]};">{escape(item)}</div>'
            f'</div>'
            for i, item in enumerate(bullets)
        )
        return f'<div style="{p}display:flex;flex-direction:column;justify-content:center;gap:12px;">{items}</div>'

    if btype == "kpi_grid":
        cards = _extract_kpi_cards(slide)
        cols = min(len(cards), 4)
        cards_html = "".join(
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
            f'padding:28px 24px;display:flex;flex-direction:column;justify-content:center;'
            f'position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:0;left:0;right:0;height:5px;background:{t["accent"]};'
            f'border-radius:16px 16px 0 0;{"opacity:.5;" if idx % 2 == 1 else ""}"></div>'
            f'<div style="font-size:52px;font-weight:800;color:{t["accent"]};letter-spacing:-.03em;line-height:1;margin-bottom:10px;">{escape(metric)}</div>'
            f'<div style="font-size:15px;color:{t["text_secondary"]};font-weight:500;line-height:1.5;">{escape(label)}</div>'
            f'</div>'
            for idx, (metric, label) in enumerate(cards[:4])
        )
        return f'<div style="{p}display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;">{cards_html}</div>'

    if btype == "timeline_steps":
        steps = slide.bullets[:6] or (slide.body.split("\n") if slide.body else [])
        steps_html = "".join(
            f'<div style="display:flex;align-items:center;gap:20px;">'
            f'<div style="width:44px;height:44px;border-radius:12px;background:{t["accent_soft"]};'
            f'border:2px solid {t["accent"]};display:flex;align-items:center;justify-content:center;'
            f'font-size:15px;font-weight:700;color:{t["accent"]};flex-shrink:0;">{i + 1}</div>'
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:12px;'
            f'padding:16px 22px;flex:1;font-size:17px;font-weight:500;line-height:1.5;color:{t["text_primary"]};">{escape(step)}</div>'
            f'</div>'
            for i, step in enumerate(steps)
        )
        return f'<div style="{p}display:flex;flex-direction:column;justify-content:space-evenly;">{steps_html}</div>'

    if btype == "comparison_cols":
        left_title, left_items, right_title, right_items = _extract_comparison(slide)

        def _col(title: str, items: list[str], accent: bool) -> str:
            bg = t["accent_soft"] if accent else t["panel_bg"]
            bc = t["accent"] if accent else t["border"]
            bw = "2px" if accent else "1px"
            tc = t["accent"] if accent else t["text_primary"]
            rows = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:10px;font-size:16px;line-height:1.5;'
                f'padding:9px 0;{"border-bottom:1px solid " + t["border"] + ";" if i < len(items)-1 else ""}">'
                f'<span style="width:7px;height:7px;border-radius:50%;background:{t["accent"]};margin-top:8px;flex-shrink:0;"></span>'
                f'<span style="color:{t["text_primary"]};">{escape(item)}</span></div>'
                for i, item in enumerate(items)
            )
            return (
                f'<div style="background:{bg};border:{bw} solid {bc};border-radius:16px;padding:22px 22px 14px;'
                f'display:flex;flex-direction:column;">'
                f'<div style="font-size:18px;font-weight:700;color:{tc};margin-bottom:14px;'
                f'padding-bottom:12px;border-bottom:2px solid {bc};">{escape(title)}</div>'
                f'<div style="display:flex;flex-direction:column;justify-content:space-evenly;flex:1;">{rows}</div>'
                f'</div>'
            )

        return (
            f'<div style="{p}display:grid;grid-template-columns:1fr 1fr;gap:20px;">'
            + _col(left_title, left_items, False)
            + _col(right_title, right_items, True)
            + "</div>"
        )

    if btype == "infographic_nodes":
        nodes = slide.bullets[:6] or (slide.body.split("\n") if slide.body else [])
        cols = 3 if len(nodes) > 3 else max(len(nodes), 1)
        nodes_html = "".join(
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
            f'padding:22px 18px;display:flex;flex-direction:column;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;bottom:0;left:0;right:0;height:3px;background:{t["accent"]};opacity:.4;"></div>'
            f'<div style="width:30px;height:30px;border-radius:8px;background:{t["accent_soft"]};'
            f'color:{t["accent"]};font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:12px;">{i + 1}</div>'
            f'<div style="font-size:15px;line-height:1.55;color:{t["text_primary"]};">{escape(node)}</div>'
            f'</div>'
            for i, node in enumerate(nodes)
        )
        return f'<div style="{p}display:grid;grid-template-columns:repeat({cols},1fr);grid-auto-rows:1fr;gap:16px;">{nodes_html}</div>'

    if btype == "quote_content":
        quote = _extract_quote(slide)
        return (
            f'<div style="{p}display:flex;flex-direction:column;align-items:center;justify-content:center;'
            f'text-align:center;padding:56px 120px;background:{t["quote_bg"]};">'
            f'<div style="font-size:160px;line-height:1;color:{t["accent"]};font-family:Georgia,serif;'
            f'position:absolute;top:20px;left:72px;opacity:.25;">&ldquo;</div>'
            f'<div style="width:56px;height:4px;background:{t["accent"]};border-radius:2px;margin-bottom:24px;"></div>'
            f'<div style="font-size:34px;font-weight:600;line-height:1.45;letter-spacing:-.015em;max-width:78%;'
            f'color:{t["text_primary"]};margin-bottom:32px;position:relative;z-index:1;">{escape(quote)}</div>'
            + (f'<div style="font-size:18px;color:{t["text_secondary"]};font-weight:400;">— {escape(slide.subtitle)}</div>' if slide.subtitle else "")
            + "</div>"
        )

    return ""


# ── Slide + document ──────────────────────────────────────────────────────────

def _render_slide(slide: SlideSpec, theme: dict) -> str:
    layout_name = _resolve_layout(slide)
    blocks = LAYOUTS.get(layout_name, LAYOUTS["content_two_column"])
    blocks_html = "".join(_render_block(b, slide, theme) for b in blocks)
    font = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    return (
        f'<div class="slide" style="position:relative;width:{W}px;height:{H}px;overflow:hidden;'
        f'background:{theme["page_bg"]};color:{theme["text_primary"]};font-family:{font};">'
        + blocks_html
        + "</div>"
    )


def build_full_html(spec: PresentationSpec) -> str:
    theme = _resolve_theme(spec)
    slides_html = "\n".join(_render_slide(s, theme) for s in spec.slides)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{escape(spec.title or "")}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #000; line-height: 1; }}
.slide {{ display: block; }}
</style>
</head>
<body>{slides_html}</body>
</html>"""


# ── Playwright screenshot → PIL PDF ──────────────────────────────────────────

async def _render_screenshots_async(html: str, path: Path) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.set_content(html, wait_until="networkidle", timeout=30_000)

        count = await page.locator(".slide").count()
        png_bytes_list: list[bytes] = []
        for i in range(count):
            png = await page.locator(".slide").nth(i).screenshot()
            png_bytes_list.append(png)

        await browser.close()

    if not png_bytes_list:
        raise RuntimeError("No slides rendered")

    from PIL import Image
    images = [Image.open(io.BytesIO(b)).convert("RGB") for b in png_bytes_list]
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        format="PDF",
        resolution=144,
    )
    logger.debug("renderer.done slides=%s path=%s", len(images), path)


def _make_standalone_slide_html(slide: SlideSpec, theme: dict, title: str = "") -> str:
    """Wrap a single _render_slide() output into a complete HTML document."""
    slide_html = _render_slide(slide, theme)
    return (
        "<!DOCTYPE html>\n<html>\n<head>"
        '<meta charset="utf-8">'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">'
        "<style>* { margin:0; padding:0; box-sizing:border-box; } body { background:#000; line-height:1; }</style>"
        f"</head>\n<body>{slide_html}</body>\n</html>"
    )


def _build_slides_with_worker(spec: PresentationSpec) -> list[str]:
    """Generate per-slide HTML using Worker LLM (parallel, with deterministic fallback).

    Returns a list of standalone HTML strings in slide order.
    """
    from app.services.worker_llm_service import WorkerLLMService

    worker = WorkerLLMService()
    theme = _resolve_theme(spec)

    def render_one(idx: int, slide: SlideSpec) -> tuple[int, str]:
        layout_name = _resolve_layout(slide)
        payload = {
            "canvas_w": W,
            "canvas_h": H,
            "theme": theme,
            "layout_type": layout_name,
            "layout_blocks": LAYOUTS.get(layout_name, LAYOUTS["content_two_column"]),
            "slide": slide.model_dump(),
            "presentation_title": spec.title,
        }
        try:
            html = worker.render_slide_html(payload=payload)
            logger.debug("worker.ok slide_id=%s", slide.id)
            return idx, html
        except Exception as exc:
            logger.warning("worker.fallback slide_id=%s err=%s", slide.id, exc)
            return idx, _make_standalone_slide_html(slide, theme, spec.title or "")

    results: list[str] = [""] * len(spec.slides)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(render_one, i, slide): i for i, slide in enumerate(spec.slides)}
        for fut in as_completed(futures):
            idx, html = fut.result()
            results[idx] = html

    return results


# ── Playwright: standalone-HTML list → PDF ────────────────────────────────────

async def _render_standalone_slides_async(html_list: list[str], path: Path) -> None:
    """Render each standalone HTML in its own Playwright page, collect screenshots → PDF."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        png_bytes_list: list[bytes] = []

        for html in html_list:
            ctx = await browser.new_context(
                viewport={"width": W, "height": H},
                device_scale_factor=2,
            )
            page = await ctx.new_page()
            await page.set_content(html, wait_until="networkidle", timeout=30_000)
            slide_el = page.locator(".slide").first
            png = await slide_el.screenshot()
            png_bytes_list.append(png)
            await ctx.close()

        await browser.close()

    if not png_bytes_list:
        raise RuntimeError("No slides rendered (worker path)")

    from PIL import Image

    images = [Image.open(io.BytesIO(b)).convert("RGB") for b in png_bytes_list]
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        format="PDF",
        resolution=144,
    )
    logger.debug("worker_renderer.done slides=%s path=%s", len(images), path)


def render_pdf_html(path: Path, spec_json: dict) -> None:
    spec = PresentationSpec.model_validate(spec_json)

    if settings.WORKER_LLM_ENABLED and settings.openai_enabled:
        logger.debug("render_pdf_html.worker_mode slides=%s", len(spec.slides))
        html_list = _build_slides_with_worker(spec)
        asyncio.run(_render_standalone_slides_async(html_list, path))
    else:
        html = build_full_html(spec)
        asyncio.run(_render_screenshots_async(html, path))

    logger.debug("render_pdf_html.done slides=%s path=%s", len(spec.slides), path)
