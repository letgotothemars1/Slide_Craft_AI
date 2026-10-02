# SlideCraft AI
<!-- impeccable:product-schema 1 -->
## Platform
web
## Users
Master’s students preparing academic presentations from an assignment, an existing AI discussion, and one PDF.
## Product purpose
Review visible, editable content while generation proceeds; approve the draft before a second AI pass designs final slides for editable PowerPoint.
## Confirmed constraints
Five English slides, one shared PDF, three themes, native text and shapes. Source suggestions require human checking. Local secrets must never be read or committed. Existing one-shot generation stays available.
## Approved workflow
Materials → quick live grayscale draft → review and save independent sections (organize older slide text if needed) → Approve & style → choose one of three themes → Generate final slides with AI → review designed slides → Download PowerPoint. Keep slide thumbnails, the central artifact canvas, and a separate inspector.

The second AI pass designs the accepted content one slide at a time. Whole native candidates become visible per slide while AI checks and improves them; a slide becomes ready after its rendered quality review passes. This final stage may take longer than the first draft. The pass preserves accepted title, body, and source text and uses six bounded composition families: hero, editorial, chart, process, comparison, and statement. The reviewed family constrains the final pass: covers stay hero, comparisons stay comparison, existing bars/process panels stay chart/process with their exact accepted labels, values, and units; ordinary text stays editorial or statement. The selected theme background stays consistent across the deck; AI cannot invert it. Completed designs and accepted text survive a failure; retry only the affected slide. Saved title/body or section edits invalidate that slide’s design and require an update before exporting a designed deck.

New AI drafts include one to four ordered sections with stable ids, headings, and their own text/data in the same content call. Older slides offer Organize slide sections and a selected-slide grouping action. Grouping partitions the accepted body without adding, dropping, or reordering words; review its headings and grouping before design. Each section can be edited independently, and clicking its slide text opens the corresponding inspector field. Section edits save together with revision checks and keep the legacy body in sync. Whole-body AI revision clears previous section bindings for renewed review.

Final design composes a candidate, renders a PNG from the shared native scene, checks text fit and readable sizes, and sends that image to the configured vision model for critique. Measured and model findings feed up to two automatic refinements, with at most three reviews per slide. The editor shows progress and the candidate; detailed findings stay internal. An unresolved or failed review remains retryable and cannot become ready or export. The active thumbnail shows a shimmer and a local Writing, Organizing, Revising, or Designing label; reduced motion uses a static tint.

The browser preview and editable PowerPoint use the same text-and-rectangle scene geometry. Chart values must occur in both the accepted body and supplied PDF excerpts. This checks provenance, not factual accuracy, unit/category meaning, or whether a suggested excerpt supports the claim; users still check sources.

## Intake continuity
Inputs are saved automatically in browser localStorage, including theme and an already-uploaded PDF reference. Choose AI or key-free generation on the intake form; creation and draft start happen before opening the editor. Start from scratch clears saved assignment/context, restores the default theme, removes the PDF reference, and clears the cached project used for retries. Reload remains blank when browser storage is available; previously created projects are retained.

## Current design limits
Existing saved designs are normalized to the reviewed structure and consistent theme for preview and PowerPoint without another normalization model call. Independent sections and automatic rendered review/refinement are implemented. Native compositions remain bounded text/shape geometry; arbitrary AI canvas composition and generated imagery remain future possibilities. Deck coordination uses the shared palette and prompt context, without a separate global AI art-direction call. The three-review limit can leave difficult input unresolved for retry and does not guarantee every input becomes presentation-ready. The quality renderer uses bundled Liberation equivalents for Arial/Georgia, so its pixels and text metrics are not identical to browser or PowerPoint; actual PowerPoint visual rendering remains unverified.
