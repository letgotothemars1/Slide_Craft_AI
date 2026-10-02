"""Single native geometry for browser previews and editable PowerPoint."""
import math
import re
from app.project_schemas import SceneElement
from app.services.modular_export import PALETTES


def _contrast(first, second):
    def luminance(color):
        channels=[int(color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
        linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels]
        return sum(c*w for c,w in zip(linear,(.2126,.7152,.0722)))
    a,b=sorted((luminance(first),luminance(second)))
    return (b+.05)/(a+.05)


def build_scene(slide, theme, order):
    if not slide.design:
        return []
    design = slide.design
    bg, fg, muted, accent, panel = ('#'+value for value in PALETTES[theme])
    if design.emphasis == 'inverse':
        bg, fg, muted, accent, panel = fg, bg, bg, accent, fg
    # The same theme accent can lose contrast after inversion or on a pale surface.
    if _contrast(accent,bg)<3:
        accent=muted
    accent_ink=max((bg,fg),key=lambda color:_contrast(color,accent))
    out = []
    font = 'Georgia' if theme == 'clean_editorial' else 'Arial'

    def rect(x,y,w,h,color):
        out.append(SceneElement(kind='rect',x=x,y=y,w=w,h=h,color=color))

    def text(value,x,y,w,h,size,color=fg,bold=False,key=None,column=None,section_id=None,section_field=None):
        # Respect explicit line breaks, estimate word wrapping, and leave room for descenders.
        while size > .95:
            columns = max(1,int(w/(size*.53)))
            lines = sum(max(1,math.ceil(len(line)/columns)) for line in value.split('\n'))
            if lines * size * 1.22 <= h-.4: break
            size -= .1
        out.append(SceneElement(kind='text',x=x,y=y,w=w,h=h,color=color,text=value,size=round(size,2),bold=bold,font=font if key=='title' else 'Arial',block_key=key,column=column,section_id=section_id,section_field=section_field))

    title, body = slide.blocks.title.text, slide.blocks.body.text
    visual = design.visual
    layout = design.layout
    if layout in {'chart','process'} and not visual:
        layout = 'editorial'
    rect(0,0,100,56.25,bg)
    if slide.sections and (layout != 'hero' or len(slide.sections)>1):
        text(title,7,5,86,9,3.8,bold=True,key='title')
        sections=slide.sections
        has_bars=visual and visual.kind=='bars'
        # Semantic sections own both heading and data; their order and wording are immutable here.
        columns=design.arrangement=='columns' and len(sections)>1 and not has_bars
        area_width=40 if has_bars else 86
        has_process=visual and visual.kind=='process'
        area_height=22 if has_process else 35
        area_top=30 if has_process else 18
        weights=[len(s.text)+70 for s in sections]
        total_weight=sum(weights)
        row_offset=0
        for index,section in enumerate(sections):
            if columns:
                width=area_width/len(sections); x=7+index*width; y=area_top; w=width-5; h=area_height
                rect(x,y,w,.25,accent)
                text(section.heading,x,y+1,w,5,2.3,bold=True,key='body',section_id=section.id,section_field='heading')
                text(section.text,x,y+7,w,h-7,2.25,fg,key='body',section_id=section.id,section_field='text')
            else:
                height=area_height*weights[index]/total_weight; y=area_top+row_offset
                row_offset+=height
                rect(7,y,area_width,.15,accent)
                if has_bars:
                    text(section.heading,7,y+1,area_width,3,1.9,bold=True,key='body',section_id=section.id,section_field='heading')
                    text(section.text,7,y+4,area_width,height-4.5,2.1,muted,key='body',section_id=section.id,section_field='text')
                else:
                    text(section.heading,7,y+1.5,24,height-2,2.1,bold=True,key='body',section_id=section.id,section_field='heading')
                    text(section.text,35,y+1.5,58,height-2,2.2,fg,key='body',section_id=section.id,section_field='text')
        if has_bars:
            maximum=max(visual.values); width=40/len(visual.values)
            rect(53,44,40,.15,muted)
            for index,(label,value) in enumerate(zip(visual.labels,visual.values)):
                x=55+index*width; height=value/maximum*23
                rect(x,44-height,width-5,height,accent if index==len(visual.values)-1 else muted)
                text(f'{value:g}{visual.unit}',x,38-height,width-2,5,2.5,bold=True)
                text(label,x,46,width-2,5,1.8,muted)
        elif visual and visual.kind=='process':
            width=86/len(visual.labels)
            for index,label in enumerate(visual.labels):
                x=7+index*width
                rect(x,18,width-2,9,panel)
                rect(x,18,width-2,.25,accent)
                if index<len(visual.labels)-1: rect(x+width-2,22.3,2,.2,accent)
                text(label,x+1.5,20,width-5,6,1.9,fg,True)
    elif layout=='hero':
        rect(83,0,17,56.25,accent)
        text(title,7,7,69,18,5.2,bold=True,key='title')
        rect(7,26,9,.35,accent)
        if len(slide.sections)==1:
            section=slide.sections[0]
            text(section.heading,7,29,66,4,2.1,bold=True,key='body',section_id=section.id,section_field='heading')
            text(section.text,7,35,66,17,2.3,muted,key='body',section_id=section.id,section_field='text')
        else:
            text(body,7,30,66,21,2.3,muted,key='body')
        text(f'{order:02d}',86,43,12,8,5,accent_ink,True)
    elif layout=='editorial':
        text(title,7,8,32,36,4.2,bold=True,key='title')
        rect(42,7,.25,41,accent)
        text(body,48,10,44,36,2.6,muted,key='body')
    elif layout=='comparison' and '|' in body:
        text(title,7,5,86,11,3.8,bold=True,key='title')
        for index,part in enumerate(body.split('|',1)):
            x=7+46*index
            rect(x,21,40,28,panel if index else accent)
            ink=fg if index else accent_ink
            text(part.strip(),x+3,25,34,20,2.7,ink,key='body',column=index)
    elif layout=='chart':
        text(title,7,5,86,10,3.8,bold=True,key='title')
        text(body,7,18,31,30,2.1,muted,key='body')
        maximum=max(visual.values)
        column_width=44/len(visual.values)
        labels=visual.labels
        parts=[re.fullmatch(r'(.+?)\s*\(([^()]+)\)',label) for label in labels]
        if all(parts) and len({part.group(1) for part in parts})==1:
            labels=[part.group(2) for part in parts]
        rect(46,44,46,.15,muted)
        for index,(label,value) in enumerate(zip(labels,visual.values)):
            x=48+column_width*index
            height=value/maximum*23
            rect(x,44-height,column_width-5,height,accent if index==len(visual.values)-1 else muted)
            text(f'{value:g}{visual.unit}',x,38-height,column_width-2,5,3.5,bold=True)
            text(label,x,46,column_width-2,5.5,2,muted)
    elif layout=='process':
        text(title,7,5,86,10,3.8,bold=True,key='title')
        text(body.replace(' | ','\n'),7,17,86,12,2.2,muted,key='body')
        width=86/len(visual.labels)
        for index,label in enumerate(visual.labels):
            x=7+index*width
            rect(x,35,width-3,14,panel)
            rect(x,35,width-3,.4,accent)
            rect(x+2,37,2,.35,accent)
            text(label,x+2,41,width-7,6.5,2.1,bold=True)
    else:
        rect(7,5,10,.4,accent)
        text(title,7,9,86,15,4.2,bold=True,key='title')
        text(body.replace('|','\n'),7,29,82,20,3,muted,key='body')
    if slide.show_source:
        text(slide.blocks.source_label.text,7,53,86,2.1,1,muted,key='source_label')
    return out
