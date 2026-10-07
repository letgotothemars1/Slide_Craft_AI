"""Provider options only for the deliberate final presentation quality passes.

Verified families: https://developers.openai.com/api/docs/models/gpt-5.4-mini
and the gpt-5.4 / gpt-5.4-nano model pages. The GPT-5.4 parameter
compatibility guide forbids temperature with reasoning above none.
Unknown model families retain their existing request options.
"""
import re

_SUPPORTED = re.compile(r'gpt-5\.4(?:-mini|-nano)?(?:-\d{4}-\d{2}-\d{2})?\Z')


def quality_model_options(model: str, temperature: float) -> dict:
    if _SUPPORTED.fullmatch(model):
        return {'reasoning': {'effort': 'high'}}
    return {'temperature': temperature}
