"""Render the native scene, inspect measured text, then request a visual review."""
import base64
import json
import math
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.services.llm_service import get_llm_service, OpenAILLMService, AnthropicLLMService


def _font(element):
    family='LiberationSerif' if element.font=='Georgia' else 'LiberationSans'
    path=Path(__file__).resolve().parent.parent/'assets'/'quality-fonts'/f'{family}-{"Bold" if element.bold else "Regular"}.ttf'
    if not path.exists(): raise RuntimeError('The bundled slide quality fonts are missing')
    return ImageFont.truetype(str(path),max(1,round(element.size*12.8)))


def wrap_text(text,font,width):
    lines=[]
    for paragraph in text.split('\n'):
        line=''
        for word in paragraph.split(' '):
            proposal=line+' '+word if line else word
            if line and font.getlength(proposal)>width: lines.append(line); line=word
            else: line=proposal
        lines.append(line)
    return lines


def render_scene(scene):
    image=Image.new('RGB',(1280,720),'white'); draw=ImageDraw.Draw(image); issues=[]
    for element in scene:
        x,y,w,h=(v*12.8 for v in (element.x,element.y,element.w,element.h))
        if element.kind=='rect': draw.rectangle((x,y,x+w,y+h),fill=element.color); continue
        font=_font(element); lines=wrap_text(element.text,font,w); line_height=font.size*1.16
        if any(font.getlength(line)>w+2 for line in lines): issues.append(f'Text exceeds width: {element.section_id or element.block_key or element.text[:25]}')
        if len(lines)*line_height>h+2: issues.append(f'Text overflows: {element.section_id or element.block_key or element.text[:25]}')
        if element.block_key=='body' and element.size<1.875: issues.append(f'Text below 18pt: {element.section_id or "body"}')
        if element.block_key=='title' and element.size<2.5: issues.append('Title below 24pt')
        # Clip text like the preview; overflow remains an explicit issue rather than a silent success.
        layer=Image.new('RGBA',(max(1,math.ceil(w)),max(1,math.ceil(h))))
        painter=ImageDraw.Draw(layer)
        for i,line in enumerate(lines): painter.text((0,i*line_height),line,font=font,fill=element.color,anchor='lt')
        image.paste(layer,(round(x),round(y)),layer)
    data=BytesIO(); image.save(data,format='PNG'); return data.getvalue(),list(dict.fromkeys(issues))


def review_design(png,sections,plan,measured):
    service=get_llm_service(); encoded=base64.b64encode(png).decode()
    system='Review this rendered academic slide as a presentation designer. Look for text clipping, unreadably small text, weak hierarchy, poor spacing, crowded charts and fragmented or merged semantic sections. Do not request text changes: content is accepted. Be specific, restrained and honest. A clean text-led slide is valid; do not demand decorative images. Approve only if the pictured slide is usable to present. The issues list contains only defects that require a change; never include praise, neutral observations, or acceptable minor preferences. Return up to four concrete issues, an arrangement recommendation (rows/columns), and approval boolean.'
    prompt=json.dumps({'accepted_sections':sections,'current_plan':plan,'measured_issues':measured})
    schema={'type':'object','additionalProperties':False,'required':['approved','issues','arrangement'],'properties':{'approved':{'type':'boolean'},'issues':{'type':'array','items':{'type':'string'}},'arrangement':{'type':'string','enum':['columns','rows']}}}
    if isinstance(service,OpenAILLMService):
        response=service.client.responses.create(model=service.model,temperature=.1,input=[{'role':'system','content':system},{'role':'user','content':[{'type':'input_text','text':prompt},{'type':'input_image','image_url':'data:image/png;base64,'+encoded}]}],text={'format':{'type':'json_schema','name':'rendered_design_review','strict':True,'schema':schema}})
        raw=service._extract_output_text(response)
    elif isinstance(service,AnthropicLLMService):
        response=service.client.messages.create(model=service.model,max_tokens=900,system=system,messages=[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image','source':{'type':'base64','media_type':'image/png','data':encoded}}]}],output_config={'format':{'type':'json_schema','schema':schema}})
        if response.stop_reason in {'max_tokens','refusal'}: raise ValueError('Incomplete review')
        raw=next((r.text for r in response.content if r.type=='text'),'')
    else: raise ValueError('Unsupported vision provider')
    result=json.loads(raw)
    if not isinstance(result.get('approved'),bool) or result.get('arrangement') not in {'rows','columns'} or not isinstance(result.get('issues'),list): raise ValueError('Invalid quality review')
    result['issues']=[str(s)[:250] for s in result['issues'][:4]]
    result['approved']=result['approved'] and not measured and not result['issues']
    return result
