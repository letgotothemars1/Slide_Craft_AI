from __future__ import annotations

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CriticLLMService:
    """Quality-review agent that checks and fixes a PresentationSpec before rendering.

    The critic receives the full spec JSON, applies quality rules defined in the
    critic prompt, and returns a corrected spec with the same schema and slide count.
    On any failure the original spec is returned unchanged (never blocks the pipeline).
    """

    def __init__(self) -> None:
        if not settings.openai_enabled:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_CRITIC_MODEL or settings.OPENAI_MODEL

    @staticmethod
    def _extract_text(response: object) -> str:
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
    def _strip_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return text

    def review_and_fix(self, spec_json: dict) -> dict:
        """Run critic review on the spec. Returns corrected spec or original on failure."""
        from app.prompts.critic_prompt import build_critic_prompt

        system, user = build_critic_prompt(spec_json=spec_json)
        original_slides = len(spec_json.get("slides", []))

        logger.debug("critic.request slides=%s model=%s", original_slides, self.model)

        try:
            response = self.client.responses.create(
                model=self.model,
                temperature=0.2,
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
                logger.warning("critic.empty_response — keeping original spec")
                return spec_json

            corrected = json.loads(self._strip_fences(raw))

            # Safety check: slide count must not change
            corrected_slides = len(corrected.get("slides", []))
            if corrected_slides != original_slides:
                logger.warning(
                    "critic.slide_count_mismatch original=%s corrected=%s — keeping original",
                    original_slides,
                    corrected_slides,
                )
                return spec_json

            logger.debug("critic.done slides=%s", corrected_slides)
            return corrected

        except Exception:
            logger.exception("critic.error — keeping original spec")
            return spec_json
