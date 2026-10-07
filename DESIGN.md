---
name: SlideCraft AI
description: Existing light application shell with a live slide content editor.
colors:
  background: "hsl(220 20% 97%)"
  foreground: "hsl(222 47% 11%)"
  card: "hsl(0 0% 100%)"
  card-foreground: "hsl(222 47% 11%)"
  popover: "hsl(0 0% 100%)"
  popover-foreground: "hsl(222 47% 11%)"
  primary: "hsl(221 83% 53%)"
  primary-foreground: "hsl(0 0% 100%)"
  secondary: "hsl(220 14% 96%)"
  secondary-foreground: "hsl(222 47% 11%)"
  muted: "hsl(220 14% 96%)"
  muted-foreground: "hsl(220 9% 46%)"
  accent: "hsl(262 83% 58%)"
  accent-foreground: "hsl(0 0% 100%)"
  destructive: "hsl(0 84% 60%)"
  destructive-foreground: "hsl(0 0% 100%)"
  border: "hsl(220 13% 91%)"
  input: "hsl(220 13% 91%)"
  ring: "hsl(221 83% 53%)"
  success: "hsl(142 71% 45%)"
  success-foreground: "hsl(0 0% 100%)"
  success-strong: "hsl(142 71% 29%)"
  warning: "hsl(38 92% 50%)"
  warning-foreground: "hsl(0 0% 100%)"
  warning-strong: "hsl(38 92% 32%)"
  sidebar-background: "hsl(0 0% 98%)"
  sidebar-foreground: "hsl(240 5.3% 26.1%)"
  sidebar-primary: "hsl(240 5.9% 10%)"
  sidebar-primary-foreground: "hsl(0 0% 98%)"
  sidebar-accent: "hsl(240 4.8% 95.9%)"
  sidebar-accent-foreground: "hsl(240 5.9% 10%)"
  sidebar-border: "hsl(220 13% 91%)"
  sidebar-ring: "hsl(217.2 91.2% 59.8%)"
  draft-background: "#ffffff"
  draft-foreground: "#18181b"
  draft-muted: "#52525b"
  draft-panel: "#f4f4f5"
  draft-accent: "#71717a"
  clean-editorial-background: "#fffcf7"
  clean-editorial-foreground: "#111827"
  clean-editorial-muted: "#57534e"
  clean-editorial-accent: "#334155"
  clean-editorial-panel: "#ffffff"
  dark-tech-pitch-background: "#0b1020"
  dark-tech-pitch-foreground: "#f8fafc"
  dark-tech-pitch-muted: "#a3b2c8"
  dark-tech-pitch-accent: "#22c55e"
  dark-tech-pitch-panel: "#162238"
  infographic-bright-background: "#f0f9ff"
  infographic-bright-foreground: "#0f172a"
  infographic-bright-muted: "#0369a1"
  infographic-bright-accent: "#0ea5e9"
  infographic-bright-panel: "#ffffff"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, sans-serif"
  body:
    fontFamily: "Inter, sans-serif"
  editor-title:
    fontFamily: "Plus Jakarta Sans, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: "2rem"
  control:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: "1.25rem"
rounded:
  lg: "0.75rem"
  md: "calc(0.75rem - 2px)"
  sm: "calc(0.75rem - 4px)"
  thumbnail: "8px"
spacing:
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  5: "1.25rem"
  6: "1.5rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    typography: "{typography.control}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  button-outline:
    backgroundColor: "{colors.background}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "40px"
  input:
    backgroundColor: "{colors.background}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: "40px"
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.card-foreground}"
    rounded: "{rounded.lg}"
  draft-thumbnail:
    rounded: "{rounded.thumbnail}"
    padding: "6px"
---

# Design System: SlideCraft AI

## Overview

SlideCraft uses its existing light application shell: pale background, white surfaces, dark text, blue actions, and rounded controls. The live editor extends that system with a slide rail, central artifact, and external inspector. The approved editor structure does not establish a new brand identity.

**Key Characteristics:**

- Actual slide content in the canvas and thumbnails.
- Grayscale content draft followed by complete AI designs per slide; selected slide and actions use the existing blue.
- Inspector controls stay outside the slide.
- Final preview and editable PowerPoint share one native text-and-rectangle scene.
- Independent section headings/text stay together through design and automatic rendered review.

## Colors

The frontmatter preserves the HSL format from `src/index.css` and literal palette values from `DraftCanvas.tsx` and `slide-themes.ts`.

### Primary

Blue `primary` identifies main actions and selected slide borders. `ring` supplies keyboard focus. Selection uses a low opacity primary background.

### Secondary

`secondary` and `muted` are light neutral surfaces. Purple `accent` is an existing shell accent and the shared outline/ghost button hover color; it is not the grayscale slide accent.

### Neutral

`background` is the application field; `card` and `popover` are white surfaces. `foreground` carries primary text, `muted-foreground` carries supporting text, and `border`/`input` define dividers and fields. Sidebar tokens remain incumbent shell tokens.

`destructive` is used for errors. Success and warning fills have separate `-strong` values for text on light backgrounds, as specified in the stylesheet.

Draft colors belong to the artifact: white background, dark title, muted body, light panel, gray bars. The three accepted-content palettes are `clean_editorial`, `dark_tech_pitch`, and `infographic_bright`; their background, foreground, muted, accent, and panel tokens apply to each slide as its final design completes. T28 keeps the selected theme background on every slide; AI cannot invert it, and older saved inverse plans are normalized to quiet emphasis for preview and export. If accent contrast against that field is below (3:1), the scene uses existing muted theme ink instead; text on an accent panel uses whichever theme foreground/background provides greater contrast. These choices preserve the palette and do not recolor the surrounding editor. The stylesheet also defines `.dark` overrides; this document captures the reviewed light interface.

## Typography

Plus Jakarta Sans is the display and heading family; Inter is the body and control family, both with sans-serif fallbacks. The editor title uses the `editor-title` role. Supporting editor text uses the existing small and extra-small utility sizes; inspector input and textarea text is explicitly (14px).

The grayscale draft sizes type relative to its own width: regular titles (4.1cqw), cover titles (5cqw), body (2.8cqw), and source labels (1.25cqw). Title line height is (1.15); body line height is (1.4). A visual reduces body size to (2cqw). Structured drafts add independently editable section headings/text; legacy ungrouped drafts retain the existing body treatment. The same renderer supplies thumbnails, so miniature content follows the actual slide.

Designed slides use the shared native scene: Georgia titles for `clean_editorial`, Arial titles for the other two themes, and Arial for supporting text, values, labels, and source footers. Text sizes scale with artifact width in the browser and map to PowerPoint points from the same scene. Each composition assigns its own title/body hierarchy; the scene estimates natural word wrapping and reduces size to fit its box, preserving whole words in narrow title rails. Browser line height and PowerPoint line spacing both use (1.16). The application shell retains its existing Plus Jakarta Sans and Inter roles. The quality renderer measures the scene with bundled Liberation equivalents for Arial/Georgia; the shared geometry does not imply identical browser or PowerPoint font metrics.

## Layout

The project page retains `AppHeader`, a centered container with (2rem) side padding, and an expandable materials section above the editor. At desktop widths from (1200px), the grid uses (180px / flexible / 340px) columns with (28px) gaps: thumbnail navigation, slide, inspector. The rail, central area and inspector stick at (88px) within `calc(100dvh - 112px)`. The rail and inspector scroll independently. The central area is a column with a stationary slide above a separately scrolling controls region; options and retry actions do not pass beneath an overlapping canvas.

From (901px) through (1199px), the same three-column relationship uses (110px / flexible / 280px) with (16px) gaps. Through (900px), the editor stacks: horizontal thumbnail rail, selected slide, inspector, composition options, revision controls. Thumbnails keep their (140px) width and the selected thumbnail is centered automatically. The notes reading area has independent overflow capped at (40dvh) on these narrow screens; desktop notes use the inspector's independent scroll. The controls wrapper becomes display-contents through (900px), preserving the same stacked visual order.
The artifact keeps a (16:9) aspect ratio and clips overflow. Legacy grayscale content uses (6%) internal padding; selected native draft compositions and designed scenes place native elements on a (100 × 56.25) coordinate field, shared by the central canvas, thumbnails, and PowerPoint export. The inspector uses an external divider and (24px) left padding on the three-column layout. Content, Sources and Notes tabs control inspector density independently of the canvas.

## Elevation & Depth

The application uses borders, light surface contrast, and existing card/elevated shadows. The slide is a bordered flat rectangle; thumbnails use a border and subtle selection tint. Exact custom shadow values and motion definitions are recorded in the sidecar. Existing reveal and bar growth animations respect reduced motion; selected-thumbnail reveal does not animate.

## Shapes

Shared controls use the `md` radius; cards use `lg`. Thumbnails use their explicit radius. The canvas preserves square corners and its presentation proportions. Process diagrams use rectangular panels; bar comparisons use actual labels and numeric values. The shared native process renderer draws a fork for the narrow three-label accepted pattern with complementary “if confident” / “if uncertain” branches; ordinary process labels retain their sequential treatment. No labels or facts are invented.

## Components

### Buttons

Shared buttons retain primary, destructive, outline, secondary, ghost, and link variants. Default buttons are (40px) high with (8px 16px) padding; small buttons are (36px) high with (12px) horizontal padding. Primary hover reduces fill opacity to (90%); outline and ghost hover use the existing accent. Focus uses a (2px) ring and (2px) offset; disabled controls use (50%) opacity.

### Inputs / Fields

Inputs and textareas use a background-colored surface, input border, `md` radius, and (8px 12px) padding. Inputs are (40px) high; textarea minimum height is (80px). Focus follows the shared ring. Disabled fields lower opacity and show a disabled cursor. Inspector fields edit the selected ready title, section heading/text, ungrouped body, or source label. Section fields retain the existing field styling and save atomically with revision checks.

### Cards / Containers

Shared cards use the card surface, border, `lg` radius, and small shadow. Header/content/footer spacing uses (24px), with the existing content/footer top-padding adjustment. The editor canvas is its own flat artifact surface rather than a shared card.

### Navigation

Each slide thumbnail is a native button with a real miniature, order/title, and generation status. Selected state has a primary border and low opacity primary fill; hover uses the muted surface. Keyboard focus uses an external ring. The rail changes direction on narrow screens, while the same selected state and real content remain visible. During body/section/final design work, the active thumbnail keeps its actual miniature behind a noninteractive shimmer: an existing-token gradient sweeps across it every (1.7s), then stops when work completes. Reduced motion replaces the sweep with a static primary tint. The busy thumbnail reports Writing, Organizing, Revising, or Designing instead of Ready; its native button exposes busy state.

### Draft canvas and inspector

The canvas renders title, body, comparison panels, process steps, bars, and source label from project content. Content drafts use the grayscale palette; each saved whole design candidate renders its scene in the selected theme while checks/refinement continue; readiness follows successful review. Missing, interrupted, and arriving content have explicit placeholders or adjacent status messages. The separate inspector switches between Content and Sources; source excerpts stay suggestions until the user checks them.

### Independent sections and native compositions (T31)
Slides retain one to four ordered sections with stable ids, headings and text/data. The whole-deck outline precedes neutral streaming content; initial content calls include deck context and grounded speaker notes. Legacy grouping preserves accepted body words in order. Clicking or pressing Enter/Space on section text selects its external inspector field. Atomic section saves synchronize the legacy body; whole-body revision clears prior section bindings for renewed review.

Below the selected canvas, exactly three persisted previews show AI-proposed arrangements of the accepted slide content and notes: Recommended, Alternative and Out of the box. One provider response produces all three plans. The main canvas shows the selected member of those three, not an additional fourth option. Each option shows its content-specific label and explanation; the selected card says it is shown above. Before final styling all three previews remain grayscale. Key-free mode explicitly labels them as prepared arrangements. Old slides have an explicit Generate three variants action; normal new draft generation prepares alternatives after accepting the slide content. Loading and retry states retain accepted text.

Options preserve the incumbent border, rounded surface, primary selection tint, focus ring and disabled treatment; they form three columns from the small breakpoint and stack below it. Selection is revision guarded and persists across reload. Editing accepted text or notes invalidates its cached alternatives. The executor's balanced, feature, bands and poster starters remain bounded native tools within six reviewed layout families; AI can choose composition, arrangement, emphasis, focal section and bounded relative poster-title/feature-support widths. This is adaptive native geometry, not arbitrary canvas generation.
Native geometry retains section order and heading/text bindings. Text length controls band height, feature/support widths and compact cover proportions. The grounded native callout treatment also recognizes a verbatim percentage transition with a separate caveat and paired duration phrases within accepted semantic content; sample/page captions are copied from accepted wording, and the original sections remain visible. Exact eligible percent transitions and duration phrases can become native callouts above their complete accepted text, preserving spelling, units, qualifications and references without computing another statistic. The tested deck exposes 42% → 29% and the accepted 18 minutes per day / two hours per week, while giving its long Limits paragraph the wider column. These artifact treatments add no application color, typography or geometry token.

### Speaker notes and actual theme previews (T31)
The right inspector includes a Notes tab beside Content and Sources, so the slide and spoken explanation remain simultaneously visible on desktop. Notes initially appear as readable multiline text with a separate Edit speaker notes action. Editing uses the shared labelled textarea with eight rows and a (4000-character) limit plus Save and Discard actions. Unsaved notes remain protected across slide selection and block final styling until saved or discarded. Arrow keys, Home and End navigate the inspector tabs. Older slides explicitly say when no generated notes exist. On narrow screens the inspector follows the slide before the variants, with a separately scrollable notes area. Notes explain the claim and spoken transitions and export as native PowerPoint notes.

The Notes panel reports a current cached semantic-agreement check when available. AI mode distinguishes a checked result from content needing review. Template mode explicitly says the AI consistency check is unavailable.
Approve & style opens the existing finish panel with three radio theme examples rendered from the actual selected slide. They preserve the shared control borders, primary selected tint and keyboard ring. Theme browsing changes these examples, while the unfinished content draft remains neutral. Final candidates use the selected existing palette when saved; changing the artifact palette does not recolor the shell.

### Rendered review and deck coherence (T31)
AI analyses the whole story using assignment, context, slides and notes and selects validated native actions. Before final styling, a separate whole-deck semantic check compares accepted visible content with speaker notes, including numbers, units, qualifiers, support and missing critical visible content. Blocking findings stop final design and remain available for correction; this is a model judgment, not proof of factual truth. The check is cached only for the same accepted content. Final design uses the selected persisted variant as its starting plan, then performs at least one refinement and two visual reviews on every AI slide. Refinement can adapt the selected variant's arrangement and updates that member so its card matches the current main slide without creating a fourth alternative. The selected finished card uses a neutral final-design label with the current rationale, avoiding obsolete composition copy. A quality PNG is (1280 × 720); mechanical checks measure fit and reject body/section type below (18pt) and titles below (24pt). At most three reviews and two refinements run per slide. Final whole-deck review checks narrative coherence and may request one targeted repair per slide and one recheck. Detailed findings stay internal; the editor exposes saved candidates, progress and concise retry. An unresolved design cannot become ready or export.

Reviews judge numerical hierarchy and geometry that responds to content length as composition requirements, even when all text fits. They preserve exact visible text and distinguish spoken explanations from required on-screen content. Bundled Liberation equivalents approximate Arial/Georgia; browser, PNG and editable PowerPoint share scene geometry without implying identical application pixels. The final independent T31 verdict resolves the earlier numerical hierarchy, proportional geometry and review-contract findings from the five opened fixed LibreOffice renders. Bounded reviews and that tested deck do not guarantee every future input succeeds.

### Workflow progress and request count (T31)
The existing shell retains Plan, Content, Review, Design & check and Ready stages plus expandable Generation activity. Stages and actions are durable. New projects default to (60) logical model requests; previously stored explicit limits persist. The T31 base workflow used (29) and its bounded worst case used (50); T32 adds persisted alternative generation and a semantic agreement gate while removing a redundant candidate-selection request when a variant is selected. The current request cap remains authoritative; user regeneration consumes the remainder. Variant generation, semantic agreement, story/design planning, per-slide/deck reviews and refinements count alongside content and manual AI revision/grouping. Local inspection, composition execution, rendering, checks and export do not; transport retries, PDF embeddings, legacy endpoints and `/generate` are outside the staged counter. Returned usage is recorded when available, and missing usage stays unknown; the counter is not billing.

Key-free template draft/final design use native compositions and mechanical PNG checks without model calls or claimed vision review. Explicit manual AI actions are counted. The T31 synthetic provider run recorded (39) logical requests and returned (135,336) input/(58,760) output tokens, including reasoning output where returned. Its final rendered-deck recheck and independent native review cover the inspected run. No generated raster assets ship.

## Do's and Don'ts

### Do:

- Do reuse the existing application color and typography tokens.
- Do render real slide text, process steps, bars, and source labels in both canvas and thumbnails.
- Do keep the selected thumbnail visible when the rail becomes horizontal.
- Do use success-strong and warning-strong for status text on light surfaces.
- Do preserve section heading/text bindings and accepted visuals through automatic design refinement.
- Do keep measured and model critique internal; show the candidate, progress, and concise retry controls.

### Don't:

- Don't place editor controls inside the slide artifact.
- Don't treat a suggested excerpt or copied chart numbers as verified evidence.
- Don't apply a new identity to the existing application shell.
- Don't mark an unresolved quality candidate ready or export it.
- Don't equate rendered model approval with factual source verification or verified PowerPoint pixels.

### Canvas selection and inspector space (T24)
Central canvas title, body, comparison columns and source label select/focus the corresponding inspector field; Enter/Space provide the same action. Hover/focus outlines mark editable elements without adding controls to the exported artifact. Thumbnail reorder arrows are sibling controls, visible on hover/focus and persistently visible for touch input, within the existing draft review phase. The desktop inspector is 340px, body fields use 12 rows, comparison fields stack, and source excerpts allow 320px of reading height. Unsaved block drafts survive switching inspector tabs for the selected slide.

### Guided revision and optional evidence footer (T25)
A labelled instruction field and explicit AI action sit below the selected canvas. They revise the selected title/text/visual while preserving other slides, and respect unsaved text edits. Sources live in the inspector; a per-slide checkbox opts into showing the footer, with the same setting in PPTX. Hidden source labels remain available in PowerPoint notes. Visual cover layouts use the available height for body and diagrams instead of cover margins.

### Loading and completion controls (T26–T27)
Clickable canvas elements use pointer cursors. Planning shows a reduced-motion-aware skeleton of the editor. Approve & style opens the finish panel without toggling it closed on repeated clicks. The panel retains the selected theme and explains that AI composes, checks a rendered preview, and refines each slide while preserving reviewed sections. Its prominent top-right Generate final slides with AI action becomes full-width on mobile. Starting design requires five completed content slides and no pending generation or unsaved text/section/note edits. Once all five designs are ready, the header shows Presentation and Download PowerPoint.

### Final slide artifacts and progress (T27)
The second AI pass uses six bounded native compositions, constrained by the reviewed family: hero with dominant title and accent side field; editorial with title/body split and divider; chart with accepted supporting text and labelled bars; process with explanatory text and two to four step panels; comparison with exactly two accepted body points in opposing panels; or statement with a large title and supporting text. Meaningful data graphics, title hierarchy, and whitespace distinguish the final artifact from the content draft. All families reuse the existing three palettes and native text/rectangles.

The header reports the actual completed design count, and the rail reports queued, generating, ready, or error for each slide. Whole candidates appear while actual rendered checks and refinements continue; ready means the quality gate passed. There is no simulated token or element streaming. The canvas and miniature both consume the same saved scene. Native scene text selects the corresponding external inspector field; section headings/text retain their id/field mapping, and legacy comparison columns retain their field mapping. The source visibility checkbox controls the visible footer in preview and export; hidden labels remain in PowerPoint notes.

### Design recovery and evidence limits (T27)
A failed design keeps accepted content and finished designs on other slides. Update this slide’s design retries the affected slide. If content or sections change during a call, the result is rejected as stale. Saving title/body or section edits later clears that slide’s design; unfinished or outdated designs must be updated before exporting a designed deck. The inspector can explicitly replace an AI design with a draft composition or remove its visual.

Chart validation requires two to four positive values present in both accepted body text and the supplied PDF excerpts; confirmed references are preferred, with suggested excerpts used when no confirmed references exist. This is provenance validation, not fact verification. Users must still check that the source supports the claim and that labels, units, and context are correct. Process visuals are bounded panels with structurally valid labels; their factual meaning still needs review.

The shared scene supplies browser positions, dimensions, colors, text, and fonts and creates native editable PowerPoint shapes/text boxes. Structural preview/export agreement does not certify PowerPoint application rendering or identical font metrics on another computer.

### Reviewed structure and fresh intake (T28)
The final pass retains reviewed covers as hero and comparisons as comparison. Existing bar or process visuals require chart or process respectively and preserve the exact accepted labels, values, and units; a slide without an accepted chart/process does not gain invented visual data; exact eligible accepted numerical phrases may receive typographic callouts. Ordinary text can use editorial or statement. Response and native export normalize older saved plans to these same constraints and remove inverse emphasis without a new provider call.

The intake has no initial theme selector and ignores legacy stored theme values for new creation. Start from scratch is an existing outline button alongside the intake title; it wraps beneath the title on narrow screens. It clears assignment/context, removes the PDF reference/file selection and cached project used for retries, and saves a blank intake for reload when browser storage is available. A status message explains that previously created projects are kept. The button is disabled while upload, demo loading, or creation is active.

T32 retains accepted visible text, notes, section bindings, visual data and consistent themes through persisted AI variants, a separate semantic-agreement gate, story planning, mandatory refinement and final deck review. The four native arrangements remain bounded by reviewed families. Arbitrary canvas composition and generated imagery remain future work; difficult inputs can remain retryable.
