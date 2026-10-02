"""Revise one slide with student guidance; retain previous content on failure."""
from copy import deepcopy
import logging
import time

from app import repository
from app.db import SessionLocal
from app.project_schemas import OutlineItem
from app.services.modular_build import _mutate
from app.services.modular_slide_llm import generate_slide_body
from app.services.draft_visual import validated_visual

logger = logging.getLogger(__name__)


def run_slide_revision(project_id, slide_id, tokens):
    with SessionLocal() as session:
        project = repository.get_project(session, project_id)
        if not project:
            return
        saved = next((row for row in project.slides_json if row['id'] == slide_id), None)
        if not saved or not all(saved['blocks'][key]['revision'] == token and saved['blocks'][key]['status'] == 'generating' for key, token in tokens.items()):
            return
        original = deepcopy(saved)
        item = next(OutlineItem.model_validate(row) for row in project.outline_json if row['id'] == slide_id)
        prompt_item = item.model_copy(update={'evidence_refs': item.evidence_refs or item.suggested_refs})
        titles, visuals = [], []
        last_save = 0.0

        def partial(text):
            nonlocal last_save
            now = time.monotonic()
            if not text or now - last_save < .15:
                return
            last_save = now
            def update(current):
                slides = deepcopy(current.slides_json)
                target = next(row for row in slides if row['id'] == slide_id)
                block = target['blocks']['body']
                if block['revision'] != tokens['body'] or block['status'] != 'generating':
                    return None
                block['text'] = text[:500]
                target['revision'] += 1
                return {'slides_json': slides}
            _mutate(project_id, update)

        try:
            context = '\n'.join(f"{key}: {block['text']}" for key, block in saved['blocks'].items())
            body = generate_slide_body(project, prompt_item, accepted_context=context,
                                       instruction=saved['revision_instruction'], on_title=titles.append,
                                       on_partial=partial, on_visual=lambda raw: visuals.append(validated_visual(raw, item)))
            if not titles:
                raise ValueError('Missing revised title')
            result = {'title': titles[0], 'body': body}
            error = None
        except Exception:
            logger.exception('slide.revision.failed project=%s slide=%s', project_id, slide_id)
            result = {}
            error = 'Slide revision failed. Your previous content is kept. Try again.'

    def finish(current):
        slides = deepcopy(current.slides_json)
        target = next(row for row in slides if row['id'] == slide_id)
        changed = False
        for key, token in tokens.items():
            block = target['blocks'][key]
            if block['revision'] != token or block['status'] != 'generating':
                continue
            block.update(text=result.get(key, original['blocks'][key]['text']), status='error' if error else 'ready',
                         error=error, revision=token + 1)
            if not error:
                target.update(design=None,design_status='none',design_error=None,sections=[],sections_status='none',design_stage='none',quality_issues=[])
            if key == 'body' and not error:
                target['visual'] = visuals[0].model_dump() if visuals and visuals[0] else None
            changed = True
        if not changed:
            return None
        target['revision'] += 1
        return {'slides_json': slides}
    _mutate(project_id, finish)
