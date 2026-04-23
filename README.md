# SlideCraft AI Backend (PostgreSQL + Supabase Storage + OpenAI Spec)

Backend полностью совместим с фронтом:
- `POST /generate`
- `POST /documents/upload`
- `GET /status/{job_id}`
- `GET /health`

API фронта не меняется.

## Что реализовано
- PostgreSQL для jobs/specs/artifacts
- Supabase Storage (с fallback в local storage mode)
- OpenAI Responses API для генерации structured presentation spec
- MVP RAG для режима "generate from document" (PDF -> chunks -> embeddings -> retrieval)
- Сохранение generated spec в `job_specs`
- Реальный рендер PDF/PPTX из `spec_json` (не placeholder)
- Система layout templates в рендере (`hero_minimal`, `agenda_clean`, `content_two_column`, `kpi_cards`, `timeline_process`, `infographic_visual`, `quote_focus`, `comparison_split`)
- Повторный LLM вызов не делается, если в `job_specs` уже есть валидный spec для job

## Структура
- `app/main.py` - endpoints и запуск job
- `app/config.py` - env-конфиг
- `app/db.py` - SQLAlchemy модели
- `app/repository.py` - CRUD jobs/specs/artifacts
- `app/prompts/presentation_prompt.py` - prompt builder
- `app/services/llm_service.py` - OpenAI Responses API + JSON validation
- `app/services/orchestrator.py` - orchestration pipeline (load -> spec -> render -> upload -> finalize)
- `app/services/render_service.py` - low-level PDF/PPTX рендер и naming helpers
- `app/services/generator.py` - минимальный background launcher
- `app/services/storage_service.py` - Supabase/local storage abstraction
- `app/services/document_service.py` - PDF parsing + chunking + indexing
- `app/services/embedding_service.py` - OpenAI embeddings
- `app/services/retrieval_service.py` - top-k retrieval по document chunks

## Установка
```bash
cd /Users/ilyapopov/Documents/SlideCraft-AI
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Env (`.env`) пример
```env
BASE_URL=http://localhost:8000
PORT=8000

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/slidecraft
STORAGE_PATH=storage
STORAGE_TEMP_PATH=storage_tmp

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=presentations

OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-5.4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_IMAGE_MODEL=gpt-image-1-mini
OPENAI_IMAGE_SIZE=1024x1024
OPENAI_IMAGE_QUALITY=medium
OPENAI_IMAGE_BACKGROUND=opaque

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
```

Примечания:
- Если `SUPABASE_*` не заданы, backend переходит в local storage mode и работает через `/files/...`.
- Если `OPENAI_API_KEY` не задан, генерация job завершится в `error` на шаге LLM.
- Для RAG режима (document upload + retrieval) также нужен `OPENAI_EMBEDDING_MODEL`.
- `OPENAI_IMAGE_*` переменные опциональны: если не заданы, backend продолжит работать с visual placeholders без image generation.
- Image generation включается только когда заданы одновременно `OPENAI_API_KEY` и `OPENAI_IMAGE_MODEL`.

## Запуск
```bash
uvicorn app.main:app --reload --port 8000 --log-level debug
```

## Проверка API

### 1) Health
```bash
curl -s http://localhost:8000/health
```

### 2) Загрузить PDF для RAG (опционально)
```bash
curl -s -X POST "http://localhost:8000/documents/upload" \
  -F "file=@/absolute/path/to/your_document.pdf"
```

Ответ:
```json
{ "document_id": "..." }
```

### 3) Создать задачу
```bash
curl -s -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Сделай презентацию по growth strategy для edtech",
    "audience": "executives",
    "style": "business",
    "language": "ru",
    "slides": 10,
    "format": "both",
    "document_id": null,
    "brandColor": "#2563eb",
    "logoUrl": null
  }'
```

Для режима RAG передай `document_id`:
```bash
curl -s -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Сделай презентацию по содержанию документа",
    "audience": "executives",
    "style": "business",
    "language": "ru",
    "slides": 10,
    "format": "both",
    "document_id": "<document_id_from_upload>",
    "brandColor": null,
    "logoUrl": null
  }'
```

### 4) Проверять статус
```bash
JOB_ID=<uuid>
curl -s "http://localhost:8000/status/$JOB_ID"
```

В `done`:
- `result.pptx_url` / `result.pdf_url` должны быть заполнены
- `job_specs` уже содержит structured spec из LLM
- PDF/PPTX содержат контент из `spec_json` (title, subtitle, slides, bullets/body)

## Проверка, что spec сохранился в `job_specs`

Через psql:
```bash
psql "$DATABASE_URL" -c "\
SELECT job_id, created_at, jsonb_pretty(spec_json::jsonb) \
FROM job_specs \
ORDER BY created_at DESC \
LIMIT 1;"
```

## LLM debug logs
В логах backend добавлены события:
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

Это помогает понять, где именно упал пайплайн.

## Layout fields in `slides[]`
На уровне презентации:
- `theme_variant` (`dark_tech_pitch | clean_editorial | infographic_bright | null`)

В `spec_json` каждый слайд теперь поддерживает:
- `layout_type` (`hero_minimal | agenda_clean | content_two_column | kpi_cards | timeline_process | infographic_visual | quote_focus | comparison_split | null`)
- `visual_density` (`low | medium | high | null`)
- `section`
- `key_message`
- `image_prompt`
- `chart_hint`
- `speaker_notes`

Если `theme_variant` или `layout_type`/`visual_density` не заданы, renderer использует эвристический fallback.

## Orchestrator debug logs
Для шагов orchestration добавлены debug-события:
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
- `renderer.quote_layout.used`
- `renderer.comparison_layout.used`
- `renderer.real_image.used`
- `renderer.placeholder_image.used`

## Image generation logs
- `image.request.started`
- `image.response.received`
- `image.saved`
- `image.error`

## Как работает image generation
1. Backend выбирает максимум 1–2 слайда для генерации изображений (по приоритету: `hero_minimal` -> `content_two_column` -> `comparison_split/infographic_visual`).
2. Для выбранных слайдов с `image_prompt` вызывается OpenAI image API.
3. Изображения сохраняются в storage по ключам:
   - `jobs/<job_id>/images/<slide_id>.png`
4. В `spec_json` у соответствующего слайда обновляется `image_url`.
5. Renderer:
   - если `image_url` доступен -> вставляет реальное изображение
   - если нет -> рисует placeholder visual block

Важно:
- Если image generation не настроена или любой image-step упал, пайплайн не падает целиком.
- Job доходит до `done`, а слайды рендерятся через placeholders.

## Как проверить, что рендер идёт из `spec_json`
1. Создай job и дождись `done`.
2. Проверь `job_specs`:
```bash
psql "$DATABASE_URL" -c "\
SELECT id, job_id, created_at, spec_json->>'title' AS title, jsonb_array_length(spec_json::jsonb->'slides') AS slides_count \
FROM job_specs \
ORDER BY created_at DESC \
LIMIT 1;"
```
3. Скачай `pdf_url`/`pptx_url` из `/status/{job_id}` и проверь, что заголовки/буллеты соответствуют `spec_json`.
4. Перезапусти генерацию для того же `job_id` (внутренний ретрай): в логах увидишь `orchestrator.spec.loaded source=db` без нового `llm.request.started`.
