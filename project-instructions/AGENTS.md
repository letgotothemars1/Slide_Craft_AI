# SlideCraft AI: context for a new coding chat

We are building a three-week course MVP with two developers and classmates who can help with research and testing. Read `project-instructions/START_HERE.md`, then `project-instructions/CONTRACT.md`, then the assigned file in `project-instructions/tasks/` before changing code.

The existing `/generate` flow is a working one-shot baseline. Keep it functional. Build the modular student journey as a separate project flow until the end-to-end demo is stable. Do not claim a feature is implemented merely because it is listed in the plan.

The demo must show: a master's student imports an assignment, a Context Pack from an existing AI conversation, and one public or synthetic PDF; approves and edits a black-and-white outline; sees five slides become ready one by one; edits a ready text block while another slide is building; regenerates only one block; selects/confirms a theme; exports a visually usable PPTX with editable text and shapes and inspectable source labels.

Use only public, synthetic, or team-authored materials for the course demo. Never commit API keys, uploaded student work, or `.env`. Keep technical scope narrow: English, one source PDF, three layout families, no free canvas, animation, image generation, collaboration, or autonomous fact checking for this MVP.

Each task card states its owner, dependencies, acceptance test, and paste-ready prompt. Work on a branch named `mvp/<task-id>-short-name`; one task per branch and pull request. Update the task card's status and evidence when finished. If a task needs a contract change, agree on `project-instructions/CONTRACT.md` first so frontend and backend stay compatible.
