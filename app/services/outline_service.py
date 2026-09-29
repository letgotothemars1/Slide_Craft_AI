"""Key-free starter outline. Its prompts require student review before approval."""

import re

from app.project_schemas import OutlineItem


def _labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?:^|\n)\s*{re.escape(label)}\s*:\s*(.+)", text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    return value[:300] if value else None


def starter_outline(context_pack: str) -> list[OutlineItem]:
    thesis = _labeled_value(context_pack, "thesis")
    prompts = [
        ("Frame the problem", "Problem and audience", "Explain the problem and who it affects.", "title"),
        ("Present the central claim", "Thesis", thesis or "State the central claim from your Context Pack.", "content"),
        ("Examine evidence", "Evidence", "Add a claim and select a supporting PDF excerpt, or mark Source needed.", "content"),
        ("Discuss the mechanism and limits", "How it works and trade-offs", "Explain the proposed approach and its limitations.", "comparison"),
        ("Conclude", "Conclusion", "Summarize the argument and name an unresolved question.", "content"),
    ]
    return [
        OutlineItem(id=f"s{index}", order=index, purpose=purpose, title=title,
                    key_message=message, evidence_refs=[], layout_type=layout)
        for index, (purpose, title, message, layout) in enumerate(prompts, start=1)
    ]
