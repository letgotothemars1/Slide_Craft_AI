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
    "chart_focus",
    "data_table",
    "process_flow",
    "multi_column",
]
ThemeVariant = Literal["dark_tech_pitch", "clean_editorial", "infographic_bright"]
VisualDensity = Literal["low", "medium", "high"]
# Deck-level image budget signal: how image-driven the topic is.
ImageDensity = Literal["rich", "moderate", "minimal"]


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
        "image_density": {"type": "string", "enum": ["rich", "moderate", "minimal"]},
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
                                    "chart_focus",
                                    "data_table",
                                    "process_flow",
                                    "multi_column",
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
                    "chart": {
                        "anyOf": [
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                                    "unit": {"type": "string"},
                                    "points": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "label": {"type": "string"},
                                                "value": {"type": "number"},
                                            },
                                            "required": ["label", "value"],
                                        },
                                    },
                                    "categories": {"type": "array", "items": {"type": "string"}},
                                    "series": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "name": {"type": "string"},
                                                "values": {"type": "array", "items": {"type": "number"}},
                                            },
                                            "required": ["name", "values"],
                                        },
                                    },
                                },
                                "required": ["chart_type", "unit", "points", "categories", "series"],
                            },
                            {"type": "null"},
                        ]
                    },
                    "table": {
                        "anyOf": [
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "headers": {"type": "array", "items": {"type": "string"}},
                                    "rows": {
                                        "type": "array",
                                        "items": {"type": "array", "items": {"type": "string"}},
                                    },
                                },
                                "required": ["headers", "rows"],
                            },
                            {"type": "null"},
                        ]
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "header": {"type": "string"},
                                "items": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["header", "items"],
                        },
                    },
                    "source": {"anyOf": [{"type": "string"}, {"type": "null"}]},
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
                    "chart",
                    "table",
                    "columns",
                    "source",
                    "speaker_notes",
                ],
            },
        },
    },
    "required": ["title", "subtitle", "theme_variant", "image_density", "audience", "language", "style", "slides"],
}


class ChartPoint(BaseModel):
    """One data point: a category label and its numeric value."""

    label: str = Field(min_length=1, max_length=40)
    value: float

    model_config = ConfigDict(extra="forbid")


class ChartSeries(BaseModel):
    """One named series for a grouped chart; values align to ChartSpec.categories."""

    name: str = Field(min_length=1, max_length=40)
    values: list[float] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ChartSpec(BaseModel):
    """Chart data the renderer draws as SVG.

    Single-series: use `points`. Grouped (2-3 series): use `categories` (shared
    x labels) + `series`.
    """

    chart_type: Literal["bar", "line", "pie"]
    unit: str = Field(default="", max_length=12)
    points: list[ChartPoint] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    series: list[ChartSeries] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TableSpec(BaseModel):
    """Simple data table: header row + body rows of string cells."""

    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ColumnSpec(BaseModel):
    """One labeled column for multi_column layout: header + list of items."""

    header: str = Field(min_length=1, max_length=60)
    items: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


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
    chart: ChartSpec | None = None
    table: TableSpec | None = None
    columns: list[ColumnSpec] = Field(default_factory=list)
    source: str | None = Field(default=None, max_length=200)
    speaker_notes: str | None = Field(default=None, max_length=4000)

    model_config = ConfigDict(extra="forbid")


class PresentationSpec(BaseModel):
    """Structured presentation spec returned by LLM."""

    title: str = Field(min_length=1, max_length=200)
    subtitle: str | None = Field(default=None, max_length=300)
    theme_variant: ThemeVariant | None = None
    image_density: ImageDensity = Field(default="moderate")
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


class AnthropicLLMService:
    """Claude Messages API wrapper for structured JSON spec generation.

    Uses structured outputs (output_config.format) to constrain the response to
    the same presentation-spec schema the OpenAI path uses.
    """

    def __init__(self) -> None:
        if not settings.anthropic_enabled:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        # Lazy import keeps app startup lightweight and explicit on dependency failures.
        import anthropic

        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

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
        """Calls Claude once and returns validated structured spec as dict."""
        system_instruction, developer_instruction, user_input = build_presentation_prompt_parts(
            prompt=prompt,
            audience=audience,
            style=style,
            language=language,
            slides=slides,
            retrieved_chunks=retrieved_chunks,
        )
        # Claude has no separate "developer" role — fold it into the system prompt.
        system_text = f"{system_instruction}\n\n{developer_instruction}"

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

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                system=system_text,
                messages=[{"role": "user", "content": user_input}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": PRESENTATION_SPEC_OPENAI_SCHEMA,
                    }
                },
            )

            logger.debug(
                "llm.response.received model=%s response_id=%s stop_reason=%s",
                self.model,
                response.id,
                response.stop_reason,
            )

            if response.stop_reason == "max_tokens":
                raise RuntimeError("Claude response truncated (max_tokens) — raise max_tokens")
            if response.stop_reason == "refusal":
                raise RuntimeError("Claude refused the request")

            raw_json = next(
                (b.text for b in response.content if b.type == "text"), ""
            ).strip()
            if not raw_json:
                raise RuntimeError("Messages API returned empty text output")

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


def get_llm_service() -> OpenAILLMService | AnthropicLLMService:
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicLLMService()
    return OpenAILLMService()
