# T29 — Independent sections and automatic rendered quality review
Status: implemented and verified
Owner: Codex
Branch: mvp/T29-structured-quality

## User scope
First draft stays quick and observable. Final design preserves independently meaningful sections/data and may take longer for presentation quality. Keep quality problems internal and automatically feed them to AI. Add a shimmer overlay to the thumbnail actively being generated or improved.

## Implementation
- Typed ordered sections (1–4 stable id/heading/text), exact accepted-word partition on AI grouping. New live drafts include sections in the same content response. Legacy projects have explicit grouping/review action.
- Atomic section editing with revision guards, click-to-field navigation and editable native slide text; section text mirrors the legacy body without losing bindings.
- Final compose → render → check → refine pipeline with a maximum three reviews/two model refinements per slide. Detailed measured/model findings are stored internally and passed to the next design call. Progress/candidate visible; unresolved results cannot become ready or export.
- Mechanical fit considers both rows and columns before the vision call, preserving every section and accepted visual. Longer sections receive more room. Process diagrams use connected panels above supporting sections. Shared scene drives browser/PPTX.
- Thumbnail shimmer during body/section/final AI work, stops on completion; static tint for reduced motion. Detailed critique hidden from editor.

## Evidence
- 37 backend tests, 20 frontend tests, app TypeScript and production build passed. Stale edit rejection, bounded refinement, rejection/export guard, exact partition, section bindings, native measured clipping/small type, internal-only critique and shimmer lifecycle covered.
- Actual provider E2E legacy project 1bbef58b-5127-4e5f-8441-da7d34fa25ff: section counts 2/2/2/3/3; all five design ready, original five body strings and visual JSON exactly unchanged against before snapshot. Real vision checks initially rejected dense chart text and detached process footer. Geometry corrected; final candidates passed. No measured text clipping or body <18pt.
- New actual-provider project cd0159fe-8ab7-471d-835c-e429fe7adbc9: five live slides ready with sections directly from original content call. Subsequent whole-slide revision used for real shimmer evidence; it invalidates that slide's sections for re-review by design.
- Clicking section2 text focused the corresponding editing field. Thumbnail shimmer observed by browser computed animation and captured while real AI edit ran; disappeared after completion.
- Required captures .impeccable/review/T29/desktop.jpg (actual desktop), mobile.jpg (375x900, page width360/no horizontal page overflow), mobile-shimmer.jpg (375x900, active thumbnail visible). desktop-slide2.jpg is older diagnostic geometry, not current final evidence. native-slide-1..5.png current renderer candidates.
- Local GET export.pptx returned 44968-byte five-slide deck. Every accepted section heading and exact text present in native editable text shapes. Button invoked without UI error. Browser blob download final filesystem placement not verified; saved verified-export.pptx via same GET endpoint for content checks.
- Detector ran once: pre-existing Inter warning and existing2px bar radius advisory retained under incumbent design system. No detector rerun after latest user-requested shimmer; CSS loading gradient is purposeful activity animation.

## Limits
- Quality renderer bundles four unmodified Liberation fonts and the full OFL/copyright notice, so no Linux system-font dependency is required. It uses Liberation font equivalents for Arial/Georgia; geometry shared, pixels not identical to browser or PowerPoint. Actual browser inspected; PowerPoint visual rendering not available locally.
- Native compositions are constrained editable geometry; no arbitrary AI canvas or generated imagery. Shared theme/prompt context coordinates deck; no separate global AI art-direction call.
- Three review limit prevents unbounded paid loops. Unresolved result stays retryable without altering accepted content; does not guarantee every input becomes presentation-ready automatically.
- No env/key files read; runtime provider loads user's configured keys. No push/PR/deployment authorized in this task.

## Finish handoffs
Fresh Impeccable full review disposition fix: independent groups/theme/native graphics match and scoped academic quality ceiling reached; busy thumbnail Ready label and stale persistence docs required correction. Both scored resolved in verdict pass disposition ship. Doc handoff updated PRODUCT/DESIGN/sidecar/editor brief preserving incumbent system. Ship applies to the two scored fixes; PowerPoint application rendering remains unverified.
