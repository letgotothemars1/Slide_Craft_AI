# MVP contract: frozen for M01 and M02 on 2026-09-28

The response shape is validated by the checked-in `demo-project.json` fixture in Python and TypeScript. The intake, source-candidate, outline draft, edit, and approval endpoints now exist locally. Build, block editing, and export remain planned. Keep the old `POST /generate` and `GET /status/{job_id}` intact. The new modular journey lives under `/projects` and `/projects/:projectId`.

## State model

Use persistent project data, not browser-only state. A project stores: `id`, `language` (`en` for MVP), `assignment_text`, `context_pack_text`, `source_document_id`, `theme`, `phase`, `revision`, `outline[]`, and `slides[]`. An outline item has stable `id`, `order`, `purpose`, `title`, `key_message`, `evidence_refs[]`, and `layout_type`. A slide has the same stable ID, `status`, `revision`, and editable blocks. Initial block keys: `title`, `body`, `source_label`. A source reference has `document_id`, `filename`, `page_number`, and a short excerpt. Use one database row or several tables as B prefers, but expose these fields in the API.

The project response also returns `source_filename` from the attached document, or `null`, so the saved-input screen can identify the PDF after refresh.

Allowed phases: `intake → outline_draft → outline_approved → building → ready`, plus `error`. Slide status: `queued | generating | ready | error`. Block status: `ready | generating | error`. A draft outline is black-and-white and editable; choosing a theme does not silently change its meaning. The theme must be confirmed at outline approval. Accepted edits survive later generation and export.

Every edit request carries an expected revision. If the current revision differs, return HTTP 409 and the latest object so the UI can offer refresh. A background result updates only the target slide or block and must be discarded if that block was edited since work began. Do not overwrite the whole project JSON with an old job snapshot. Revision protection matters especially when a student edits while another slide is generating.

## Proposed endpoints

| Endpoint | Purpose | Response the UI needs |
| --- | --- | --- |
| `POST /projects` | Save assignment, Context Pack, selected theme, one `source_document_id`, and five-slide intent. | `project_id`, `revision`, `phase` |
| `GET /projects/{id}` | Read complete project state for refresh and 2-second polling. | All project fields, outline, slide states and blocks |
| `POST /projects/{id}/outline/generate` | One model call creates five outline items. | Updated project in `outline_draft` |
| `PUT /projects/{id}/outline` | Save text/order edits with `expected_revision`. | Updated outline and revision |
| `POST /projects/{id}/outline/approve` | Freeze thesis/order/theme for this build. | `outline_approved` state |
| `GET /projects/{id}/source-candidates` | List page-numbered PDF excerpts for manual selection. | `SourceRef[]` |
| `POST /projects/{id}/build` | Start a background loop: generate one slide spec, validate, save, then move to next. | 202 + project state |
| `PATCH /projects/{id}/slides/{slide_id}/blocks/{block_key}` | Edit one ready block with `expected_revision`. | Updated block and revision |
| `POST /projects/{id}/slides/{slide_id}/blocks/{block_key}/regenerate` | Rebuild only that block from approved outline, source, theme and neighboring slide context. | 202 + block `generating` |
| `GET /projects/{id}/export.pptx` | Render the current accepted slide state. | PPTX download |

Reuse existing `POST /documents/upload` for the one PDF, but adjust page extraction before presenting source references. Polling is sufficient for the three-week MVP; server-sent events are an upgrade, not a gate. Use existing auth only if local demo requires it; do not redesign authentication.

The key-free local demo uses a five-slide starter template for `/outline/generate`. It does not make an AI model call or assert that PDF excerpts support the draft's claims. The student selects source candidates manually and must check them before approval.

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
