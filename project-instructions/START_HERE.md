# SlideCraft AI: three-week MVP

This folder is the handoff package for Project Team 1. Start here in any new chat, even if you have never seen the project. The product idea is a presentation generator for master's students preparing English-language reports and project presentations. A student brings an assignment, one source PDF, and a structured summary of work already discussed with ChatGPT or Claude. SlideCraft first produces a plain, editable outline. After approval, styled slides appear progressively. The student can edit the result inside SlideCraft and export an editable PowerPoint file that is good enough to submit or present.

## What exists in the cloned repository

Checked against `main` at commit `9f11c62` (2026-09-23). The current product is a one-shot generator. `src/pages/GeneratePage.tsx` and `src/components/PromptForm.tsx` collect a prompt, style, language, slide count, and one optional PDF. `POST /generate` in `app/main.py` starts a background job. `app/services/orchestrator.py` asks the model for one complete `PresentationSpec`, then renders and uploads the entire deck. `app/services/document_service.py` extracts PDF text but loses page boundaries when chunking; `app/services/retrieval_service.py` returns plain chunk strings. `src/pages/JobPage.tsx` polls job status and shows previews only after completion. `app/services/render_service.py` already creates a PPTX with native text boxes and shapes, but there is no in-app slide editor. OpenAI and Anthropic are selectable for text generation; document embeddings currently depend on OpenAI.

This means the MVP extends a functioning base. It must not be described as already implemented. The previous paper and this plan express a target, not a guarantee that every part is present now.

## Demo contract: what must visibly work

1. Import a Context Pack: SlideCraft offers a copyable instruction for the AI chat that already knows the assignment; the student pastes its structured response back into SlideCraft.
2. Store the assignment separately from presentation content and attach one public, synthetic, or team-authored PDF. Show the source filename and page number for a supported claim.
3. Generate a black-on-white outline of five slides. Edit a title or main point, reorder a slide, select one of three themes, and approve the outline.
4. Generate the deck one slide at a time. Show honest states: queued, generating, ready, error. Display ready slides while later slides continue to build.
5. Edit at least a title, body/bullet text, and source label inside SlideCraft. Regenerate one text block without replacing other accepted edits. During regeneration, only that block is locked.
6. Export a visually presentable PPTX with editable native text and shapes. Its slide count, wording, order, theme, and source labels match the in-app result.

One-click Context Pack transfer is a copy/paste bridge, not an integration with private ChatGPT or Claude accounts. Source labels provide traceability, not a claim that every statement has been fact-checked. The project keeps the existing one-shot flow available as a baseline.

## Scope guard

For the course demo: English only; one assignment text; one PDF source; five slides; three layout families (title, content, comparison/conclusion); three preselected themes; text and simple shapes. No free-canvas positioning, animations, generated images, collaboration, automatic web research, or proof of factual truth. If time is tight, preserve the complete five-slide user journey before adding visual variety or extra controls.

## Who does what

| Workstream | Owner | Main task cards | Integration rule |
| --- | --- | --- | --- |
| Student experience | Developer A | M01, M03 UI, M05 | Uses the shared API types and mock responses from day 1. Owns `src/` only until integration. |
| Data and generation | Developer B | M02, M03 API, M04, M06 | Owns `app/` only until integration. Keeps old `/generate` working. |
| Shared contract and demo | A + B | M00, M07 | Agree on schemas before parallel changes; integrate daily. |
| Non-coding classmates | 1–3 volunteers | N01, N02 | Prepare a safe example, test the journey, record observations and help present it. No API keys needed. |

`M00` is the first task. Each task card has a difficulty score from 1 (beginner-friendly) to 5 (integration-heavy), a definition of done, and a prompt that can be pasted into a new chat. The cards are in `project-instructions/tasks/`. The proposed API and state model are in `CONTRACT.md`.

## Three-week sequence

| Time | Developers | Checkpoint |
| --- | --- | --- |
| Week 1, days 1–2 | M00 shared contract and local run; A starts M01; B starts M02 | Both can show a project created with assignment, Context Pack, and source metadata. |
| Week 1, days 3–5 | M03 outline API and editor | Five black-and-white slides can be edited and approved. Demo checkpoint 1. |
| Week 2 | B builds M04 progressive generation; A builds M05 slide editor with mock project data, then connects it | A ready slide can be edited while another is generating. Demo checkpoint 2. |
| Week 3, days 1–3 | B completes M06 export parity; A and B handle M07 integration | Five-slide editable PPTX round trip works. |
| Week 3, days 4–5 | Fix the highest-impact failures; classmates run N02; record demo | Rehearsed 3–5 minute demo and issue log. |

At the end of each day, merge only a working vertical slice. Do not let both developers independently rewrite `app/services/llm_service.py`, `app/services/render_service.py`, or `src/lib/api.ts` without agreeing on ownership. Use branches named `mvp/M00-contract`, `mvp/M01-intake`, and so on. Before merging, run the relevant local checks from the task card and show a short screen recording or screenshot of changed behavior.

## What to show the teacher

A live or recorded 3–5 minute journey: import the assignment/Context Pack/PDF; approve a corrected outline; start build; edit a ready block while another slide builds; regenerate one block; export and edit a text box in PowerPoint or LibreOffice Impress. Bring one slide that explains the innovation and one slide with what was implemented, what was deferred, and what five to eight student testers observed. The working app matters more than a long list of planned features.

## If the schedule slips

Freeze new features at the end of week 2. Keep the demonstration path with five slides. First reduce layouts to title + content + comparison; then reduce theme choices to two; then make source mapping manually selectable from the uploaded PDF. Never replace the progressive build and editable PPTX with a video that only simulates them. Do not spend the final week on dashboard, auth redesign, generated images, or animation.

## New-chat entry

Open the cloned folder `/home/alex/Desktop/Slide_Craft_AI` in the new chat. Paste the prompt in the assigned task card, or use `NEW_CHAT_PROMPT.md` for general continuation. Include the branch name and any issue observed. The new chat should read `AGENTS.md`, this file, `CONTRACT.md`, and the task card before editing.
