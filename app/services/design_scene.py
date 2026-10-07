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


def _grounded_callouts(sections):
    """Recognize only verbatim explicit comparisons, never infer a statistic."""
    if 1<=len(sections)<=2:
        matches=[re.search(r'\bfrom\s+(\d+(?:\.\d+)?%)\s+to\s+(\d+(?:\.\d+)?%)',section.text,re.I) for section in sections]
        found=[match for match in matches if match]
        if len(found)==1:return [found[0].group(1),found[0].group(2)]
    if len(sections)==1:
        match=re.search(r'\bfrom\s+(\d+(?:\.\d+)?%)\s+to\s+(\d+(?:\.\d+)?%)',sections[0].text,re.I)
        if match: return [match.group(1),match.group(2)]
    if len(sections)==2:
        pattern=r'\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:minutes?|hours?)\s+per\s+(?:day|week)\b'
        values=re.findall(pattern,' '.join(section.text for section in sections),re.I)
        if len(values)==2 and len(set(value.lower() for value in values))==2:return values
    return []


def build_scene(slide, theme, order):
    design = slide.design or _default_design(slide, order)
    # A content draft is deliberately independent of the final theme choice.
    # This also means approval cannot silently recolour an unfinished draft.
    if slide.design:
        bg, fg, muted, accent, panel = ('#'+value for value in PALETTES[theme])
    else:
        bg, fg, muted, accent, panel = '#FFFFFF', '#111827', '#475569', '#64748B', '#F1F5F9'
    if design.emphasis == 'inverse':
        bg, fg, muted, accent, panel = fg, bg, bg, accent, fg
    # The same theme accent can lose contrast after inversion or on a pale surface.
    if _contrast(accent,bg)<3:
        accent=muted
    accent_ink=max((bg,fg),key=lambda color:_contrast(color,accent))
    out = []
    font = 'Georgia' if slide.design and theme == 'clean_editorial' else 'Arial'

    def rect(x,y,w,h,color):
        out.append(SceneElement(kind='rect',x=x,y=y,w=w,h=h,color=color))

    def fit(value,w,h,size):
        """Largest size at or below `size` whose wrapped text fits, and its height."""
        # Keep natural words intact in narrow title rails. The prior height-only
        # fit let browser/PowerPoint wrap a long word in the middle.
        longest=max((len(word) for word in value.split()),default=1)
        size=min(size,max(.95,w/(longest*.64)))
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
    composition=getattr(design,'composition','balanced')
    has_visual=visual and visual.kind in {'bars','process'}
    callouts=_grounded_callouts(slide.sections) if slide.design and not has_visual else []
    if callouts:
        # Large values are copied verbatim; accepted sentences and qualifiers
        # remain below them with their original section editing bindings.
        text(title,7,4.6,86,9,3.9,bold=True,key='title')
        metric_rows=composition=='balanced' and design.arrangement=='rows' and len(slide.sections)==2
        for index,value in enumerate(callouts):
            x=7 if composition=='bands' else 7+index*46
            y=16+index*17 if composition=='bands' else 14 if metric_rows else 16
            ink=accent_ink if composition=='poster' else accent
            inset=2 if composition=='poster' else 0
            if composition=='poster': rect(x,y,40,14,accent)
            else: rect(x,y,40,.25,accent)
            if '%' in value:
                text(value,x+inset,y+1,40-inset*2,12,6.5 if composition=='poster' else 6 if metric_rows else 6.8,ink,True)
            else:
                # Split only the existing phrase at its first space. The
                # numeric word is untouched ("two" never becomes "2").
                amount,unit=value.split(' ',1)
                text(amount,x+inset,y+1,40-inset*2,10,6.5,ink,True)
                text(unit,x+inset,y+10,40-inset*2,4,2.4,ink,True)
        if '%' in callouts[0] and composition!='bands':
            text('→',48,19,5,6,3.3,muted)
        if '%' in callouts[0] and composition!='bands':
            accepted_text=' '.join(section.text for section in slide.sections)
            sample=re.search(r'\b[\d,]+ inspected items per week\b',accepted_text)
            citation=re.search(r'\((source PDF, p\. \d+)\)',accepted_text)
            if sample:text(sample.group(),7,24 if metric_rows else 27,53,3,2.1,muted)
            if citation:text(citation.group(1),62,24 if metric_rows else 27,31,3,1.8,muted)
        sections=slide.sections
        width=40 if composition=='bands' or len(sections)>1 else 86
        for index,section in enumerate(sections):
            x=53 if composition=='bands' else 7+index*46 if len(sections)>1 else 7
            y=17+index*17 if composition=='bands' else 31
            section_width=width
            band_height=None
            if composition=='bands' and len(sections)==2:
                weights=[len(s.text)+80 for s in sections]
                heights=[31.5*weight/sum(weights) for weight in weights]
                x=47;section_width=46
                y=17 if index==0 else 18.5+heights[0]
                band_height=heights[index]
            if composition=='feature' and len(sections)==2:
                lead_width=max(36,min(48,80*(1-design.support_share))) if design.support_share is not None else 46
                is_lead=section.id==(design.focal_section_id or sections[0].id)
                x=7 if is_lead else 13+lead_width
                section_width=lead_width if is_lead else 80-lead_width
            if metric_rows:
                ordered=sorted(sections,key=lambda s:s.id!=design.focal_section_id) if design.focal_section_id else sections
                weights=[len(s.text)+160 for s in ordered]
                heights=[21*weight/sum(weights) for weight in weights]
                position=next(i for i,s in enumerate(ordered) if s.id==section.id)
                x=7;section_width=86;y=28+sum(heights[:position])+position
                band_height=heights[position]
            text(section.heading,x,y,section_width,3.4 if metric_rows else 4,2.3 if metric_rows else 2.4,fg,True,key='body',section_id=section.id,section_field='heading')
            height=28 if composition=='bands' and len(sections)==1 else 14
            body_gap=3.4 if metric_rows else 4.2 if band_height is not None else 5
            if band_height is not None:height=band_height-body_gap
            text(section.text,x,y+body_gap,section_width,height,2.6,fg,key='body',section_id=section.id,section_field='text')
    elif composition=='poster' and not has_visual:
        # Strong title rail plus native semantic content: never rasterized.
        compact_hero=len(slide.sections)==1 and len(slide.sections[0].text)<140 and len(title)>30
        rail_width=100*design.title_share if design.title_share is not None else 47 if compact_hero else 35
        rail_top=9 if compact_hero else 5
        rail_height=36 if compact_hero else 45
        rect(4.5,rail_top,rail_width,rail_height,accent)
        title_size,title_used=fit(title,rail_width-7,rail_height-7,5.1 if compact_hero else 5.5)
        text(title,8,rail_top+3,rail_width-7,rail_height-6,title_size,accent_ink,True,key='title')
        sections=slide.sections
        if sections:
            count=len(sections)
            columns=2 if count>=3 else 1
            content_x=rail_width+9
            content_width=93-content_x
            col_width=(content_width-3)/2 if columns==2 else content_width
            for index,section in enumerate(sections):
                column=index%columns
                row=index//columns
                rows=(count+columns-1)//columns
                height=((34 if compact_hero else 44)-3*(rows-1))/rows
                x=content_x+column*(col_width+3); y=(14 if compact_hero else 6)+row*(height+3)
                rect(x,y,8,.35,accent)
                heading_size,heading_used=fit(section.heading,col_width,height*.35,2.7)
                text(section.heading,x,y+1.4,col_width,heading_used+.6,heading_size,fg,True,key='body',section_id=section.id,section_field='heading')
                body_top=y+heading_used+3.2
                text(section.text,x,body_top,col_width,y+height-body_top,2.8,fg,key='body',section_id=section.id,section_field='text')
        else:
            body_size,body_used=fit(body,49,39,3.3)
            text(body,44,7,49,42,body_size,fg,key='body')
    elif composition=='bands' and not slide.sections and not has_visual:
        text(title,7,6,32,42,4.1,fg,True,key='title')
        rect(43,6,.2,43,accent)
        body_size,body_used=fit(body,45,40,3.1)
        text(body,48,8,45,41,body_size,fg,key='body')
    elif slide.sections and (layout != 'hero' or len(slide.sections)>1 or composition!='balanced'):
        text(title,7,4.6,86,9,3.9,bold=True,key='title')
        sections=slide.sections
        composition=getattr(design,'composition','balanced')
        focal=next((s for s in sections if s.id==getattr(design,'focal_section_id','')),sections[0])
        has_bars=visual and visual.kind=='bars'
        has_process=visual and visual.kind=='process'
        area_width=(44 if composition=='bands' else 40) if has_bars else 86
        area_top=24 if has_process else 15.5 if composition=='poster' and has_bars else 17
        area_height=50-area_top
        gap=1.5 if composition=='bands' or has_bars else 2
        cells={}

        def stacked(items,x,y,w,h):
            # Allocate room to the text that needs it without merging sections.
            weights=[len(s.text)+len(s.heading)*1.5+65 for s in items]
            usable=h-gap*(len(items)-1)
            offset=0
            for section,weight in zip(items,weights):
                height=usable*weight/sum(weights)
                cells[section.id]=(x,y+offset,w,height)
                offset+=height+gap

        if composition=='poster':
            # Keep accepted native charts/processes and vary their text rail.
            stacked(sections,7,area_top,area_width,area_height)
            for index,section in enumerate(sections):
                x,y,w,h=cells[section.id]
                inset=0 if has_bars else 3.5 if index%2 else 1.5
                cells[section.id]=(x+inset,y,w-inset,h)
            rect(5,area_top,.35,area_height,accent)
        elif composition=='feature' and len(sections)>1:
            others=[s for s in sections if s.id!=focal.id]
            if has_bars:
                # Dense chart rails emphasize with ink rather than wasting
                # supporting text space on an oversized lead paragraph.
                stacked(sections,7,area_top,area_width,area_height)
            else:
                # Space follows text demand; a brief takeaway cannot force a
                # lengthy limitations paragraph into a narrow sidebar.
                focal_weight=len(focal.text)+80
                support_weight=max(len(section.text) for section in others)+80
                focal_width=80*(1-design.support_share) if design.support_share is not None else max(32,min(54,80*focal_weight/(focal_weight+support_weight)))
                support_x=7+focal_width+6
                cells[focal.id]=(7,area_top,focal_width,area_height)
                stacked(others,support_x,area_top,80-focal_width,area_height)
                rect(7+focal_width+3,area_top,.15,area_height,accent)
        elif composition=='balanced' and design.arrangement=='columns' and len(sections)>1 and not has_bars:
            width=(area_width-gap*(len(sections)-1))/len(sections)
            for index,section in enumerate(sections):
                cells[section.id]=(7+index*(width+gap),area_top,width,area_height)
        else:
            stacked(sections,7,area_top,area_width,area_height)

        # Emit in accepted section order despite asymmetric visual hierarchy.
        for section in sections:
            x,y,w,h=cells[section.id]
            is_feature=composition=='feature' and section.id==focal.id
            if (composition=='bands' or composition=='poster' and has_process) and not has_bars:
                rect(x,y,w,.14,accent)
                heading_width=min(18 if composition=='poster' else 23,w*.3)
                text(section.heading,x,y+.9,heading_width,h-1,3.1 if len(sections)==1 else 2.2,bold=True,key='body',section_id=section.id,section_field='heading')
                text(section.text,x+heading_width+4,y+.9,w-heading_width-4,h-1,3.6 if len(sections)==1 else 2.35,key='body',section_id=section.id,section_field='text')
            elif is_feature and not has_bars:
                rect(x,y,9,.35,accent)
                heading_size,heading_used=fit(section.heading,w,h*.28,3.1)
                text(section.heading,x,y+2,w,heading_used+.6,heading_size,bold=True,key='body',section_id=section.id,section_field='heading')
                body_top=y+heading_used+4.5
                text(section.text,x,body_top,w,y+h-body_top,2.7,key='body',section_id=section.id,section_field='text')
            else:
                rect(x,y,w,.2,accent)
                heading_size,heading_used=fit(section.heading,w,max(3.3,h*.3),1.95 if has_bars else 2.25)
                text(section.heading,x,y+.8,w,heading_used+.5,heading_size,accent if is_feature else fg,bold=True,key='body',section_id=section.id,section_field='heading')
                body_top=y+heading_used+(1.5 if has_bars else 2)
                body_size=3.8 if len(sections)==1 and not has_bars else 3 if composition=='balanced' and design.arrangement=='columns' and len(sections)<=3 and not has_bars else 2.3
                text(section.text,x,body_top,w,max(.6,y+h-body_top),body_size if not has_bars else 2,
                     fg if composition=='balanced' else muted,key='body',section_id=section.id,section_field='text')
        if has_bars and composition=='bands':
            maximum=max(max(visual.values),1)
            row_height=30/len(visual.values)
            for index,(label,value) in enumerate(zip(visual.labels,visual.values)):
                y=18+index*row_height
                text(label,54,y,27,3.5,2,fg,True)
                text(f'{value:g}{visual.unit}',83,y,10,3.5,2.4,fg,True)
                rect(54,y+4,39,2.7,panel)
                rect(54,y+4,max(.15,value/maximum*39),2.7,accent)
        elif has_bars:
            maximum=max(max(visual.values),1)
            width=40/len(visual.values)
            rect(53,43,40,.15,muted)
            for index,(label,value) in enumerate(zip(visual.labels,visual.values)):
                x=54+index*width; height=value/maximum*22
                rect(x,43-height,width-3,height,accent if index==len(visual.values)-1 else muted)
                text(f'{value:g}{visual.unit}',x,37.5-height,width-2,4.7,2.5,bold=True)
                text(label,x,45,width-2,5.5,1.9,muted)
        elif has_process:
            labels=visual.labels
            # These explicitly complementary conditions are alternatives, not
            # consecutive steps. Keep every accepted label verbatim.
            fork=(len(labels)==3 and 'if confident' in labels[1].lower()
                  and 'if uncertain' in labels[2].lower())
            if fork:
                rect(7,15,24,6,panel)
                rect(7,15,24,.25,accent)
                text(labels[0],8.5,16.4,21,4,1.95,fg,True)
                rect(31,17.9,10,.2,accent)
                rect(41,13.9,.2,7,accent)
                for index,label in enumerate(labels[1:]):
                    y=11+index*7
                    rect(41,y+2.9,6,.2,accent)
                    rect(47,y,46,6,panel)
                    rect(47,y,46,.25,accent)
                    text(label,48.5,y+1.4,43,4,1.95,fg,True)
            else:
                width=86/len(labels)
                for index,label in enumerate(labels):
                    x=7+index*width
                    rect(x,15,width-2,6,panel)
                    rect(x,15,width-2,.25,accent)
                    if index<len(labels)-1: rect(x+width-2,17.8,2,.2,accent)
                    text(label,x+1.5,16.4,width-5,4,1.95,fg,True)
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
    if has_visual and visual.kind=='bars' and slide.sections and composition=='poster':
        # Move the chart to the reading lead and put commentary at its right.
        # This changes composition without changing any chart facts or text.
        for element in out:
            if element.section_id or element.kind=='rect' and element.x==7 and element.w==40:
                element.x+=48
            elif element.kind=='rect' and element.x==5 and element.w==.35:
                element.x+=48
            elif element.x>=53 and element.block_key not in {'title','source_label'}:
                element.x-=46
    if has_visual and not slide.sections and composition in {'bands','poster'}:
        for element in out:
            if element.block_key=='title':
                element.w=74 if composition=='bands' else 62
                element.size=min(element.size,3.5 if composition=='bands' else 4.1)
            elif element.block_key=='body':
                if layout=='chart':
                    element.x=5 if composition=='bands' else 8
                    element.w=35 if composition=='bands' else 32
                    element.size=fit(element.text,element.w,element.h,2.5)[0]
                else:
                    element.x=5 if composition=='bands' else 11
                    element.w=90 if composition=='bands' else 78
                    element.size=fit(element.text,element.w,element.h,2.5)[0]
        if composition=='poster':
            rect(4,5,.35,43,accent)
    if slide.show_source:
        text(slide.blocks.source_label.text,7,53,86,2.1,1,muted,key='source_label')
    return out
