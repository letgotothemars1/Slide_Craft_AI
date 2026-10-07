"""Shared response contract for the modular course MVP.

The first endpoint serves a checked-in fixture. Persistence and generation are
added by later MVP modules without changing this response shape.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProjectPhase = Literal["intake", "designing", "drafting", "outline_draft", "outline_approved", "building", "ready", "error"]
SlideStatus = Literal["queued", "generating", "ready", "error"]
BlockStatus = Literal["ready", "generating", "error"]
Theme = Literal["clean_editorial", "dark_tech_pitch", "infographic_bright"]
LayoutType = Literal["title", "content", "comparison"]
BuildMode = Literal["template", "model"]


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
    suggested_refs: list[SourceRef] = Field(default_factory=list)
    layout_type: LayoutType


class SlideBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    status: BlockStatus
    revision: int = Field(ge=0)
    error: str | None = None


class SlideBlocks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: SlideBlock
    body: SlideBlock
    source_label: SlideBlock


class DraftVisual(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["none", "process", "bars"]
    labels: list[str] = Field(max_length=4)
    values: list[float] = Field(max_length=4)
    unit: str = Field(max_length=20)


class SlideSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1,max_length=80)
    heading: str = Field(max_length=100)
    text: str = Field(min_length=1,max_length=500)


class SectionEditRequest(BaseModel):
    expected_revision: int
    sections: list[SlideSection] = Field(min_length=1,max_length=4)


class DesignPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    layout: Literal["hero", "editorial", "chart", "process", "comparison", "statement"]
    emphasis: Literal["quiet", "accent", "inverse"]
    visual: DraftVisual | None = None
    rationale: str = Field(max_length=300)
    arrangement: Literal["columns", "rows"] = "columns"
    composition: Literal["balanced", "feature", "bands", "poster"] = "balanced"
    focal_section_id: str = Field(default="", max_length=80)
    title_share: float | None = Field(default=None, ge=.30, le=.55)
    support_share: float | None = Field(default=None, ge=.35, le=.70)


class SceneElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["text", "rect"]
    x: float
    y: float
    w: float
    h: float
    text: str = ""
    color: str
    size: float = 2
    bold: bool = False
    font: Literal["Arial", "Georgia"] = "Arial"
    block_key: Literal["title", "body", "source_label"] | None = None
    column: int | None = None
    section_id: str | None = None
    section_field: Literal["heading", "text"] | None = None


class CompositionVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Literal["selected", "alternative", "out_of_box"]
    label: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    unconventional: bool = False
    design: DesignPlan


class ProjectSlide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: SlideStatus
    revision: int = Field(ge=0)
    visual: DraftVisual | None = None
    design: DesignPlan | None = None
    preview_design: DesignPlan | None = None
    design_status: Literal["none", "queued", "generating", "ready", "error"] = "none"
    design_error: str | None = None
    sections: list[SlideSection] = Field(default_factory=list,max_length=4)
    sections_status: Literal["none", "generating", "ready", "error"] = "none"
    sections_error: str | None = None
    design_stage: Literal["none", "composing", "checking", "refining", "complete"] = "none"
    quality_issues: list[str] = Field(default_factory=list)
    quality_attempts: int = 0
    scene: list[SceneElement] = Field(default_factory=list)
    show_source: bool = False
    speaker_notes: str = Field(default="", max_length=4000)
    composition_preference: Literal["balanced", "feature", "bands", "poster"] | None = None
    composition_variants: list[CompositionVariant] = Field(default_factory=list, max_length=3)
    selected_variant_id: Literal["selected", "alternative", "out_of_box"] | None = None
    variants_status: Literal["none", "generating", "ready", "error"] = "none"
    variants_fingerprint: str | None = None
    variants_token: str | None = None
    variants_error: str | None = None
    variants_origin: Literal["model", "template"] | None = None
    revision_instruction: str = Field(default="", max_length=1000)
    blocks: SlideBlocks


class WorkflowAction(BaseModel):
    sequence: int
    action: str
    status: Literal["running", "complete", "error"]
    slide_id: str | None = None
    detail: str = ""


class WorkflowState(BaseModel):
    stage: Literal["idle", "planning", "content", "review", "design_planning", "designing", "checking", "complete", "error", "budget_exhausted"] = "idle"
    model_calls: int = 0
    request_budget: int = Field(default=60, ge=1)
    input_tokens: int = 0
    output_tokens: int = 0
    actions: list[WorkflowAction] = Field(default_factory=list)
    coherence_review: dict | None = None
    story_analysis: dict | None = None
    deck_review: dict | None = None
    deck_design: dict | None = None
    deck_design_signature: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    language: Literal["en"]
    phase: ProjectPhase
    revision: int = Field(ge=0)
    assignment_text: str
    context_pack_text: str
    source_document_id: str | None
    source_filename: str | None = None
    theme: Theme
    build_mode: BuildMode = "template"
    workflow: WorkflowState = Field(default_factory=WorkflowState)
    outline: list[OutlineItem]
    slides: list[ProjectSlide]


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignment_text: str = Field(min_length=1)
    context_pack_text: str = Field(min_length=1)
    source_document_id: str | None = None
    theme: Theme = "clean_editorial"
    language: Literal["en"] = "en"


class OutlineRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)


class BuildRequest(OutlineRevisionRequest):
    mode: BuildMode = "template"


class OutlineGenerateRequest(OutlineRevisionRequest):
    mode: BuildMode = "template"


class OutlineSaveRequest(OutlineRevisionRequest):
    outline: list[OutlineItem] = Field(min_length=5, max_length=5)


class OutlineApproveRequest(OutlineRevisionRequest):
    theme: Theme


class BlockEditRequest(OutlineRevisionRequest):
    text: str = Field(min_length=1, max_length=2000)

class SpeakerNotesEditRequest(OutlineRevisionRequest):
    speaker_notes: str = Field(max_length=4000)


class CompositionRequest(OutlineRevisionRequest):
    layout_type: LayoutType

class ConfirmSourceRequest(OutlineRevisionRequest):
    source_ref: SourceRef


class SourceVisibilityRequest(OutlineRevisionRequest):
    show_source: bool


class SlideRegenerateRequest(OutlineRevisionRequest):
    instruction: str = Field(min_length=1, max_length=1000)
