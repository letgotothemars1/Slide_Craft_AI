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
Materials → live grayscale draft → review and save content → Approve & style → choose one of three themes → Generate final slides with AI → review designed slides → Download PowerPoint. Keep slide thumbnails, the central artifact canvas, and a separate inspector.

The second AI pass designs the accepted content one slide at a time. Each completed slide arrives as a whole native composition; queued and generating slides retain their content draft. The pass preserves accepted title, body, and source text and uses six bounded composition families: hero, editorial, chart, process, comparison, and statement. The reviewed family constrains the final pass: covers stay hero, comparisons stay comparison, existing bars/process panels stay chart/process with their exact accepted labels, values, and units; ordinary text stays editorial or statement. The selected theme background stays consistent across the deck; AI cannot invert it. Completed designs and accepted text survive a failure; retry only the affected slide. Saved title/body edits invalidate that slide’s design and require an update before exporting a designed deck.

The browser preview and editable PowerPoint use the same text-and-rectangle scene geometry. Chart values must occur in both the accepted body and supplied PDF excerpts. This checks provenance, not factual accuracy, unit/category meaning, or whether a suggested excerpt supports the claim; users still check sources.

## Intake continuity
Inputs are saved automatically in browser localStorage, including theme and an already-uploaded PDF reference. Choose AI or key-free generation on the intake form; creation and draft start happen before opening the editor. Start from scratch clears saved assignment/context, restores the default theme, removes the PDF reference, and clears the cached project used for retries. Reload remains blank when browser storage is available; previously created projects are retained.

## Current design limits
Existing saved designs are normalized to the reviewed structure and consistent theme for preview and PowerPoint without another model call. The body is still one text field; preserving an existing visual does not provide separate heading/body/data bindings for meaningful sections. A richer content model and a render, critique, and revision pipeline remain planned work; this narrow fix does not establish final presentation quality.
