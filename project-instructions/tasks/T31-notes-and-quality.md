# T31 — Talk track, composition choices and deliberate design

## User goal
The first draft must connect what appears on each slide with what the presenter says. Every slide offers three previews using its actual content, including an unconventional alternative. Final design prioritizes quality through story analysis, candidate comparison and mandatory refinement rather than accepting the first readable layout.

## Implementation
- Speaker notes generated in the same first content request, editable separately and exported as native PowerPoint notes.
- Three native composition previews: balanced, bands and asymmetric poster. Selection persists, invalidates the previous final design and guides later model passes. Draft preview remains grayscale.
- Theme selection previews the actual selected slide; palette changes occur only at final design approval.
- Whole-deck analysis includes assignment, context, all slides and notes. Three candidates are rendered and compared; every AI slide receives at least one refinement and two visual reviews. Final deck coherence review may request bounded targeted repairs.
- Verified GPT-5.4/base/mini/nano final quality calls request high reasoning effort without temperature. Other models preserve existing provider options. Fast content generation remains unchanged.
- Exact approved title, sections, visuals and notes are preserved during styling. Model findings remain internal. Unapproved results cannot become ready.

## Constraints
Four native editable composition families remain a quality ceiling. More model calls cannot invent approved missing evidence or guarantee an attractive presentation. No generated pictures or arbitrary HTML slide designs. New projects have a logical request budget of 60; existing explicitly stored limits are preserved. Transport retries and PDF embeddings are outside it. The five-slide base workflow uses 29 calls; the bounded worst case uses 50 (three reviews per slide, one deck-driven repair per slide, then one final deck recheck). Additional user regeneration shares the remaining budget.

## Verification
- Backend: 81 tests passed; frontend: 35 tests passed. TypeScript, production build and whitespace checks passed. Existing bundle-size/Browserslist notices remain.
- Actual provider E2E on a synthetic campus case: five ready slides, preserved accepted content and preferred poster, 39 logical calls including retries and the final rendered-deck recheck, 135,336 returned input and 58,760 output tokens. This includes reasoning output where returned by the provider. An initial section mismatch and overly strict notes-to-screen review were found and fixed before the successful targeted retry.
- Browser: actual choices, persistence across reload, notes edit/save and unsaved protection; template final design, real content theme previews; desktop and mobile inspected.
- Native export: five editable slides; exact accepted titles, section text/headings and speaker notes (plus source metadata); all five pages opened and visually inspected through LibreOffice PDF conversion. Browser download manager was not independently verified.
- Evidence in `.impeccable/review/T31/`. Functional passing does not establish general presentation quality. Final independent review recorded separately. No credential file was read.

## Independent visual corrections
The first review accepted the UI but rejected native output: numbers were buried in prose, the cover panel dominated, and Limits was too narrow. The native executor now creates exact accepted percent transitions and duration callouts without computing new statistics, scales compact cover proportions and allocates feature columns using actual text length. All accepted text remains editable and intact. Review prompts assess numerical discoverability and content-dependent geometry. A real model's final whole-deck recheck accepted the revised renderer; native five-slide export was re-rendered in LibreOffice. Final independent verdict is in `verdict.md`.
The old synthetic verification fixture explicitly used the new 60-call ceiling for this final check; other stored earlier limits remain unchanged. No user project or production record was migrated.
