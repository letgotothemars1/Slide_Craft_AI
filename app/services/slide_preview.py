"""Cached slide previews for the review workspace.

The workspace asks for every thumbnail at once. Rendering them one request at a
time launches a headless browser per request — ten concurrent Chromium
instances, which exhausts the machine and returns 500s. So the whole deck is
rendered once per spec version and served from memory afterwards.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import threading
from collections import OrderedDict

from PIL import Image

from app.services.html_render_service import PENDING_IMAGE, render_slide_pngs

logger = logging.getLogger(__name__)

# Decks are a few MB each; a handful is plenty for concurrent reviews.
_MAX_DECKS = 8
# Full-size renders, keyed by (job id, spec fingerprint).
_cache: OrderedDict[tuple[str, str], dict[int, bytes]] = OrderedDict()
# Downscaled copies of those, keyed by (job id, spec fingerprint, width).
_scaled: OrderedDict[tuple[str, str, int], dict[int, bytes]] = OrderedDict()
_lock = threading.Lock()


def _spec_fingerprint(spec_json: dict) -> str:
    """Identity of this exact text, so an edit misses the cache by construction."""
    payload = json.dumps(spec_json, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _with_pending_images(spec_json: dict) -> dict:
    """Mark the slides that will actually receive an illustration.

    Not every slide with an `image_prompt` gets one: the budget comes from the
    deck's `image_density` and only some layouts are eligible. Asking the same
    selector the pipeline uses keeps the preview honest — a placeholder appears
    exactly where a picture will, and nowhere else.
    """
    from app.services.llm_service import PresentationSpec
    from app.services.orchestrator import _select_image_candidates

    try:
        spec = PresentationSpec.model_validate(spec_json)
        chosen = {index for index, _rank, _prompt in _select_image_candidates(spec)}
    except Exception:
        logger.exception("preview.image_candidates.failed")
        return spec_json

    if not chosen:
        return spec_json

    marked = dict(spec_json)
    marked["slides"] = [
        {**slide, "image_url": PENDING_IMAGE}
        if i in chosen and not slide.get("image_url")
        else slide
        for i, slide in enumerate(spec_json.get("slides", []))
    ]
    return marked


def _downscale(png: bytes, width: int) -> bytes:
    """A slide at the size it will actually be shown.

    The renderer works at 2560x1440 so a slide stays sharp when it fills the
    stage. The thumbnail rail is 180 CSS px wide, and serving it that same file
    costs ~1.7 MB on the wire and a 14 MB decoded bitmap per thumbnail — a
    ten-slide deck then holds well over a hundred megabytes of image memory for
    pictures the size of a stamp, which is where the rail starts dropping them.
    """
    with Image.open(io.BytesIO(png)) as image:
        if image.width <= width:
            return png
        height = round(image.height * width / image.width)
        resized = image.convert("RGB").resize((width, height), Image.LANCZOS)
    buffer = io.BytesIO()
    resized.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _evict(job_id: str, key: tuple[str, str]) -> None:
    """Drop other versions of this deck: only the current text is useful."""
    for stale in [k for k in _cache if k[0] == job_id and k != key]:
        _cache.pop(stale, None)
    for stale in [k for k in _scaled if k[:2] != key and k[0] == job_id]:
        _scaled.pop(stale, None)
    while len(_cache) > _MAX_DECKS:
        dropped, _ = _cache.popitem(last=False)
        for stale in [k for k in _scaled if k[:2] == dropped]:
            _scaled.pop(stale, None)


def get_slide_png(job_id: str, spec_json: dict, index: int, width: int | None = None) -> bytes | None:
    """One slide's PNG, rendering the deck on first use for this spec version.

    `width` asks for a downscaled copy; without it the slide comes back at full
    render resolution.
    """
    key = (job_id, _spec_fingerprint(spec_json))

    with _lock:
        if width is None:
            cached = _cache.get(key)
            if cached is not None:
                _cache.move_to_end(key)
                return cached.get(index)
        else:
            small = _scaled.get((*key, width))
            if small is not None:
                _scaled.move_to_end((*key, width))
                return small.get(index)

    # Held across the render so ten parallel thumbnail requests produce one
    # browser launch rather than ten.
    with _lock:
        cached = _cache.get(key)
        if cached is None:
            logger.debug("preview.render.started job_id=%s", job_id)
            cached = render_slide_pngs(_with_pending_images(spec_json))
            _cache[key] = cached
            _evict(job_id, key)
            logger.debug("preview.render.done job_id=%s slides=%s", job_id, len(cached))
        _cache.move_to_end(key)

        if width is None:
            return cached.get(index)

        # Scaled in one pass: the rail asks for every thumbnail at once, so
        # doing them together turns the other nine requests into cache hits.
        small = _scaled.get((*key, width))
        if small is None:
            small = {i: _downscale(png, width) for i, png in cached.items()}
            _scaled[(*key, width)] = small
            # `width` comes from the query string, so one deck could otherwise
            # accumulate a bucket per requested size.
            while len(_scaled) > _MAX_DECKS * 2:
                _scaled.popitem(last=False)
        _scaled.move_to_end((*key, width))
        return small.get(index)
