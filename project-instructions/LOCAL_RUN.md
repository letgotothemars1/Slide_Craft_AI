# Local MVP development run

Checked on 2026-09-29 in an isolated working copy on branch `mvp/M07-demo`.
No model API key was supplied.

## Start locally

From the repository root:

1. `npm ci`
2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Start the API with `DATABASE_URL=sqlite:///./storage_tmp/slidecraft-mvp-local.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. In another terminal, run `npm run dev -- --host 127.0.0.1`.
5. Open `http://127.0.0.1:8080/projects/new`.

The Vite development server proxies API routes to port 8000 while preserving the browser's `/auth` and `/generate` pages. The SQLite file is ignored by Git and persists across local server restarts; no production database or model key is needed for the checks below.

## Verified

- Frontend production build succeeds with `npm run build`.
- `GET /health` returns `{"ok":true}`.
- `GET /projects/demo-project` returns the checked-in five-item fixture and passes Python Pydantic validation.
- Browser landing page and login screen render.
- The new-project screen copies the Context Pack instruction, accepts separate assignment and Context Pack text, uploads and indexes one synthetic PDF, stores a chosen theme, and opens the saved project. The assignment, Context Pack, PDF filename, and theme remain visible after refresh.
- The saved project now creates a five-slide key-free starter outline. The editor changes titles and key messages, moves slides, and lets the student select page-numbered excerpts from the uploaded PDF. Browser checks confirmed title/order/source edits persist after refresh. A stale revision returns 409 with the latest project; a fabricated PDF reference returns 422. Approval stores the confirmed theme and order.
- Browser E2E: approved the saved outline, built five slides without API keys, edited the first slide title/body, edited the comparison slide's second point, refreshed, and saw the edits persist. The PDF page label stayed on slide 2. The PPTX download fired in the browser and returned HTTP 200.
- The M07 demo button loads a separate synthetic assignment, Context Pack, and two-page PDF into the new-project form, then uploads the PDF into the local document index. A fresh browser project used these materials, selected PDF excerpts on slides 2 and 4, reordered slides, and saw 0/5 then 3/5 then 5/5 ready. The title of the first ready slide was edited and saved. The downloaded PPTX contained all five editable slides, the revised title, and page 1 and page 2 labels.
- Opened the exported PPTX programmatically and rendered all five slides through LibreOffice for visual inspection. It has the saved order, edited text, page label, dark theme, and native editable title/body text boxes. The two-panel comparison has no overflow in the five-slide demo.
- Inspected the browser at desktop and 390px width. The narrow view initially clipped the slide preview and squeezed navigation labels; after adjustment, it uses a smaller preview and horizontally scrollable slide navigation without text overlap.
- `python -m unittest discover -s tests -p test_modular_project.py -v` covers per-slide persistence while later slides are queued, concurrent edit preservation, stale revision 409, one-slide failure/retry, block reset, and PPTX export.
- Full TypeScript check succeeds with `./node_modules/.bin/tsc --noEmit -p tsconfig.app.json`.
- Existing `POST /generate` accepts a synthetic request and `GET /status/{id}` reaches `done`, but this is **not real generation without a model key**. The resulting PPTX contains one placeholder slide. Do not show this as a successful five-slide demo.

On 2026-09-30, T11 was checked in an isolated worktree with a locally configured provider and the synthetic two-page case. The local key file was used by the application but was not opened or committed. The browser completed project intake, PDF indexing, outline approval, and model slide building. Four slides became ready while the comparison slide returned an invalid format; after the comparison schema was changed to explicit left/right points, retrying only that slide yielded 5/5 ready. Page 1 and page 2 source labels remained attached to the selected slides. Editing a ready slide title survived refresh and appeared in the exported PPTX, which contained five slides and 41 native editable text frames. Browser inspection showed the comparison points and source label. Targeted Python tests, TypeScript check, and frontend build passed.

## Known limitations

- M02 provides persisted `POST /projects` and `GET /projects/{id}`. The `demo-project` fixture remains read-only. The outline draft is a template, not AI-generated content; model-based outline generation is still future work.
- PDF upload uses deterministic local lexical vectors when no OpenAI key is configured. They support basic source lookup for the course demo; switching embedding providers requires re-uploading the PDF.
- The existing one-shot flow reports `done` with a placeholder PPTX when model generation fails. Treat the output as a fallback and make this state clear before using the flow in a demo.
- The modular slides can be model-written drafts or key-free copies of the approved outline. Users must review text and sources before presenting. Model-based regeneration of one block is still future work; `reset-from-outline` restores one block locally.
- The brief delay between local slides is intentional for live demonstration of progressive persistence and editing. It is not model latency.
