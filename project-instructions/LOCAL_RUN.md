# Local MVP development run

Checked on 2026-09-28 in an isolated working copy on branch `mvp/M00-contract`.
No model API key was supplied.

## Start locally

From the repository root:

1. `npm ci`
2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Start the API with `DATABASE_URL=sqlite:////tmp/slidecraft-mvp-local.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. In another terminal, run `npm run dev -- --host 127.0.0.1`.
5. Open `http://127.0.0.1:8080/`.

The Vite development server proxies API routes to port 8000 while preserving the browser's `/auth` and `/generate` pages. The SQLite file is a disposable local database; no production database or model key is needed for the checks below.

## Verified

- Frontend production build succeeds with `npm run build`.
- `GET /health` returns `{"ok":true}`.
- `GET /projects/demo-project` returns the checked-in five-item fixture and passes Python Pydantic validation.
- Browser landing page and login screen render.
- Existing `POST /generate` accepts a synthetic request and `GET /status/{id}` reaches `done`, but this is **not real generation without a model key**. The resulting PPTX contains one placeholder slide. Do not show this as a successful five-slide demo.

## Known limitations

- M02 now provides persisted `POST /projects` and `GET /projects/{id}`. The `demo-project` fixture remains read-only; outline editing and generation are still future work.
- PDF upload uses deterministic local lexical vectors when no OpenAI key is configured. They support basic source lookup for the course demo; switching embedding providers requires re-uploading the PDF.
- The current full TypeScript check has two pre-existing errors in `src/lib/analytics.ts` and `src/lib/api.ts`; the frontend build still succeeds.
- The existing one-shot flow reports `done` with a placeholder PPTX when model generation fails. Treat the output as a fallback and make this state clear before using the flow in a demo.
