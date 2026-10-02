"""Bounded native visuals; numeric values must occur in the shared PDF."""
import re
from app.project_schemas import DraftVisual

VISUAL_SCHEMA = {'type': 'object', 'additionalProperties': False,
                'required': ['kind', 'labels', 'values', 'unit'],
                'properties': {'kind': {'type':'string','enum':['none','process','bars']},
                               'labels': {'type':'array','items':{'type':'string'}},
                               'values': {'type':'array','items':{'type':'number'}},
                               'unit': {'type':'string'}}}


def validated_visual(raw, item):
    try:
        visual = DraftVisual.model_validate(raw)
    except ValueError:
        return None
    if visual.kind == 'none':
        return None
    if not 2 <= len(visual.labels) <= 4 or any(not label.strip() or len(label) > 70 for label in visual.labels):
        return None
    if visual.kind == 'process':
        return visual if not visual.values else None
    refs = item.evidence_refs or item.suggested_refs
    numbers = {float(n) for ref in refs for n in re.findall(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])', ref.excerpt)}
    if not refs or len(visual.labels) != len(visual.values) or any(value <= 0 or value not in numbers for value in visual.values):
        return None
    return visual
