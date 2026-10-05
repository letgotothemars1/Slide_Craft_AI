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
from app.services.llm_service import get_llm_service, OpenAILLMService, AnthropicLLMService

logger=logging.getLogger(__name__)
DESIGN_SCHEMA={'type':'object','additionalProperties':False,'required':['layout','emphasis','visual','rationale','arrangement'],
 'properties':{'layout':{'type':'string','enum':['hero','editorial','chart','process','comparison','statement']},
 'arrangement':{'type':'string','enum':['columns','rows']},'emphasis':{'type':'string','enum':['quiet','accent','inverse']}, 'visual':VISUAL_SCHEMA,'rationale':{'type':'string'}}}


def generate_design(project,item,slide,previous,feedback=None):
    system=('You are an art director for contemporary academic presentations. Design ONE 16:9 slide from ACCEPTED content. '
      'Preserve all supplied title/body text: it is rendered separately and must not be rewritten. Choose a composition based on the information: '
      'hero for an opening, editorial for an argument with supporting text, chart for evidenced quantitative comparison, process for a sequence, '
      'comparison for exactly two body points separated by |, statement for a measured conclusion. '
      'Use a strong typographic hierarchy, deliberate whitespace, and varied compositions across the deck. '
      'Visuals must explain the accepted content. Do not add new numbers, claims, or unrelated decorative charts. '
      'For bars copy values and units from accepted body AND PDF evidence, use meaningful labels. '
      'For process use 2–4 short labels grounded in the accepted body, with empty values and unit. '
      'For no visual return kind none, empty labels/values/unit. chart requires bars; process requires process. '
      'emphasis quiet keeps the theme surface, accent creates focal hierarchy, inverse reverses the theme foreground/background. '
      'Keep chart category labels under 18 characters and process labels under 45 characters and rationale under 250 characters. Use the supplied theme consistently. Return requested JSON only.')
    accepted_visual=DraftVisual.model_validate(slide['visual']) if slide.get('visual') else None
    refs=item.evidence_refs or item.suggested_refs
    user=json.dumps({'theme':project.theme,'slide_order':item.order,'purpose':item.purpose,
      'reviewed_sections':slide.get('sections',[]),'reviewed_layout':item.layout_type,'reviewed_visual':slide.get('visual'),'accepted_title':slide['blocks']['title']['text'],'accepted_body':slide['blocks']['body']['text'],
      'evidence':[ref.model_dump() for ref in refs], 'previous_designs':previous,
      'deck':[{'order':r['order'],'title':r['title']} for r in project.outline_json]},ensure_ascii=False)
    accepted_numbers={float(n) for n in re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])',slide['blocks']['body']['text'])}
    schema=deepcopy(DESIGN_SCHEMA)
    schema['properties']['layout']['enum']=allowed_layouts(item.layout_type,accepted_visual)
    schema['properties']['emphasis']['enum']=['quiet','accent']
    schema['properties']['visual']['properties']['kind']['enum']=[accepted_visual.kind if accepted_visual else 'none']
    system += ' Preserve the reviewed structure and any existing visual exactly (labels, values, units). Do not introduce or remove visuals. Keep the selected theme background on every slide; never invert it.'
    user += '\nAllowed numeric values on this slide: '+str(sorted(accepted_numbers))+'. If this list has fewer than two values, choose a text or process composition, never a chart.'
    if feedback: user += '\nRENDERED REVIEW FEEDBACK: '+json.dumps(feedback)
    system += ' Choose rows for longer section text and columns for short independent sections. Preserve every section heading/text and binding; never merge sections. Final design needs readable presentation typography, not tiny text. The deck uses a consistent restrained academic visual system.'
    service=get_llm_service()
    if isinstance(service,OpenAILLMService):
        response=service.client.responses.create(model=service.model,temperature=.3,input=[{'role':'system','content':system},{'role':'user','content':user}],
            text={'format':{'type':'json_schema','name':'slide_art_direction','strict':True,'schema':schema}})
        raw=service._extract_output_text(response)
    elif isinstance(service,AnthropicLLMService):
        response=service.client.messages.create(model=service.model,max_tokens=1000,system=system,messages=[{'role':'user','content':user}],
            output_config={'format':{'type':'json_schema','schema':schema}})
        if response.stop_reason in {'max_tokens','refusal'}: raise ValueError('Incomplete design')
        raw=next((b.text for b in response.content if b.type=='text'),'')
    else: raise ValueError('Unsupported provider')
    data=json.loads(raw)
    if accepted_visual: data['visual']=accepted_visual.model_dump()
    plan=DesignPlan.model_validate(data)
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


def run_design(project_id,only_slide_id=None):
    from app.project_schemas import ProjectSlide
    from app.services.design_scene import build_scene
    from app.services.design_quality import render_scene, review_design
    with SessionLocal() as session:
        project=repository.get_project(session,project_id)
        if not project or project.phase!='designing': return
        ids=[r['id'] for r in sorted(project.outline_json,key=lambda r:r['order']) if not only_slide_id or r['id']==only_slide_id]
    for slide_id in ids:
        def begin(current):
            rows=deepcopy(current.slides_json); target=next(r for r in rows if r['id']==slide_id)
            if current.phase!='designing' or target.get('design_status')!='queued': return None
            target.update(design_status='generating',design_stage='composing',design_error=None,quality_issues=[],quality_attempts=0,revision=target['revision']+1)
            return {'slides_json':rows}
        if not _mutate(project_id,begin): continue
        with SessionLocal() as session:
            project=repository.get_project(session,project_id)
            target=deepcopy(next(r for r in project.slides_json if r['id']==slide_id))
            tokens={key:block['revision'] for key,block in target['blocks'].items()}
            sections_token=deepcopy(target.get('sections',[]))
            item=next(OutlineItem.model_validate(r) for r in project.outline_json if r['id']==slide_id)
            previous=[{'layout':r['design']['layout'],'emphasis':r['design']['emphasis']} for r in project.slides_json if r.get('design_status')=='ready' and r.get('design')]
            plan=None; issues=[]; attempts=0
            def stage(name,candidate=None,issues=None):
                def change(current):
                    rows=deepcopy(current.slides_json); row=next(r for r in rows if r['id']==slide_id)
                    if row.get('design_status')!='generating': return None
                    if any(row['blocks'][k]['revision']!=token for k,token in tokens.items()) or row.get('sections',[])!=sections_token: return None
                    row.update(design_stage=name,quality_attempts=attempts)
                    if candidate: row['design']=candidate.model_dump()
                    if issues is not None: row['quality_issues']=issues
                    return {'slides_json':rows}
                return _mutate(project_id,change)
            try:
                candidate=generate_design(project,item,target,previous)
                for attempt in range(3):
                    attempts=attempt+1
                    current_slide=ProjectSlide.model_validate({**target,'design':candidate.model_dump()})
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
                    review=review_design(png,target.get('sections',[]),candidate.model_dump(),measured)
                    issues=list(dict.fromkeys(measured+review['issues']))
                    if review['approved'] and not issues:
                        plan=candidate.model_dump(); break
                    if attempt<2:
                        if not stage('refining',candidate,issues): raise ValueError('Content changed during design')
                        candidate=generate_design(project,item,target,previous,feedback={'issues':issues,'recommended_arrangement':review['arrangement']})
                        candidate.arrangement=review['arrangement']
                if plan:
                    error=None
                else:
                    # Keep the best candidate rather than throwing away three
                    # model calls. An unapproved design still renders, and
                    # showing it with the open issues beats leaving the slide on
                    # a stale design — or none — behind an error message.
                    plan=candidate.model_dump()
                    error='Design needs attention after three checks. Your text and sections are preserved.'
            except Exception:
                logger.exception('design.failed project=%s slide=%s',project_id,slide_id)
                error='Design or visual review could not complete. Your content is kept. Retry this slide.'
        def finish(current):
            rows=deepcopy(current.slides_json); row=next(r for r in rows if r['id']==slide_id)
            if row.get('design_status')!='generating': return None
            stale=any(row['blocks'][k]['revision']!=token for k,token in tokens.items()) or row.get('sections',[])!=sections_token
            row.update(design_status='error' if error or stale else 'ready',design_stage='complete' if not error and not stale else 'none',quality_issues=issues,quality_attempts=attempts,design_error='Content changed during design. Retry with current sections.' if stale else error,revision=row['revision']+1)
            if plan and not stale: row['design']=plan
            if stale: row['design']=None
            return {'slides_json':rows}
        _mutate(project_id,finish)
    _mutate(project_id,lambda current:{'phase':'ready' if all(r.get('design_status')=='ready' for r in current.slides_json) else 'outline_draft'} if current.phase=='designing' else None)
