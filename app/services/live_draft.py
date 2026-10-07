"""Visible content draft: real provider deltas, durable blocks, guarded edits."""
from copy import deepcopy
import logging
import re
import time

from app import repository
from app.db import SessionLocal
from app.project_schemas import OutlineItem, SourceRef
from app.services.modular_build import _mutate, build_slide_from_outline
from app.services.outline_service import starter_outline
from app.services.project_outline_llm import generate_model_outline
from app.services.modular_slide_llm import generate_slide_body

from app.services.presentation_workflow import operation, set_stage, BudgetExhausted

logger = logging.getLogger(__name__)


def suggest_sources(item, candidates):
    words = set(re.findall(r"[a-z]{4,}", item.title.lower() + " " + item.key_message.lower()))
    scored = [(len(words & set(re.findall(r"[a-z]{4,}", ref.excerpt.lower()))), ref) for ref in candidates]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [scored[0][1]] if scored and scored[0][0] >= 2 else []


def write_body(project_id, slide_id, token, text, status, visual=None, sections=None, speaker_notes=""):
    def change(project):
        slides = deepcopy(project.slides_json)
        target = next((row for row in slides if row['id'] == slide_id), None)
        if not target or target['blocks']['body']['revision'] != token or target['blocks']['body']['status'] != 'generating':
            return None
        block = target['blocks']['body']
        block.update(text=text, status=status, error='Generation failed. Retry this slide.' if status == 'error' else None)
        if status != 'generating':
            block['revision'] += 1
            target['status'] = status
            if status == 'ready':
                target['speaker_notes'] = speaker_notes
                target['visual'] = visual.model_dump() if visual else None
                target['sections'] = [s.model_dump() for s in sections] if sections else []
                target['sections_status'] = 'ready' if sections else 'none'
        target['revision'] += 1
        return {'slides_json': slides}
    return _mutate(project_id, change)


def run_live_draft(project_id, only_slide_id=None):
    try:
        with SessionLocal() as session:
            project = repository.get_project(session, project_id)
            if not project or project.phase != 'drafting':
                return
            if not only_slide_id:
                source = repository.get_document(session, project.source_document_id) if project.source_document_id else None
                candidates = [SourceRef(document_id=source.id, filename=source.filename, page_number=c.page_number, excerpt=c.chunk_text[:600])
                              for c in repository.list_document_chunks(session, source.id) if c.page_number is not None][:30] if source else []
                set_stage(project_id, 'planning')
                with operation(project_id, 'plan_deck', model=project.build_mode=='model'):
                    outline = generate_model_outline(project.assignment_text, project.context_pack_text, candidates) if project.build_mode == 'model' else starter_outline(project.context_pack_text)
                if len(outline)!=5: raise ValueError('Outline must contain all five slides')
                slides = []
                for item in outline:
                    item.suggested_refs = suggest_sources(item, candidates)
                    slide = build_slide_from_outline(item)
                    slide.status = 'queued'
                    slide.blocks.body.text = ''
                    slide.blocks.body.status = 'generating'
                    if item.suggested_refs:
                        ref = item.suggested_refs[0]
                        slide.blocks.source_label.text = f'Suggested: {ref.filename}, p. {ref.page_number}'
                    slides.append(slide.model_dump())
                _mutate(project_id, lambda latest: {'outline_json': [i.model_dump() for i in outline], 'slides_json': slides} if latest.phase == 'drafting' else None)
        with SessionLocal() as session:
            project = repository.get_project(session, project_id)
            outline = [OutlineItem.model_validate(raw) for raw in project.outline_json]
        set_stage(project_id, 'content')
        for item in outline:
            if only_slide_id and item.id != only_slide_id:
                continue
            def begin(latest):
                slides = deepcopy(latest.slides_json)
                target = next(row for row in slides if row['id'] == item.id)
                if target['status'] not in {'queued', 'error'}:
                    return None
                target['status'] = 'generating'
                target['blocks']['body'].update(status='generating', revision=target['blocks']['body']['revision'] + 1, error=None)
                return {'slides_json': slides}
            if not _mutate(project_id, begin):
                continue
            with SessionLocal() as session:
                project = repository.get_project(session, project_id)
                target = next(row for row in project.slides_json if row['id'] == item.id)
                token = target['blocks']['body']['revision']
                previous = target['blocks']['body']['text']
            last_save = 0.0
            def partial(text):
                nonlocal last_save
                now = time.monotonic()
                if text and now - last_save >= .15:
                    write_body(project_id, item.id, token, text[:500], 'generating')
                    last_save = now
            try:
                # Suggestions are possible evidence, never confirmed citations.
                prompt_item = item.model_copy(update={'evidence_refs': item.evidence_refs or item.suggested_refs})
                from app.services.draft_visual import validated_visual
                proposed_visual = []
                proposed_sections = []
                proposed_notes = []
                with operation(project_id, 'write_content', item.id, model=project.build_mode=='model'):
                    body = generate_slide_body(project, prompt_item, on_partial=partial, on_visual=lambda raw: proposed_visual.append(validated_visual(raw, item)), on_sections=proposed_sections.append, on_notes=proposed_notes.append) if project.build_mode == 'model' else item.key_message
                from app.services.draft_sections import draft_sections
                sections = draft_sections(proposed_sections[0],body,item.id,item.title,comparison=item.layout_type == "comparison") if proposed_sections else None
                committed=write_body(project_id, item.id, token, body, 'ready', visual=proposed_visual[0] if proposed_visual else None, sections=sections, speaker_notes=proposed_notes[0] if proposed_notes else f"Explain the message: {item.key_message}. Connect it to the presentation argument without adding unsupported claims.")
                if committed:
                    from app.services.composition_choices import ensure_composition_variants
                    ensure_composition_variants(project_id,item.id)
            except BudgetExhausted:
                write_body(project_id,item.id,token,previous,'error')
                def stop(latest):
                    rows=deepcopy(latest.slides_json)
                    for row in rows:
                        if row['status']=='queued':
                            row['status']='error'; row['blocks']['body'].update(status='error',error='Request budget reached. Saved results are kept.')
                    return {'slides_json':rows,'phase':'outline_draft'}
                _mutate(project_id,stop);set_stage(project_id,'budget_exhausted');return
            except Exception:
                logger.exception('live.draft.slide.failed project=%s slide=%s', project_id, item.id)
                write_body(project_id, item.id, token, previous, 'error')
        _mutate(project_id, lambda latest: {'phase': 'outline_draft'} if latest.phase=='drafting' else None)
        set_stage(project_id,'review',expected_phase='outline_draft')
    except Exception as exc:
        set_stage(project_id,'budget_exhausted' if isinstance(exc,BudgetExhausted) else 'error')
        logger.exception('live.draft.outline.failed project=%s', project_id)
        _mutate(project_id, lambda latest: {'phase': 'error'} if not latest.outline_json else {'phase': 'outline_draft'})
