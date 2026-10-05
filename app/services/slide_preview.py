"""Cached slide previews for the review workspace.

The workspace asks for every thumbnail at once. Rendering them one request at a
time launches a headless browser per request — ten concurrent Chromium
instances, which exhausts the machine and returns 500s. So the whole deck is
rendered once per spec version and served from memory afterwards.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections import OrderedDict

from app.services.html_render_service import PENDING_IMAGE, render_slide_pngs

logger = logging.getLogger(__name__)

# Decks are a few hundred KB each; a handful is plenty for concurrent reviews.
_MAX_DECKS = 8
_cache: OrderedDict[tuple[str, str], dict[int, bytes]] = OrderedDict()
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


def get_slide_png(job_id: str, spec_json: dict, index: int) -> bytes | None:
    """One slide's PNG, rendering the deck on first use for this spec version."""
    key = (job_id, _spec_fingerprint(spec_json))

    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            _cache.move_to_end(key)
            return cached.get(index)

    # Held across the render so ten parallel thumbnail requests produce one
    # browser launch rather than ten.
    with _lock:
        cached = _cache.get(key)
        if cached is None:
            logger.debug("preview.render.started job_id=%s", job_id)
            cached = render_slide_pngs(_with_pending_images(spec_json))
            _cache[key] = cached
            # Drop other versions of this deck: only the current text is useful.
            for stale in [k for k in _cache if k[0] == job_id and k != key]:
                _cache.pop(stale, None)
            while len(_cache) > _MAX_DECKS:
                _cache.popitem(last=False)
            logger.debug("preview.render.done job_id=%s slides=%s", job_id, len(cached))
        _cache.move_to_end(key)
        return cached.get(index)
