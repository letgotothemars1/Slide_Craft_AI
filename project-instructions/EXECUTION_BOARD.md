# Concrete tickets for the three-week SlideCraft MVP

Use this board as the daily work queue. A ticket is complete only when its **Check** passes in the running app or a repeatable local test. Difficulty is 1 (easy) to 5 (hard). The estimates are focused developer time, not a promise that AI will get it right on the first try. The larger module cards in `tasks/` explain product context; `CONTRACT.md` holds the proposed API. Start with T00 and freeze the contract before parallel work.

**Definition of the demo:** import assignment + Context Pack + one PDF → edit/approve five black-and-white outline slides → show real slide-by-slide build → edit one ready block while another slide builds → regenerate only that block → export a good-looking PPTX with editable text and source labels.

## Week 1: inputs and outline

| ID | Owner | Time / difficulty | Exact work | Check |
| --- | --- | --- | --- | --- |
| T00 | A + B | 0.5–1 day / 3 | Run existing frontend/backend/Postgres; try old `/generate`; record launch commands and failures in `LOCAL_RUN.md`. Freeze `CONTRACT.md`. Add one shared five-slide JSON fixture. | Both machines start app; fixture has stable slide IDs and passes Python + TypeScript validation. |
| T01 | B | 1 day / 3 | Add a persisted `Project` and `POST/GET /projects` in `app/db.py`, `app/repository.py`, `app/routers/projects.py`, `app/schemas.py`; store assignment, Context Pack, theme, source ID separately. | Create project, restart backend, GET returns exactly the saved fields. Old `/generate` still responds. |
| T02 | A | 0.5–1 day / 2 | Add typed `project-api.ts`, a `/projects/new` route, and a form with separate assignment and Context Pack fields. Use the T00 fixture until T01 is merged. | Enter two distinct texts, save, refresh; neither is lost or silently merged. |
| T03 | A | 0.5 day / 1 | Add “Copy instruction for your AI chat”; write an English instruction asking for purpose, thesis, claims, constraints, cited evidence and open questions. Add paste instructions; no account integration claim. | Button copies correct text; another person can paste a sample response into Context Pack field. |
| T04 | B | 1–1.5 days / 4 | Make PDF extraction page-aware in `document_service.py` and retrieval return filename, page number and excerpt. Add DB storage/migration or a new page-aware table; keep old retrieval compatible. | A two-page synthetic PDF yields at least one correctly numbered excerpt from each page; missing page is never invented. |
| T05 | A | 0.5 day / 2 | Connect one-PDF upload via existing `/documents/upload`; show filename, indexing/error state and block continuing if upload fails. | Valid PDF attaches; invalid/non-extractable PDF gives a readable error; project stores returned document ID. |
| T06 | B | 1 day / 4 | Add `POST /projects/{id}/outline/generate`: one model call returning exactly five stable outline items from assignment + Context Pack + source candidates. Validate response and label unsupported claims `Source needed`. | API returns five items with ID, title, purpose, key message, layout and evidence refs. No styled slide is generated yet. |
| T07 | A | 1 day / 3 | Build black-on-white outline cards with title/key message edits and up/down reorder controls. Show source label and chosen theme separately. | Swap slides 2 and 3, change slide 2 title, refresh; order and title persist through API. |
| T08 | B | 0.5–1 day / 3 | Add outline `PUT` with `expected_revision`, 409 on stale edit, and approve endpoint that saves final order + theme. | Two simulated clients edit same outline; stale save gets 409. Approved state matches last accepted edit. |
| T09 | A | 0.5 day / 2 | Add approve UI: theme confirmation, missing-source warning, approve action; disable outline edits only after approval or provide explicit reopen. | User sees and confirms theme; a changed title reaches approved project state. |

**Week 1 checkpoint:** a classmate can import material and correct a five-slide outline without help. If not, pause new features until this works.

## Week 2: progressive build and in-app editing

| ID | Owner | Time / difficulty | Exact work | Check |
| --- | --- | --- | --- | --- |
| T10 | B | 1 day / 4 | Add `POST /projects/{id}/build` and a background loop that marks slide 1 generating/ready before starting slide 2. Persist after each slide. Start with deterministic fake-model output. | Poll GET: slide 1 is ready while slide 5 is queued. Restart/refresh does not erase ready slides. |
| T11 | B | 1–1.5 days / 5 | Add one-slide LLM prompt and validation; pass approved outline, thesis, neighboring slide summaries, theme and page-aware excerpts. Use only title/content/comparison layout families. | Real provider produces five coherent slides individually; one bad response marks just that slide error and allows retry. |
| T12 | A | 1 day / 3 | Render 16:9 slide previews for the three layouts using saved project data. Poll `GET /projects/{id}` every ~2 seconds and show queued/generating/ready/error states. | Slide 1 can be read while slide 2 is generating; refresh restores same states and text. |
| T13 | B | 0.5–1 day / 4 | Implement `PATCH .../blocks/{key}` for title/body/source_label with expected revision. Update only target block, persist it, and return 409 for stale revision. | Edit one block; other blocks, slide order and source metadata stay unchanged. Stale edit cannot overwrite it. |
| T14 | A | 1 day / 3 | Add inline edit/save for title, body/bullets and source label. Show save/error/409 conflict states, retry or refresh. | Change body while a later slide generates; reload and see exact edited wording. |
| T15 | B | 1–1.5 days / 5 | Implement `POST .../blocks/{key}/regenerate`: lock target block, call model with local context, check revision before save, discard stale output, unlock on success/failure. | Regenerate title: body remains editable and unchanged. Edit title during delayed request: old model result cannot replace the newer edit. |
| T16 | A | 0.5–1 day / 3 | Add Regenerate button and block-only busy state. Keep other blocks usable; show failure/retry. | During title regeneration, body field still accepts and saves changes; no whole-slide spinner blocks editing. |

**Week 2 checkpoint:** record a short screen capture showing one ready slide edited while another builds. Freeze feature scope here. Do not add animations, image generation, extra layouts or dashboards.

## Week 3: export, reliability and teaching demo

| ID | Owner | Time / difficulty | Exact work | Check |
| --- | --- | --- | --- | --- |
| T17 | B | 1–1.5 days / 4 | Build `GET /projects/{id}/export.pptx` from the saved, accepted project state. Reuse native text boxes/shapes in `render_service.py`; include theme and source labels. Refuse export if a required slide is unfinished. | PPTX has five slides in approved order; title/body/source edits appear; text boxes can be edited in PowerPoint or Impress. |
| T18 | A | 0.5–1 day / 2 | Add export button and useful failure state; compare all five browser slides to PPTX and log wording/layout mismatches. | Download succeeds only after deck ready; no stale original text is exported. |
| T19 | A + B | 1–2 days / 5 | Run the full N01 fixture path without mocks. Fix contract mismatch, source labels, reload persistence, model errors and PPTX parity. Keep old one-shot flow available. | Fresh project completes all six demo steps without console/DB intervention. |
| T20 | A + B | 0.5–1 day / 2 | Write `DEMO.md`: exact launch steps, click sequence, fallback recording, and honest known limitations. Rehearse 3–5 minute presentation. | An uninvolved classmate follows the script and reaches editable PPTX. |

## Tasks for classmates who do not code

| ID | Owner | Time / difficulty | Exact work | Check |
| --- | --- | --- | --- | --- |
| C01 | 1 classmate | 0.5 day / 1 | Prepare one English master's assignment (audience, five-slide goal, 3 required points, one “do not change” instruction), one two-page public/synthetic PDF, and sample Context Pack. See `tasks/N01.md`. | Devs can point to one fact on each PDF page and build a coherent five-slide outline. |
| C02 | 1 classmate | 0.5 day / 1 | Make a 3–5 minute demo script and a simple “what is built / what is future” slide. | Script includes outline edit, ready slide during build, local block edit, editable PPTX. |
| C03 | 2 classmates | 1 day / 1 | Run five to eight short student tests using N01 data; do not coach during first attempt. Record success/failure for each of six demo steps and exact confusing words. See `tasks/N02.md`. | `TEST_NOTES.md` contains anonymized observations, not invented feedback. |
| C04 | 1 classmate | 0.5 day / 1 | Check five exported slides against assignment: required points, source labels, readable English and slide order. Flag claims without source support. | A one-page issue list is given to devs, ordered by impact on the demo. |

## How to hand one ticket to a new chat

Open this repository folder in the new chat and paste:

> Work on ticket **T__** in `project-instructions/EXECUTION_BOARD.md`. Read `AGENTS.md`, `project-instructions/START_HERE.md`, `project-instructions/CONTRACT.md`, the relevant module card in `project-instructions/tasks/`, and the ticket. First inspect the existing code path and say which files need changing. Then implement only this ticket, preserve `/generate`, run its Check, and report what works, what remains, and how I can reproduce it. Do not commit secrets or private student material.

For classmate tasks replace `T__` with `C__` and ask for a no-code explanation. Developers should record completed ticket ID, branch, date, and evidence in the matching module card. If a ticket needs an API change, update the contract with the other developer before coding against it.
