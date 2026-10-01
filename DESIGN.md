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
- Grayscale draft; selected slide and actions use the existing blue.
- Inspector controls stay outside the slide.

## Colors

The frontmatter preserves the HSL format from `src/index.css` and literal palette values from `DraftCanvas.tsx` and `slide-themes.ts`.

### Primary

Blue `primary` identifies main actions and selected slide borders. `ring` supplies keyboard focus. Selection uses a low opacity primary background.

### Secondary

`secondary` and `muted` are light neutral surfaces. Purple `accent` is an existing shell accent and the shared outline/ghost button hover color; it is not the grayscale slide accent.

### Neutral

`background` is the application field; `card` and `popover` are white surfaces. `foreground` carries primary text, `muted-foreground` carries supporting text, and `border`/`input` define dividers and fields. Sidebar tokens remain incumbent shell tokens.

`destructive` is used for errors. Success and warning fills have separate `-strong` values for text on light backgrounds, as specified in the stylesheet.

Draft colors belong to the artifact: white background, dark title, muted body, light panel, gray bars. The three accepted-content palettes are `clean_editorial`, `dark_tech_pitch`, and `infographic_bright`; their background, foreground, muted, accent, and panel tokens apply to slides when the project is ready. They do not recolor the surrounding editor. The stylesheet also defines `.dark` overrides; this document captures the reviewed light interface.

## Typography

Plus Jakarta Sans is the display and heading family; Inter is the body and control family, both with sans-serif fallbacks. The editor title uses the `editor-title` role. Supporting editor text uses the existing small and extra-small utility sizes; inspector input and textarea text is explicitly (13px).

The slide sizes type relative to its own width: regular titles (4.1cqw), cover titles (5cqw), body (2.8cqw), and source labels (1.25cqw). Title line height is (1.15); body line height is (1.4). A visual reduces body size to (2cqw). This same renderer supplies thumbnails, so miniature content follows the actual slide.

## Layout

The project page retains `AppHeader`, a centered container with (2rem) side padding, and an expandable materials section above the editor. The editor grid uses (180px / flexible / 300px) columns with (28px) gaps: thumbnail navigation, canvas, inspector. At desktop widths starting at (1200px), the rail and inspector have independent vertical overflow with maximum height `calc(100dvh - 265px)`.

At widths through (1199px), the grid becomes (130px / flexible), with (20px) gaps; the inspector moves under the canvas in column two. At widths through (640px), the editor stacks with (24px) gaps. The rail becomes horizontally scrollable, with thumbnails fixed to (140px); the selected thumbnail is centered automatically on selection and resize using immediate scroll behavior.

The artifact keeps a (16:9) aspect ratio, clips overflow, and uses (6%) internal padding. The inspector uses an external divider and (24px) left padding on the three-column layout. Content and Sources views control inspector density independently of the canvas.

## Elevation & Depth

The application uses borders, light surface contrast, and existing card/elevated shadows. The slide is a bordered flat rectangle; thumbnails use a border and subtle selection tint. Exact custom shadow values and motion definitions are recorded in the sidecar. Existing reveal and bar growth animations respect reduced motion; selected-thumbnail reveal does not animate.

## Shapes

Shared controls use the `md` radius; cards use `lg`. Thumbnails use their explicit radius. The canvas preserves square corners and its presentation proportions. Process diagrams use rectangular panels; bar comparisons use actual labels and numeric values.

## Components

### Buttons

Shared buttons retain primary, destructive, outline, secondary, ghost, and link variants. Default buttons are (40px) high with (8px 16px) padding; small buttons are (36px) high with (12px) horizontal padding. Primary hover reduces fill opacity to (90%); outline and ghost hover use the existing accent. Focus uses a (2px) ring and (2px) offset; disabled controls use (50%) opacity.

### Inputs / Fields

Inputs and textareas use a background-colored surface, input border, `md` radius, and (8px 12px) padding. Inputs are (40px) high; textarea minimum height is (80px). Focus follows the shared ring. Disabled fields lower opacity and show a disabled cursor. Inspector fields edit the selected ready title/body or source label.

### Cards / Containers

Shared cards use the card surface, border, `lg` radius, and small shadow. Header/content/footer spacing uses (24px), with the existing content/footer top-padding adjustment. The editor canvas is its own flat artifact surface rather than a shared card.

### Navigation

Each slide thumbnail is a native button with a real miniature, order/title, and generation status. Selected state has a primary border and low opacity primary fill; hover uses the muted surface. Keyboard focus uses an external ring. The rail changes direction on narrow screens, while the same selected state and real content remain visible.

### Draft canvas and inspector

The canvas renders title, body, comparison panels, process steps, bars, and source label from project content. Draft states use the grayscale palette; ready slides use the selected theme. Missing, interrupted, and arriving content have explicit placeholders or adjacent status messages. The separate inspector switches between Content and Sources; source excerpts stay suggestions until the user checks them.

## Do's and Don'ts

### Do:

- Do reuse the existing application color and typography tokens.
- Do render real slide text, process steps, bars, and source labels in both canvas and thumbnails.
- Do keep the selected thumbnail visible when the rail becomes horizontal.
- Do use success-strong and warning-strong for status text on light surfaces.

### Don't:

- Don't place editor controls inside the slide artifact.
- Don't treat a suggested excerpt or copied chart numbers as verified evidence.
- Don't apply a new identity to the existing application shell.

### Canvas selection and inspector space (T24)
Central canvas title, body, comparison columns and source label select/focus the corresponding inspector field; Enter/Space provide the same action. Hover/focus outlines mark editable elements without adding controls to the exported artifact. Thumbnail reorder arrows are sibling controls, visible on hover/focus and persistently visible for touch input, within the existing draft review phase. The desktop inspector is 340px, body fields use 12 rows, comparison fields stack, and source excerpts allow 320px of reading height. Unsaved block drafts survive switching inspector tabs for the selected slide.

### Guided revision and optional evidence footer (T25)
A labelled instruction field and explicit AI action sit below the selected canvas. They revise the selected title/text/visual while preserving other slides, and respect unsaved text edits. Sources live in the inspector; a per-slide checkbox opts into showing the footer, with the same setting in PPTX. Hidden source labels remain available in PowerPoint notes. Visual cover layouts use the available height for body and diagrams instead of cover margins.

### Loading and current completion controls (T26)
Clickable canvas elements use pointer cursors. Planning shows a reduced-motion-aware skeleton of the editor. Approve & style opens a finish panel without toggling it closed on repeated clicks; its prominent top-right Finish presentation action becomes full-width on mobile. The selected theme is retained. The current backend applies a palette; a substantive AI design pass is a separate required follow-up from the user.
