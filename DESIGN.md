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

Plus Jakarta Sans is the display and heading family; Inter is the body and control family, both with sans-serif fallbacks. The editor title uses the `editor-title` role. Supporting editor text uses the existing small and extra-small utility sizes; inspector input and textarea text is explicitly (13px).

The grayscale draft sizes type relative to its own width: regular titles (4.1cqw), cover titles (5cqw), body (2.8cqw), and source labels (1.25cqw). Title line height is (1.15); body line height is (1.4). A visual reduces body size to (2cqw). Structured drafts add independently editable section headings/text; legacy ungrouped drafts retain the existing body treatment. The same renderer supplies thumbnails, so miniature content follows the actual slide.

Designed slides use the shared native scene: Georgia titles for `clean_editorial`, Arial titles for the other two themes, and Arial for supporting text, values, labels, and source footers. Text sizes scale with artifact width in the browser and map to PowerPoint points from the same scene. Each composition assigns its own title/body hierarchy; the scene reduces size to fit an estimated line count. Browser line height and PowerPoint line spacing both use (1.16). The application shell retains its existing Plus Jakarta Sans and Inter roles. The quality renderer measures the scene with bundled Liberation equivalents for Arial/Georgia; the shared geometry does not imply identical browser or PowerPoint font metrics.

## Layout

The project page retains `AppHeader`, a centered container with (2rem) side padding, and an expandable materials section above the editor. The editor grid uses (180px / flexible / 300px) columns with (28px) gaps: thumbnail navigation, canvas, inspector. At desktop widths starting at (1200px), the rail and inspector have independent vertical overflow with maximum height `calc(100dvh - 265px)`.

At widths through (1199px), the grid becomes (130px / flexible), with (20px) gaps; the inspector moves under the canvas in column two. At widths through (640px), the editor stacks with (24px) gaps. The rail becomes horizontally scrollable, with thumbnails fixed to (140px); the selected thumbnail is centered automatically on selection and resize using immediate scroll behavior.

The artifact keeps a (16:9) aspect ratio and clips overflow. Grayscale content uses (6%) internal padding; designed scenes place native elements on a (100 × 56.25) coordinate field, shared by the central canvas, thumbnails, and PowerPoint export. The inspector uses an external divider and (24px) left padding on the three-column layout. Content and Sources views control inspector density independently of the canvas.

## Elevation & Depth

The application uses borders, light surface contrast, and existing card/elevated shadows. The slide is a bordered flat rectangle; thumbnails use a border and subtle selection tint. Exact custom shadow values and motion definitions are recorded in the sidecar. Existing reveal and bar growth animations respect reduced motion; selected-thumbnail reveal does not animate.

## Shapes

Shared controls use the `md` radius; cards use `lg`. Thumbnails use their explicit radius. The canvas preserves square corners and its presentation proportions. Process diagrams use rectangular panels; bar comparisons use actual labels and numeric values.

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

### Independent sections and rendered review (T29)
Slides carry one to four ordered sections, each with a stable id, heading, and its own text/data. New AI drafts return sections in the same content response. Older slides expose Organize slide sections in the header and Organize text into sections with AI in the inspector. Grouping preserves every accepted body word in order, with whitespace and comparison separators normalized for validation; the user reviews its headings and boundaries. Each section heading/text in draft and designed canvases targets its matching external inspector field by click or Enter/Space. Section edits save together and update the legacy body; a whole-body AI revision invalidates prior section bindings for renewed review.

Native geometry keeps each heading with its section text in ordered rows or columns. Longer sections receive more vertical room. Bar comparisons retain accepted labels/values/units beside their supporting sections; process visuals use connected panels above the supporting sections. Canvas, thumbnails, quality PNG and editable PowerPoint derive from the same scene, including section bindings. These are bounded native compositions, with the existing palette and typography.

The final pass composes, renders a (1280 × 720) PNG, measures text width/height and presentation type sizes, then asks the configured vision model to review hierarchy, spacing, chart crowding, clipping, and section separation. It can compare row/column fit locally before the vision call. A successful design needs both clear mechanical checks and approval with no actionable review findings. Measured body/section type below (18pt) and titles below (24pt) fail review. Findings stay internal and feed the next AI refinement; the editor shows only the candidate, concise progress, and a retry message when needed. There are at most three reviews and two AI refinements per slide. An unresolved result cannot become ready or export; accepted content and completed slides remain available.

The review is an implemented quality gate, with bounded coverage. Bundled Liberation font equivalents approximate Arial/Georgia in the PNG; actual PowerPoint rendering has not been visually checked. Shared themes and deck/previous-slide context coordinate the deck without a separate global AI art-direction call. Arbitrary AI canvas layouts and generated imagery remain beyond the current native composition scope; the review limit can leave difficult inputs retryable.

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
Clickable canvas elements use pointer cursors. Planning shows a reduced-motion-aware skeleton of the editor. Approve & style opens the finish panel without toggling it closed on repeated clicks. The panel retains the selected theme and explains that AI composes, checks a rendered preview, and refines each slide while preserving reviewed sections. Its prominent top-right Generate final slides with AI action becomes full-width on mobile. Starting design requires five completed content slides and no pending generation or unsaved title/body edits. Once all five designs are ready, the header shows Presentation and Download PowerPoint.

### Final slide artifacts and progress (T27)
The second AI pass uses six bounded native compositions, constrained by the reviewed family: hero with dominant title and accent side field; editorial with title/body split and divider; chart with accepted supporting text and labelled bars; process with explanatory text and two to four step panels; comparison with exactly two accepted body points in opposing panels; or statement with a large title and supporting text. Meaningful data graphics, title hierarchy, and whitespace distinguish the final artifact from the content draft. All families reuse the existing three palettes and native text/rectangles.

The header reports the actual completed design count, and the rail reports queued, generating, ready, or error for each slide. Whole candidates appear while actual rendered checks and refinements continue; ready means the quality gate passed. There is no simulated token or element streaming. The canvas and miniature both consume the same saved scene. Native scene text selects the corresponding external inspector field; section headings/text retain their id/field mapping, and legacy comparison columns retain their field mapping. The source visibility checkbox controls the visible footer in preview and export; hidden labels remain in PowerPoint notes.

### Design recovery and evidence limits (T27)
A failed design keeps accepted content and finished designs on other slides. Update this slide’s design retries the affected slide. If content or sections change during a call, the result is rejected as stale. Saving title/body or section edits later clears that slide’s design; unfinished or outdated designs must be updated before exporting a designed deck. The inspector can explicitly replace an AI design with a draft composition or remove its visual.

Chart validation requires two to four positive values present in both accepted body text and the supplied PDF excerpts; confirmed references are preferred, with suggested excerpts used when no confirmed references exist. This is provenance validation, not fact verification. Users must still check that the source supports the claim and that labels, units, and context are correct. Process visuals are bounded panels with structurally valid labels; their factual meaning still needs review.

The shared scene supplies browser positions, dimensions, colors, text, and fonts and creates native editable PowerPoint shapes/text boxes. Structural preview/export agreement does not certify PowerPoint application rendering or identical font metrics on another computer.

### Reviewed structure and fresh intake (T28)
The final pass retains reviewed covers as hero and comparisons as comparison. Existing bar or process visuals require chart or process respectively and preserve the exact accepted labels, values, and units; a slide without a visual remains without one. Ordinary text can use editorial or statement. Response and native export normalize older saved plans to these same constraints and remove inverse emphasis without a new provider call.

Start from scratch is an existing outline button alongside the intake title; it wraps beneath the title on narrow screens. It clears assignment/context, resets the theme to `clean_editorial`, removes the PDF reference/file selection and cached project used for retries, and saves a blank intake for reload when browser storage is available. A status message explains that previously created projects are kept. The button is disabled while upload, demo loading, or creation is active.

T28 established visual preservation and a consistent theme. T29 adds independently bound section headings/text and an automatic candidate render/check/critique/refinement pipeline, described in Components. The legacy body remains synchronized for compatibility; it no longer defines the only editing structure. Further composition freedom and generated imagery remain future work, and bounded review does not guarantee every input passes.
