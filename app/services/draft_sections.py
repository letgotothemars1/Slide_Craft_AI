"""Recover only fresh draft grouping; accepted-content regrouping stays strict."""
import re
from app.project_schemas import SlideSection
from app.services.semantic_sections import validated_sections


def draft_sections(raw, body, slide_id, title, comparison=False):
    """Never replace body with a model's rewritten section copies.

    Fresh content and its notes are valid independently of suggested grouping.
    A failed partition falls back to exact complete body text, not fragmented
    copies, without a provider retry or silently modifying a claim.
    """
    try:
        sections=validated_sections(raw, body, slide_id)
        # A numeric transition is one semantic unit, even when copied exactly.
        # Splitting “from 42%” and “to 29%” into separate panels passed the old
        # word-preservation check but fractured the argument.
        for first,second in zip(sections,sections[1:]):
            if re.search(r'\bfrom\b[^.!?]*\d[^.!?]*$',first.text,re.I) and re.match(r'^to\s+\d',second.text,re.I):
                raise ValueError('Numeric transition split across sections')
        return sections
    except (ValueError, TypeError, KeyError, AttributeError):
        if comparison:
            parts = body.split('|')
            if len(parts) != 2 or not all(part.strip() for part in parts):
                raise ValueError('Comparison needs exactly two complete points')
            return [SlideSection(id=f'{slide_id}-section-{i+1}', heading=heading, text=text.strip())
                    for i, (heading, text) in enumerate(zip(('First perspective', 'Second perspective'), parts))]
        return [SlideSection(id=f'{slide_id}-section-1', heading=title[:100], text=body)]
