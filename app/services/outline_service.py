"""Key-free starter outline. Its prompts require student review before approval."""

import re

from app.project_schemas import OutlineItem


def _labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?:^|\n)\s*{re.escape(label)}\s*:\s*(.+)", text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    return value[:300] if value else None


def _without_inline_source_note(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s*See the demo source, page \d+\.", "", value, flags=re.IGNORECASE).strip()


def starter_outline(context_pack: str) -> list[OutlineItem]:
    topic = _labeled_value(context_pack, "topic")
    problem = _labeled_value(context_pack, "problem")
    thesis = _labeled_value(context_pack, "thesis")
    claim_one = _without_inline_source_note(_labeled_value(context_pack, "claim 1"))
    claim_two = _without_inline_source_note(_labeled_value(context_pack, "claim 2"))
    tradeoffs = _without_inline_source_note(_labeled_value(context_pack, "trade-offs"))
    conclusion = _labeled_value(context_pack, "conclusion")
    comparison = " | ".join(part for part in (claim_two, tradeoffs) if part)
    prompts = [
        ("Frame the problem", topic or "Problem and audience", problem or "Explain the problem and who it affects.", "title"),
        ("Present the central claim", "Central claim", thesis or "State the central claim from your Context Pack.", "content"),
        ("Examine evidence", "Pilot observations", claim_one or "Add a claim and select a supporting PDF excerpt, or mark Source needed.", "content"),
        ("Discuss the mechanism and limits", "Workflow and trade-offs", comparison or "Explain the proposed approach and its limitations. | Add a second comparison point.", "comparison"),
        ("Conclude", "Conclusion and next test", conclusion or "Summarize the argument and name an unresolved question.", "content"),
    ]
    return [
        OutlineItem(id=f"s{index}", order=index, purpose=purpose, title=title,
                    key_message=message, evidence_refs=[], layout_type=layout)
        for index, (purpose, title, message, layout) in enumerate(prompts, start=1)
    ]
