"""Single native geometry for browser previews and editable PowerPoint."""
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


def _wrapped_lines(value: str, width: float, size: float) -> int:
    """Count the lines greedy word wrapping actually produces.

    Dividing the character count by the line width assumes perfect packing.
    Real wrapping breaks on word boundaries and leaves a ragged edge, so it
    needs one more line more often than not — and that extra line is the one
    that gets clipped, because every box here has a fixed height. The same
    estimate caused visibly cut headlines in the one-shot renderer before it
    was replaced with this simulation.
    """
    columns = max(1, int(width / (size * .53)))
    total = 0
    for paragraph in (value or "").split('\n'):
        words = paragraph.split()
        if not words:
            total += 1
            continue
        lines, current = 1, 0
        for word in words:
            needed = len(word) if current == 0 else current + 1 + len(word)
            if needed <= columns:
                current = needed
            else:
                lines += 1
                # A word longer than the line wraps onto further lines of its own.
                current = len(word)
                while current > columns:
                    lines += 1
                    current -= columns
        total += lines
    return total


# Footer line: every layout keeps its content above it so the source label
# never collides with the body.
FOOTER = 51.0


def _default_design(slide, order):
    """A layout for slides that never went through the design pass.

    Key-free drafts have no `design`, and returning nothing left them with no
    scene at all — the PDF export had nothing to draw, and the PPTX exporter
    kept a second, hand-written layout path just for them. Deriving a plan from
    the content keeps one layout engine behind every surface.
    """
    from app.project_schemas import DesignPlan

    visual = getattr(slide, 'visual', None)
    if visual and visual.kind == 'bars':
        layout = 'chart'
    elif visual and visual.kind == 'process':
        layout = 'process'
    elif '|' in slide.blocks.body.text:
        layout = 'comparison'
    elif order == 1:
        layout = 'hero'
    else:
        layout = 'statement'
    return DesignPlan(layout=layout, emphasis='quiet',
                      rationale='Derived from slide content; no design pass ran.',
                      visual=visual)


def build_scene(slide, theme, order):
    design = slide.design or _default_design(slide, order)
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

    def fit(value,w,h,size):
        """Largest size at or below `size` whose wrapped text fits, and its height."""
        while size > .95:
            used = _wrapped_lines(value, w, size) * size * 1.22
            if used <= h-.4: return round(size,2), used
            size -= .1
        return round(size,2), _wrapped_lines(value, w, size) * size * 1.22

    def text(value,x,y,w,h,size,color=fg,bold=False,key=None,column=None,section_id=None,section_field=None):
        # Respect explicit line breaks and shrink until the text fits its box.
        size,_ = fit(value,w,h,size)
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
        # The process strip is a compact band; the sections get everything left
        # down to the footer. At the previous 22% three paragraphs could only
        # fit by shrinking below the 18pt floor, which the render check flags —
        # and the design loop then failed the slide outright.
        area_height=27.5 if has_process else 35
        area_top=22.5 if has_process else 18
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
                rect(x,15,width-2,5.4,panel)
                rect(x,15,width-2,.25,accent)
                if index<len(visual.labels)-1: rect(x+width-2,17.5,2,.2,accent)
                text(label,x+1.5,16.1,width-5,3.6,1.9,fg,True)
    elif layout=='hero':
        # Geometry from the one-shot renderer's full-width hero: a hairline
        # accent on the left rather than a heavy slab on the right, and the
        # text spanning the canvas instead of stopping at two thirds.
        rect(0,0,.4,56.25,accent)
        single = slide.sections[0] if len(slide.sections)==1 else None
        lead = single.text if single else body
        title_size,title_used = fit(title,84.4,20,5.9)
        lead_size,lead_used = fit(lead,73.4,16,2.3)
        heading_space = 5.2 if single else 0
        block = title_used+4.4+heading_space+lead_used
        top = max(10,(FOOTER-block)/2)
        text(f'{order:02d}',5.6,top-5,31.2,2.8,1.9,accent,True)
        text(title,5.6,top,84.4,title_used+.6,title_size,bold=True,key='title')
        rect(5.6,top+title_used+2,9,.35,accent)
        lead_top = top+title_used+4.4
        if single:
            text(single.heading,5.6,lead_top,73.4,4,2.4,bold=True,key='body',section_id=single.id,section_field='heading')
            lead_top += heading_space
        text(lead,5.6,lead_top,73.4,lead_used+.6,lead_size,muted,key='body',
             **({'section_id':single.id,'section_field':'text'} if single else {}))
    elif layout=='editorial':
        # Title over body, both full width. The group is balanced vertically
        # instead of anchored to the top: a two-sentence body cannot fill a
        # fixed box, and anchoring dumped all the slack below the text.
        title_size,title_used = fit(title,90,13,4.2)
        body_size,body_used = fit(body,85,29,2.4)
        top = max(6.9,(FOOTER-(title_used+3.6+body_used))/2)
        rect(5,top-3.5,8,.35,accent)
        text(title,5,top,90,title_used+.6,title_size,bold=True,key='title')
        body_top = top+title_used+3.6
        rect(5,body_top-.9,.25,body_used+1.8,accent)
        text(body,8.5,body_top,85,body_used+.6,body_size,muted,key='body')
    elif layout=='comparison' and '|' in body:
        text(title,5,3.8,90.6,9.4,3.8,bold=True,key='title')
        # Panels reach the footer line, so the pair reads as the slide's content
        # rather than as two cards floating above empty space. Both sides are
        # set at one size — the shorter half must not look louder than the
        # longer one — and each is centred inside its panel.
        parts=[part.strip() for part in body.split('|',1)]
        shared=min(fit(part,37,29,2.6)[0] for part in parts)
        for index,part in enumerate(parts):
            x=5+46*index
            rect(x,14.4,43,36,panel if index else accent)
            used=_wrapped_lines(part,37,shared)*shared*1.22
            text(part,x+3,14.4+(36-used)/2,37,used+.6,shared,
                 fg if index else accent_ink,key='body',column=index)
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
        # Statement and anything unrecognised: the one-shot content layout,
        # balanced the same way as editorial.
        plain = body.replace('|','\n')
        title_size,title_used = fit(title,90,13,4.2)
        body_size,body_used = fit(plain,88.8,30,2.6)
        top = max(6.9,(FOOTER-(title_used+3.6+body_used))/2)
        rect(5,top-3.5,8,.35,accent)
        text(title,5,top,90,title_used+.6,title_size,bold=True,key='title')
        text(plain,5,top+title_used+3.6,88.8,body_used+.6,body_size,muted,key='body')
    if slide.show_source:
        text(slide.blocks.source_label.text,7,53,86,2.1,1,muted,key='source_label')
    return out
