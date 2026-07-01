"""
Slide renderer: HTML → per-slide PNG screenshots → combined PDF
Canvas: 1280 × 720 px (16:9), device_scale_factor=2 → effective 2560 × 1440
Inspired by block-based absolute positioning approach.
"""
from __future__ import annotations

import asyncio
import io
import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape
from pathlib import Path

from app.config import settings
from app.services.llm_service import PresentationSpec, SlideSpec, ThemeVariant

logger = logging.getLogger(__name__)

# ── Canvas dimensions ─────────────────────────────────────────────────────────
W, H = 1280, 720

# ── Accent color variants per theme (worker picks one per slide for visual variety) ──
THEME_ACCENT_VARIANTS: dict[str, list[str]] = {
    "dark_tech_pitch":    ["#22C55E", "#3B82F6", "#A855F7", "#F59E0B"],
    "clean_editorial":    ["#334155", "#7C3AED", "#0369A1", "#B45309"],
    "infographic_bright": ["#0EA5E9", "#10B981", "#F59E0B", "#8B5CF6"],
}

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
        {"type": "title",        "x": 64,  "y": 88,  "w": 740,  "h": 130, "fontSize": 32, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "accent_sub",   "x": 64,  "y": 222, "w": 720,  "h": 46,  "fontSize": 22, "fontWeight": 700},
        {"type": "body",         "x": 64,  "y": 276, "w": 700,  "h": 76,  "fontSize": 18, "fontWeight": 400, "always": True},
        {"type": "bullets",      "x": 64,  "y": 360, "w": 700,  "h": 298, "fontSize": 17, "fontWeight": 500, "plain": True},
        {"type": "key_message",  "x": 64,  "y": 676, "w": 700,  "h": 26,  "fontSize": 14},
        {"type": "image",        "x": 824, "y": 44,  "w": 400,  "h": 614, "radius": 22},
    ],
    "kpi_cards": [
        {"type": "title",        "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "subtitle",     "x": 64,  "y": 150, "w": 900,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "kpi_grid",     "x": 64,  "y": 202, "w": 1152, "h": 474},
    ],
    "timeline_process": [
        {"type": "title",           "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "subtitle",        "x": 64,  "y": 140, "w": 800,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "timeline_steps",  "x": 64,  "y": 190, "w": 1152, "h": 490},
    ],
    "quote_focus": [
        {"type": "quote_content",   "x": 0,   "y": 0,   "w": 1280, "h": 720},
    ],
    "comparison_split": [
        {"type": "title",           "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "comparison_cols", "x": 64,  "y": 184, "w": 1152, "h": 496},
    ],
    "infographic_visual": [
        {"type": "title",              "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "subtitle",           "x": 64,  "y": 140, "w": 800,  "h": 36,  "fontSize": 17, "fontWeight": 400},
        {"type": "infographic_nodes",  "x": 64,  "y": 190, "w": 1152, "h": 490},
    ],
    "chart_focus": [
        {"type": "title",        "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "chart",        "x": 64,  "y": 196, "w": 1152, "h": 448},
        {"type": "key_message",  "x": 64,  "y": 668, "w": 1152, "h": 30,  "fontSize": 14},
    ],
    "data_table": [
        {"type": "title",        "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "table",        "x": 64,  "y": 196, "w": 1152, "h": 448},
        {"type": "key_message",  "x": 64,  "y": 668, "w": 1152, "h": 30,  "fontSize": 14},
    ],
    "process_flow": [
        {"type": "title",        "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "flow_steps",   "x": 64,  "y": 244, "w": 1152, "h": 268},
        {"type": "key_message",  "x": 64,  "y": 668, "w": 1152, "h": 30,  "fontSize": 14},
    ],
    "multi_column": [
        {"type": "title",        "x": 64,  "y": 48,  "w": 1160, "h": 120, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "columns",      "x": 64,  "y": 196, "w": 1152, "h": 452},
        {"type": "key_message",  "x": 64,  "y": 668, "w": 1152, "h": 30,  "fontSize": 14},
    ],
}

# ── No-image variants: when a slide has no image, reflow content to full width ──
# instead of leaving an empty image panel / dead right column.
LAYOUTS_NO_IMAGE: dict[str, list[dict]] = {
    "hero_minimal": [
        {"type": "accent_bar",   "x": 0,   "y": 0,   "w": 5,    "h": 720},
        {"type": "tag",          "x": 72,  "y": 64,  "w": 400,  "h": 36},
        {"type": "title",        "x": 72,  "y": 128, "w": 1080, "h": 250, "fontSize": 76, "fontWeight": 800, "lineHeight": 1.05},
        {"type": "subtitle",     "x": 72,  "y": 392, "w": 940,  "h": 64,  "fontSize": 24, "fontWeight": 400},
        {"type": "bullets",      "x": 72,  "y": 476, "w": 1136, "h": 184, "fontSize": 18, "fontWeight": 500, "cols": 2},
        {"type": "key_message",  "x": 72,  "y": 672, "w": 1000, "h": 28,  "fontSize": 14},
    ],
    "content_two_column": [
        {"type": "tag",          "x": 64,  "y": 44,  "w": 400,  "h": 36},
        {"type": "title",        "x": 64,  "y": 88,  "w": 1152, "h": 130, "fontSize": 34, "fontWeight": 700, "lineHeight": 1.2, "action": True},
        {"type": "accent_sub",   "x": 64,  "y": 224, "w": 1100, "h": 46,  "fontSize": 22, "fontWeight": 700},
        {"type": "body",         "x": 64,  "y": 300, "w": 1080, "h": 200, "fontSize": 18, "fontWeight": 400},
        {"type": "bullets",      "x": 64,  "y": 300, "w": 1152, "h": 358, "fontSize": 18, "fontWeight": 500, "cols": 2},
        {"type": "key_message",  "x": 64,  "y": 676, "w": 1152, "h": 26,  "fontSize": 14},
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _layout_blocks(slide: SlideSpec, layout_name: str) -> list[dict]:
    """Pick the full-width variant when a slide has no image, else the default."""
    if not slide.image_url and layout_name in LAYOUTS_NO_IMAGE:
        return LAYOUTS_NO_IMAGE[layout_name]
    return LAYOUTS.get(layout_name, LAYOUTS["content_two_column"])

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


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _theme_with_accent(base: dict, accent: str) -> dict:
    """Per-slide copy of the theme with the accent (and its soft tint) swapped."""
    t = dict(base)
    t["accent"] = accent
    t["accent_soft"] = _hex_to_rgba(accent, 0.12)
    return t


def _assign_slide_accents(spec: PresentationSpec, theme_key: str) -> list[str]:
    """One single accent color for the whole deck — a deck must not turn into a
    traffic light of colors. Every slide uses the theme's base accent."""
    base = THEME_VARS.get(theme_key, THEME_VARS["clean_editorial"])["accent"]
    return [base] * len(spec.slides)


def _extract_quote(slide: SlideSpec) -> str:
    return slide.body or slide.key_message or (slide.bullets[0] if slide.bullets else slide.subtitle or "")


def _extract_kpi_cards(slide: SlideSpec) -> list[tuple[str, str]]:
    cards = []
    for idx, item in enumerate(slide.bullets[:4], 1):
        item = item.replace("**", "")
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


# ── Chart + table renderers ───────────────────────────────────────────────────

def _fmt_num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def _grouped_chart_svg(chart, t: dict, w: int, h: int) -> str:
    """Render a grouped (multi-series) bar or line chart as inline SVG."""
    accent, grid, txt, sub = t["accent"], t["border"], t["text_primary"], t["text_secondary"]
    cats = chart.categories[:6]
    series = chart.series[:3]
    if not cats or not series:
        return ""
    opac = [1.0, 0.6, 0.38]
    vmax = max((v for s in series for v in (s.values or [])), default=0) or 1
    PL, PR, PT, PB = 28, 28, 64, 54
    plot_w, plot_h = w - PL - PR, h - PT - PB
    base_y = PT + plot_h
    n = len(cats)
    slot = plot_w / n
    body = [f'<line x1="{PL}" y1="{base_y:.1f}" x2="{w-PR}" y2="{base_y:.1f}" stroke="{grid}" stroke-width="2"/>']
    lx = PL
    for si, s in enumerate(series):
        o = opac[si % 3]
        body.append(f'<rect x="{lx:.1f}" y="14" width="20" height="20" rx="4" fill="{accent}" fill-opacity="{o:.2f}"/>')
        body.append(f'<text x="{lx+28:.1f}" y="31" font-size="16" fill="{txt}">{escape(s.name)}</text>')
        lx += 48 + len(s.name) * 10
    if chart.chart_type == "line":
        for si, s in enumerate(series):
            vals = s.values
            o = max(opac[si % 3], 0.5)
            poly = " ".join(f"{PL+slot*(ci+0.5):.1f},{base_y-(vals[ci]/vmax)*plot_h:.1f}" for ci in range(min(n, len(vals))))
            body.append(f'<polyline points="{poly}" fill="none" stroke="{accent}" stroke-opacity="{o:.2f}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
            for ci in range(min(n, len(vals))):
                body.append(f'<circle cx="{PL+slot*(ci+0.5):.1f}" cy="{base_y-(vals[ci]/vmax)*plot_h:.1f}" r="5" fill="{accent}" fill-opacity="{o:.2f}"/>')
    else:
        m = len(series)
        group_w = slot * 0.66
        bw = group_w / m
        for ci in range(n):
            gx = PL + slot * ci + (slot - group_w) / 2
            for si, s in enumerate(series):
                v = s.values[ci] if ci < len(s.values) else 0
                bh = (v / vmax) * plot_h
                body.append(f'<rect x="{gx + bw*si:.1f}" y="{base_y-bh:.1f}" width="{bw*0.86:.1f}" height="{bh:.1f}" rx="4" fill="{accent}" fill-opacity="{opac[si % 3]:.2f}"/>')
    for ci, cat in enumerate(cats):
        body.append(f'<text x="{PL+slot*(ci+0.5):.1f}" y="{base_y+28:.1f}" text-anchor="middle" font-size="16" fill="{sub}">{escape(cat)}</text>')
    inner = "".join(body)
    return f'<svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg"><g font-family="Inter, sans-serif">{inner}</g></svg>'


def _render_chart_svg(chart, t: dict, w: int, h: int) -> str:
    """Render a chart as inline SVG (single-series points, or grouped series)."""
    if chart.series and chart.categories and chart.chart_type in ("bar", "line"):
        return _grouped_chart_svg(chart, t, w, h)
    pts = chart.points[:8]
    if not pts:
        return ""
    unit = chart.unit or ""
    accent, grid, txt, sub = t["accent"], t["border"], t["text_primary"], t["text_secondary"]

    if chart.chart_type == "pie":
        total = sum(p.value for p in pts) or 1
        cx, cy = w * 0.30, h * 0.52
        r = min(w * 0.26, h * 0.40)
        opac = [1.0, 0.74, 0.54, 0.40, 0.30, 0.22, 0.16, 0.12]
        body, ang = [], -90.0
        for i, pp in enumerate(pts):
            frac = pp.value / total
            a2 = ang + frac * 360
            x1, y1 = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
            x2, y2 = cx + r * math.cos(math.radians(a2)), cy + r * math.sin(math.radians(a2))
            large = 1 if frac > 0.5 else 0
            o = opac[i % len(opac)]
            body.append(f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} A{r:.1f},{r:.1f} 0 {large},1 {x2:.1f},{y2:.1f} Z" fill="{accent}" fill-opacity="{o:.2f}"/>')
            ly = cy - r + i * 42
            body.append(f'<rect x="{w*0.60:.1f}" y="{ly:.1f}" width="22" height="22" rx="5" fill="{accent}" fill-opacity="{o:.2f}"/>')
            body.append(f'<text x="{w*0.60+32:.1f}" y="{ly+17:.1f}" font-size="19" fill="{txt}">{escape(pp.label)} — {_fmt_num(pp.value)}{unit}</text>')
            ang = a2
        body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.56:.1f}" fill="{t["page_bg"]}"/>')
        inner = "".join(body)
        return f'<svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg"><g font-family="Inter, sans-serif">{inner}</g></svg>'

    PL, PR, PT, PB = 28, 28, 44, 54
    plot_w, plot_h = w - PL - PR, h - PT - PB
    base_y = PT + plot_h
    vmax = max((p.value for p in pts), default=0) or 1
    slot = plot_w / len(pts)

    def cx_(i: int) -> float:
        return PL + slot * (i + 0.5)

    def cy_(v: float) -> float:
        return base_y - (v / vmax) * plot_h

    body = [f'<line x1="{PL}" y1="{base_y:.1f}" x2="{w-PR}" y2="{base_y:.1f}" stroke="{grid}" stroke-width="2"/>']
    if chart.chart_type == "line":
        poly = " ".join(f"{cx_(i):.1f},{cy_(p.value):.1f}" for i, p in enumerate(pts))
        body.append(f'<polyline points="{poly}" fill="none" stroke="{accent}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
        for i, p in enumerate(pts):
            x, y = cx_(i), cy_(p.value)
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{accent}"/>')
            body.append(f'<text x="{x:.1f}" y="{y-14:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="{txt}">{_fmt_num(p.value)}{unit}</text>')
            body.append(f'<text x="{x:.1f}" y="{base_y+28:.1f}" text-anchor="middle" font-size="16" fill="{sub}">{escape(p.label)}</text>')
    else:  # bar
        bw = min(slot * 0.52, 130)
        for i, p in enumerate(pts):
            bh = (p.value / vmax) * plot_h
            x, y = cx_(i) - bw / 2, base_y - bh
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="{accent}"/>')
            body.append(f'<text x="{cx_(i):.1f}" y="{y-10:.1f}" text-anchor="middle" font-size="20" font-weight="700" fill="{txt}">{_fmt_num(p.value)}{unit}</text>')
            body.append(f'<text x="{cx_(i):.1f}" y="{base_y+28:.1f}" text-anchor="middle" font-size="16" fill="{sub}">{escape(p.label)}</text>')
    inner = "".join(body)
    return f'<svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg"><g font-family="Inter, sans-serif">{inner}</g></svg>'


def _render_table_html(table, t: dict) -> str:
    headers, rows = table.headers, table.rows[:9]
    thead = ""
    if headers:
        ths = "".join(
            f'<th style="text-align:{"left" if i == 0 else "right"};padding:15px 20px;font-size:16px;'
            f'font-weight:700;color:{t["text_primary"]};border-bottom:2px solid {t["accent"]};">{escape(h)}</th>'
            for i, h in enumerate(headers)
        )
        thead = f"<thead><tr>{ths}</tr></thead>"
    trs = ""
    for r in rows:
        tds = "".join(
            f'<td style="text-align:{"left" if i == 0 else "right"};padding:13px 20px;font-size:16px;'
            f'color:{t["text_primary"] if i == 0 else t["text_secondary"]};border-bottom:1px solid {t["border"]};'
            f'{"font-weight:600;" if i == 0 else ""}">{escape(c)}</td>'
            for i, c in enumerate(r)
        )
        trs += f"<tr>{tds}</tr>"
    return (
        f'<div style="width:100%;border:1px solid {t["border"]};border-radius:16px;overflow:hidden;background:{t["panel_bg"]};">'
        f'<table style="width:100%;border-collapse:collapse;">{thead}<tbody>{trs}</tbody></table></div>'
    )


# ── Block renderer ────────────────────────────────────────────────────────────

def _pos(b: dict) -> str:
    return f"position:absolute;left:{b['x']}px;top:{b['y']}px;width:{b['w']}px;height:{b['h']}px;overflow:hidden;"


def _rich(text: str, t: dict) -> str:
    """Escape text, then turn **key phrase** markers into accent-colored spans."""
    out = escape(text)
    return re.sub(
        r"\*\*(.+?)\*\*",
        lambda m: f'<span style="color:{t["accent"]};font-weight:700;">{m.group(1)}</span>',
        out,
    )


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
        if b.get("action"):
            # Consulting "action title": takeaway sentence + thin accent rule beneath.
            return (
                f'<div style="{p}display:flex;flex-direction:column;justify-content:flex-start;">'
                f'<div style="font-size:{fs}px;font-weight:{fw};line-height:{lh};letter-spacing:-.015em;'
                f'color:{t["text_primary"]};">{escape(slide.title or "")}</div>'
                f'<div style="margin-top:14px;width:60px;height:3px;background:{t["accent"]};border-radius:2px;flex-shrink:0;"></div>'
                f'</div>'
            )
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
        if not slide.body:
            return ""
        if slide.bullets and not b.get("always"):
            return ""
        fs = b.get("fontSize", 18)
        return (
            f'<div style="{p}font-size:{fs}px;color:{t["text_secondary"]};line-height:1.6;">'
            f'{_rich(slide.body, t)}</div>'
        )

    if btype == "bullets":
        bullets = slide.bullets[:8]
        if not bullets:
            return ""
        fs = b.get("fontSize", 17)
        fw = b.get("fontWeight", 500)
        if b.get("cols") == 2:
            items = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:12px;padding:9px 0;">'
                f'<span style="color:{t["accent"]};font-weight:700;font-size:{fs+1}px;flex-shrink:0;line-height:1.5;">—</span>'
                f'<span style="font-size:{fs}px;font-weight:{fw};line-height:1.5;color:{t["text_primary"]};">{_rich(item, t)}</span>'
                f'</div>'
                for item in bullets
            )
            return (
                f'<div style="{p}background:{t["panel_bg"]};border:1px solid {t["border"]};'
                f'border-radius:20px;padding:24px 36px;display:grid;grid-template-columns:1fr 1fr;'
                f'gap:4px 48px;align-content:center;">' + items + "</div>"
            )
        rows = []
        for i, item in enumerate(bullets):
            border = f"border-bottom:1px solid {t['border']};" if i < len(bullets) - 1 else ""
            rows.append(
                f'<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;{border}">'
                f'<span style="color:{t["accent"]};font-weight:700;font-size:{fs+1}px;flex-shrink:0;line-height:1.5;">—</span>'
                f'<span style="font-size:{fs}px;font-weight:{fw};line-height:1.5;color:{t["text_primary"]};">{_rich(item, t)}</span>'
                f'</div>'
            )
        if b.get("plain"):
            return (
                f'<div style="{p}display:flex;flex-direction:column;justify-content:center;">'
                + "".join(rows) + "</div>"
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
            f'<div style="font-size:18px;font-weight:500;color:{t["text_primary"]};">{_rich(item, t)}</div>'
            f'</div>'
            for i, item in enumerate(bullets)
        )
        return f'<div style="{p}display:flex;flex-direction:column;justify-content:center;gap:12px;">{items}</div>'

    if btype == "kpi_grid":
        cards = _extract_kpi_cards(slide)
        cols = min(len(cards), 4)
        cards_html = "".join(
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
            f'padding:32px 28px;display:flex;flex-direction:column;justify-content:center;'
            f'height:300px;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:0;left:0;right:0;height:5px;background:{t["accent"]};'
            f'border-radius:16px 16px 0 0;{"opacity:.5;" if idx % 2 == 1 else ""}"></div>'
            f'<div style="font-size:54px;font-weight:800;color:{t["accent"]};letter-spacing:-.03em;line-height:1;margin-bottom:12px;">{escape(metric)}</div>'
            f'<div style="font-size:16px;color:{t["text_secondary"]};font-weight:500;line-height:1.5;">{escape(label)}</div>'
            f'</div>'
            for idx, (metric, label) in enumerate(cards[:4])
        )
        return f'<div style="{p}display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;align-items:center;">{cards_html}</div>'

    if btype == "timeline_steps":
        steps = slide.bullets[:6] or (slide.body.split("\n") if slide.body else [])
        steps_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:22px;">'
            f'<div style="width:44px;height:44px;border-radius:12px;background:{t["page_bg"]};'
            f'border:2px solid {t["accent"]};display:flex;align-items:center;justify-content:center;'
            f'font-size:16px;font-weight:700;color:{t["accent"]};flex-shrink:0;position:relative;z-index:1;">{i + 1}</div>'
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:12px;'
            f'padding:0 22px;flex:1;min-height:44px;display:flex;align-items:center;'
            f'font-size:17px;font-weight:500;line-height:1.45;color:{t["text_primary"]};"><span>{_rich(step, t)}</span></div>'
            f'</div>'
            for i, step in enumerate(steps)
        )
        return (
            f'<div style="{p}display:flex;flex-direction:column;justify-content:center;">'
            f'<div style="position:relative;display:flex;flex-direction:column;gap:18px;">'
            f'<div style="position:absolute;left:21px;top:22px;bottom:22px;width:2px;background:{t["border"]};"></div>'
            + steps_html
            + "</div></div>"
        )

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
                f'<span style="color:{t["text_primary"]};">{_rich(item, t)}</span></div>'
                for i, item in enumerate(items)
            )
            return (
                f'<div style="background:{bg};border:{bw} solid {bc};border-radius:16px;padding:22px 22px 14px;'
                f'display:flex;flex-direction:column;">'
                f'<div style="font-size:18px;font-weight:700;color:{tc};margin-bottom:14px;'
                f'padding-bottom:12px;border-bottom:2px solid {bc};">{escape(title)}</div>'
                f'<div style="display:flex;flex-direction:column;justify-content:flex-start;gap:6px;">{rows}</div>'
                f'</div>'
            )

        return (
            f'<div style="{p}display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:center;">'
            + _col(left_title, left_items, False)
            + _col(right_title, right_items, True)
            + "</div>"
        )

    if btype == "infographic_nodes":
        nodes = slide.bullets[:6] or (slide.body.split("\n") if slide.body else [])
        cols = 3 if len(nodes) > 3 else max(len(nodes), 1)
        nodes_html = "".join(
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
            f'padding:28px 24px;display:flex;flex-direction:column;justify-content:center;'
            f'height:300px;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;bottom:0;left:0;right:0;height:3px;background:{t["accent"]};opacity:.4;"></div>'
            f'<div style="width:40px;height:40px;border-radius:10px;background:{t["accent_soft"]};border:1.5px solid {t["accent"]};'
            f'color:{t["accent"]};font-size:16px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:18px;">{i + 1}</div>'
            f'<div style="font-size:18px;line-height:1.5;color:{t["text_primary"]};font-weight:500;">{_rich(node, t)}</div>'
            f'</div>'
            for i, node in enumerate(nodes)
        )
        return f'<div style="{p}display:grid;grid-template-columns:repeat({cols},1fr);gap:16px;align-items:center;">{nodes_html}</div>'

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

    if btype == "flow_steps":
        steps = slide.bullets[:6] or [c.header for c in slide.columns[:6]]
        if not steps:
            return ""
        n = len(steps)
        parts = []
        for i, step in enumerate(steps):
            title, desc = step, ""
            for sep in (" — ", " – ", ": "):
                if sep in step:
                    title, desc = step.split(sep, 1)
                    break
            parts.append(
                f'<div style="flex:1;background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
                f'padding:24px 20px;display:flex;flex-direction:column;justify-content:center;min-width:0;">'
                f'<div style="width:36px;height:36px;border-radius:10px;background:{t["accent_soft"]};border:1.5px solid {t["accent"]};'
                f'color:{t["accent"]};font-size:15px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:14px;">{i + 1}</div>'
                f'<div style="font-size:17px;font-weight:700;line-height:1.3;color:{t["text_primary"]};">{_rich(title, t)}</div>'
                + (f'<div style="font-size:14px;line-height:1.45;color:{t["text_secondary"]};margin-top:8px;">{_rich(desc, t)}</div>' if desc else "")
                + "</div>"
            )
            if i < n - 1:
                parts.append(
                    f'<div style="flex-shrink:0;display:flex;align-items:center;padding:0 8px;'
                    f'color:{t["accent"]};font-size:30px;font-weight:700;">&#8594;</div>'
                )
        return f'<div style="{p}display:flex;align-items:stretch;">{"".join(parts)}</div>'

    if btype == "columns":
        cols = slide.columns[:5]
        if not cols:
            return ""
        col_html = "".join(
            f'<div style="background:{t["panel_bg"]};border:1px solid {t["border"]};border-radius:16px;'
            f'padding:24px 22px;display:flex;flex-direction:column;min-width:0;">'
            f'<div style="font-size:17px;font-weight:700;color:{t["accent"]};margin-bottom:14px;padding-bottom:12px;'
            f'border-bottom:2px solid {t["accent"]};">{escape(c.header)}</div>'
            + "".join(
                f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;font-size:15px;'
                f'line-height:1.45;color:{t["text_primary"]};">'
                f'<span style="color:{t["accent"]};font-weight:700;flex-shrink:0;">—</span>'
                f'<span>{_rich(it, t)}</span></div>'
                for it in c.items[:6]
            )
            + "</div>"
            for c in cols
        )
        return (
            f'<div style="{p}display:grid;grid-template-columns:repeat({len(cols)},1fr);gap:18px;">'
            f'{col_html}</div>'
        )

    if btype == "chart":
        if not slide.chart or not (slide.chart.points or slide.chart.series):
            return ""
        return f'<div style="{p}">{_render_chart_svg(slide.chart, t, b["w"], b["h"])}</div>'

    if btype == "table":
        if not slide.table or not slide.table.rows:
            return ""
        return f'<div style="{p}display:flex;align-items:center;">{_render_table_html(slide.table, t)}</div>'

    return ""


# ── Slide + document ──────────────────────────────────────────────────────────

def _render_slide(slide: SlideSpec, theme: dict) -> str:
    layout_name = _resolve_layout(slide)
    blocks = _layout_blocks(slide, layout_name)
    blocks_html = "".join(_render_block(b, slide, theme) for b in blocks)
    source_html = (
        f'<div style="position:absolute;right:56px;bottom:22px;max-width:55%;text-align:right;'
        f'font-size:13px;color:{theme["text_secondary"]};opacity:.6;">{escape(slide.source)}</div>'
        if getattr(slide, "source", None) else ""
    )
    font = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    return (
        f'<div class="slide" style="position:relative;width:{W}px;height:{H}px;overflow:hidden;'
        f'background:{theme["page_bg"]};color:{theme["text_primary"]};font-family:{font};">'
        + blocks_html
        + source_html
        + "</div>"
    )


def build_full_html(spec: PresentationSpec) -> str:
    theme = _resolve_theme(spec)
    theme_key = spec.theme_variant or "clean_editorial"
    accents = _assign_slide_accents(spec, theme_key)
    slides_html = "\n".join(
        _render_slide(s, _theme_with_accent(theme, a))
        for s, a in zip(spec.slides, accents)
    )
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


def _slide_neighbor_summary(slide: SlideSpec | None) -> dict | None:
    """Compact slide summary for worker context (prev/next awareness)."""
    if slide is None:
        return None
    return {
        "title": slide.title,
        "layout_type": slide.layout_type,
        "type": slide.type,
    }


def _build_slides_with_worker(spec: PresentationSpec) -> list[str]:
    """Generate per-slide HTML using Worker LLM (parallel, with deterministic fallback).

    Each slide payload includes:
    - Neighbor context (prev/next slide summaries) for visual continuity
    - slide_index + total_slides for narrative positioning
    - accent_variants so the worker can vary colors across slides

    Returns a list of standalone HTML strings in slide order.
    """
    from app.services.worker_llm_service import WorkerLLMService

    worker = WorkerLLMService()
    theme_key = spec.theme_variant or "clean_editorial"
    theme = _resolve_theme(spec)
    accent_variants = THEME_ACCENT_VARIANTS.get(theme_key, [theme["accent"]])
    total = len(spec.slides)

    def render_one(idx: int, slide: SlideSpec) -> tuple[int, str]:
        layout_name = _resolve_layout(slide)
        prev_slide = spec.slides[idx - 1] if idx > 0 else None
        next_slide = spec.slides[idx + 1] if idx < total - 1 else None

        payload = {
            "canvas_w": W,
            "canvas_h": H,
            "theme": theme,
            "accent_variants": accent_variants,
            "suggested_accent": accent_variants[idx % len(accent_variants)],
            "layout_type": layout_name,
            "layout_blocks": LAYOUTS.get(layout_name, LAYOUTS["content_two_column"]),
            "slide": slide.model_dump(),
            "slide_index": idx,
            "total_slides": total,
            "position": "first" if idx == 0 else ("last" if idx == total - 1 else "middle"),
            "prev_slide": _slide_neighbor_summary(prev_slide),
            "next_slide": _slide_neighbor_summary(next_slide),
            "presentation_title": spec.title,
        }
        try:
            html = worker.render_slide_html(payload=payload)
            logger.debug("worker.ok slide_id=%s idx=%s", slide.id, idx)
            return idx, html
        except Exception as exc:
            logger.warning("worker.fallback slide_id=%s idx=%s err=%s", slide.id, idx, exc)
            return idx, _make_standalone_slide_html(slide, theme, spec.title or "")

    results: list[str] = [""] * total
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
