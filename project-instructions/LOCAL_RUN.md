# Local MVP development run

Checked on 2026-09-29 in an isolated working copy on branch `mvp/M04-progressive-build`.
No model API key was supplied.

## Start locally

From the repository root:

1. `npm ci`
2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Start the API with `DATABASE_URL=sqlite:////tmp/slidecraft-mvp-local.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. In another terminal, run `npm run dev -- --host 127.0.0.1`.
5. Open `http://127.0.0.1:8080/projects/new`.

The Vite development server proxies API routes to port 8000 while preserving the browser's `/auth` and `/generate` pages. The SQLite file is a disposable local database; no production database or model key is needed for the checks below.

## Verified

- Frontend production build succeeds with `npm run build`.
- `GET /health` returns `{"ok":true}`.
- `GET /projects/demo-project` returns the checked-in five-item fixture and passes Python Pydantic validation.
- Browser landing page and login screen render.
- The new-project screen copies the Context Pack instruction, accepts separate assignment and Context Pack text, uploads and indexes one synthetic PDF, stores a chosen theme, and opens the saved project. The assignment, Context Pack, PDF filename, and theme remain visible after refresh.
- The saved project now creates a five-slide key-free starter outline. The editor changes titles and key messages, moves slides, and lets the student select page-numbered excerpts from the uploaded PDF. Browser checks confirmed title/order/source edits persist after refresh. A stale revision returns 409 with the latest project; a fabricated PDF reference returns 422. Approval stores the confirmed theme and order.
- Browser E2E: approved the saved outline, built five slides without API keys, edited the first slide title/body, edited the comparison slide's second point, refreshed, and saw the edits persist. The PDF page label stayed on slide 2. The PPTX download fired in the browser and returned HTTP 200.
- Opened the exported PPTX programmatically and rendered all five slides through LibreOffice for visual inspection. It has the saved order, edited text, page label, dark theme, and native editable title/body text boxes. The two-panel comparison has no overflow in the five-slide demo.
- Inspected the browser at desktop and 390px width. The narrow view initially clipped the slide preview and squeezed navigation labels; after adjustment, it uses a smaller preview and horizontally scrollable slide navigation without text overlap.
- `python -m unittest discover -s tests -p test_modular_project.py -v` covers per-slide persistence while later slides are queued, concurrent edit preservation, stale revision 409, one-slide failure/retry, block reset, and PPTX export.
- Full TypeScript check succeeds with `./node_modules/.bin/tsc --noEmit -p tsconfig.app.json`.
- Existing `POST /generate` accepts a synthetic request and `GET /status/{id}` reaches `done`, but this is **not real generation without a model key**. The resulting PPTX contains one placeholder slide. Do not show this as a successful five-slide demo.

## Known limitations

- M02 provides persisted `POST /projects` and `GET /projects/{id}`. The `demo-project` fixture remains read-only. The outline draft is a template, not AI-generated content; model-based outline generation is still future work.
- PDF upload uses deterministic local lexical vectors when no OpenAI key is configured. They support basic source lookup for the course demo; switching embedding providers requires re-uploading the PDF.
- The existing one-shot flow reports `done` with a placeholder PPTX when model generation fails. Treat the output as a fallback and make this state clear before using the flow in a demo.
- The modular slides are drafts copied from the approved outline. The local path does not write new slide content with an LLM or regenerate with a model; users must review text and sources before presenting. The `reset-from-outline` action restores one block locally.
