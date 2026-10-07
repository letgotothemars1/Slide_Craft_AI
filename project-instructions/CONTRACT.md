# MVP contract: frozen for M01 and M02 on 2026-09-28

The response shape is validated by the checked-in `demo-project.json` fixture in Python and TypeScript. The modular path covers intake, model or template outline generation, editing and approval, one-slide-at-a-time model or template build, block editing and regeneration, and PPTX export. Keep the old `POST /generate` and `GET /status/{job_id}` intact. The modular journey's **pages** live under `/projects` and `/projects/:projectId`. Its **API** lives under `/api/projects`.

## State model

Use persistent project data, not browser-only state. A project stores: `id`, `language` (`en` for MVP), `assignment_text`, `context_pack_text`, `source_document_id`, `theme`, `phase`, `revision`, `outline[]`, and `slides[]`. An outline item has stable `id`, `order`, `purpose`, `title`, `key_message`, `evidence_refs[]`, and `layout_type`. A slide has the same stable ID, `status`, `revision`, and editable blocks. Initial block keys: `title`, `body`, `source_label`. A source reference has `document_id`, `filename`, `page_number`, and a short excerpt. Use one database row or several tables as B prefers, but expose these fields in the API.

The project response also returns `source_filename` from the attached document, or `null`, so the saved-input screen can identify the PDF after refresh.

Allowed phases: `intake → outline_draft → outline_approved → building → ready`, plus `error`. Slide status: `queued | generating | ready | error`. Block status: `ready | generating | error`. A draft outline is black-and-white and editable; choosing a theme does not silently change its meaning. The theme must be confirmed at outline approval. Accepted edits survive later generation and export.

Every edit request carries an expected revision. If the current revision differs, return HTTP 409 and the latest object so the UI can offer refresh. A background result updates only the target slide or block and must be discarded if that block was edited since work began. Do not overwrite the whole project JSON with an old job snapshot. Revision protection matters especially when a student edits while another slide is generating.

## Amendment, 2026-10-02: API moved to `/api/projects`

The pages and the API originally shared the `/projects` prefix. In production that
is not resolvable: `GET /projects/<id>` is simultaneously a page the SPA router
owns and an endpoint the backend owns, and the reverse proxy has to pick one.
Routing the prefix to the backend made `/projects/new` answer
`{"detail":"Project not found"}`; routing it to the SPA made every API call return
`index.html`, which the client then failed to parse as JSON.

The API therefore moved to `/api/projects`. Page routes are unchanged, so the user
journey described above still holds. nginx now needs a single permanent rule for
`/api/`, instead of one entry per endpoint prefix.

Changed: `APIRouter(prefix=...)` in `app/routers/projects.py`, the `PROJECTS_API`
constant in `src/lib/project-api.ts`, and the call paths in
`scripts/smoke_modular_mvp.py`. Needs sign-off from the owner of `app/`.

## Proposed endpoints

| Endpoint | Purpose | Response the UI needs |
| --- | --- | --- |
| `POST /api/projects` | Save assignment, Context Pack, selected theme, one `source_document_id`, and five-slide intent. | `project_id`, `revision`, `phase` |
| `GET /api/projects/{id}` | Read complete project state for refresh and 2-second polling. | All project fields, outline, slide states and blocks |
| `POST /api/projects/{id}/outline/generate` | With `expected_revision` and `mode: "model"`, use one provider call to draft five items; `mode: "template"` (also the default) retains the key-free starter. | Updated project in `outline_draft` |
| `PUT /api/projects/{id}/outline` | Save text/order edits with `expected_revision`. | Updated outline and revision |
| `POST /api/projects/{id}/outline/approve` | Freeze thesis/order/theme for this build. | `outline_approved` state |
| `GET /api/projects/{id}/source-candidates` | List page-numbered PDF excerpts for manual selection. | `SourceRef[]` |
| `POST /api/projects/{id}/build` | With `expected_revision` and `mode: "model"`, generate each slide body in a separate model call; `mode: "template"` (the default) copies approved outline text. Save each slide before the next. | 202 + project state |
| `PATCH /api/projects/{id}/slides/{slide_id}/blocks/{block_key}` | Edit one ready block with `expected_revision`. | Updated block and revision |
| `POST /api/projects/{id}/slides/{slide_id}/blocks/{block_key}/regenerate` | Regenerate title/body using the configured provider. Return immediately; poll block status. | 202 + project state |
| `POST /api/projects/{id}/slides/{slide_id}/blocks/{block_key}/reset-from-outline` | Restore only a title or body from the approved outline. | Updated project and revision |
| `POST /api/projects/{id}/slides/{slide_id}/retry` | Retry one failed slide without restarting ready slides. | 202 + project state |
| `GET /api/projects/{id}/export.pptx` | Render the current accepted slide state. | PPTX download |

Reuse existing `POST /documents/upload` for the one PDF, but adjust page extraction before presenting source references. Polling is sufficient for the three-week MVP; server-sent events are an upgrade, not a gate. Use existing auth only if local demo requires it; do not redesign authentication.

The project response persists `build_mode` (`template` or `model`). A failed slide's retry uses that mode. The approved outline title and selected PDF source label remain fixed during model slide building; the model writes only the slide body. A comparison body has two explicit fields in the model response, displayed as two editable points.

Template mode copies labeled Context Pack fields into a starter outline and approved text into slides without model calls. Model outline generation drafts five items using the assignment, Context Pack and source candidates. In both modes, only manually selected PDF excerpts become `evidence_refs`; the student must check them before approval and export.

## Source rules

The assignment is a constraint, not evidence. The Context Pack is background from another chat, not evidence. Only the uploaded PDF can support a source label. Preserve PDF page numbers during extraction; a retrieved chunk should carry a page number. If no relevant excerpt is found, the slide remains editable but says `Source needed` instead of fabricating a citation. Show a compact `filename, p. N` label on the slide and in PPTX. Linking to an excerpt in the app is enough for MVP; exact APA reference formatting is a later refinement. Always allow the student to correct a source label.

## Rendering rules

Use three layouts with tested PPTX equivalents: title, content, comparison/conclusion. Reuse the current `PresentationSpec` and native PPTX renderer where feasible. The browser editor and PPTX exporter must read the same saved text and order. Images may be absent. The exported file must contain native text boxes and shapes, not screenshots of slides. A final manual check must open the PPTX and alter at least one title and one body box.

## Small example

```json
{
  "id": "project-uuid",
  "language": "en",
  "phase": "building",
  "revision": 12,
  "theme": "clean_editorial",
  "outline": [
    {"id": "s1", "order": 1, "purpose": "Set up the problem", "title": "Why waste collection needs better routing", "key_message": "Current routing wastes time", "evidence_refs": [], "layout_type": "hero_minimal"}
  ],
  "slides": [
    {"id": "s1", "status": "ready", "revision": 3, "blocks": {"title": {"text": "Why waste collection needs better routing", "status": "ready", "revision": 1}, "body": {"text": "A concise opening claim", "status": "ready", "revision": 2}, "source_label": {"text": "Source needed", "status": "ready", "revision": 1}}}
  ]
}
```

The example shows field shape, not a requirement to use those exact words or IDs. M00 should add a checked-in fixture matching the final API so both developers can work independently.

## Block regeneration

T15 marks only the requested title/body as `generating` and increments its revision before calling the model. A second request for that block returns 409. Other blocks stay editable. A manual edit or reset to the target supersedes its pending model result; the worker saves only if the target revision and status still match its start token. Failures retain previous text and return block `status: error` with a safe `error` message. Retry starts a new revision. Export waits for pending block generation; failed regeneration leaves the accepted text exportable.

## Local recovery and export constraints

Run one API process/worker for this MVP. Background tasks are in memory. Startup marks interrupted queued/generating slides retryable and interrupted block generations as errors while retaining accepted text. This recovery is not a distributed job queue and must not be used with multiple workers.

Accepted titles are limited to 200 characters, outline key messages and slide bodies to 500. Comparison edits require exactly two nonempty points separated internally by `|`. Export refuses pending slides or block generations. Browser download surfaces API errors and exports the current persisted state.

## T22 approved live draft extension
`drafting` is a new phase. POST `/draft/start` returns immediately and generates an outline then streamed bodies. GET polling exposes actual model text; unvalidated partial text is marked generating. Suggested PDF references are separate from confirmed evidence. All five ready slides can be approved directly into `ready`, applying the theme without generating again. Old outline/build routes remain supported. Draft completion and retry update target blocks with revision protection.

## T23 intake continuity
The client retains assignment, Context Pack, theme, uploaded PDF ID and filename in versioned browser storage scoped to the API origin. PDF bytes remain on the server. Intake buttons choose model or template, create the project and call `/draft/start` before navigation. Start errors remain on the form with the local draft retained; retry in the same form session reuses the created project if inputs are unchanged.

## T25 guided revision and optional source footer
User requested per-slide revision instructions and regeneration, and questioned repeating a PDF label on every slide. Slides add `revision_instruction` (default empty, max 1000) and `show_source` (default false). PATCH `/draft/slides/{id}/source-visibility` sets the footer flag with revision protection; browser and PPTX share it, retaining evidence and source labels in the inspector. POST `/draft/slides/{id}/regenerate` accepts `instruction` and expected revision, stores the instruction, locks only title/body, and streams/replaces the selected slide's title/body/visual in one provider call. Other slides and source labels are retained. Whole-slide failures retain prior accepted content; unchanged block revision tokens guard completion. The existing single-block regeneration remains available.

## T27 AI design pass
After reviewing content, POST `/design/start` with theme and expected revision runs a separate provider design call per slide. Phase `designing` exposes queued/generating/ready/error design states. Title/body/source text is preserved. Design plans select native composition families and bounded visuals; numeric charts require values in accepted text and the attached evidence. One server scene builder provides identical text/shape coordinates to preview and editable PPTX. Individual design errors can be retried via `/design/slides/{id}/retry`, preserving completed slides. Revision guards discard plans after concurrent content edits. Existing palette-only approval stays compatible; the updated UI uses the separate design endpoint.

T28 clarification: final AI design preserves reviewed layout families and exact accepted visuals (labels, values and units), as well as title/body/source. All slides retain the selected theme surface; model-selected inversion is disallowed. Existing stored design plans are normalized in responses and export to this constraint. Intake offers Start from scratch, resetting locally saved fields/theme/PDF reference without deleting created projects.

T29: slides may carry 1–4 ordered semantic sections (stable id, heading, text). Section text must partition the accepted body without altering its words. Fast model drafts return sections in the same content response; legacy slides can request AI grouping via POST /sections/prepare and review it before styling. PATCH /slides/{id}/sections updates sections with expected_revision, mirrors body and invalidates only that slide's design. Final design retains sections and data and exposes composing/checking/refining stages, bounded rendered-image critique and at most two refinements. Unresolved quality checks prevent ready/export; UI shows a concise retry state and keeps detailed critique internal. Preview and editable PPTX share section-bound scene elements.

T29 UX clarification: quality findings remain internal and are passed to the model for automatic refinement. UI shows improvement progress, current candidates and a concise retry message only. Running generation, section grouping and final improvement show a thumbnail shimmer, with reduced-motion fallback; queued/completed slides do not shimmer.

## T30 approved staged workflow
Theme selection moves from intake to the final-design transition after content review. New projects use a neutral draft regardless of internal/default or legacy theme. The initial five-slide deck is planned together and each streamed body receives deck context. Project responses add optional `workflow` for backwards compatibility: stage, request budget, reserved model-call count, observed input/output token usage, ordered safe action records and a deck-design plan. This is application activity, not raw model reasoning. Persisted defaults retain legacy projects.

Global final-design planning selects validated composition actions for all existing slide IDs. Controlled tools inspect accepted content/catalog, apply native compositions, render, review and refine. The exact content/section/visual revision snapshot guards design results. Final designs preserve accepted words, ordered semantic bindings and data. Max two refinements per slide; a project call budget also bounds retries. Template mode supports the same finalization without provider calls. The UI shows stages and recorded actions, never invented completion percentages. Five slides remain this first-version contract.

## T31 talk track and deliberate quality
Initial model content also returns speaker_notes (max 4000), kept atomically with accepted body/sections and exported as native notes alongside source metadata. PATCH notes uses expected_revision and invalidates that slide's design. Invalid grouping of fresh generated text falls back to exact complete body sections; regrouping existing approved text remains strict.
GET composition choices returns three actual native previews without model calls or mutation. PATCH selection preserves accepted content, saves composition_preference and resets final quality state. Response-only preview_design gives chosen draft geometry without claiming finished design; grayscale draft is independent of final theme.
Final design analyses the whole story with notes, compares three rendered candidates, always refines each AI slide at least once, then reviews deck coherence with bounded targeted repair. Notes-only transitions need not appear on slides. Compatible verified GPT-5.4 quality calls use high reasoning effort; first draft options stay unchanged. New workflows have a 60-request ceiling (29 base, 50 bounded worst case); stored earlier ceilings are retained. Rejection and exhaustion preserve inspectable content and never certify ready.

## T32 — Content-led AI alternatives and explicit notes agreement

This supersedes T31's prepared-choice API behavior in model mode. A slide persists exactly three `composition_variants` with IDs `selected`, `alternative`, `out_of_box`, plus `selected_variant_id`, generation status/origin/fingerprint/token/error. One model request uses accepted visible text, sections, visual data and speaker notes to propose distinct native plans. Template mode uses explicit prepared alternatives. GET compositions never calls a provider and returns only current persisted alternatives; POST compositions/generate with expected_revision reserves background work; PATCH composition-choice selects an existing variant ID with revision protection. The main response scene derives from that member, and final refinement synchronizes its plan rather than creating a fourth choice. Content fingerprints invalidate alternatives and worker tokens discard stale completions; interrupted work is retryable.

DesignPlan optionally carries bounded nullable `title_share` and `support_share` for adaptive native proportions; legacy null values retain existing geometry. Starter families remain executable tools, never authority to rewrite accepted content.

Workflow adds optional `coherence_review`. A dedicated whole-deck semantic check compares visible content and speaker notes before final design. Blocking findings prevent progression and preserve accepted text for correction; a content fingerprint guards cache and completion. Template mode explicitly has no AI agreement validation. Normal spoken elaboration/transitions need not appear on screen; critical visible claims, numbers, units and qualifiers must agree. Rendered design review remains a separate bounded step. Model approval is not factual certification.

Notes now use a readable inspector tab with an explicit edit action, independent desktop scrolling and narrow-screen placement between the slide and alternatives. Existing note revision checks and unsaved-edit guards remain.

## T33 review hardening

Selecting the current variant is idempotent after checking the expected revision. Legacy composition requests must map to one of the current alternatives in model mode. Final generation retains the selected composition and focal section through schema constraints and validation. Hiding a visual invalidates final design and coherence; model final exports require current approved notes/content coherence. Stale global design reviews cannot invalidate unchanged completed slides. Startup recovery records lost running workflow operations as errors while preserving accepted content. Browser downloads require saved body and notes, project navigation rejects stale responses, and demo inputs update atomically after upload.
