from __future__ import annotations

import json
import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings
from app.prompts.presentation_prompt import build_presentation_prompt_parts

logger = logging.getLogger(__name__)

SlideType = Literal["title", "agenda", "content", "quote", "conclusion"]
LayoutType = Literal[
    "hero_minimal",
    "agenda_clean",
    "content_two_column",
    "kpi_cards",
    "timeline_process",
    "infographic_visual",
    "quote_focus",
    "comparison_split",
]
ThemeVariant = Literal["dark_tech_pitch", "clean_editorial", "infographic_bright"]
VisualDensity = Literal["low", "medium", "high"]


# OpenAI strict structured outputs requires:
# - required includes every key from properties
# - additionalProperties is explicitly false for every object
# - nullable fields represented via anyOf with {"type":"null"}
PRESENTATION_SPEC_OPENAI_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "subtitle": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "theme_variant": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": ["dark_tech_pitch", "clean_editorial", "infographic_bright"],
                },
                {"type": "null"},
            ]
        },
        "audience": {"type": "string"},
        "language": {"type": "string"},
        "style": {"type": "string"},
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["title", "agenda", "content", "quote", "conclusion"],
                    },
                    "layout_type": {
                        "anyOf": [
                            {
                                "type": "string",
                                "enum": [
                                    "hero_minimal",
                                    "agenda_clean",
                                    "content_two_column",
                                    "kpi_cards",
                                    "timeline_process",
                                    "infographic_visual",
                                    "quote_focus",
                                    "comparison_split",
                                ],
                            },
                            {"type": "null"},
                        ]
                    },
                    "title": {"type": "string"},
                    "subtitle": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "visual_density": {
                        "anyOf": [
                            {"type": "string", "enum": ["low", "medium", "high"]},
                            {"type": "null"},
                        ]
                    },
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "body": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "visual_hint": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "section": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "key_message": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "image_prompt": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "image_url": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "chart_hint": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "speaker_notes": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
                "required": [
                    "id",
                    "type",
                    "layout_type",
                    "title",
                    "subtitle",
                    "visual_density",
                    "bullets",
                    "body",
                    "visual_hint",
                    "section",
                    "key_message",
                    "image_prompt",
                    "image_url",
                    "chart_hint",
                    "speaker_notes",
                ],
            },
        },
    },
    "required": ["title", "subtitle", "theme_variant", "audience", "language", "style", "slides"],
}


class SlideSpec(BaseModel):
    """One slide description for downstream renderer pipeline."""

    id: str = Field(min_length=1, max_length=64)
    type: SlideType
    layout_type: LayoutType | None = None
    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    visual_density: VisualDensity | None = None
    bullets: list[str] = Field(default_factory=list)
    body: str | None = Field(default=None, max_length=2000)
    visual_hint: str | None = Field(default=None, max_length=300)
    section: str | None = Field(default=None, max_length=120)
    key_message: str | None = Field(default=None, max_length=300)
    image_prompt: str | None = Field(default=None, max_length=600)
    image_url: str | None = Field(default=None, max_length=2000)
    chart_hint: str | None = Field(default=None, max_length=300)
    speaker_notes: str | None = Field(default=None, max_length=4000)

    model_config = ConfigDict(extra="forbid")


class PresentationSpec(BaseModel):
    """Structured presentation spec returned by LLM."""

    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    theme_variant: ThemeVariant | None = None
    audience: str = Field(min_length=1, max_length=200)
    language: str = Field(min_length=1, max_length=16)
    style: str = Field(min_length=1, max_length=500)
    slides: list[SlideSpec] = Field(min_length=1, max_length=60)

    model_config = ConfigDict(extra="forbid")


class OpenAILLMService:
    """OpenAI Responses API wrapper for deterministic JSON spec generation."""

    def __init__(self) -> None:
        if not settings.openai_enabled:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        # Lazy import keeps app startup lightweight and explicit on dependency failures.
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    @staticmethod
    def _extract_output_text(response: object) -> str:
        """Extracts plain text payload from Responses API object."""
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

    def generate_presentation_spec(
        self,
        *,
        prompt: str,
        audience: str,
        style: str,
        language: str,
        slides: int,
        retrieved_chunks: list[str] | None = None,
    ) -> dict:
        """Calls OpenAI once and returns validated structured spec as dict."""
        system_instruction, developer_instruction, user_input = build_presentation_prompt_parts(
            prompt=prompt,
            audience=audience,
            style=style,
            language=language,
            slides=slides,
            retrieved_chunks=retrieved_chunks,
        )

        try:
            logger.debug("model.used model=%s", self.model)
            logger.debug(
                "llm.request.started model=%s slides=%s audience=%s style=%s language=%s",
                self.model,
                slides,
                audience,
                style,
                language,
            )

            response = self.client.responses.create(
                model=self.model,
                temperature=0.1,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_instruction}],
                    },
                    {
                        "role": "developer",
                        "content": [{"type": "input_text", "text": developer_instruction}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_input}],
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "presentation_spec",
                        "strict": True,
                        "schema": PRESENTATION_SPEC_OPENAI_SCHEMA,
                    }
                },
            )

            logger.debug(
                "llm.response.received model=%s response_id=%s",
                self.model,
                getattr(response, "id", None),
            )

            raw_json = self._extract_output_text(response)
            if not raw_json:
                raise RuntimeError("Responses API returned empty output_text")

            parsed_json = json.loads(raw_json)
            spec = PresentationSpec.model_validate(parsed_json)

            if len(spec.slides) != slides:
                raise ValueError(
                    f"Model returned {len(spec.slides)} slides, but {slides} requested"
                )

            logger.debug("llm.response.parsed slides=%s title=%s", len(spec.slides), spec.title)
            return spec.model_dump()

        except Exception:
            logger.exception("llm.error model=%s", self.model)
            raise


def get_llm_service() -> OpenAILLMService:
    return OpenAILLMService()
