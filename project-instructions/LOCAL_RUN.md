# Local MVP development run

Checked on 2026-09-29 in an isolated working copy on branch `mvp/M07-demo`.
No model API key was supplied.

On 2026-09-30, T06 was checked separately with a locally configured provider. The local key file was not opened or committed.

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
- With a configured provider, the new **Generate AI outline** action returned five persisted, editable slides from the synthetic assignment, Context Pack, and two-page PDF. Browser refresh preserved the draft. Source references remained empty until selected by the student. A live old-flow generation returned five slides; the modular key-free flow built and exported five editable slides with page labels. Python model-outline and modular-project tests and the frontend build passed.
- Existing `POST /generate` accepts a synthetic request and `GET /status/{id}` reaches `done`, but this is **not real generation without a model key**. The resulting PPTX contains one placeholder slide. Do not show this as a successful five-slide demo.

On 2026-09-30, T11 was checked in an isolated worktree with a locally configured provider and the synthetic two-page case. The local key file was used by the application but was not opened or committed. The browser completed project intake, PDF indexing, outline approval, and model slide building. Four slides became ready while the comparison slide returned an invalid format; after the comparison schema was changed to explicit left/right points, retrying only that slide yielded 5/5 ready. Page 1 and page 2 source labels remained attached to the selected slides. Editing a ready slide title survived refresh and appeared in the exported PPTX, which contained five slides and 41 native editable text frames. Browser inspection showed the comparison points and source label. Targeted Python tests, TypeScript check, and frontend build passed.

## Known limitations

- M02 provides persisted `POST /projects` and `GET /projects/{id}`. The `demo-project` fixture remains read-only. The outline can be either a model draft or an explicitly labeled key-free template. The model draft still requires student review and manual PDF evidence selection.
- PDF upload uses deterministic local lexical vectors when no OpenAI key is configured. They support basic source lookup for the course demo; switching embedding providers requires re-uploading the PDF.
- The existing one-shot flow reports `done` with a placeholder PPTX when model generation fails. Treat the output as a fallback and make this state clear before using the flow in a demo.
- The modular slides can be model-written drafts or key-free copies of the approved outline. Users must review text and sources before presenting. Model-backed title/body regeneration is available and locks only its target; `reset-from-outline` remains a separate local reset.
- The brief delay between local slides is intentional for live demonstration of progressive persistence and editing. It is not model latency.

## Integrated model MVP — 2026-09-30

For the current test session the API is at `127.0.0.1:8001` and frontend at `127.0.0.1:8081`. For the same ports in a fresh checkout, run from its root:

```sh
DATABASE_URL=sqlite:///./storage_tmp/slidecraft-mvp-local.db CORS_ORIGINS='["http://127.0.0.1:8081","http://localhost:8081"]' .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

In a second terminal:

```sh
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 8081 --strictPort
```

Open `http://127.0.0.1:8081/projects/new`. Use one API process, without multiple workers or reload, because generation tasks run in memory. Restart recovery preserves accepted content and exposes retries for interrupted work.

The backend uses the existing ignored `.env` file, **not** frontend `.env.local`. Configure the provider using the documented settings in `app/config.py`: `LLM_PROVIDER` plus `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` as appropriate. Restart the API after changing settings. Never prefix server credentials with `VITE_`, commit them, or paste them into a test report. The agent did not open the user's key file.

Repeatable HTTP checks (server already running):

```sh
python3 scripts/smoke_modular_mvp.py --api http://127.0.0.1:8001
python3 scripts/smoke_modular_mvp.py --api http://127.0.0.1:8001 --model
```

The second command calls the configured provider and consumes generation usage. Each creates a fresh synthetic project, checks PDF pages, reordered outline, progressive build, edit during build and native PPTX text parity. Model mode additionally checks title regeneration isolation. A PPTX and JSON receipt are written under `/tmp` by default.

Verification: 14 Python tests, 3 Vitest tests, TypeScript check and production build passed. The browser model journey and HTTP model/template journeys passed. Desktop and 390px inspection passed, and all five model-exported slides were rendered and inspected without clipping. Native text editing was verified by programmatic save/reopen. A human must still edit one title and one body in PowerPoint or Impress and perform the independent N02 usability run.
