"""Durable observable operations and bounded provider attempts for staged work.

These events describe executed application operations, never hidden reasoning.
Usage is recorded only when returned by the provider; missing usage stays unknown.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from app.project_schemas import WorkflowState
from app.services.modular_build import _mutate

_ACTIVE = ContextVar("presentation_call", default=None)

class BudgetExhausted(RuntimeError):
    pass

def state(project):
    return WorkflowState.model_validate(project.workflow_json or {}).model_dump()

def set_stage(project_id, stage, expected_phase=None, **values):
    def change(project):
        if expected_phase and project.phase!=expected_phase:
            return None
        workflow = state(project)
        workflow.update(stage=stage, **values)
        return {"workflow_json": workflow}
    return _mutate(project_id, change)

def start_action(project_id, action, slide_id=None, model=False):
    number = []
    def change(project):
        workflow = state(project)
        if model and workflow["model_calls"] >= workflow["request_budget"]:
            raise BudgetExhausted("Generation request budget reached. Saved results are kept.")
        sequence = max((row["sequence"] for row in workflow["actions"]), default=0) + 1
        number[:] = [sequence]
        workflow["actions"] = (workflow["actions"] + [{"sequence": sequence, "action": action,
            "status": "running", "slide_id": slide_id, "detail": ""}])[-120:]
        if model:
            workflow["model_calls"] += 1
        return {"workflow_json": workflow}
    if not _mutate(project_id, change):
        raise RuntimeError("Project is no longer available")
    return number[0]

def finish_action(project_id, sequence, success=True):
    def change(project):
        workflow = state(project)
        for row in workflow["actions"]:
            if row["sequence"] == sequence:
                row["status"] = "complete" if success else "error"
        return {"workflow_json": workflow}
    _mutate(project_id, change)

@contextmanager
def operation(project_id, action, slide_id=None, model=False):
    try:
        sequence = start_action(project_id, action, slide_id, model)
    except BudgetExhausted:
        set_stage(project_id,"budget_exhausted")
        raise
    token = _ACTIVE.set(project_id if model else None)
    try:
        yield
    except Exception:
        finish_action(project_id, sequence, False)
        raise
    else:
        finish_action(project_id, sequence)
    finally:
        _ACTIVE.reset(token)

def record_usage(response):
    project_id = _ACTIVE.get()
    usage = getattr(response, "usage", None)
    if not project_id or usage is None:
        return
    def number(*names):
        for name in names:
            value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
            if isinstance(value, int) and value >= 0:
                return value
        return 0
    incoming, outgoing = number("input_tokens", "prompt_tokens"), number("output_tokens", "completion_tokens")
    if incoming or outgoing:
        def change(project):
            workflow = state(project)
            workflow["input_tokens"] += incoming
            workflow["output_tokens"] += outgoing
            return {"workflow_json": workflow}
        _mutate(project_id, change)
