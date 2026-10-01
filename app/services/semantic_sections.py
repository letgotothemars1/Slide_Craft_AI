"""Partition content into editable sections; never silently rewrite accepted text."""
from copy import deepcopy
import json
import re
from app.project_schemas import SlideSection
from app.services.llm_service import get_llm_service, OpenAILLMService, AnthropicLLMService

SECTION_SCHEMA={'type':'array','items':{'type':'object','additionalProperties':False,'required':['heading','text'],
 'properties':{'heading':{'type':'string'},'text':{'type':'string'}}}}


def validated_sections(raw, body, slide_id):
    if not raw or not 1<=len(raw)<=4: raise ValueError('Expected 1–4 sections')
    if ' | ' in body and len(raw)!=2: raise ValueError('Comparison needs exactly two sections')
    sections=[SlideSection(id=f'{slide_id}-section-{i+1}',heading=row['heading'].strip(),text=row['text'].strip()) for i,row in enumerate(raw)]
    normalize=lambda s:re.sub(r'\s+',' ',s.replace(' | ',' ').strip())
    if normalize(' '.join(s.text for s in sections))!=normalize(body):
        raise ValueError('Sections must retain every accepted word in order')
    return sections


def generate_sections(body, slide_id):
    service=get_llm_service()
    system='Partition this accepted presentation text into 1–4 meaningful sections. Copy all text exactly, in the original order, without adding, dropping or rewriting any word. Each section has a short grounded heading and its own text/data. Do not distribute a section heading separately from its data. Return JSON only.'
    schema={'type':'object','additionalProperties':False,'required':['sections'],'properties':{'sections':SECTION_SCHEMA}}
    if isinstance(service,OpenAILLMService):
        response=service.client.responses.create(model=service.model,temperature=.1,input=[{'role':'system','content':system},{'role':'user','content':body}],text={'format':{'type':'json_schema','name':'semantic_sections','strict':True,'schema':schema}})
        raw=service._extract_output_text(response)
    elif isinstance(service,AnthropicLLMService):
        response=service.client.messages.create(model=service.model,max_tokens=1600,system=system,messages=[{'role':'user','content':body}],output_config={'format':{'type':'json_schema','schema':schema}})
        if response.stop_reason in {'max_tokens','refusal'}: raise ValueError('Incomplete sections')
        raw=next((r.text for r in response.content if r.type=='text'),'')
    else: raise ValueError('Unsupported provider')
    return validated_sections(json.loads(raw)['sections'],body,slide_id)


def run_sections(project_id, slide_id, body_token):
    from app.db import SessionLocal
    from app import repository
    from app.services.modular_build import _mutate
    with SessionLocal() as session:
        project=repository.get_project(session,project_id)
        row=next(r for r in project.slides_json if r['id']==slide_id)
        try: result=[s.model_dump() for s in generate_sections(row['blocks']['body']['text'],slide_id)]; error=None
        except Exception: result=None; error='Could not group the text without changing it. Retry or keep the original text.'
    def finish(current):
        rows=deepcopy(current.slides_json); target=next(r for r in rows if r['id']==slide_id)
        if target.get('sections_status')!='generating': return None
        if target['blocks']['body']['revision']!=body_token:
            target.update(sections_status='error',sections_error='Text changed while grouping. Retry with current text.')
        elif error: target.update(sections_status='error',sections_error=error)
        else: target.update(sections=result,sections_status='ready',sections_error=None,design=None,design_status='none',design_stage='none',quality_issues=[])
        return {'slides_json':rows,'phase':'outline_draft'}
    _mutate(project_id,finish)
