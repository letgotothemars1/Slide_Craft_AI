# T24 — Canvas selection and roomy inspector
Status: implemented and verified
Owner: frontend
Dependencies: T22 live draft editor
User request: click slide elements to edit or focus the corresponding field; move earlier/later controls into the left thumbnail rail as hover arrows; give body and suggested PDF excerpts more space.

Implementation: central title, body, each comparison column and source label activate the corresponding inspector field by click or Enter/Space. Thumbnail previews stay non-interactive inside their selection buttons. Block editors remain mounted when inspector tabs change, preserving unsaved wording. Reorder arrows operate on their own thumbnail, show on hover/focus and remain visible for touch input; existing outline-draft phase restriction is retained. Inspector is 340px on desktop, body is 12 rows (258px measured), comparison fields are stacked with six rows each, suggested excerpts have up to 320px for reading. Long cover text uses more of the available canvas height.

Evidence (2026-10-01): 3 new behavior tests, 10 frontend tests total pass; TypeScript check and production build pass. Browser checks on synthetic ready/draft projects verified title/body/source field focus, unsaved body retention, keyboard activation of second comparison column, reorder of a non-selected slide and restoration of original order. Desktop and 375px mobile inspected; mobile field focus works and document has no horizontal overflow. On tested long cover body scrollHeight equals clientHeight (160px). Screenshots: /tmp/slidecraft-canvas-editing.jpg and /tmp/slidecraft-canvas-mobile.jpg. Detector findings concerned incumbent Inter and legacy preview font sizes; new arrow radius uses shared token. No API or key files were read or changed; no model calls were needed.
