# Repeatable four-minute course demo

Use only the fictional team-authored campus case. See [LOCAL_RUN.md](LOCAL_RUN.md) for installation, local keys and server commands. Start one API worker and the frontend. Open `http://127.0.0.1:8081/projects/new`.

## Before presenting

- Load the synthetic example and check the two-page PDF is indexed.
- Make a rehearsal project using the configured provider and save its exported PPTX. Keep that reviewed deck available if the network/provider fails during the live demo.
- Check the conclusion retains **“promising, not proven.”** Generation varies between runs; source labels show selected evidence, not automatic fact checking.
- For a laptop, use the fork branch containing the complete integration. Local keys stay in an ignored backend `.env`; do not share that file.

## Live sequence

| Time | Action | What to explain |
| --- | --- | --- |
| 0:00–0:35 | Load synthetic demo, choose Dark tech, Save project. | Assignment is separate from the Context Pack. One PDF is the inspectable evidence. The Context Pack bridge is copy/paste from an existing chat. |
| 0:35–1:25 | Generate AI outline; change a title, move an item, select page 1 for observations and page 2 for workflow/trade-offs; Save outline. | Five plain draft items are reviewed before styled slides. Source selection remains the student's responsibility. |
| 1:25–2:10 | Confirm theme and approve; Build with AI. | Watch queued/generating/ready states. As soon as slide 1 is ready, save a short body edit while later slides build. Refresh after completion to show persistence. |
| 2:10–3:00 | Regenerate title with AI. Type a body draft while it runs, then save that draft after completion. | Only the target title is busy. Other accepted edits and unsaved neighboring drafts survive. The model may return similar wording. |
| 3:00–4:00 | Check comparison points and PDF labels; Download draft PPTX; open in PowerPoint/Impress and edit a title and body. | Five native editable slides reflect the saved order, theme and text. Export is disabled while generation is pending. |

Provider timing may extend the live sequence. Rehearse and use the reviewed saved deck for the final editor step rather than pretending an unfinished request succeeded.

## Failure and fallback

- A failed slide has its own retry; ready slides and edits remain saved.
- Failed block regeneration keeps previous text and offers retry or manual editing.
- After an API restart, interrupted work becomes retryable. Reload and retry the affected slide or block.
- Without a provider, use **Use key-free template** and the template build. Explicitly say this copies reviewed outline text; it does not demonstrate AI regeneration.
- If the live provider fails, show the reviewed rehearsal PPTX and explain the failure. A recorded walkthrough can be prepared by a team member; no recording has been claimed here.

## Claims to state accurately

All campus figures are synthetic. Page 1 describes four weeks, 1,000 inspected items per week and an observed incorrect-sorting share of 42% to 29%; the design cannot establish causation. Page 2 describes human review, 18 minutes per day and two hours of camera maintenance per week. Transfer to another campus is unverified.

Scope is English, five slides, one PDF, three themes and title/content/comparison layouts. There is no free canvas, generated imagery, live chat-account import, automated factual verification or multi-user editing. The local task runner requires one API worker.

## Independent acceptance — not yet completed

Ask an uninvolved classmate to follow these instructions without coaching. Record actual results in `TEST_NOTES.md`: intake, outline edit/order, evidence selection, approval/build, edit/regeneration, export. Note confusing wording and completion time. Do not invent feedback.

In PowerPoint or Impress, verify five slides and page labels, change one title and one body, save, close and reopen. Programmatic native-text roundtrip and five-slide rendering passed; this manual editor check remains pending. Prepare a 3–5 minute recording only after that rehearsal.
