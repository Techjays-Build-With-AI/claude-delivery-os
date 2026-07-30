# Techjays deck — design system

The full visual specification. Every value here is what produced the reference deck.
Coordinates assume a 13.33" × 7.5" widescreen canvas (`LAYOUT_WIDE`).

## Table of contents
- [1. Feel in one paragraph](#1-feel-in-one-paragraph)
- [2. Colour tokens](#2-colour-tokens)
- [3. Type](#3-type)
- [4. Geometry / margins](#4-geometry--margins)
- [5. Every-page furniture (watermark + footer)](#5-every-page-furniture)
- [6. Slide patterns](#6-slide-patterns)
- [7. Logos & co-branding](#7-logos--co-branding)
- [8. Do / Don't](#8-do--dont)

---

## 1. Feel in one paragraph
Editorial, calm, and confident — closer to a design studio's one-pager than a corporate
template. Pure white content pages, oversized bold grotesque headlines, and lots of
whitespace. The only recurring "decoration" is a very faint brand mark bleeding off one
corner. Colour is used sparingly and with intent: one brand colour dominates, two
supporting colours appear only on small marks (index numbers, ticks, bars). Small
small labels are set UPPERCASE and letter-spaced to create editorial contrast with the
big headlines (all in one typeface — see §3).
No cards, no drop shadows on content, no gradient fills, **no accent stripes or
underlines under titles** (those read as generic/AI-made).

## 2. Colour tokens
```
INK    #141414   near-black — headlines & body
LBL    #424B5B   dark slate — SMALL LABELS / SUBTEXT (KPI labels, eyebrows, captions)
MUT    #6B7280   muted grey — secondary body copy, descriptions
FAINT  #9AA0AA   faint grey — only truly incidental marks
LINE   #E7E7EC   hairlines & dividers
WHITE  #FFFFFF   content background
DARK   #141B2E   background for separator slides only
```
Legibility rule for small text (learned the hard way): grey micro-labels on white are
hard to read. Any small label / eyebrow / caption uses **LBL**, not MUT/FAINT, at
**≥11.5pt**, and semibold where it's a standalone label (KPI labels, week tags, section
labels like "What's Included"). Reserve MUT for longer secondary copy and FAINT for
almost nothing. On dark separator slides, small text goes light (`#8A93A8`–`#B7C0D4`).
Accent trio (max three; brand first, two supporting):
```
C1  #6870F8  indigo/periwinkle — PRIMARY brand (techjays). Dominant accent.
C2  #E3A03C  mild amber        — supporting, used sparingly
C3  #1FA98A  teal              — supporting, used sparingly
```
Light tints (for Gantt QA segments / soft fills only):
```
C1L #C3C7FB   light indigo
C3L #AEE4D7   light teal
SG  #9098A6   neutral grey (setup / launch bars)
```
Accent discipline: the brand colour (C1) carries most accents. C2/C3 appear only where
you are **coding distinct items** — e.g. module 01 vs 02, or the four timeline steps
cycling `[C1, C2, C3]`. Never colour body text; never give all colours equal weight.

## 3. Type
**One typeface for everything** — headlines, body, and every label. The Techjays
default is **Google Sans**:
```
FONT = "Google Sans"   // set once (CFG.font); used for headlines, body AND labels
```
Earlier versions paired Arial headlines with a Roboto Mono label font for editorial
contrast; that was retired in favour of a single unified font. The eyebrow/label
"micro" feel now comes from styling, not a different family: UPPERCASE, letter-spacing
(charSpacing ~0.3–1.6), semibold, in LBL — not from monospace.

Font caveat (important): **Google Sans is a proprietary Google font.** It renders
correctly only where installed, and is **not** in the Google Slides font picker, so a
Slides import substitutes it. It also can't be legally embedded/downloaded here. So:
- If the deck is presented from a machine that has Google Sans → use it as-is.
- If it must look identical everywhere (incl. Google Slides) → set `CFG.font` to
  **"Poppins"** (a close, freely available geometric match, in the Slides picker) or
  **"Arial"** (universal, renders true). Confirm the target with the user.

Sizes (pt):
```
Cover headline        52–62 bold
Section headline      32–36 bold
Separator headline    48–54 bold
Module/stat number    30–40 bold
Big money/number      54–60 bold
KPI number            34 bold
Body / description    13.5–17
Eyebrow / label       11.5–14 in LBL, semibold for standalone labels (charSpacing ~0.3–1.6)
Footer                9.5 in a mid grey (#7A828E)
```
The `mono(...)` helper in the generator is just the label helper — despite the name it
renders in the single deck font, not a monospace family.
Headlines are often two lines set with tight `lineSpacing` (≈ fontSize + 2..6).
Titles are left-aligned, never centered. Body is always left-aligned.

## 4. Geometry / margins
```
W = 13.33   H = 7.5
LX = 0.75   (left margin / content start x)
RX = 12.58  (right margin / content end x)
CW = 11.83  (content width)
```
Keep ≥0.5" from every edge. Section headline baseline sits around y≈1.5.
Footer lives at y≈7.02.

## 5. Every-page furniture

### Bird watermark (brand presence, very mild)
A single brand "bird" mark bleeds off the **top-right** corner of every page, extremely
faint so it never competes with text.
```
white pages: bird.png        at x 11.25, y −0.62, w 3.1, h 2.816, transparency 90
dark pages:  bird_white.png   same box, transparency 90
```
(w:h ratio of the bird is 1.101.) transparency 90 = ~10% opacity. It's meant to be
noticed only if you look for it.

### Confidential footer (every page)
Small brand mark + one mono line, bottom-left:
```
mark:  bird.png (white pages) / bird_white.png (dark) at x LX, y 7.06, w 0.17, h 0.154
text:  9.5pt, "Confidential    ·    <VENDOR> × <CLIENT>"
       colour #7A828E on white pages, #8891A6 on dark pages, at x LX+0.28, y 7.02
```
Bake both the watermark and the footer into the slide-creation helper so they appear on
every page automatically.

## 6. Slide patterns

### topbar (content pages)
Section label top-left + page marker top-right, both mono:
```
label : 13pt INK, charSpacing 0.8, at (LX, 0.6)
marker: 11.5pt MUT, right-aligned, at (RX-4, 0.62)  e.g. "02  /  06"
```
Appendix pages use a marker like `"APPENDIX  ·  A1 / A3"`.

### Cover (white)
Vendor logo top-left; if co-branding, a thin vertical divider (`D3D8E0`, ~0.31" tall)
then the client logo. Date top-right in mono. A mono eyebrow in the brand colour
(`90-DAY ENGAGEMENT · VENDOR × CLIENT`) sits above a huge two-line headline in the lower
-left third. No arrow, no graphic — the corner watermark is the only motif.

### Executive summary (white)
`topbar` → 2-line bold headline (36pt) → one tight lead paragraph (15.5pt MUT, key
phrases bolded in C1) → a full-width hairline → a KPI row of 4:
each KPI = big number (34pt INK) with a small **colour-coded square** (cycling
`[C1,C2,C3]`) beside a mono label under it.

### Solution summary (white) — the "at a glance" module slide
Two borderless columns split by a vertical hairline. Each column:
big index number in the module's colour (01 = C1, 02 = C3), module name (22pt INK),
a one-line tagline (INK), a 2–3 line summary (MUT), and a mono efficiency badge in the
module colour (e.g. `4–5× FASTER THAN TODAY`). A faint mono note under the title says
"At a glance — full detail in the appendix". **Detailed bullets do NOT live here** — they
live in the appendix.

### Timeline — high level (white)
Section headline (e.g. "Go live in 12 weeks") → a row of 4 phase blocks connected by a
hairline. Each phase: a small colour square + big index number (cycling `[C1,C2,C3]`),
a mono week tag, a bold title, a short description. A mono caveat line can sit at the
bottom.

### Investment (white)
Left block: giant money figure (60pt, C1) + two mono lines (price cadence, timeline
flow). A hairline, then a secondary big number (e.g. hours returned) with a mono label
in C3. Right block, split by a vertical hairline: a mono "What's Included" label and 3
colour-cycled bullets. Keep it borderless.

### Closing / call-to-action (white)
Vendor logo top-left, mono eyebrow in C1 ("LET'S BEGIN"), a big decisive two-line
headline, one self-contained supporting sentence. Decisive, not dependent on prior
slides.

### Separator slides (DARK) — how you signal a section change
Background `DARK`. This dark↔light flip is the cleanest possible "a new section starts
here" signal. Two uses:
- **Appendix divider:** a small mono kicker `END OF CORE DECK · PAGES 1–N` (colour
  `7E8BA6`), then `APPENDIX` in light indigo `9AA6FF`, then a big white headline, then a
  mono line listing what's inside. White bird watermark, light footer.
- **Thank-you:** white-wordmark logo (`logo_white.png`), a big white "Thank you.", one
  short mono line. Minimal.

### Appendix — module detail (white)
`topbar` "Module scope" + marker "APPENDIX · A#/A#". Coloured index + module name
headline. Two columns split by a hairline: **WHAT WE BUILD** (left) and
**WHAT <CLIENT> GETS** (right), each a mono mini-label in the module colour over a list
of rows. Each row = a small coloured square + **bold lead — muted description** (one
`addText` with two runs). Optional faint mono footnote for caveats.

### Appendix — Gantt (white) — the right way to show a timeline breakdown
A true Gantt beats a text list. Geometry:
```
chart x start gx = 4.35 (task labels occupy LX..gx-0.15, right-aligned, 11pt INK)
chart width = RX - gx, split into 12 (or N) week columns
faint vertical gridlines "F0F1F5" per column; week numbers on top in LBL semibold
row pitch ≈ 0.33, bar height ≈ 0.19, rounded rects (rectRadius 0.03)
```
Each task row draws a **build bar** in its workstream colour spanning its week range,
plus an optional lighter **QA segment** (one column, light tint) at the end. Colour bars
by workstream (e.g. Intake = C1, Mission Control = C3, setup/launch = SG/C2). Add a
small legend beneath: coloured squares + labels for each workstream and "QA".

## 7. Logos & co-branding
- Vendor (techjays) assets are bundled in `assets/`: `logo.png` (dark wordmark, for
  white pages), `logo_white.png` (white wordmark, for dark pages), `bird.png` (brand
  mark), `bird_white.png` (mark for dark pages).
- **Client logo:** this environment can't download images from the web. Get the client
  logo from a file the user provides or from an existing asset (e.g. a prior PDF/deck) —
  extract with `pdfimages`, crop, and drop the background to transparent. Beware colour:
  a white-on-transparent client logo is invisible on white pages — crop a version whose
  mark is a dark/brand colour, or place it on a small white chip on dark pages.
- Co-brand lockup on the cover: `vendor logo | client logo` separated by a thin vertical
  divider, vertically centered, top-left.

## 8. Do / Don't
Do: whitespace, one dominant accent, dark legible uppercase micro-labels, borderless layouts, dark
separators, a faint corner watermark, a confidential footer on every page, decisive
to-the-point headlines.
Don't: centered body text, accent stripes/edge bars, underlines beneath titles, drop
shadows on content blocks, gradient fills, more than three accent colours, cramming
detail onto core slides (push it to the appendix), emoji/dingbat arrows as motifs.
