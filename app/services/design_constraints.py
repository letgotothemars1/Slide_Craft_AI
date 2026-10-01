"""Keep reviewed content structure and one theme throughout final design."""
from app.project_schemas import DesignPlan


def allowed_layouts(layout_type, visual):
    if visual and visual.kind != 'none':
        return ['chart' if visual.kind == 'bars' else 'process']
    if layout_type == 'title':
        return ['hero']
    if layout_type == 'comparison':
        return ['comparison']
    return ['editorial', 'statement']


def preserve_reviewed_structure(plan, layout_type, visual):
    result = plan.model_copy(deep=True)
    choices = allowed_layouts(layout_type, visual)
    if result.layout not in choices:
        result.layout = choices[0]
    result.visual = visual.model_copy(deep=True) if visual and visual.kind != 'none' else None
    if result.emphasis == 'inverse':
        result.emphasis = 'quiet'
    return result
