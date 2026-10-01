# SlideCraft AI

A service that turns a written request into a finished presentation. The user describes a topic; the system builds a structured deck and returns a ready PDF.

## What it does

- Takes a prompt plus audience, style, language and slide count
- Produces a JSON specification of the whole deck through a generative model
- Optionally reviews and repairs quality in a separate critic pass
- Renders each slide to PNG through headless Chromium (Playwright) and stitches them into a PDF
- Stores the result in cloud storage and returns a download link

## Stack

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL (Supabase)

**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui

**Generation:** the provider is switched through `LLM_PROVIDER`; the specification comes back against a strict JSON schema. Illustrations and embeddings run through a separate provider.

**Rendering:** Playwright (headless Chromium) → PNG → PIL → PDF

**Storage:** Supabase Storage, with a fallback to a local directory

## Technical notes

**Absolute pixel positioning** — every element on a slide carries exact x/y/w/h coordinates on a 1280×720 canvas. Twelve layout types (title, agenda, charts, tables, process chains, multi-column arrangements and others), each with its own set of blocks.

**Multi-stage generation** — the main model emits the specification for the whole deck, an optional critic pass clears defects (empty bullets, unsuitable layouts, overloaded slides), and the renderer assembles each slide's HTML in parallel through `ThreadPoolExecutor`.

**RAG mode** — the user uploads a PDF; the system splits it into chunks, builds embeddings and pulls the relevant context into the prompt at generation time.

## Implemented

- PostgreSQL for jobs/specs/artifacts
- Supabase Storage, with a local storage mode fallback
- Structured presentation spec generated against a strict JSON schema
- MVP RAG for "generate from document" (PDF → chunks → embeddings → retrieval)
- Generated spec persisted to `job_specs`
- Real PDF/PPTX rendering from `spec_json`, not placeholders
- Layout template system in the renderer (`hero_minimal`, `agenda_clean`, `content_two_column`, `kpi_cards`, `timeline_process`, `infographic_visual`, `comparison_split`, `chart_focus`, `data_table`, `process_flow`, `multi_column`, `section_break`)
- Generation is not re-run when `job_specs` already holds a valid spec for the job

## Recent work

- **Account page** — `/account` carries the profile with an initials avatar, editable first name, last name and username, password change, and the generation history. History moved here from its own page; `/history` redirects to the account, so existing links keep working. The header now shows an avatar leading to the account instead of a log-out button, and signing out moved inside.
- **User profile in the database** — `users` gained `username` (with a unique index), `first_name` and `last_name`. All three are optional: existing accounts stay valid and sign-in still happens by email. The columns are added by the startup migration mechanism, so no manual SQL is needed on deploy.
- **Two new endpoints** — `PATCH /auth/me` for a partial profile update (only the supplied fields are touched) and `POST /auth/change-password`. The password change verifies the current password even though the caller already holds a valid token: a stolen token should not be enough to lock the owner out.
- **Personalised greeting** — the generation page greets the user by name, falling back from first name to username to the email local part; when none of those is known, no greeting is shown at all.
- **Header width budget on phones** — when space runs short, button labels collapse into icons, then secondary links are hidden, then the wordmark drops below 420px. The 44px touch targets are never shrunk. An `xs` breakpoint was added because Tailwind has nothing between 375px and `sm`.
- **One header for the whole app** — every page used to render its own: two different heights, three different link sets, and the language switch on exactly one of them. Extracted into a shared `AppHeader`; no page carries its own `<header>` any more.
- **Bilingual interface (ru/en)** — a switch in the header, the choice persisted and seeded from the browser on first visit, and `<html lang>` kept in sync. The dictionary is typed so that a key without an English translation fails the build. Dates and relative times are formatted through `Intl` for the active language; the `ru-RU` locale used to be hardcoded in four places.
- **Reworked prompt page** — one composer instead of a long vertical form: a large input, a compact row of settings inside the card, a character counter and the submit button. The right-hand column that promised to show job status was removed; it could never fill, because submitting navigates to the job page.
- **Reworked landing page** — a centred hero with a product preview, a capability row, and cards on tinted panels. The footer with three dozen dead links to non-existent sections was removed.
- **Scroll reveal** — built on `IntersectionObserver` and CSS transitions, with no animation library: only `opacity` and `transform` animate, and all motion is disabled under the system "reduce motion" setting.
- **Accessibility** — status colour contrast fixed: the green "Done" scored 2.3:1 against a 4.5:1 minimum and was unreadable; fill and text now use separate tokens. Touch targets raised to 44px, `cursor: pointer` restored on buttons, and text links given a visible focus ring.
- **Design system** — the rules live in `design-system/slidecraft-ai/MASTER.md`: tokens, typography, spacing, components, motion, localisation, and a pre-delivery checklist.
- **`/health` monitoring** — the endpoint accepts `GET` and `HEAD`. UptimeRobot polls with `HEAD` on the free plan; the endpoint used to answer `GET` only and returned `405`, so the external monitor read the service as down. `HEAD` now returns `200` with an empty body, per the HTTP spec, which is what UptimeRobot checks.
- **JWT auth for the admin dashboards** — sign-in issues a JWT, the token is validated through `/auth/me`, the metrics endpoints (`/metrics/*`) check administrator rights, and an `AdminRoute` guard was added on the frontend.
- **Playwright rendering (HTML → PDF)** — slide rendering moved from ReportLab to headless Chromium: full CSS (flex/grid, fonts, shadows, gradients) and correct text wrapping.
- **16:9 slides** — slides moved from portrait A4 to landscape 16:9, as in PowerPoint and Google Slides; the dark theme paints the background across the whole slide.
- **Secret hygiene** — `.env.*` files, backups included, were added to `.gitignore` so real keys never reach the repository; `.env.example` stays in the repo as a template.
- **Production monitoring** — three layers: external uptime (UptimeRobot → `/health`), a server resource watchdog (Disk/RAM/CPU → Telegram), and a daily database backup check (dead man's switch → Telegram). Scripts and setup notes in [`ops/`](ops/MONITORING.md).

## Monitoring

Three independent layers watching production (`slidecraft.org`). Resource and backup alerts go to a separate admin bot on Telegram.

| Layer | What it catches | How |
|-------|-----------------|-----|
| External uptime | the whole site is down, SSL expired | UptimeRobot — HEAD `/health` every 5 min |
| Server resources | disk filling up, memory leak, CPU overload | `ops/slidecraft-watchdog.sh` (cron `*/5`) |
| Database backups | the nightly `pg_dump` stopped running or is corrupt | `ops/slidecraft-backup-check.sh` (cron `0 9`) |

Installation details, thresholds and manual checks are in [`ops/MONITORING.md`](ops/MONITORING.md).

## Layout

- `app/main.py` — endpoints and job launch
- `app/config.py` — env configuration
- `app/db.py` — SQLAlchemy models
- `app/repository.py` — CRUD for jobs/specs/artifacts
- `app/prompts/presentation_prompt.py` — prompt builder
- `app/services/llm_service.py` — provider call and JSON validation
- `app/services/orchestrator.py` — orchestration pipeline (load → spec → render → upload → finalize)
- `app/services/render_service.py` — low-level PDF/PPTX rendering and naming helpers
- `app/services/generator.py` — minimal background launcher
- `app/services/storage_service.py` — Supabase/local storage abstraction
- `app/services/document_service.py` — PDF parsing, chunking and indexing
- `app/services/embedding_service.py` — embedding construction
- `app/services/retrieval_service.py` — top-k retrieval over document chunks

## Install

```bash
git clone https://github.com/letgotothemars1/Slide_Craft_AI.git
cd Slide_Craft_AI
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Example `.env`

```env
BASE_URL=http://localhost:8000
PORT=8000

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/slidecraft
STORAGE_PATH=storage
STORAGE_TEMP_PATH=storage_tmp

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=presentations

OPENAI_API_KEY=<your-api-key>
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_IMAGE_MODEL=gpt-image-1-mini
OPENAI_IMAGE_SIZE=1024x1024
OPENAI_IMAGE_QUALITY=medium
OPENAI_IMAGE_BACKGROUND=opaque

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Notes:

- With no `SUPABASE_*` set, the backend falls back to local storage mode and serves files through `/files/...`.
- With no `OPENAI_API_KEY` set, a job ends in `error` at the generation step.
- RAG mode (document upload and retrieval) also needs `OPENAI_EMBEDDING_MODEL`.
- The `OPENAI_IMAGE_*` variables are optional: without them the backend keeps working and renders visual placeholders instead of generated images.
- Image generation turns on only when `OPENAI_API_KEY` **and** `OPENAI_IMAGE_MODEL` are both set.

## Run

```bash
uvicorn app.main:app --reload --port 8000 --log-level debug
```

## Checking the API

### 1) Health

```bash
curl -s http://localhost:8000/health
```

### 2) Upload a PDF for RAG (optional)

```bash
curl -s -X POST "http://localhost:8000/documents/upload" \
  -F "file=@/absolute/path/to/your_document.pdf"
```

Response:

```json
{ "document_id": "..." }
```

### 3) Create a job

```bash
curl -s -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a deck on growth strategy for edtech",
    "audience": "executives",
    "style": "business",
    "language": "en",
    "slides": 10,
    "format": "both",
    "document_id": null,
    "brandColor": "#2563eb",
    "logoUrl": null
  }'
```

For RAG mode, pass `document_id`:

```bash
curl -s -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Build a deck from the contents of the document",
    "audience": "executives",
    "style": "business",
    "language": "en",
    "slides": 10,
    "format": "both",
    "document_id": "<document_id_from_upload>",
    "brandColor": null,
    "logoUrl": null
  }'
```

### 4) Poll the status

```bash
JOB_ID=<uuid>
curl -s "http://localhost:8000/status/$JOB_ID"
```

On `done`:

- `result.pptx_url` and `result.pdf_url` are filled in
- `job_specs` already holds the structured spec from the model
- the PDF and PPTX carry content from `spec_json` (title, subtitle, slides, bullets/body)

## Checking that the spec was saved to `job_specs`

Through psql:

```bash
psql "$DATABASE_URL" -c "\
SELECT job_id, created_at, jsonb_pretty(spec_json::jsonb) \
FROM job_specs \
ORDER BY created_at DESC \
LIMIT 1;"
```

## Generation logs

The backend emits these events:

- `model.used`
- `llm.request.started`
- `llm.response.received`
- `llm.response.parsed`
- `orchestrator.spec.saved`
- `llm.error`
- `document.upload.started`
- `document.upload.completed`
- `document.parsed`
- `document.chunked`
- `document.embeddings.created`
- `retrieval.started`
- `retrieval.completed`
- `rag.enabled`
- `rag.skipped`

They make it clear where the pipeline failed.

## Layout fields in `slides[]`

At deck level:

- `theme_variant` (`dark_tech_pitch | clean_editorial | infographic_bright | null`)

Each slide in `spec_json` supports:

- `layout_type` (`hero_minimal | agenda_clean | content_two_column | kpi_cards | timeline_process | infographic_visual | comparison_split | chart_focus | data_table | process_flow | multi_column | section_break | null`)
- `visual_density` (`low | medium | high | null`)
- `section`
- `key_message`
- `image_prompt`
- `speaker_notes`

When `theme_variant`, `layout_type` or `visual_density` is missing, the renderer falls back to a heuristic.

## Orchestrator debug logs

- `orchestrator.job.loaded`
- `orchestrator.spec.generating`
- `orchestrator.spec.saved`
- `orchestrator.pdf.render.started`
- `orchestrator.pdf.render.finished`
- `orchestrator.pptx.render.started`
- `orchestrator.pptx.render.finished`
- `orchestrator.artifacts.upload.started`
- `orchestrator.artifacts.upload.finished`
- `orchestrator.job.completed`
- `orchestrator.job.failed`

## Renderer template logs

- `layout_type.selected`
- `theme_variant.selected`
- `visual_density.selected`
- `renderer.theme.applied`
- `renderer.layout.applied`
- `renderer.template.applied`
- `renderer.template.fallback_used`
- `renderer.visual_block.created`
- `renderer.comparison_layout.used`
- `renderer.real_image.used`
- `renderer.placeholder_image.used`

## Image generation logs

- `image.request.started`
- `image.response.received`
- `image.saved`
- `image.error`

## How image generation works

1. The backend picks a small number of slides for image generation, prioritising `hero_minimal` → `content_two_column` → `comparison_split`/`infographic_visual`. The budget depends on the deck's `image_density`.
2. For the selected slides with an `image_prompt`, the image generation API is called.
3. Images are stored under `jobs/<job_id>/images/<slide_id>.png`.
4. `image_url` is updated on the corresponding slide in `spec_json`.
5. The renderer inserts the real image when `image_url` is available, and draws a placeholder visual block otherwise.

Worth knowing:

- If image generation is not configured, or any image step fails, the pipeline does not fail as a whole.
- The job still reaches `done`, and those slides render with placeholders.

## Confirming the render comes from `spec_json`

1. Create a job and wait for `done`.
2. Check `job_specs`:

```bash
psql "$DATABASE_URL" -c "\
SELECT id, job_id, created_at, spec_json->>'title' AS title, jsonb_array_length(spec_json::jsonb->'slides') AS slides_count \
FROM job_specs \
ORDER BY created_at DESC \
LIMIT 1;"
```

3. Download `pdf_url`/`pptx_url` from `/status/{job_id}` and confirm the titles and bullets match `spec_json`.
4. Re-run generation for the same `job_id` (internal retry): the logs show `orchestrator.spec.loaded source=db` with no new `llm.request.started`.
