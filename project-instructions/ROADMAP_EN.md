# SlideCraft AI MVP: a three-week roadmap

This roadmap shows the order of work and dependencies. It does not assign tasks to specific people: any next ticket can be taken as a separate task. Detailed acceptance checks for T00–T20 and C01–C04 are in `EXECUTION_BOARD.md`; the product scope is defined in `START_HERE.md` and `CONTRACT.md`. To continue in a new AI chat, provide the ticket number and these files.

## MVP goal

In one continuous journey, a user adds an assignment, a Context Pack, and one PDF; receives five plain black-and-white slide drafts; edits and approves them; sees finished slides become available one by one; edits one block while another slide is being generated; regenerates just one block; and exports a PPTX with editable text and shapes.

## Roadmap

| Stage and timing | Tasks in order | Working result at the end of the stage | Gate before moving on |
| --- | --- | --- | --- |
| **0. Foundation — days 1–2** | **T00** run the existing app and freeze the data contract; **C01** prepare a safe assignment, Context Pack, and two-page PDF. | The current one-shot flow runs; the team has one shared project fixture and realistic test material. | Do not build the screen and API against different data structures. |
| **1. Intake — days 2–4** | **T01** persist a project; **T02** build the intake screen; **T03** add a copyable instruction for the user's AI chat; **T04** retain PDF page numbers; **T05** connect PDF upload. | After a refresh, assignment, Context Pack, theme, and PDF remain separate and visible; a retrieved excerpt identifies its page. | Test project creation and an upload error using the C01 material. |
| **2. Draft — days 4–5** | **T06** generate a five-slide outline; **T07** display and edit it; **T08** save edits with revision checks; **T09** approve the outline and theme. | A user can change a title, reorder slides, refresh, and approve the corrected black-and-white draft. | **End-of-week-1 checkpoint.** If this does not work, do not move to visual polish. |
| **3. Progressive slides — days 6–8** | **T10** save each ready slide independently; **T11** generate one real slide at a time; **T12** display ready slides and queued/error states. | Slide 1 is usable while slide 5 is still queued; refreshing preserves progress. | Show actual build state, not a simulated progress animation. |
| **4. Local edits — days 8–10** | **T13** add an API for editing one block; **T14** add in-app editing; **T15** regenerate one block with stale-result protection; **T16** lock only that block in the UI. | An edit survives a refresh; regenerating a title does not change or lock the slide body. | **End-of-week-2 checkpoint.** Record a short screen capture and freeze feature scope. |
| **5. Final file — days 11–12** | **T17** build the PPTX from saved edits; **T18** add download and compare the file with the app. | Five slides have the approved order, theme, and sources; title and body text can be changed in PowerPoint or Impress. | Export must use accepted project state, including user edits. |
| **6. Testing and submission — days 13–15** | **T19** run the full journey without mocks; **C02** write the demo script; **C03** test with students; **C04** review content and sources; **T20** prepare a repeatable demonstration. | Someone outside the development work can follow written steps through to an editable PPTX; the team can show a 3–5 minute demo and state its limitations honestly. | Fix only failures in the journey and steps users find unclear. |

Tasks within a stage may overlap once the shared contract is frozen. Move to the next stage when the working result is demonstrated, not merely when the calendar says so. Critical dependency path: **T00 → T01/T04 → T06/T08 → T10/T11 → T13/T15 → T17 → T19/T20**.

## If time runs short

Preserve the complete user journey: materials → editable draft → slides appearing one by one → local edit → editable PPTX. First reduce layouts to two and themes to two; then allow manual selection of the PDF page for a source. Do not substitute UI animation for actual progressive generation. Slide animations, free positioning, image generation, collaboration, and new dashboards are outside this MVP.

## Continue in a new AI chat

Open `/home/alex/Desktop/Slide_Craft_AI` and paste:

> Take the next unfinished ticket **T__** from `project-instructions/ROADMAP_EN.md`. Read `AGENTS.md`, `project-instructions/START_HERE.md`, `project-instructions/CONTRACT.md`, `project-instructions/EXECUTION_BOARD.md`, and the relevant card in `project-instructions/tasks/`. First explain the current code path and dependencies, then complete only this ticket. Run the acceptance check from the board and briefly record what works, what remains, and how to reproduce the check. Keep the existing `/generate` flow working.

For C01–C04, use the same request with the relevant ticket number and add: “Explain everything without programming jargon; no code changes are needed.”
