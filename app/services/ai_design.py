"""A separate AI art-direction pass over accepted content, one slide at a time."""
from copy import deepcopy
import json
import logging
import re
from app import repository
from app.db import SessionLocal
from app.project_schemas import DesignPlan, OutlineItem, DraftVisual
from app.services.design_constraints import allowed_layouts, preserve_reviewed_structure
from app.services.modular_build import _mutate
from app.services.draft_visual import VISUAL_SCHEMA, validated_visual
from app.services.composition_catalog import COMPOSITION_CATALOG
from app.services.llm_service import get_llm_service, OpenAILLMService, AnthropicLLMService
from app.services.quality_model_options import quality_model_options

logger=logging.getLogger(__name__)
class StaleDesignReview(ValueError):
    """The reviewed content no longer belongs to the active design snapshot."""
DESIGN_SCHEMA={'type':'object','additionalProperties':False,'required':['layout','emphasis','visual','rationale','arrangement','composition','focal_section_id','title_share','support_share'],
 'properties':{'title_share':{'type':['number','null'],'minimum':.30,'maximum':.55},'support_share':{'type':['number','null'],'minimum':.35,'maximum':.70},'layout':{'type':'string','enum':['hero','editorial','chart','process','comparison','statement']},
 'composition':{'type':'string','enum':['balanced','feature','bands','poster']},'focal_section_id':{'type':'string','maxLength':80},'arrangement':{'type':'string','enum':['columns','rows']},'emphasis':{'type':'string','enum':['quiet','accent','inverse']}, 'visual':VISUAL_SCHEMA,'rationale':{'type':'string','maxLength':300}}}


def generate_design(project,item,slide,previous,feedback=None):
    system=('You are an art director for contemporary academic presentations. Design ONE 16:9 slide from ACCEPTED content. '
      'Preserve all supplied title/body text: it is rendered separately and must not be rewritten. Choose a composition based on the information: '
      'hero for an opening, editorial for an argument with supporting text, chart for evidenced quantitative comparison, process for a sequence, '
      'comparison for exactly two body points separated by |, statement for a measured conclusion. '
      'Use a strong typographic hierarchy, deliberate whitespace, and varied compositions across the deck. '
      'When current_design is supplied, improve that selected variant; keep its composition family and focal section. '
      'Adapt title_share (0.30–0.55 poster title width) and support_share (0.35–0.70 feature support width) to text demand, or null for automatic geometry. '
      'When accepted visual is none, do not claim a chart, bars, graph or diagram in the rationale; improve native text hierarchy and numeric callouts. '
      'Visuals must explain the accepted content. Do not add new numbers, claims, or unrelated decorative charts. '
      'For bars copy values and units from accepted body AND PDF evidence, use meaningful labels. '
      'For process use 2–4 short labels grounded in the accepted body, with empty values and unit. '
      'For no visual return kind none, empty labels/values/unit. chart requires bars; process requires process. '
      'emphasis quiet keeps the theme surface, accent creates focal hierarchy, inverse reverses the theme foreground/background. '
      'Keep chart category labels under 18 characters and process labels under 45 characters and rationale under 250 characters. Use the supplied theme consistently. Return requested JSON only.')
    accepted_visual=DraftVisual.model_validate(slide['visual']) if slide.get('visual') else None
    refs=item.evidence_refs or item.suggested_refs
    user=json.dumps({'theme':project.theme,'slide_order':item.order,'purpose':item.purpose,
      'speaker_notes':slide.get('speaker_notes',''),'story_analysis':(project.workflow_json or {}).get('story_analysis'),'composition_preference':slide.get('composition_preference'),'reviewed_sections':slide.get('sections',[]),'reviewed_layout':item.layout_type,'reviewed_visual':slide.get('visual'),'accepted_title':slide['blocks']['title']['text'],'accepted_body':slide['blocks']['body']['text'],
      'evidence':[ref.model_dump() for ref in refs], 'previous_designs':previous,
      'deck_design':(project.workflow_json or {}).get('deck_design'),
      'composition_catalog':COMPOSITION_CATALOG,
      'deck':[{'order':r['order'],'title':r['title'],'key_message':r['key_message']} for r in project.outline_json]},ensure_ascii=False)
    accepted_numbers={float(n) for n in re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])',slide['blocks']['body']['text'])}
    schema=deepcopy(DESIGN_SCHEMA)
    schema['properties']['layout']['enum']=allowed_layouts(item.layout_type,accepted_visual)
    schema['properties']['emphasis']['enum']=['quiet','accent']
    selected_plan=feedback.get('current_design') if slide.get('selected_variant_id') and feedback else None
    if slide.get('composition_preference'):schema['properties']['composition']['enum']=[slide['composition_preference']]
    elif selected_plan:
        schema['properties']['composition']['enum']=[selected_plan['composition']]
    if selected_plan:
        schema['properties']['focal_section_id']['enum']=[selected_plan.get('focal_section_id','')]
        system += ' Retain the selected variant composition and exact focal section; improve fit, proportions and hierarchy without changing which argument leads.'
    schema['properties']['visual']['properties']['kind']['enum']=[accepted_visual.kind if accepted_visual else 'none']
    system += ' Preserve the reviewed structure and any existing visual exactly (labels, values, units). Do not introduce or remove visuals. Keep the selected theme background on every slide; never invert it.'
    user += '\nAllowed numeric values on this slide: '+str(sorted(accepted_numbers))+'. If this list has fewer than two values, choose a text or process composition, never a chart.'
    if feedback: user += '\nRENDERED REVIEW FEEDBACK: '+json.dumps(feedback)
    system += ' Choose rows for longer section text and columns for short independent sections. Preserve every section heading/text and binding; never merge sections. Final design needs readable presentation typography, not tiny text. The deck uses a consistent restrained academic visual system.'
    service=get_llm_service()
    if isinstance(service,OpenAILLMService):
        response=service.client.responses.create(model=service.model,**quality_model_options(service.model,.3),input=[{'role':'system','content':system},{'role':'user','content':user}],
            text={'format':{'type':'json_schema','name':'slide_art_direction','strict':True,'schema':schema}})
        from app.services.presentation_workflow import record_usage
        record_usage(response)
        raw=service._extract_output_text(response)
    elif isinstance(service,AnthropicLLMService):
        response=service.client.messages.create(model=service.model,max_tokens=1000,system=system,messages=[{'role':'user','content':user}],
            output_config={'format':{'type':'json_schema','schema':schema}})
        from app.services.presentation_workflow import record_usage
        record_usage(response)
        if response.stop_reason in {'max_tokens','refusal'}: raise ValueError('Incomplete design')
        raw=next((b.text for b in response.content if b.type=='text'),'')
    else: raise ValueError('Unsupported provider')
    data=json.loads(raw)
    if accepted_visual: data['visual']=accepted_visual.model_dump()
    plan=DesignPlan.model_validate(data)
    if slide.get('composition_preference') and plan.composition!=slide['composition_preference']:raise ValueError('Refinement changes selected composition')
    if selected_plan and (plan.composition!=selected_plan['composition'] or plan.focal_section_id!=selected_plan.get('focal_section_id','')):
        raise ValueError('Refinement changes selected variant composition or focal section')
    ids={s['id'] for s in slide.get('sections',[])}
    if plan.focal_section_id and plan.focal_section_id not in ids: raise ValueError('Unknown focal section')
    if plan.composition=='feature' and ids and not plan.focal_section_id: raise ValueError('Feature requires focal section')
    if plan.visual and plan.visual.kind=='none': plan.visual=None
    if plan.visual:
        validated=validated_visual(plan.visual.model_dump(),item)
        if not validated: raise ValueError('Visual is not supported by evidence')
        if validated.kind=='bars':
            numbers={float(n) for n in re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])',slide['blocks']['body']['text'])}
            if any(value not in numbers for value in validated.values): raise ValueError('Chart changes accepted numbers')
        plan.visual=validated
    if plan.layout=='chart' and (not plan.visual or plan.visual.kind!='bars'): raise ValueError('Chart requires data')
    if plan.layout=='process' and (not plan.visual or plan.visual.kind!='process'): raise ValueError('Process requires steps')
    if plan.layout=='comparison' and '|' not in slide['blocks']['body']['text']: raise ValueError('Comparison requires two accepted points')
    return preserve_reviewed_structure(plan,item.layout_type,accepted_visual)


def initial_design(project,item,slide,previous):
    from app.services.composition_choices import variants_current
    if variants_current(slide,item):
        selected=next(v for v in slide['composition_variants'] if v['id']==slide.get('selected_variant_id','selected'))
        return DesignPlan.model_validate(selected['design'])
    from app.services.deck_design import apply_composition
    action=next(a for a in project.workflow_json['deck_design']['actions'] if a['slide_id']==item.id)
    return apply_composition(action,slide)


def ensure_deck_variants(project_id,ids):
    """Old or edited drafts get the same three-member contract before styling."""
    from app.services.composition_choices import ensure_composition_variants,variants_current
    with SessionLocal() as session:
        project=repository.get_project(session,project_id)
        if project.build_mode!='model':return
    for slide_id in ids:
        ensure_composition_variants(project_id,slide_id)
    with SessionLocal() as session:
        project=repository.get_project(session,project_id)
        for slide_id in ids:
            row=next(r for r in project.slides_json if r['id']==slide_id)
            item=next(r for r in project.outline_json if r['id']==slide_id)
            if not variants_current(row,item) or row.get('variants_origin')!='model':
                raise ValueError('Three current AI variants are required before design')
    def requeue(current):
        if current.phase!='designing':raise ValueError('Design was cancelled during variant preparation')
        rows=deepcopy(current.slides_json)
        for row in rows:
            if row['id'] in ids and row.get('design_status')=='none':row['design_status']='queued'
        return {'slides_json':rows}
    _mutate(project_id,requeue)


def run_design(project_id,only_slide_id=None):
    from app.services.presentation_workflow import operation,set_stage,BudgetExhausted,state
    from app.services.deck_design import generate_deck_design,validate_plan,design_signature,analyze_story
    from app.project_schemas import ProjectSlide
    from app.services.design_scene import build_scene
    from app.services.design_quality import render_scene, review_design
    from app.services.coherence_service import cached_coherence, review_coherence, coherence_fingerprint
    with SessionLocal() as session:
        project=repository.get_project(session,project_id)
        if not project or project.phase!='designing': return
        ids=[r['id'] for r in sorted(project.outline_json,key=lambda r:r['order']) if not only_slide_id or r['id']==only_slide_id]
    try:
        set_stage(project_id,'design_planning')
        with SessionLocal() as session:
            project=repository.get_project(session,project_id)
            # Whole-deck actions are reused for a targeted retry if still valid.
            coherence_review=cached_coherence(project)
            if not coherence_review:
                with operation(project_id,'check_slide_notes',model=project.build_mode=='model'):
                    coherence_review=review_coherence(project)
            def save_coherence(current):
                if current.phase!='designing' or coherence_fingerprint(current)!=coherence_review['fingerprint']:
                    return None
                workflow=state(current);workflow['coherence_review']=coherence_review
                if coherence_review['approved']:
                    return {'workflow_json':workflow}
                rows=deepcopy(current.slides_json)
                for row in rows:
                    if row.get('design_status')=='queued':
                        row.update(design_status='error',design_error='Slide content and speaker notes need review before design. Saved content is kept.')
                workflow['stage']='error'
                return {'workflow_json':workflow,'slides_json':rows,'phase':'outline_draft'}
            if not _mutate(project_id,save_coherence):
                raise ValueError('Content changed during slide/notes agreement check')
            if not coherence_review['approved']:
                return
            project.workflow_json={**(project.workflow_json or {}),'coherence_review':coherence_review}
            ensure_deck_variants(project_id,ids)
            session.refresh(project)
            if not cached_coherence(project):raise ValueError('Content changed after the agreement check')
            fingerprint=deepcopy((project.theme,project.outline_json,[(r['id'],r['blocks'],r.get('sections',[]),r.get('visual'),r.get('speaker_notes',''),r.get('composition_preference'),r.get('selected_variant_id'),r.get('variants_token')) for r in project.slides_json]))
            signature=design_signature(project)
            deck_plan=state(project).get('deck_design') if only_slide_id and state(project).get('deck_design_signature')==signature else None
            with operation(project_id,'inspect_deck'):
                from app.services.deck_design import inspect_deck
                inspect_deck(project)
            with operation(project_id,'inspect_compositions'):
                dict(COMPOSITION_CATALOG)
            if deck_plan:
                try: validate_plan(deck_plan,project)
                except ValueError: deck_plan=None
            story_analysis=state(project).get('story_analysis') if deck_plan else None
            if not deck_plan:
                with operation(project_id,'analyze_story',model=project.build_mode=='model'):
                    story_analysis=analyze_story(project)
                project.workflow_json={**(project.workflow_json or {}),'story_analysis':story_analysis}
                with operation(project_id,'plan_design',model=project.build_mode=='model'):
                    deck_plan=generate_deck_design(project)
        def save_plan(current):
            now=(current.theme,current.outline_json,[(r['id'],r['blocks'],r.get('sections',[]),r.get('visual'),r.get('speaker_notes',''),r.get('composition_preference'),r.get('selected_variant_id'),r.get('variants_token')) for r in current.slides_json])
            if current.phase!='designing' or now!=fingerprint:return None
            workflow=state(current);workflow.update(deck_design=deck_plan,deck_design_signature=signature,story_analysis=story_analysis,deck_review=None,stage='designing')
            return {'workflow_json':workflow}
        if not _mutate(project_id,save_plan):raise ValueError('Content changed during deck planning')
    except Exception as exc:
        def stop(current):
            if current.phase!='designing':return None
            rows=deepcopy(current.slides_json)
            for row in rows:
                if row.get('design_status')=='queued':
                    row.update(design_status='error',design_error='Design planning could not complete. Saved content is kept. Retry.')
            workflow=state(current)
            workflow['stage']='budget_exhausted' if isinstance(exc,BudgetExhausted) else 'error'
            return {'slides_json':rows,'phase':'outline_draft','workflow_json':workflow}
        _mutate(project_id,stop)
        logger.exception('design.plan.failed project=%s',project_id)
        return
    exhausted=False
    for slide_id in ids:
        def begin(current):
            rows=deepcopy(current.slides_json); target=next(r for r in rows if r['id']==slide_id)
            if current.phase!='designing' or target.get('design_status')!='queued': return None
            target.update(design_status='generating',design_stage='composing',design_error=None,quality_issues=[],quality_attempts=0,revision=target['revision']+1)
            return {'slides_json':rows}
        if not _mutate(project_id,begin): continue
        set_stage(project_id,'designing')
        with SessionLocal() as session:
            project=repository.get_project(session,project_id)
            target=deepcopy(next(r for r in project.slides_json if r['id']==slide_id))
            tokens={key:block['revision'] for key,block in target['blocks'].items()}
            sections_token=deepcopy(target.get('sections',[]))
            variant_token=target.get('selected_variant_id'); variants_token=target.get('variants_token')
            notes_token=target.get('speaker_notes','');preference_token=target.get('composition_preference');visual_token=deepcopy(target.get('visual'))
            story_context={'speaker_notes':notes_token,'title':target['blocks']['title']['text'],
                'body':target['blocks']['body']['text'],'story_analysis':state(project).get('story_analysis')}
            item=next(OutlineItem.model_validate(r) for r in project.outline_json if r['id']==slide_id)
            previous=[{'layout':r['design']['layout'],'emphasis':r['design']['emphasis']} for r in project.slides_json if r.get('design_status')=='ready' and r.get('design')]
            plan=None; issues=[]; attempts=0
            def stage(name,candidate=None,issues=None):
                def change(current):
                    rows=deepcopy(current.slides_json); row=next(r for r in rows if r['id']==slide_id)
                    if row.get('design_status')!='generating': return None
                    if any(row['blocks'][k]['revision']!=token for k,token in tokens.items()) or row.get('sections',[])!=sections_token or row.get('speaker_notes','')!=notes_token or row.get('composition_preference')!=preference_token or row.get('visual')!=visual_token or row.get('selected_variant_id')!=variant_token or row.get('variants_token')!=variants_token: return None
                    row.update(design_stage=name,quality_attempts=attempts)
                    if candidate:
                        row['design']=candidate.model_dump()
                        _sync_selected_variant(row,candidate.model_dump())
                    if issues is not None: row['quality_issues']=issues
                    return {'slides_json':rows}
                return _mutate(project_id,change)
            try:
                with operation(project_id,'apply_composition',slide_id):
                    candidate=initial_design(project,item,target,previous)
                for attempt in range(3):
                    attempts=attempt+1
                    current_slide=ProjectSlide.model_validate({**target,'design':candidate.model_dump()})
                    with operation(project_id,'render_slide',slide_id):
                        png,measured=render_scene(build_scene(current_slide,project.theme,item.order))
                    # Resolve measurable fit locally before spending a visual-review call.
                    # The content and all visual data remain identical in both candidates.
                    if measured and target.get('sections'):
                        alternate=candidate.model_copy(update={'arrangement':'rows' if candidate.arrangement=='columns' else 'columns'})
                        alternate_slide=current_slide.model_copy(update={'design':alternate})
                        alternate_png,alternate_issues=render_scene(build_scene(alternate_slide,project.theme,item.order))
                        if len(alternate_issues)<len(measured):
                            candidate,png,measured=alternate,alternate_png,alternate_issues
                    if not stage('checking',candidate): raise ValueError('Content changed during design')
                    set_stage(project_id,'checking')
                    with operation(project_id,'review_slide',slide_id,model=project.build_mode=='model'):
                        review=review_design(png,target.get('sections',[]),candidate.model_dump(),measured,context=story_context) if project.build_mode=='model' else {'approved':not measured,'issues':[],'arrangement':candidate.arrangement}
                    issues=list(dict.fromkeys(measured+review['issues']))
                    if review['approved'] and not issues and (attempt>=1 or project.build_mode!='model'):
                        plan=candidate.model_dump(); break
                    if attempt<2:
                        if not stage('refining',candidate,issues): raise ValueError('Content changed during design')
                        set_stage(project_id,'designing')
                        with operation(project_id,'refine_slide',slide_id,model=project.build_mode=='model'):
                            if project.build_mode=='model':
                                candidate=generate_design(project,item,target,previous,feedback={'issues':issues,'improvement_goals':['Strengthen the visible focal argument and information hierarchy without rewriting accepted content.'],'current_design':candidate.model_dump(),'pass':attempt+2,'selected_variant_id':variant_token,'recommended_arrangement':review['arrangement']})
                                candidate.arrangement=review['arrangement']
                            else:
                                candidate=candidate.model_copy(update={'composition':preference_token or ['bands','balanced'][attempt], 'arrangement':'rows'})
                if plan:
                    error=None
                else:
                    # Keep the best candidate rather than throwing away three
                    # model calls. An unapproved design still renders, and
                    # showing it with the open issues beats leaving the slide on
                    # a stale design — or none — behind an error message.
                    plan=candidate.model_dump()
                    error='Design needs attention after three checks. Your text and sections are preserved.'
            except BudgetExhausted:
                exhausted=True
                error='Generation request budget reached. Saved results are kept.'
            except Exception:
                logger.exception('design.failed project=%s slide=%s',project_id,slide_id)
                error='Design or visual review could not complete. Your content is kept. Retry this slide.'
        def finish(current):
            rows=deepcopy(current.slides_json); row=next(r for r in rows if r['id']==slide_id)
            if row.get('design_status')!='generating': return None
            stale=any(row['blocks'][k]['revision']!=token for k,token in tokens.items()) or row.get('sections',[])!=sections_token or row.get('speaker_notes','')!=notes_token or row.get('composition_preference')!=preference_token or row.get('visual')!=visual_token or row.get('selected_variant_id')!=variant_token or row.get('variants_token')!=variants_token
            row.update(design_status='error' if error or stale else 'ready',design_stage='complete' if not error and not stale else 'none',quality_issues=issues,quality_attempts=attempts,design_error='Content changed during design. Retry with current sections.' if stale else error,revision=row['revision']+1)
            if plan and not stale:
                row['design']=plan
                _sync_selected_variant(row,plan)
            if stale: row['design']=None
            return {'slides_json':rows}
        _mutate(project_id,finish)
        if exhausted:
            def stop_remaining(current):
                rows=deepcopy(current.slides_json)
                for row in rows:
                    if row.get('design_status')=='queued':row.update(design_status='error',design_error='Request budget reached. Saved results are kept.')
                return {'slides_json':rows}
            _mutate(project_id,stop_remaining);break
    if not exhausted:
        try:
            _complete_deck_check(project_id)
        except StaleDesignReview:
            logger.info('design.deck_review.stale project=%s',project_id)
        except BudgetExhausted:
            exhausted=True
            _mark_deck_review_error(project_id,expected_signature=signature)
        except Exception:
            logger.exception('design.deck_review.failed project=%s',project_id)
            _mark_deck_review_error(project_id,expected_signature=signature)
    _mutate(project_id,lambda current:{'phase':'ready' if all(r.get('design_status')=='ready' for r in current.slides_json) else 'outline_draft'} if current.phase=='designing' else None)

    with SessionLocal() as session:
        current=repository.get_project(session,project_id)
        final_stage="budget_exhausted" if exhausted else "complete" if current.phase=="ready" else "error"
    set_stage(project_id,final_stage,expected_phase="ready" if final_stage=="complete" else "outline_draft")


def _sync_selected_variant(row,plan):
    for variant in row.get('composition_variants',[]):
        if variant['id']==row.get('selected_variant_id'):
            variant['design']=deepcopy(plan)
            variant['description']=plan.get('rationale',variant.get('description',''))


def _mark_deck_review_error(project_id,slide_ids=None,expected_signature=None):
    def change(current):
        from app.services.deck_design import design_signature
        if current.phase!='designing' or (expected_signature and design_signature(current)!=expected_signature):return None
        rows=deepcopy(current.slides_json)
        for row in rows:
            if row.get('design_status') in {'ready','generating'} and (slide_ids is None or row['id'] in slide_ids):
                row.update(design_status='error',design_stage='none',design_error='Final presentation review needs another design pass. Accepted content is preserved.')
        return {'slides_json':rows}
    _mutate(project_id,change)

def _complete_deck_check(project_id):
    """One global critique, bounded targeted repair, then one final coherence check."""
    from app.services.presentation_workflow import operation,state,set_stage
    from app.services.design_quality import render_scene,review_design,review_deck
    from app.services.design_scene import build_scene
    from app.project_schemas import ProjectSlide
    from app.services.deck_design import design_signature
    def snapshot():
        with SessionLocal() as session:
            current=repository.get_project(session,project_id)
            if current.phase!='designing' or not all(r.get('design_status')=='ready' for r in current.slides_json):return None
            return current
    current=snapshot()
    if current is None:return
    if current.build_mode!='model':return
    signature=design_signature(current)
    def render(project):
        ordered=sorted(project.outline_json,key=lambda r:r['order'])
        return [(r['id'],render_scene(build_scene(ProjectSlide.model_validate(next(s for s in project.slides_json if s['id']==r['id'])),project.theme,r['order']))[0]) for r in ordered]
    set_stage(project_id,'checking')
    with operation(project_id,'review_deck',model=True):result=review_deck(current,render(current))
    def save_review(project):
        if project.phase!='designing' or design_signature(project)!=signature:return None
        workflow=state(project);workflow['deck_review']=result
        return {'workflow_json':workflow}
    if not _mutate(project_id,save_review):raise StaleDesignReview('Content changed during final deck review')
    if result['approved']:return
    affected={r['slide_id']:r['issues'] for r in result['slides'] if r['issues']}
    for slide_id,issues in affected.items():
        target=deepcopy(next(r for r in current.slides_json if r['id']==slide_id))
        item=next(OutlineItem.model_validate(r) for r in current.outline_json if r['id']==slide_id)
        def begin_repair(project):
            if project.phase!='designing' or design_signature(project)!=signature:return None
            rows=deepcopy(project.slides_json);row=next(r for r in rows if r['id']==slide_id)
            row.update(design_status='generating',design_stage='refining',revision=row['revision']+1)
            return {'slides_json':rows}
        if not _mutate(project_id,begin_repair):raise StaleDesignReview('Content changed before deck refinement')
        with operation(project_id,'refine_slide',slide_id,model=True):
            candidate=generate_design(current,item,target,[],feedback={'issues':issues,'current_design':target['design'],'whole_deck_review':True})
        png,measured=render_scene(build_scene(ProjectSlide.model_validate({**target,'design':candidate.model_dump()}),current.theme,item.order))
        with operation(project_id,'review_slide',slide_id,model=True):
            local=review_design(png,target.get('sections',[]),candidate.model_dump(),measured,context={'speaker_notes':target.get('speaker_notes',''),'story_analysis':state(current).get('story_analysis')})
        def save_repair(project):
            if project.phase!='designing' or design_signature(project)!=signature:return None
            rows=deepcopy(project.slides_json);row=next(r for r in rows if r['id']==slide_id)
            row.update(design=candidate.model_dump(),quality_attempts=row.get('quality_attempts',0)+1,quality_issues=local['issues']+measured,revision=row['revision']+1,design_stage='complete' if local['approved'] else 'none',
                design_status='ready' if local['approved'] else 'error',
                design_error=None if local['approved'] else 'Final presentation review needs another design pass. Accepted content is preserved.')
            _sync_selected_variant(row,candidate.model_dump())
            return {'slides_json':rows}
        if not _mutate(project_id,save_repair):raise StaleDesignReview('Content changed during deck refinement')
    current=snapshot()
    if current is None:return
    with operation(project_id,'review_deck',model=True):result=review_deck(current,render(current))
    if not _mutate(project_id,save_review):raise StaleDesignReview('Content changed during final deck review')
    if not result['approved']:_mark_deck_review_error(project_id,{r['slide_id'] for r in result['slides'] if r['issues']},expected_signature=signature)
