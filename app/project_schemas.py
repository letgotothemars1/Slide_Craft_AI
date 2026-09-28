"""Shared response contract for the modular course MVP.

The first endpoint serves a checked-in fixture. Persistence and generation are
added by later MVP modules without changing this response shape.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProjectPhase = Literal["intake", "outline_draft", "outline_approved", "building", "ready", "error"]
SlideStatus = Literal["queued", "generating", "ready", "error"]
BlockStatus = Literal["ready", "generating", "error"]
Theme = Literal["clean_editorial", "dark_tech_pitch", "infographic_bright"]
LayoutType = Literal["title", "content", "comparison"]


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    page_number: int = Field(ge=1)
    excerpt: str


class OutlineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    order: int = Field(ge=1)
    purpose: str
    title: str
    key_message: str
    evidence_refs: list[SourceRef]
    layout_type: LayoutType


class SlideBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    status: BlockStatus
    revision: int = Field(ge=0)


class SlideBlocks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: SlideBlock
    body: SlideBlock
    source_label: SlideBlock


class ProjectSlide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: SlideStatus
    revision: int = Field(ge=0)
    blocks: SlideBlocks


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    language: Literal["en"]
    phase: ProjectPhase
    revision: int = Field(ge=0)
    assignment_text: str
    context_pack_text: str
    source_document_id: str | None
    theme: Theme
    outline: list[OutlineItem]
    slides: list[ProjectSlide]
