"""PDF export for the modular journey, drawn from the same scene as PPTX.

The browser preview, the PowerPoint export and this PDF all consume
`build_scene`, so a slide cannot look like three different things depending on
where it is viewed. PPTX carries native text boxes for editing; this file is
the fixed, presentable copy.
"""
from __future__ import annotations

import logging
from io import BytesIO

from PIL import Image

from app.project_schemas import ProjectResponse
from app.services.design_quality import render_scene
from app.services.design_scene import build_scene

logger = logging.getLogger(__name__)


def render_project_pdf(project: ProjectResponse) -> bytes:
    """Render every ready slide to a page and stitch them into one PDF."""
    order_of = {item.id: item.order for item in project.outline}
    pages: list[Image.Image] = []

    for slide in project.slides:
        scene = build_scene(slide, project.theme, order_of.get(slide.id, len(pages) + 1))
        if not scene:
            # A slide with no design has nothing to draw; skipping keeps the
            # export usable instead of emitting a blank page.
            logger.warning("pdf.slide.skipped slide=%s reason=no_scene", slide.id)
            continue
        png, issues = render_scene(scene)
        if issues:
            # Not fatal: the student may still want the file. Record it so a
            # clipped slide is traceable rather than silently shipped.
            logger.warning("pdf.slide.issues slide=%s issues=%s", slide.id, issues)
        pages.append(Image.open(BytesIO(png)).convert("RGB"))

    if not pages:
        raise ValueError("No slides are ready to export")

    buffer = BytesIO()
    pages[0].save(buffer, format="PDF", save_all=True, append_images=pages[1:], resolution=96.0)
    return buffer.getvalue()
