# Repeatable local course demo

This run uses fictional, team-authored material and needs no generation API key. The local outline and slides are editable drafts copied from the Context Pack; they are not AI-written. See [LOCAL_RUN.md](LOCAL_RUN.md) for installation and start commands.

## Prepare

1. Start the API and frontend using `LOCAL_RUN.md`. Open `http://127.0.0.1:8080/projects/new`.
2. Click **Load synthetic demo example**. Wait for the notice that the two-page PDF has been indexed. The assignment and Context Pack fields should be filled.
3. Choose **Dark tech pitch** and click **Save project**. A new project URL is created each time, so the demo is restartable without clearing the database.

## Six-step walkthrough

1. Show the saved assignment, Context Pack, attached PDF, and chosen theme.
2. Click **Create starter outline**. Explain that the five items come from labeled fields in the Context Pack and must be reviewed.
3. Edit a title or key message. Move one item. On **Pilot observations**, select a page 1 source excerpt; on **Workflow and trade-offs**, select a page 2 excerpt. Save, then approve the outline.
4. Click **Build five slides from outline**. Watch the counter rise while later slides remain queued. The local worker pauses briefly between slides so progress is visible.
5. Select a ready slide, edit its title or body, and save. Refresh to show the edit persists. **Reset from outline** can restore one edited block. It is a local reset, not model regeneration.
6. Download the draft PPTX. Open it in a presentation editor to show native text boxes, five slides in the approved order, and source labels `p. 1` and `p. 2` on the cited slides.

## Claims and limits to state aloud

- All campus figures are synthetic. The PDF says 1,000 inspected items per week and an observed incorrect-sorting share of 42% to 29% on page 1. It does not establish causation.
- Page 2 describes uncertain-item staff review, 18 minutes per day of review, and two hours per week of maintenance. Transfer to another campus is unverified.
- The conclusion must keep **“promising, not proven.”** Check that phrase before presenting.
- Without a generation API key, the demo cannot demonstrate model-authored content or model-backed regeneration. A classmate usability run and a recorded 3–5 minute walkthrough are still to be done.
