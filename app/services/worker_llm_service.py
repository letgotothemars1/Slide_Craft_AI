from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


class WorkerLLMService:
    """Per-slide HTML rendering via OpenAI LLM (Worker agent).

    Each call receives a payload dict describing one slide (spec + theme + layout blocks)
    and returns a complete standalone HTML document string ready for Playwright rendering.
    """

    def __init__(self) -> None:
        if not settings.openai_enabled:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Worker uses a dedicated model if configured, otherwise falls back to the main model.
        self.model = settings.OPENAI_WORKER_MODEL or settings.OPENAI_MODEL

    @staticmethod
    def _extract_text(response: object) -> str:
        """Extracts plain text from Responses API object."""
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                content_type = getattr(content, "type", None)
                if content_type in {"output_text", "text"}:
                    text = getattr(content, "text", None) or getattr(content, "value", None)
                    if isinstance(text, str):
                        chunks.append(text)
        return "".join(chunks).strip()

    @staticmethod
    def _strip_fences(html: str) -> str:
        """Remove markdown code fences if the model disobeys the instruction."""
        html = html.strip()
        if html.startswith("```"):
            # Drop first line (```html or ```) and last ``` fence
            html = html.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return html

    def render_slide_html(self, *, payload: dict) -> str:
        """Call Worker LLM with a slide payload and return raw HTML for one slide.

        Raises on API failure so the caller can fall back to deterministic rendering.
        """
        from app.prompts.worker_prompt import build_worker_slide_prompt

        system, user = build_worker_slide_prompt(payload=payload)
        slide_id = payload.get("slide", {}).get("id", "?")

        logger.debug("worker.request slide_id=%s model=%s", slide_id, self.model)

        response = self.client.responses.create(
            model=self.model,
            temperature=0.7,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user}],
                },
            ],
        )

        raw = self._extract_text(response)
        if not raw:
            raise RuntimeError(f"Worker returned empty response for slide {slide_id}")

        html = self._strip_fences(raw)
        logger.debug("worker.done slide_id=%s html_len=%s", slide_id, len(html))
        return html
