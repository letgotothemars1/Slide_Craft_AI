# How our team will learn while building

The two developers own and understand the MVP. AI can explain the repository, propose a small edit, and help debug it; the team decides what enters the product. A working demo is the goal, but each developer should be able to explain the main data path without the chat open.

## One task, one chat, one branch

1. Read `START_HERE.md`, `CONTRACT.md`, and your task card. Tell the chat your task ID and branch. Ask it to locate the existing code path before editing.
2. Ask for the smallest vertical slice that can be run: API response → saved state → visible UI, or one editable PPTX slide. Do not request “build the entire app” in one prompt.
3. After each edit, inspect the changed files. Ask: “What changed in plain language, and which existing behavior could break?” If neither developer can answer, pause and simplify the change.
4. Run the task card's acceptance checks. Include at least one unhappy path: invalid PDF, stale edit, model failure, or failed export. A screenshot without a saved-state check is not enough.
5. Record the result and one known limitation in the task card. Share a short screen capture with the other developer. Merge only after the shared contract still works.

## Useful prompts

- “Trace this request from the button to the database and back. Name files and functions; do not edit yet.”
- “Implement only the first acceptance criterion of M04. Show the API response and a repeatable local check.”
- “Explain this diff as if I need to defend it in a course demo. What would fail if this field were missing?”
- “Review this module for race conditions that can overwrite a student's edit. Give a concrete reproduction.”
- “The UI shows `ready` but export is stale. Follow the saved data path and find the mismatch.”

## Daily ten-minute handoff

Each developer answers: (1) what runs today; (2) what changed in the contract; (3) what is blocked; (4) one thing learned. The non-coding classmates can be involved by trying the flow and reporting where labels or steps are unclear. Their feedback is part of product work, not a substitute for coding.

## Rules for the final week

Do not start animations, image generation, extra themes, a free canvas, or a dashboard. If a part fails, fix the end-to-end demo first. If the model is unreliable, use a deterministic fixture to diagnose the UI and persistence, then repeat with the real provider. Clearly label fixtures in development; the final demonstration should include a real model call for at least the outline and slides. Keep secret keys in local environment files and do not paste them into chats or screenshots.
