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

The second AI pass designs the accepted content one slide at a time. Each completed slide arrives as a whole native composition; queued and generating slides retain their content draft. The pass preserves accepted title, body, and source text and chooses from six bounded composition families: hero, editorial, chart, process, comparison, and statement. Completed designs and accepted text survive a failure; retry only the affected slide. Saved title/body edits invalidate that slide’s design and require an update before exporting a designed deck.

The browser preview and editable PowerPoint use the same text-and-rectangle scene geometry. Chart values must occur in both the accepted body and supplied PDF excerpts. This checks provenance, not factual accuracy, unit/category meaning, or whether a suggested excerpt supports the claim; users still check sources.

## Intake continuity
Inputs are saved automatically in browser localStorage, including theme and an already-uploaded PDF reference. Choose AI or key-free generation on the intake form; creation and draft start happen before opening the editor.
