# T30 — Observable staged presentation workflow
Status: implemented and verified
Owner: Codex
Branch: mvp/T30-presentation-composition

## Approved scope
User approved a controlled workflow with prepared actions, fast whole-deck content draft, content review, theme selection only before final design, and high-quality render/review/refine finalization. All computation is for the course homework; no billing system. Keep the existing `/generate` path. Do not read credentials or env files. Five slides remain the first-version boundary; variable slide count is deferred until this slice is verified.

## Implementation contract
- Persist observable stages/actions and bounded model request usage on the project. Report actual actions/results, not internal reasoning or elapsed-time percentages.
- Outline first reveals the whole deck; content streams with whole-deck context.
- Delayed theme choice: neutral draft independent of any legacy saved theme; reviewed text/sections/data preserved during styling.
- Global design planning selects validated actions/compositions for existing stable slide IDs. A bounded executor builds native editable scene elements and checks rendered output.
- Three checks/two refinements per slide, plus a project request budget. Stopped/interrupted results remain inspectable and retryable within the budget.
- Template draft/final design makes no model calls. Model mode uses configured providers. Prepared compositions retain shared browser/PPTX geometry.

## Verification
- Backend: 51 tests pass, including mocked real-delta generation/design, exact content preservation, invalid action validation, request-budget stop, stale results/cache invalidation and recovery.
- Frontend: 27 tests pass; TypeScript and production build pass. Existing bundle-size/Browserslist warnings remain.
- Browser E2E: synthetic demo loads, neutral intake has no theme choice, five draft slides appear, canvas click targets an editor, saved body survives reload, content approval reveals theme choice, template finalization succeeds. Export is verified separately through the API. Post-design text edit returns progress to Review, invalidates export and targeted template design retry returns to Ready with zero model calls.
- Actual configured provider E2E (synthetic data): whole-deck outline, real partial content, global design and five accepted final designs; 14 logical model calls, 19,532 returned input tokens, 1,431 output tokens. One slide received an extra refinement; all accepted blocks/sections/visuals stayed unchanged.
- Native export: both template and model PPTX have five slides, exact editable titles/sections and no flattened slide screenshots. LibreOffice opened both; all five model pages were rendered and visually inspected.
- Desktop (reported viewport 1715×1250) and mobile (390×844) inspected. Independent Impeccable review confirms incumbent layout and progress UI; final documentation/counter corrections separately scored.
- Evidence: `.impeccable/review/T30/` contains captures, recorded draft/final project responses, native export montage and verified PPTX.

## Limits
This is a controlled staged workflow with model-selected composition actions, not an unrestricted autonomous agent. No generated images, web research, billing, or exposure of internal chain of thought. PDF upload's existing embedding calls are separate from presentation generation usage.

## Manual evaluation next
Open the local demo or start a new project with your homework context. First judge the five-slide story and section content, then approve and choose the theme. Compare final slides with the approved content and open exported PowerPoint. Review whether the result is usable without substantial editing; this single synthetic E2E verifies the pipeline, not general presentation quality.

## Operational notes
The local verification API uses a separate SQLite test database and local storage. Actual usage totals require the provider to return usage. The budget bounds logical application requests; provider SDK transport retries and the existing PDF embedding calls are not separately counted. Legacy outline/build endpoints stay outside the new counters. No key/env file was read; the application loads its existing runtime configuration. Font rendering varies across browser, PNG renderer, LibreOffice and PowerPoint. The browser automation did not capture the blob download event, so saving via the browser download manager was not independently verified; the HTTP export and native file contents were verified.
