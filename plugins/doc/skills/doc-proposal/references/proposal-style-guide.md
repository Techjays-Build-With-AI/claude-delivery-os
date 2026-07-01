# Techjays Proposal Style Guide

A reusable design system for single-file HTML client proposals. Derived from `docs/ValleyRAA/valleyraa-techjays-proposal.html`, which remains the canonical reference implementation.

**Use it like this:** start a new proposal by copying the `<style>` block from the [Full stylesheet](#9-full-stylesheet) section below into a fresh HTML file, paste in the `<symbol id="tj-logo">` block, then assemble the deck from the component snippets in [§ 4 Components](#4-components). Proposals stay single-file, offline-portable, and print-ready — no shared CSS, no webfont fetch, no build step.

This guide is the **proposal** counterpart to `STYLE_GUIDE_old.md` (which covers status reports). The two artifacts share a sensibility — tokens-first, print-as-first-class, semantic color — but the proposal system is deck-shaped: every section is a 100vh snap-scrolled slide that doubles as a printed page.

---

## Table of contents

1. [Principles](#1-principles)
2. [Foundations](#2-foundations) — tokens, type, slide & container
3. [Layout primitives](#3-layout-primitives) — slide system, persistent UI, section header, grids
4. [Components](#4-components)
5. [Interaction patterns](#5-interaction-patterns)
6. [Responsive rules](#6-responsive-rules)
7. [Print rules](#7-print-rules)
8. [Content & flow conventions](#8-content--flow-conventions)
9. [Full stylesheet](#9-full-stylesheet)

---

## 1. Principles

- **Single file, offline-portable.** One `.html` with inline CSS, inline JS, and inline SVG symbols. No external stylesheets, no webfont fetch, no CDN — the file must read fine from an email attachment with the network unplugged.
- **Tokens before values.** Color, radius, and shadow flow from CSS custom properties on `:root`. Re-skin a whole deck by overriding tokens; never hand-roll a hex inline.
- **Color is semantic.** Navy = authority and structure. Teal = forward action, links, solutions, "what we'll do". Coral = emphasis, "what's wrong today", problems. The coral↔teal binding is consistent across every two-sided component (today/tomorrow, track 1/track 2, pilot A/pilot B, metrics/ops). Don't flip it for variety.
- **Deck format is the contract.** Each section is a full viewport (`min-height: 100vh`) and snaps on scroll. Sections are read one-screen-at-a-time, optimized for live walkthrough *and* PDF export.
- **Fluid type scales.** Headings use `clamp(min, vw, max)` so the same HTML reads well from laptop to projector without breakpoint juggling.
- **Print is a first-class view.** Dark slides invert to white; accent colors are preserved with `!important`; `page-break-after: always`; `@page { margin: 0; }`. The on-screen deck and the printed PDF use the same source markup.
- **Tabular numbers everywhere figures live** — stats (`.stat-num`), comparison tables, slide counters, week labels. `font-variant-numeric: tabular-nums` keeps columns aligned.
- **Emphasis via color + weight, not slant.** `<em>` is restyled to non-italic, weight 600, coral (or teal-300 on dark). Do not undo this with `font-style: italic`.

---

## 2. Foundations

### 2.1 Design tokens

Defined on `:root`. Reference: `docs/ValleyRAA/valleyraa-techjays-proposal.html:12–36`.

| Token | Value | Role |
|---|---|---|
| `--navy-900` | `#0B2545` | Default heading color, UI text, deep gradient stop |
| `--navy-700` | `#13315C` | Lighter navy, gradient stop, `.tracks-foot` accent |
| `--navy-500` | `#1E4D8B` | Mid-tone navy (rarely used) |
| `--white` | `#FFFFFF` | Default slide background, card background |
| `--paper` | `#F7F9FC` | `.slide.alt` background, comparison thead, layer-pill |
| `--paper-2` | `#EEF2F8` | Chip background, layer-icon, sources-line code pill |
| `--teal-500` | `#1AC0C6` | Primary accent — links, CTAs, eyebrow, Track 2 / Pilot B / solutions |
| `--teal-300` | `#7FE0E3` | Light teal — eyebrow on dark, pilot B badge border, attribution-tag |
| `--coral-500` | `#F26B5B` | Secondary accent — `<em>` emphasis, Track 1 / Pilot A / problems |
| `--coral-300` | `#FAA89E` | Light coral — pilot A badge border |
| `--slate-900` | `#111827` | Print-mode body text |
| `--slate-700` | `#374151` | Default body text |
| `--slate-600` | `#6B7280` | Secondary text, labels, audience lines |
| `--slate-400` | `#9CA3AF` | Muted dot bullets, slide-num |
| `--slate-300` | `#D1D5DB` | "Today" column border, print borders |
| `--slate-200` | `#E5E7EB` | Default 1px hairline |
| `--slate-100` | `#F3F4F6` | Almost white (rare) |
| `--shadow-sm` | `0 1px 2px rgba(11,37,69,.06)` | Default card depth |
| `--shadow-md` | `0 8px 24px rgba(11,37,69,.08)` | Lifted cards (reserved) |
| `--shadow-lg` | `0 20px 60px rgba(11,37,69,.14)` | Heavy elevation (reserved) |
| `--radius-sm` | `6px` | Inputs, small pills, code pills |
| `--radius` | `10px` | Layer cards, chips' container, metric-cards |
| `--radius-lg` | `18px` | `.card`, `.track`, `.pilot-card`, `.split-card` |

```css
:root{
  --navy-900:#0B2545;
  --navy-700:#13315C;
  --navy-500:#1E4D8B;
  --white:#FFFFFF;
  --paper:#F7F9FC;
  --paper-2:#EEF2F8;
  --teal-500:#1AC0C6;
  --teal-300:#7FE0E3;
  --coral-500:#F26B5B;
  --coral-300:#FAA89E;
  --slate-900:#111827;
  --slate-700:#374151;
  --slate-600:#6B7280;
  --slate-400:#9CA3AF;
  --slate-300:#D1D5DB;
  --slate-200:#E5E7EB;
  --slate-100:#F3F4F6;
  --shadow-sm:0 1px 2px rgba(11,37,69,.06);
  --shadow-md:0 8px 24px rgba(11,37,69,.08);
  --shadow-lg:0 20px 60px rgba(11,37,69,.14);
  --radius-sm:6px;
  --radius:10px;
  --radius-lg:18px;
}
```

### 2.2 Typography

**Primary stack** — Inter (with Inter Variable if installed) and an exhaustive system fallback. No webfont download.

```css
font-family: 'Inter', 'InterVariable', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
font-feature-settings: 'cv02','cv03','cv04','cv11';
```

The `font-feature-settings` enables Inter's stylistic alternates for slightly tighter, more proposal-appropriate letterforms. Keep this on.

**Body defaults**

```css
body{
  font-size: 17px;
  line-height: 1.6;
  color: var(--slate-700);
  background: var(--white);
}
html{
  scroll-behavior: smooth;
  scroll-snap-type: y mandatory;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

**Headings (h1–h4)** are colored navy-900, tracked tight (`-0.018em`), and use line-height 1.15. `h1` adds `letter-spacing: -0.025em` and weight 700; `h3` drops to weight 600.

**Inline elements**

| Element | Treatment |
|---|---|
| `<strong>` | `color: var(--navy-900); font-weight: 600;` |
| `<em>` | **Not italic.** `color: var(--coral-500); font-weight: 600;` on light, `var(--teal-300)` on dark. Emphasis via color + weight is a deliberate house rule — write `<em>weeks</em>` to land the idea in coral. |
| `<a>` | `color: var(--teal-500); text-decoration: none;`, underline on hover only. |
| `<ul>`, `<ol>` | Fully reset (`list-style: none; padding: 0; margin: 0`). Every list re-applies its own bullets via `::before` or inline `<svg>` icons. |

**Monospace** — used only inside `.sources-line code`, and intentionally **kept as Inter** to match the surrounding text:

```css
.sources-line code { font-family: 'Inter', inherit; }
```

If you do need a true monospace block somewhere (rare for proposals), fall back to the report-guide stack: `'JetBrains Mono', Menlo, Monaco, Consolas, monospace`.

### 2.3 Type scale

| Role | Class / selector | Size | Weight | Tracking | Notes |
|---|---|---|---|---|---|
| Hero title (dark) | `.hero-title` | `clamp(2.6rem, 6.4vw, 5.4rem)` | 700 | `-0.03em` | line-height 1, white on navy gradient |
| Hero alt headline | `.h-hero` | `clamp(2.6rem, 5.6vw, 4.6rem)` | 700 | `-0.028em` | line-height 1.05 |
| Section heading | `.h-section` | `clamp(1.85rem, 3.4vw, 2.85rem)` | 700 | inherits `-0.018em` | margin-bottom 1.4rem |
| Hero sub | `.hero-sub` | `clamp(1.1rem, 1.6vw, 1.45rem)` | 400 | — | `max-width: 780px`, line-height 1.5, `#C9D3E0` |
| Lede | `.lede` | `clamp(1.05rem, 1.4vw, 1.25rem)` | 400 | — | `max-width: 820px`, line-height 1.55 |
| Pullquote | `.pullquote` | `clamp(1.5rem, 2.6vw, 2.2rem)` | 500 | `-0.012em` | line-height 1.35 |
| Closing quote | `.closing-quote` | `clamp(1.6rem, 2.8vw, 2.4rem)` | 500 | `-0.012em` | line-height 1.3 |
| Stat number | `.stat-num` | `clamp(2.4rem, 4.6vw, 3.6rem)` | 700 | `-0.03em` | `font-variant-numeric: tabular-nums` |
| Pilot card title | `.pilot-card h3` | 1.4rem | 600 | inherits | one per pilot card |
| Track title | `.track h3` | 1.35rem | 600 | inherits | one per track |
| Critique title | `.critique h3` | 1.18rem | 600 | inherits | next to giant number |
| Step / pillar h3 | `.step h4`, `.pillar h3` | ~1.0–1.1rem | 600 | inherits | small headlines inside cards |
| Body | `body` | 17px | 400 | — | line-height 1.6 |
| Eyebrow | `.eyebrow` | 0.78rem | 600 | `0.16em` upper | teal-500 / teal-300 |
| Track / column h3 (label-style) | `.col-* h3`, `.track-tag`, etc. | 0.74–0.82rem | 600–700 | `0.14–0.18em` upper | colored per role |
| Slide num / counter | `.slide-num`, `#counter` | 0.78rem | 500–600 | `0.12–0.14em` upper | tabular-nums on counter |
| Code pill | `.sources-line code` | 0.84rem | 500 | — | Inter, paper-2 background |
| Chip | `.chip` | 0.78rem | 500 | — | rounded 999px, paper-2 fill |

### 2.4 Slide & container

Every section lives inside a `.slide` (one viewport) → `.slide-inner` (max-width content rail).

```css
.slide{
  scroll-snap-align: start;
  scroll-snap-stop: always;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6vh 6vw;
  position: relative;
  overflow: hidden;
}
.slide-inner{
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
}
.slide.alt  { background: var(--paper); }
.slide.dark { background: linear-gradient(160deg, var(--navy-900) 0%, var(--navy-700) 100%); color: #E6ECF4; }
.slide.dark h1, .slide.dark h2, .slide.dark h3, .slide.dark strong { color: var(--white); }
.slide.dark em { color: var(--teal-300); }
```

- **Default slide** = white background.
- **`.slide.alt`** = light blue-gray background (`--paper`). Alternate `default → alt → default` to give the deck visual rhythm. Don't run three of the same background back-to-back.
- **`.slide.dark`** = navy gradient. Reserve for the hero, the principle/pullquote slide, and the closing slide — high-contrast bookends.

---

## 3. Layout primitives

### 3.1 Slide system

The deck is built on CSS scroll-snap. Three modifiers cover every slide variant:

```html
<section class="slide" data-num="02" data-title="The growth problem">
  <div class="slide-inner">
    <!-- content -->
  </div>
  <span class="slide-num">02 / 16</span>
</section>

<section class="slide alt" data-num="03" data-title="The shared diagnosis">…</section>

<section class="slide dark" data-num="05" data-title="The counter">…</section>
```

- `data-num` is a 2-digit padded slide index used by the JS counter logic.
- `data-title` is metadata for tooling (analytics, table of contents generation). Optional but recommended.
- `.slide-num` is a per-slide bottom-left number badge that hides in print.

### 3.2 Persistent UI

Three fixed-position UI affordances live outside the slide markup, just inside `<body>`:

```html
<div id="progress" aria-hidden="true"></div>
<div id="counter" aria-live="polite">01 / 16</div>
<button id="print-btn" type="button" onclick="window.print()" aria-label="Print or save as PDF">
  <svg viewBox="0 0 24 24" …>…</svg>
  Print / Save PDF
</button>
```

| Element | Position | Purpose |
|---|---|---|
| `#progress` | Top-edge 2px bar | Scroll-position progress, teal→coral gradient. |
| `#counter` | Top-right pill, blur-backed | Current slide / total. Toggles `.on-dark` over dark slides. |
| `#print-btn` | Bottom-left pill, blur-backed | One-click `window.print()`. Toggles `.on-dark` over dark slides. |

All three hide in print (`display: none !important`).

### 3.3 Section header pattern (eyebrow → h-section → lede)

The canonical opening for every non-hero slide:

```html
<div class="eyebrow">The starting point</div>
<h2 class="h-section">What works at $100M will not scale to $500M.</h2>
<p class="lede">Lede paragraph — one sentence that frames the slide, capped at ~820px so the eye can read it in a single sweep.</p>
```

- **Eyebrow** is a 0.78rem uppercase teal label that names the section's *role* in the narrative ("The starting point", "How we deliver", "The ask").
- **`.h-section`** carries the actual claim — declarative, often punctuated like a sentence ("Two tracks. One foundation.").
- **`.lede`** is one paragraph; lists, grids, and component blocks follow.

### 3.4 Grids

Every multi-column layout is a `display: grid` with explicit `grid-template-columns`. All collapse to 1 column at 980px (see §6).

| Grid | Template | 980px | 640px |
|---|---|---|---|
| `.cols-2` | `1fr 1fr`, gap 2rem | 1 col | 1 col |
| `.tracks` | `1fr 1fr`, gap 1.6rem | 1 col | 1 col |
| `.pilot-grid` | `1fr 1fr`, gap 1.5rem | 1 col | 1 col |
| `.pilot-detail` | `1.05fr 1fr`, gap 2.2rem | 1 col | 1 col |
| `.split` | `1fr 1fr`, gap 2rem | 1 col | 1 col |
| `.next-steps` | `repeat(3, 1fr)`, gap 1rem | 1 col | 1 col |
| `.metrics-grid` | `1fr 1fr`, gap 1rem | 1 col | 1 col |
| `.workflow` | `repeat(2, 1fr)`, gap 0.6rem/1.2rem | 1 col | 1 col |
| `.check-grid` | `repeat(2, 1fr)`, gap 0.9rem/2rem | 1 col | 1 col |
| `.tl-grid` | `repeat(6, 1fr)`, gap 0.6rem | `repeat(3, 1fr)` + vertical fallback | 1 col |
| `.tl-grid.two-phase` | `1fr 2.5fr` | 1 col | 1 col |
| `.phase-chips` | `repeat(4, 1fr)`, gap 0.7rem | `repeat(2, 1fr)` | 1 col |
| `.arch .layer` (row-level) | `200px 1fr` (label \| detail) | 1 col stacked | 1 col |
| `.pillar-grid` | `repeat(3, 1fr)`, gap 1rem | `repeat(2, 1fr)` | 1 col |

All grids stay inside `.slide-inner` (no edge-to-edge layouts).

---

## 4. Components

### 4.1 Hero

The deck opener: dark slide with a navy gradient + soft radial accents, the Techjays wordmark, a `hero-tag` eyebrow, the giant title, the sub, and a prepared-by/-for/date/approach meta strip.

```html
<section class="slide dark" id="s1" data-num="01" data-title="Hero">
  <div class="slide-inner hero-grid">
    <div>
      <svg class="tj-logo tj-logo-lg" viewBox="0 0 223 41" role="img" aria-label="Techjays"><use href="#tj-logo"/></svg>
      <div class="hero-tag" style="margin-top:2.4rem">A Proposal for [Client]</div>
      <h1 class="hero-title">[Client]<br>[Engagement Name]</h1>
      <p class="hero-sub">One-sentence value proposition. End with <em>color emphasis</em> on the speed word.</p>
      <div class="hero-meta">
        <div><strong>Prepared by</strong><span>Techjays</span></div>
        <div><strong>Prepared for</strong><span>[Client] Leadership</span></div>
        <div><strong>Date</strong><span>Mmm YYYY</span></div>
        <div><strong>Approach</strong><span>Workflow-first applied AI</span></div>
      </div>
    </div>
  </div>
  <div class="scroll-hint">
    <span>Scroll</span>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
  </div>
</section>
```

The hero slide carries `id="s1"` and gets an extra radial-gradient overlay (teal at top-right, coral at bottom-left) on top of the base navy gradient — see `:root + #s1` rule in §9. `.scroll-hint` is the bobbing "Scroll ↓" pill at the bottom-center.

### 4.2 Eyebrow label

Used above every section heading and inside several components (track-tag, phase-chip-tag, step-num, hero-tag, attribution-tag, post-90-tag, sources-line `<strong>`).

```html
<div class="eyebrow">The starting point</div>
```

Style: `0.78rem; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--teal-500); margin-bottom: 1.1rem;`. On `.slide.dark`, color flips to `var(--teal-300)`.

### 4.3 Section header (`.h-section` / `.lede`)

```html
<div class="eyebrow">From visibility to action</div>
<h2 class="h-section">Visibility is the start. Workflow change is the result.</h2>
<p class="lede">One sentence that frames the slide. Cap at ~820px so the eye reads it in a single line-sweep.</p>
```

### 4.4 Today / Tomorrow two-column card

Problem-framing pair used early in the deck. The left column is muted ("today's reality"), the right column is coral ("what growth breaks").

```html
<div class="cols-2">
  <div class="col-today">
    <h3>Today — the operating reality</h3>
    <div class="card">
      <ul>
        <li>Today statement…</li>
        <li>Another current-state observation…</li>
      </ul>
    </div>
  </div>
  <div class="col-tomorrow">
    <h3>Tomorrow — what growth breaks</h3>
    <div class="card">
      <ul>
        <li>Future strain…</li>
        <li>Another forward-looking risk…</li>
      </ul>
    </div>
  </div>
</div>
```

- `.col-today h3` → slate-600; `.col-today .card` → 4px left border slate-300; bullets are slate-400 dots.
- `.col-tomorrow h3` → coral-500; `.col-tomorrow .card` → 4px left border coral-500; bullets are coral-500 dots.

### 4.5 Check grid

Two-column grid of "shared understanding" items. Each item is a green-equivalent (here: teal) check svg + a single line.

```html
<div class="check-grid">
  <div class="check">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span>One concise statement of mutual understanding.</span>
  </div>
  <!-- five to seven more .check items -->
</div>
<div class="note-line">Closing transition sentence. <em>Italic-as-coral phrase pulls the eye.</em></div>
```

`.check svg` is teal-500, 22px. `.note-line` is a navy-900 1.1rem block separated from the grid by a 1px top border — a "and here's the so-what" line.

### 4.6 Critique stack (numbered)

Three (or more) numbered observations, stacked vertically. The number is huge, coral, tabular.

```html
<div class="critique-stack">
  <div class="critique">
    <div class="critique-num">01</div>
    <div>
      <h3>Short, declarative claim.</h3>
      <p>One paragraph of explanation. Keep it to 2–3 sentences.</p>
    </div>
  </div>
  <!-- 02, 03, … -->
</div>
```

`.critique-num` is `2.6rem`, 700, coral-500, tabular-nums. The card grid is `80px 1fr`, padding 1.5rem 1.7rem, radius 18px.

### 4.7 Pullquote + attribution-tag

Used on a `.slide.dark` to land the central thesis. Teal left bar, soft serif curly-quote glyph behind the text.

```html
<section class="slide dark" data-num="05" data-title="The counter">
  <div class="slide-inner">
    <div class="eyebrow">The Techjays principle</div>
    <h2 class="h-section" style="color:#fff;max-width:880px">Section claim, one sentence.</h2>
    <blockquote class="pullquote">
      The thesis sentence(s). Long enough to land the idea, short enough to read aloud in one breath. Use <em>em-emphasis</em> for the operative phrase.
    </blockquote>
    <div class="attribution-tag">A short signature line in teal-300.</div>
  </div>
  <span class="slide-num">05 / 16</span>
</section>
```

The `::before` curly quote (`'\201C'`, Georgia serif, 5rem, opacity 0.3) sits behind and slightly above the text — the only place Georgia is used in the system.

### 4.8 Two-track card

Side-by-side "parallel paths" cards. Track 1 gets a 5px coral top strip; Track 2 gets teal. Closes with a `.tracks-foot` synthesis line.

```html
<div class="tracks">
  <div class="track t1">
    <div class="track-tag">Track 1 — Visible to the business</div>
    <h3>Working solutions.</h3>
    <p>One-paragraph description of the track.</p>
    <div class="chips">
      <span class="chip">Tag</span>
      <span class="chip">Tag</span>
      <span class="chip">Tag</span>
    </div>
  </div>
  <div class="track t2">
    <div class="track-tag">Track 2 — Built behind each workflow</div>
    <h3>Single source of truth.</h3>
    <p>One-paragraph description of the track.</p>
    <div class="chips">…</div>
  </div>
</div>
<div class="tracks-foot">Synthesis sentence — why these two tracks belong together.</div>
```

Color binding (locked):
- `.track.t1` → coral-500 top bar and `track-tag`. Use for the "visible / problem-facing" path.
- `.track.t2` → teal-500 top bar and `track-tag`. Use for the "platform / solution" path.

### 4.9 Comparison table (`.compare`)

Available in the stylesheet but **not used in the ValleyRAA deck** — it's there for proposals that need a head-to-head ("Techjays vs. typical vendor") comparison. Highlight the Techjays column with `.tj`.

```html
<table class="compare">
  <thead>
    <tr>
      <th>Dimension</th>
      <th>Typical approach</th>
      <th class="tj">Techjays approach</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Cadence</th>
      <td class="left">Monthly status reports</td>
      <td class="tj">Weekly working demos</td>
    </tr>
    <!-- more rows -->
  </tbody>
</table>
```

`.compare thead th.tj` → coral text on a 6%-coral tint. `.compare td.tj` → 4%-coral tint, navy-900 text, weight 500. Hover tint is teal at 4%.

### 4.10 Timeline

Horizontal time-banded grid with a teal→coral connecting line (`::before`), per-item dots, and a week label / name / desc per item. Comes in two variants — the default 6-column grid for granular weekly slots, and the `.two-phase` variant for "Discovery + Pilot" two-block summaries.

```html
<div class="timeline">
  <div class="tl-grid two-phase">
    <div class="tl-item">
      <span class="tl-dot"></span>
      <div class="tl-week">Weeks 1–3</div>
      <div class="tl-name">Phase 0 — Discovery Sprint</div>
      <div class="tl-desc">What happens in this phase. 2–3 sentences max.</div>
    </div>
    <div class="tl-item">
      <span class="tl-dot"></span>
      <div class="tl-week">Weeks 4–12</div>
      <div class="tl-name">Phase 1 — First Pilot</div>
      <div class="tl-desc">What happens in this phase.</div>
    </div>
  </div>
</div>

<div class="post-90">
  <div class="post-90-head">
    <span class="post-90-tag">Beyond the first 90 days</span>
    <p class="post-90-note">One italic note explaining how phase ordering is decided.</p>
  </div>
  <div class="phase-chips">
    <div class="phase-chip">
      <span class="phase-chip-tag">Phase 2</span>
      <span class="phase-chip-name">Pilot name</span>
      <span class="phase-chip-desc">One-line description.</span>
    </div>
    <!-- up to four phase-chips -->
  </div>
</div>
<div class="tl-foot">Italic closing transition.</div>
```

Per-item dot colors are assigned by position (`nth-child`): first item navy, middle items teal, later items coral, trailing item slate. This communicates *narrative phase* visually — "discovery → execute → expand → wind down". The first `.phase-chip` gets the coral left border; the others stay teal.

At 980px, the horizontal line hides and items rotate to a vertical layout with a left-side accent border (see §6).

### 4.11 Pilot option card

Two-up "choose your path" cards with a notched badge sitting on the top edge. Pilot A = coral, Pilot B = teal.

```html
<div class="pilot-grid">
  <div class="pilot-card a">
    <div class="badge">Pilot A</div>
    <h3>Pilot A title.</h3>
    <div class="audience">Audience tagline — who this conversation is for</div>
    <p>One paragraph describing the pilot.</p>
    <div class="ms">
      <span class="chip">Outcome chip</span>
      <span class="chip">Outcome chip</span>
      <span class="chip">Outcome chip</span>
    </div>
  </div>
  <div class="pilot-card b">
    <div class="badge">Pilot B</div>
    <h3>Pilot B title.</h3>
    <div class="audience">Audience tagline</div>
    <p>Paragraph.</p>
    <div class="ms">…</div>
  </div>
</div>
<div class="cta-line">Our recommendation: <em>propose both, [Client] chooses one</em> for the 6-week pilot.</div>
```

Badge variants:
- `.pilot-card.a .badge` → coral-500 text, coral-300 border.
- `.pilot-card.b .badge` → teal-500 text, teal-300 border.

### 4.12 Pilot detail block

The deep-dive slide for each pilot. Two-column layout: problem bullets on the left, solution metrics + sources on the right.

```html
<div class="pilot-detail a">  <!-- or .b for teal solution accent -->
  <div class="pilot-problem">
    <h3>The pain today</h3>
    <ul>
      <li>Pain point with <strong>quantified figure</strong> inline</li>
      <li>Another pain point</li>
      <!-- 4–6 items -->
    </ul>
  </div>
  <div class="pilot-solution">
    <h3>Target outcomes after 6 weeks</h3>
    <div class="metrics-grid">
      <div class="metric-card stat">
        <div class="stat-num coral">80%</div>     <!-- .coral for pilot A, .teal for pilot B -->
        <div class="stat-label">reduction in month-end close time</div>
      </div>
      <!-- four metric cards in a 2×2 -->
    </div>
    <div class="sources-line">
      <strong>Sources reconciled</strong>
      <code>QGenda</code><code>ADP</code><code>QuickBooks</code><code>Power BI</code>
    </div>
  </div>
</div>
```

- `.pilot-problem h3` → slate-600 (problem labels are muted, not loud).
- `.pilot-solution h3` → coral-500 by default. On `.pilot-detail.b`, the solution h3 flips to teal-500.
- `.stat-num.coral` for Pilot A target outcomes; `.stat-num.teal` for Pilot B.
- `.sources-line code` pills are Inter, paper-2 fill, navy-700 text — used to list system names ("HubSpot", "QGenda") that feed the workflow.

### 4.13 Workflow grid

Two-column numbered step list. Each step is a small bordered card with a square number tile + body text. Use to walk through an end-to-end automated workflow.

```html
<div class="workflow">
  <div class="wf-step">
    <div class="wf-num">1</div>
    <div class="wf-text"><strong>Trigger.</strong> What kicks off the workflow.</div>
  </div>
  <div class="wf-step">
    <div class="wf-num">2</div>
    <div class="wf-text">Second step — describe in one sentence.</div>
  </div>
  <!-- … up to 10 steps in the canonical example -->
</div>
```

`.wf-num` is a 30×30 rounded square — navy-900 by default, **coral-500 on steps 7 and 8, teal-500 on step 10** in the canonical example (signaling "human approval" → "system write" → "completed" phase boundaries). Authors should re-pick these `nth-child` boundaries per workflow rather than copying the exact rule.

### 4.14 Architecture layers

A vertical stack of one-row-per-layer cards. Each layer = an icon + label + a flex row of `.layer-pill` chips describing what's in that layer.

```html
<div class="arch">
  <div class="layer action">
    <div class="layer-name">
      <div class="layer-icon">
        <svg viewBox="0 0 24 24" …>…</svg>
      </div>
      Action Dashboard
    </div>
    <div class="layer-detail">
      <span class="layer-pill">"3 providers at risk of missing deadline"</span>
      <span class="layer-pill">"2 shifts uncovered next week"</span>
    </div>
  </div>
  <div class="layer workflow">
    <div class="layer-name">
      <div class="layer-icon"><svg …>…</svg></div>
      Workflow Automation
    </div>
    <div class="layer-detail">
      <span class="layer-pill">Gap detection</span>
      <span class="layer-pill">Human approval gates</span>
    </div>
  </div>
  <div class="layer">
    <!-- no modifier = neutral navy icon -->
    <div class="layer-name">
      <div class="layer-icon"><svg …>…</svg></div>
      Integration
    </div>
    <div class="layer-detail">
      <span class="layer-pill">HubSpot</span>
      <span class="layer-pill">QGenda</span>
    </div>
  </div>
</div>
```

Layer icon variants:
- `.layer.action` → coral-tinted icon background + coral icon stroke.
- `.layer.workflow` → teal-tinted icon background + teal icon stroke.
- (no modifier) → paper-2 background + navy-700 icon stroke.

### 4.15 Risk pillars (`.pillar-grid`)

A 3-column grid (collapses to 2 then 1) of bordered "principle" cards: gradient-fill rounded icon, h3, one paragraph. Reused twice in the canonical deck — once for delivery principles, once for AI risk controls.

```html
<div class="pillar-grid">
  <div class="pillar">
    <div class="pillar-icon">
      <svg viewBox="0 0 24 24" …>…</svg>
    </div>
    <h3>Principle name</h3>
    <p>One sentence (max two) on the principle.</p>
  </div>
  <!-- 5 more pillars; six total per slide -->
</div>
```

`.pillar-icon` uses a 135deg paper-2 → paper gradient with teal-500 stroke icons by default. Authors can recolor on a per-slide basis if a slide's theme is more coral-leaning.

### 4.16 Metrics-vs-Operations split

Two big cards side-by-side — one lists measurable outcomes (coral), the other lists ways of working / commercial model (teal).

```html
<div class="split">
  <div class="split-card metrics">
    <h3>Measurable outcomes</h3>
    <ul>
      <li>
        <svg viewBox="0 0 24 24" …><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span><strong>50–80%</strong> reduction in invoice prep time</span>
      </li>
      <!-- more rows -->
    </ul>
  </div>
  <div class="split-card ops">
    <h3>Operating &amp; commercial model</h3>
    <ul>
      <li>
        <svg viewBox="0 0 24 24" …>…</svg>
        <span><strong>Weekly working demos</strong> — not status reports, working software</span>
      </li>
      <!-- more rows -->
    </ul>
  </div>
</div>
```

`.split-card.metrics ul li svg` → coral-500. `.split-card.ops ul li svg` → teal-500. Both h3 labels are 0.78rem uppercase.

### 4.17 Closing slide

Dark slide. Closing quote (coral left bar), a sub paragraph, then a 3-step `.next-steps` grid with backdrop-blurred translucent step cards, then a `.signoff` row with the Techjays logo + contact email.

```html
<section class="slide dark" data-num="16" data-title="The path forward">
  <div class="slide-inner">
    <div class="eyebrow">In closing</div>
    <h2 class="h-section" style="color:#fff">The path forward.</h2>
    <blockquote class="closing-quote">
      The final commitment — one sentence that sums up what Techjays will deliver.
    </blockquote>
    <p class="closing-sub">
      One paragraph that softens the quote and points to the first action. Indented under the bar.
    </p>

    <div class="next-steps">
      <div class="step">
        <div class="step-num">Step 01</div>
        <h4>Discovery call</h4>
        <p>What this step is, in one sentence.</p>
      </div>
      <div class="step">
        <div class="step-num">Step 02</div>
        <h4>Pilot selection</h4>
        <p>One sentence.</p>
      </div>
      <div class="step">
        <div class="step-num">Step 03</div>
        <h4>6-week sprint</h4>
        <p>One sentence.</p>
      </div>
    </div>

    <div class="signoff">
      <div class="signoff-brand">
        <svg class="tj-logo tj-logo-sm" viewBox="0 0 223 41" role="img" aria-label="Techjays"><use href="#tj-logo"/></svg>
        <span class="signoff-tagline">Applied AI for healthcare operations</span>
      </div>
      <div>Contact · <a href="mailto:name@techjays.com" style="color:#7FE0E3">name@techjays.com</a></div>
    </div>
  </div>
  <span class="slide-num">16 / 16</span>
</section>
```

`.step` cards use a translucent white overlay (`rgba(255,255,255,0.05)`) plus a `backdrop-filter: blur(8px)` — they "float" on the dark gradient. In print, the rule in §7 swaps them to a light paper background.

### 4.18 Stat / KPI (`.stat`)

A reusable label-over-number block. Mostly used inside `.metric-card` (pilot detail), but valid standalone or in any grid.

```html
<div class="stat">
  <div class="stat-num coral">80%</div>     <!-- .coral / .teal / (default navy) -->
  <div class="stat-label">reduction in month-end close time</div>
</div>
```

Size scales by container — `.pilot-detail .stat-num` is bumped down to `clamp(2rem, 3.4vw, 2.8rem)` from the default `clamp(2.4rem, 4.6vw, 3.6rem)` so four 2×2 metric cards fit comfortably.

### 4.19 Brand mark

> **Client brand pair: match the client's site.** The Title Deck shows the Techjays mark next to the *client's* logo, and the deck's accent should be the *client's* primary brand color. Before building, visit the client's website: sample their primary brand color (header, logo, primary buttons) to set the client-accent ramp, and pull their official logo. See `proposal_standard.md` §2 for the accent-ramp derivation and token table.
>
> **How to place the client logo (in priority order):**
>
> 1. **Embedded base64 (preferred, fully offline-portable).** Download the official logo (SVG or transparent PNG), base64-encode it, and inline it as `<img class="client-logo" src="data:image/png;base64,…" alt="{{CLIENT_NAME}}">`. This keeps the single-file deck readable with the network unplugged and guarantees the logo prints.
> 2. **Remote URL (fast, needs network at view/print time).** Reference the logo straight from the client's site, e.g. `<img class="client-logo" src="https://client.com/logo.png" alt="{{CLIENT_NAME}}">`. Pull the URL from the client's homepage `<img>` or `og:image`. Renders in-browser and embeds into the PDF when saved online. Note it is not offline-portable, so swap to base64 (option 1) before archiving or emailing the raw HTML.
> 3. **Text-wordmark placeholder (last resort).** Render the client name in their accent color via styled `<text>`/`<span>` until a real asset is available, then replace it.
>
> Size the logo by height so any aspect ratio fits the brand pair:
>
> ```css
> .client-logo{ height:50px; width:auto; max-width:280px; object-fit:contain; display:block; }
> ```

The Techjays wordmark is an inline `<symbol>` defined once at the top of `<body>`, referenced everywhere via `<use href="#tj-logo"/>`. Wordmark paths use `currentColor` so the logo recolors per slide (white on dark, navy on light, navy in print even when the slide was dark).

```html
<!-- Once, immediately after <body> -->
<svg aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">
  <defs>
    <symbol id="tj-logo" viewBox="0 0 223 41">
      <!-- path d="…" elements — see canonical deck lines 1068–1080 -->
    </symbol>
  </defs>
</svg>

<!-- Then anywhere you need the logo -->
<svg class="tj-logo" viewBox="0 0 223 41" role="img" aria-label="Techjays"><use href="#tj-logo"/></svg>
<svg class="tj-logo tj-logo-lg" viewBox="0 0 223 41"><use href="#tj-logo"/></svg>   <!-- hero -->
<svg class="tj-logo tj-logo-sm" viewBox="0 0 223 41"><use href="#tj-logo"/></svg>   <!-- signoff -->
```

A simpler "branded dot" mark (gradient teal→coral square) is also defined as `.brand .dot` — useful in compact contexts where the full wordmark would be too heavy. The wordmark `<symbol>` block is reproduced in §9.

---

## 5. Interaction patterns

The script block lives at the bottom of `<body>` (`docs/ValleyRAA/valleyraa-techjays-proposal.html:1747–1816`). It's a single IIFE that wires up four behaviors. Drop it into a new deck verbatim — the only contract it relies on is that slides have class `.slide` and the persistent UI nodes (`#progress`, `#counter`, `#print-btn`) exist.

### 5.1 Scroll progress bar

```js
function updateProgress(){
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  progress.style.width = pct + '%';
}
window.addEventListener('scroll', updateProgress, {passive:true});
window.addEventListener('resize', updateProgress);
updateProgress();
```

The teal→coral gradient is purely CSS (`#progress { background: linear-gradient(...); }`). The JS only writes `width`.

### 5.2 Slide counter (Intersection Observer)

```js
const slides   = Array.from(document.querySelectorAll('.slide'));
const counter  = document.getElementById('counter');
const printBtn = document.getElementById('print-btn');
const total    = slides.length;
const pad      = n => String(n).padStart(2,'0');

let activeIdx = 0;
const io = new IntersectionObserver((entries)=>{
  let best = {idx:activeIdx, ratio:0};
  entries.forEach(e=>{
    if(!e.isIntersecting) return;
    const idx = slides.indexOf(e.target);
    if(e.intersectionRatio > best.ratio) best = {idx, ratio:e.intersectionRatio};
  });
  if(best.ratio > 0 && best.idx !== activeIdx){
    activeIdx = best.idx;
    counter.textContent = pad(activeIdx+1) + ' / ' + pad(total);
    const onDark = slides[activeIdx].classList.contains('dark');
    counter.classList.toggle('on-dark', onDark);
    printBtn.classList.toggle('on-dark', onDark);
  }
}, {threshold:[0.25, 0.5, 0.75]});
slides.forEach(s=>io.observe(s));
```

Both `#counter` and `#print-btn` toggle `.on-dark` when the current slide has class `.dark`, so the blur-backed pills stay readable against the navy gradient.

### 5.3 Keyboard navigation

```js
function jumpTo(idx){
  idx = Math.max(0, Math.min(total-1, idx));
  slides[idx].scrollIntoView({behavior:'smooth', block:'start'});
}
document.addEventListener('keydown', e=>{
  const tag = (e.target && e.target.tagName) || '';
  if(tag === 'INPUT' || tag === 'TEXTAREA') return;
  if(e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' '){
    e.preventDefault(); jumpTo(activeIdx + 1);
  } else if(e.key === 'ArrowUp' || e.key === 'PageUp'){
    e.preventDefault(); jumpTo(activeIdx - 1);
  } else if(e.key === 'Home'){
    e.preventDefault(); jumpTo(0);
  } else if(e.key === 'End'){
    e.preventDefault(); jumpTo(total-1);
  }
});
```

Bindings: ↓ / PageDown / Space advance; ↑ / PageUp go back; Home / End jump to first / last. Typing into form fields (if any) is preserved.

### 5.4 Print button

```html
<button id="print-btn" type="button" onclick="window.print()" aria-label="Print or save as PDF">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"></polyline>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
    <rect x="6" y="14" width="12" height="8"></rect>
  </svg>
  Print / Save PDF
</button>
```

Plain `window.print()`. The §7 print rules do the heavy lifting.

---

## 6. Responsive rules

Two breakpoints, both scoped to `@media screen`.

> **Critical, recurring PDF bug. Scope every responsive breakpoint to `screen`.** US Letter at 96dpi is **816px wide**, which sits below the 980px breakpoint. A bare `@media (max-width: 980px)` therefore fires *during print*: grids collapse to a single column and padding shrinks, so the saved PDF comes out as stacked rows with no table or grid structure. Writing `@media screen and (max-width: …)` confines the collapse to real small viewports and leaves the printed page on the full multi-column layout. Any legacy deck that omits `screen and` must be patched before export.

```css
/* Scope to `screen` so these never fire during print. Letter @96dpi is 816px,
   which is below 980px; a bare query would collapse the PDF to stacked rows. */
@media screen and (max-width: 980px){
  .cols-2, .tracks, .pilot-grid, .pilot-detail, .split,
  .next-steps, .metrics-grid, .workflow, .check-grid {
    grid-template-columns: 1fr;
  }
  .pillar-grid { grid-template-columns: repeat(2, 1fr); }
  .tl-grid     { grid-template-columns: repeat(3, 1fr); gap: 1rem 1rem; }
  .tl-grid.two-phase { grid-template-columns: 1fr; gap: 1rem; }
  .timeline::before  { display: none; }
  .tl-item { padding-top: 0; padding-left: 1.2rem; border-left: 2px solid var(--teal-500); }
  .tl-dot  { display: none; }
  .layer       { grid-template-columns: 1fr; gap: 0.6rem; }
  .phase-chips { grid-template-columns: repeat(2, 1fr); }
}

@media screen and (max-width: 640px){
  .pillar-grid { grid-template-columns: 1fr; }
  .tl-grid     { grid-template-columns: 1fr; }
  .phase-chips { grid-template-columns: 1fr; }
  .compare th, .compare td { font-size: 0.92rem; padding: 0.8rem 0.9rem; }
  #counter  { top: 0.7rem; right: 0.7rem; font-size: 0.7rem; padding: 0.35rem 0.65rem; }
  #print-btn { bottom: 0.7rem; left: 0.7rem; }
}
```

Notable, non-obvious collapses:

- **Timeline switches visual mode at 980px.** The horizontal connecting line hides, the dots hide, and each `.tl-item` becomes a left-bordered vertical card. This is a *different layout* — not just narrower columns — so test it explicitly.
- **Architecture `.layer` flattens.** The `200px 1fr` label/detail split becomes a single column at 980px.
- **`.pillar-grid` is the only grid that has an intermediate (2-col) step** between 3-col and 1-col.

---

## 7. Print rules

> **Print depends on §6 being scoped to `screen`.** The single most common print defect (structure collapsing to rows, padding vanishing) is caused by an unscoped responsive breakpoint firing on the 816px-wide Letter page, not by the print rules below. Fix §6 first. As belt-and-suspenders for quirky PDF engines, you may also re-assert the key multi-column grid templates inside `@media print` (e.g. `.value-grid{display:grid;grid-template-columns:repeat(4,1fr)}`), and keep `overflow:visible` on `.slide` in print so tall content is never clipped.

Verbatim from `docs/ValleyRAA/valleyraa-techjays-proposal.html:1019–1058`.

```css
@media print{
  html { scroll-snap-type: none; scroll-behavior: auto; }
  #progress, #counter, #print-btn, .scroll-hint, .slide-num {
    display: none !important;
  }
  .slide {
    min-height: auto;
    page-break-after: always;
    break-after: page;
    padding: 2.2cm 1.8cm;
    background: var(--white) !important;
    color: var(--slate-900) !important;
  }
  .slide.dark {
    background: var(--white) !important;
    color: var(--slate-900) !important;
  }
  .slide.dark h1, .slide.dark h2, .slide.dark h3, .slide.dark .hero-title,
  .slide.dark strong, .slide.dark .pullquote, .slide.dark .closing-quote {
    color: var(--navy-900) !important;
  }
  .slide.dark .lede, .slide.dark .hero-sub,
  .slide.dark .closing-sub, .slide.dark .step p {
    color: var(--slate-700) !important;
  }
  .slide.dark .hero-meta, .slide.dark .signoff, .slide.dark .step {
    background: var(--paper) !important;
    border: 1px solid var(--slate-300) !important;
    color: var(--slate-700) !important;
  }
  .slide.dark .pullquote     { border-left-color: var(--coral-500) !important; }
  .slide.dark .closing-quote { border-left-color: var(--coral-500) !important; }
  .slide.dark .eyebrow       { color: var(--teal-500) !important; }
  .slide.dark .hero-tag,
  .slide.dark .attribution-tag,
  .slide.dark .step-num      { color: var(--coral-500) !important; }
  .slide.dark .tj-logo       { color: var(--navy-900) !important; }
  .signoff-tagline           { color: var(--slate-700) !important;
                               border-left-color: var(--slate-300) !important; }
  .card, .pilot-card, .track, .metric-card, .split-card,
  .layer, .pillar, .critique, .wf-step {
    box-shadow: none !important;
    break-inside: avoid;
  }
  .compare { box-shadow: none !important; }
  body { font-size: 12pt; }
  h1, .h-hero, .hero-title { font-size: 30pt !important; }
  h2, .h-section           { font-size: 20pt !important; }
  .lede, .hero-sub         { font-size: 13pt !important; }
  @page { margin: 0; size: auto; }
}
```

Key behaviors to know:

- Scroll-snap is disabled; the page becomes a normal block layout.
- All three persistent UI nodes hide.
- `.slide` becomes `page-break-after: always; padding: 2.2cm 1.8cm` — each slide is its own physical page.
- `.slide.dark` inverts to white background with navy text; **accent colors (coral-500, teal-500, teal-300) are preserved** via `!important`. Translucent dark backgrounds (`.step`) get a light paper background + slate-300 border so they remain readable.
- Type sizes are pinned in `pt` (12pt body / 30pt h1 / 20pt h2 / 13pt lede) for predictable PDF rendering.
- Box shadows and `break-inside: avoid` on every card ensure clean page breaks.
- `@page { margin: 0; size: auto; }` — the printer's default margin is suppressed because `.slide` already pads itself with `2.2cm 1.8cm`.

---

## 8. Content & flow conventions

The visual system has an opinion about narrative shape. The canonical 16-slide arc:

| # | Slide title | Component(s) | Variant |
|---|---|---|---|
| 1 | Hero | `.hero-grid` + `.hero-title` + `.hero-sub` + `.hero-meta` + `.scroll-hint` | `.slide.dark` |
| 2 | The starting point — current vs. growth | `.cols-2` (today / tomorrow) | default |
| 3 | The shared diagnosis | `.check-grid` + `.note-line` | `.slide.alt` |
| 4 | What real change requires | `.critique-stack` (3 numbered) | default |
| 5 | The principle | `.pullquote` + `.attribution-tag` | `.slide.dark` |
| 6 | Two-track approach | `.tracks` (t1 / t2) + `.chips` + `.tracks-foot` | default |
| 7 | How we deliver | `.pillar-grid` (6 principles) | `.slide.alt` |
| 8 | The first 90 days | `.timeline.two-phase` + `.post-90` + `.phase-chips` + `.tl-foot` | default |
| 9 | Choose your first pilot | `.pilot-grid` (a / b badges) + `.cta-line` | `.slide.alt` |
| 10 | Pilot A detail | `.pilot-detail.a` (problem + solution + `.metrics-grid` + `.sources-line`) | default |
| 11 | Pilot B detail | `.pilot-detail.b` (same shape, teal solution accent) | `.slide.alt` |
| 12 | Sample workflow | `.workflow` (numbered steps) | default |
| 13 | Solution architecture | `.arch` (5 layers, `.action` + `.workflow` variants) | `.slide.alt` |
| 14 | Risk-controlled AI | `.pillar-grid` (6 safeguards) | default |
| 15 | Outcomes + operating model | `.split` (`.metrics` + `.ops`) | `.slide.alt` |
| 16 | The path forward | `.closing-quote` + `.closing-sub` + `.next-steps` + `.signoff` | `.slide.dark` |

The slide order is not load-bearing — drop, reorder, or replace slides freely — but **the dark-bookend pattern is**: slides 1, 5, and 16 are `.slide.dark`. Two dark slides at the bookends plus one in the middle creates a natural three-act rhythm.

### Voice notes

- **Speed framing.** "In weeks, not years", "from week one", "value before the platform is finished". Quantify time, not effort.
- **Workflow-first vocabulary.** "Workflow-first", "single source of truth", "outcome-based", "weekly working demos, not status reports", "human in the loop", "no autonomous writes", "detect → recommend → act".
- **First-person plural for Techjays, second-person for the client.** "We will ship…", "your team", "[Client] picks one".
- **Italics-as-coral emphasis.** Write `<em>weeks</em>`, `<em>before the platform</em>`, `<em>both, you choose one</em>` to land the operative phrase in coral. Use sparingly — 1–2 per slide at most.
- **Numbered stats are tabular and paired with a sub-label.** `.stat-num.coral` for problem framing or pilot-A outcomes; `.stat-num.teal` for solution framing or pilot-B outcomes. Always pair with a short, plain-English `.stat-label`.
- **System names as code-pills.** Use `<code>HubSpot</code><code>QGenda</code>…` inside `.sources-line` to enumerate the systems a workflow touches. Don't quote them in body text — the pill treatment signals "these are the integration endpoints".
- **Alternate background rhythm.** Pattern: dark · default · alt · default · dark · default · alt · default · alt · default · alt · default · alt · default · alt · dark. Don't run three of the same background back-to-back.
- **Neutral framing for client-side work.** Problems are described as "the operating reality", "what growth breaks", "the pain today" — never "your fault" or "you should have…". The proposal is a "we" document about a shared trajectory.

### Naming conventions

- **Slide IDs** are `id="s1"…"s16"` (only the hero typically needs one for the `#s1` extra-gradient rule).
- **`data-num`** is the 2-digit padded slide index used by the JS counter.
- **`data-title`** is human-readable metadata — useful for tooling / analytics / a future auto-generated table of contents.
- **`.slide-num`** spans display as `NN / TT` matching the IO counter format.
- **Dates** in `.hero-meta` display as `Mmm YYYY` (e.g., `May 2026`). For pilot timelines, use `Weeks 1–3` style — let week ranges, not dates, carry the timing.

---

## 9. Full stylesheet

Drop this `<style>` block into a new proposal's `<head>` and you have the full system. Lifted verbatim from `docs/ValleyRAA/valleyraa-techjays-proposal.html:8–1059`. Pair with the `<symbol id="tj-logo">` SVG block (immediately below) so a fresh file has a working Techjays wordmark.

```css
/* ============================================================
   Design tokens
   ============================================================ */
:root{
  --navy-900:#0B2545;
  --navy-700:#13315C;
  --navy-500:#1E4D8B;
  --white:#FFFFFF;
  --paper:#F7F9FC;
  --paper-2:#EEF2F8;
  --teal-500:#1AC0C6;
  --teal-300:#7FE0E3;
  --coral-500:#F26B5B;
  --coral-300:#FAA89E;
  --slate-900:#111827;
  --slate-700:#374151;
  --slate-600:#6B7280;
  --slate-400:#9CA3AF;
  --slate-300:#D1D5DB;
  --slate-200:#E5E7EB;
  --slate-100:#F3F4F6;
  --shadow-sm:0 1px 2px rgba(11,37,69,.06);
  --shadow-md:0 8px 24px rgba(11,37,69,.08);
  --shadow-lg:0 20px 60px rgba(11,37,69,.14);
  --radius-sm:6px;
  --radius:10px;
  --radius-lg:18px;
}

/* ============================================================
   Reset + base
   ============================================================ */
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0}
html{
  scroll-behavior:smooth;
  scroll-snap-type:y mandatory;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  text-rendering:optimizeLegibility;
}
body{
  font-family:'Inter','InterVariable',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
  font-feature-settings:'cv02','cv03','cv04','cv11';
  font-size:17px;
  line-height:1.6;
  color:var(--slate-700);
  background:var(--white);
}
h1,h2,h3,h4{margin:0;color:var(--navy-900);letter-spacing:-.018em;line-height:1.15}
h1{font-weight:700;letter-spacing:-.025em}
h2{font-weight:700}
h3{font-weight:600}
p{margin:0 0 .9rem}
strong{color:var(--navy-900);font-weight:600}
em{font-style:normal;color:var(--coral-500);font-weight:600}
a{color:var(--teal-500);text-decoration:none}
a:hover{text-decoration:underline}
ul,ol{margin:0;padding:0;list-style:none}

/* ============================================================
   Slide system
   ============================================================ */
.slide{
  scroll-snap-align:start;
  scroll-snap-stop:always;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:6vh 6vw;
  position:relative;
  overflow:hidden;
}
.slide-inner{
  width:100%;
  max-width:1180px;
  margin:0 auto;
}
.slide.alt{background:var(--paper)}
.slide.dark{background:linear-gradient(160deg,var(--navy-900) 0%,var(--navy-700) 100%);color:#E6ECF4}
.slide.dark h1,.slide.dark h2,.slide.dark h3,.slide.dark strong{color:var(--white)}
.slide.dark em{color:var(--teal-300)}

/* Slide number badge (bottom-left of each slide, subtle) */
.slide-num{
  position:absolute;
  left:6vw;
  bottom:3vh;
  font-size:.78rem;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--slate-400);
  font-weight:500;
}
.slide.dark .slide-num{color:rgba(230,236,244,.5)}

/* Eyebrow label */
.eyebrow{
  display:inline-block;
  font-size:.78rem;
  font-weight:600;
  letter-spacing:.16em;
  text-transform:uppercase;
  color:var(--teal-500);
  margin-bottom:1.1rem;
}
.slide.dark .eyebrow{color:var(--teal-300)}

/* Headline scales */
.h-hero{font-size:clamp(2.6rem,5.6vw,4.6rem);font-weight:700;letter-spacing:-.028em;line-height:1.05}
.h-section{font-size:clamp(1.85rem,3.4vw,2.85rem);font-weight:700;line-height:1.15;margin-bottom:1.4rem}
.lede{font-size:clamp(1.05rem,1.4vw,1.25rem);color:var(--slate-700);max-width:820px;line-height:1.55}
.slide.dark .lede{color:#C9D3E0}

/* Stat block */
.stat{
  display:flex;
  flex-direction:column;
  gap:.25rem;
}
.stat-num{
  font-size:clamp(2.4rem,4.6vw,3.6rem);
  font-weight:700;
  color:var(--navy-900);
  line-height:1;
  letter-spacing:-.03em;
  font-variant-numeric:tabular-nums;
}
.stat-num.coral{color:var(--coral-500)}
.stat-num.teal{color:var(--teal-500)}
.stat-label{
  font-size:.92rem;
  color:var(--slate-600);
  font-weight:500;
  line-height:1.35;
}

/* Card */
.card{
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius-lg);
  padding:1.6rem 1.7rem;
  box-shadow:var(--shadow-sm);
}
.card.flush{padding:0;overflow:hidden}
.card.accent{border-top:4px solid var(--teal-500)}
.card.coral{border-top:4px solid var(--coral-500)}

/* ============================================================
   Persistent UI: progress bar, slide counter, print button
   ============================================================ */
#progress{
  position:fixed;top:0;left:0;height:2px;width:0%;
  background:linear-gradient(90deg,var(--teal-500) 0%,var(--coral-500) 100%);
  z-index:100;
  transition:width .12s ease-out;
}
#counter{
  position:fixed;
  top:1.4rem;right:1.6rem;
  font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--slate-600);
  font-weight:600;
  background:rgba(255,255,255,.85);
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
  padding:.45rem .8rem;
  border-radius:999px;
  border:1px solid var(--slate-200);
  z-index:90;
  font-variant-numeric:tabular-nums;
}
#counter.on-dark{
  color:#E6ECF4;
  background:rgba(11,37,69,.55);
  border-color:rgba(255,255,255,.12);
}
#print-btn{
  position:fixed;
  bottom:1.4rem;left:1.6rem;
  font-family:inherit;
  font-size:.78rem;
  letter-spacing:.06em;
  font-weight:600;
  color:var(--slate-700);
  background:rgba(255,255,255,.9);
  backdrop-filter:blur(8px);
  -webkit-backdrop-filter:blur(8px);
  border:1px solid var(--slate-200);
  border-radius:999px;
  padding:.5rem .95rem;
  cursor:pointer;
  z-index:90;
  display:inline-flex;align-items:center;gap:.4rem;
}
#print-btn:hover{background:var(--white);box-shadow:var(--shadow-sm)}
#print-btn.on-dark{
  color:#E6ECF4;
  background:rgba(11,37,69,.55);
  border-color:rgba(255,255,255,.18);
}
#print-btn svg{width:14px;height:14px}

/* ============================================================
   Slide 1 — Hero
   ============================================================ */
#s1{
  background:
    radial-gradient(ellipse at 80% 20%, rgba(26,192,198,.18), transparent 55%),
    radial-gradient(ellipse at 10% 90%, rgba(242,107,91,.10), transparent 60%),
    linear-gradient(160deg, var(--navy-900) 0%, var(--navy-700) 100%);
  color:#E6ECF4;
}
.hero-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:2.4rem;
  align-items:end;
}
.hero-tag{
  font-size:.82rem;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:var(--teal-300);
  font-weight:600;
}
.hero-title{
  color:var(--white);
  font-size:clamp(2.6rem,6.4vw,5.4rem);
  font-weight:700;
  letter-spacing:-.03em;
  line-height:1;
  margin:1rem 0 1.2rem;
}
.hero-sub{
  color:#C9D3E0;
  font-size:clamp(1.1rem,1.6vw,1.45rem);
  max-width:780px;
  line-height:1.5;
  font-weight:400;
}
.hero-meta{
  display:flex;
  gap:2.4rem;
  flex-wrap:wrap;
  margin-top:3.2rem;
  padding-top:1.6rem;
  border-top:1px solid rgba(255,255,255,.12);
  font-size:.92rem;
  color:#9DB1C8;
}
.hero-meta strong{color:#E6ECF4;font-weight:600;display:block;margin-bottom:.15rem;font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-300)}
.hero-meta div span{color:#E6ECF4;font-weight:500}
.scroll-hint{
  position:absolute;
  left:50%;bottom:3rem;
  transform:translateX(-50%);
  font-size:.74rem;
  letter-spacing:.2em;
  text-transform:uppercase;
  color:rgba(230,236,244,.55);
  display:flex;flex-direction:column;align-items:center;gap:.4rem;
  animation:bob 2.4s ease-in-out infinite;
}
.scroll-hint svg{width:14px;height:14px;opacity:.7}
@keyframes bob{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,6px)}}

/* Brand mark (TJ) */
.brand{
  display:inline-flex;align-items:center;gap:.55rem;
  font-weight:700;letter-spacing:.04em;color:var(--white);
  font-size:.92rem;
}
.brand .dot{
  width:22px;height:22px;border-radius:6px;
  background:linear-gradient(135deg,var(--teal-500) 0%,var(--coral-500) 100%);
  display:inline-block;
}

/* Techjays logo (SVG symbol referenced via <use>) */
.tj-logo{
  display:inline-block;
  height:34px;
  width:auto;
  color:var(--navy-900);
  vertical-align:middle;
  flex-shrink:0;
}
.tj-logo-lg{height:42px}
.tj-logo-sm{height:26px}
.slide.dark .tj-logo{color:#fff}

/* Signoff brand row (slide 16) — logo + tagline */
.signoff-brand{
  display:inline-flex;
  align-items:center;
  gap:.95rem;
  flex-wrap:wrap;
}
.signoff-tagline{
  font-size:.88rem;
  color:#9DB1C8;
  border-left:1px solid rgba(255,255,255,.18);
  padding-left:.95rem;
  line-height:1.3;
}

/* ============================================================
   Slide 2 — Growth problem (two-column)
   ============================================================ */
.cols-2{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:2rem;
  margin-top:2rem;
}
.cols-2 > div h3{
  font-size:.82rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  margin-bottom:1.1rem;
  font-weight:600;
}
.col-today h3{color:var(--slate-600)}
.col-tomorrow h3{color:var(--coral-500)}
.col-today .card,.col-tomorrow .card{height:100%}
.col-tomorrow .card{border-left:4px solid var(--coral-500)}
.col-today .card{border-left:4px solid var(--slate-300)}
.cols-2 ul li{
  display:flex;gap:.7rem;
  margin-bottom:.85rem;
  font-size:1rem;color:var(--slate-700);
}
.cols-2 ul li::before{
  content:'';
  flex:0 0 6px;
  height:6px;width:6px;
  margin-top:.55rem;
  border-radius:50%;
  background:var(--slate-400);
}
.col-tomorrow ul li::before{background:var(--coral-500)}

/* ============================================================
   Slide 3 — what they got right (checklist)
   ============================================================ */
.check-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:.9rem 2rem;
  margin-top:1.8rem;
}
.check{
  display:flex;gap:.85rem;align-items:flex-start;
  font-size:1.02rem;color:var(--slate-700);
}
.check svg{flex:0 0 22px;width:22px;height:22px;margin-top:2px;color:var(--teal-500)}
.note-line{
  margin-top:2.4rem;
  padding-top:1.6rem;
  border-top:1px solid var(--slate-200);
  font-size:1.1rem;
  font-weight:500;
  color:var(--navy-900);
}

/* ============================================================
   Slide 4 — critique cards (3 stacked)
   ============================================================ */
.critique-stack{
  display:grid;
  grid-template-columns:1fr;
  gap:1rem;
  margin-top:2rem;
}
.critique{
  display:grid;
  grid-template-columns:80px 1fr;
  gap:1.4rem;
  align-items:center;
  padding:1.5rem 1.7rem;
  border-radius:var(--radius-lg);
  background:var(--white);
  border:1px solid var(--slate-200);
  box-shadow:var(--shadow-sm);
}
.critique-num{
  font-size:2.6rem;font-weight:700;
  color:var(--coral-500);
  line-height:1;
  font-variant-numeric:tabular-nums;
}
.critique h3{font-size:1.18rem;margin-bottom:.3rem;color:var(--navy-900)}
.critique p{margin:0;color:var(--slate-700);font-size:.98rem}

/* ============================================================
   Slide 5 — pull quote
   ============================================================ */
.pullquote{
  position:relative;
  font-size:clamp(1.5rem,2.6vw,2.2rem);
  font-weight:500;
  line-height:1.35;
  letter-spacing:-.012em;
  color:var(--white);
  max-width:980px;
  margin:0;
  padding:1rem 0 1rem 2.2rem;
  border-left:4px solid var(--teal-500);
}
.pullquote::before{
  content:'\201C';
  position:absolute;
  left:.5rem;top:-.7rem;
  font-size:5rem;
  line-height:1;
  color:var(--teal-300);
  opacity:.3;
  font-family:Georgia,serif;
}
.attribution-tag{
  margin-top:1.8rem;
  font-size:.84rem;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:var(--teal-300);
  font-weight:600;
}

/* ============================================================
   Slide 6 — two tracks
   ============================================================ */
.tracks{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:1.6rem;
  margin-top:2.2rem;
}
.track{
  background:var(--white);
  border-radius:var(--radius-lg);
  padding:1.8rem;
  border:1px solid var(--slate-200);
  box-shadow:var(--shadow-sm);
  position:relative;
  overflow:hidden;
}
.track::before{
  content:'';
  position:absolute;left:0;top:0;
  width:100%;height:5px;
}
.track.t1::before{background:var(--coral-500)}
.track.t2::before{background:var(--teal-500)}
.track-tag{
  font-size:.75rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  font-weight:600;
  margin-bottom:.5rem;
}
.track.t1 .track-tag{color:var(--coral-500)}
.track.t2 .track-tag{color:var(--teal-500)}
.track h3{font-size:1.35rem;margin-bottom:.85rem}
.track p{font-size:.98rem;color:var(--slate-700)}
.track .chips{margin-top:1rem;display:flex;flex-wrap:wrap;gap:.4rem}
.chip{
  font-size:.78rem;
  font-weight:500;
  background:var(--paper-2);
  color:var(--navy-700);
  padding:.3rem .6rem;
  border-radius:999px;
  border:1px solid var(--slate-200);
}
.tracks-foot{
  margin-top:1.8rem;
  padding:1.1rem 1.4rem;
  background:var(--paper-2);
  border-radius:var(--radius);
  font-size:1.02rem;
  color:var(--navy-900);
  font-weight:500;
  border-left:3px solid var(--navy-700);
}

/* ============================================================
   Slide 7 — comparison table (optional component)
   ============================================================ */
.compare{
  width:100%;
  border-collapse:separate;
  border-spacing:0;
  margin-top:1.8rem;
  background:var(--white);
  border-radius:var(--radius-lg);
  overflow:hidden;
  box-shadow:var(--shadow-sm);
  border:1px solid var(--slate-200);
}
.compare th,.compare td{
  padding:1rem 1.2rem;
  text-align:left;
  font-size:.98rem;
  vertical-align:top;
  border-bottom:1px solid var(--slate-200);
}
.compare tr:last-child th,.compare tr:last-child td{border-bottom:none}
.compare thead th{
  font-size:.74rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  font-weight:700;
  background:var(--paper);
  color:var(--slate-600);
  padding:.85rem 1.2rem;
}
.compare thead th.tj{
  color:var(--coral-500);
  background:rgba(242,107,91,.06);
}
.compare td.tj{
  background:rgba(242,107,91,.04);
  color:var(--navy-900);
  font-weight:500;
}
.compare td.left{
  color:var(--slate-700);
}
.compare tr:hover td{background:rgba(26,192,198,.04)}

/* ============================================================
   Slide 8 — timeline
   ============================================================ */
.timeline{
  margin-top:2.2rem;
  position:relative;
}
.timeline::before{
  content:'';
  position:absolute;
  left:0;right:0;top:33px;
  height:2px;
  background:linear-gradient(90deg,var(--teal-500) 0%,var(--coral-500) 100%);
  border-radius:2px;
}
.tl-grid{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  gap:.6rem;
}
.tl-item{
  position:relative;
  padding-top:60px;
}
.tl-dot{
  position:absolute;
  left:50%;top:24px;
  width:18px;height:18px;
  background:var(--white);
  border:3px solid var(--teal-500);
  border-radius:50%;
  transform:translateX(-50%);
  box-shadow:0 0 0 4px var(--white);
}
.tl-item:nth-child(1) .tl-dot{border-color:var(--navy-700)}
.tl-item:nth-child(2) .tl-dot{border-color:var(--teal-500)}
.tl-item:nth-child(3) .tl-dot{border-color:var(--teal-500)}
.tl-item:nth-child(4) .tl-dot{border-color:var(--coral-500)}
.tl-item:nth-child(5) .tl-dot{border-color:var(--coral-500)}
.tl-item:nth-child(6) .tl-dot{border-color:var(--slate-400)}
.tl-week{
  font-size:.74rem;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--slate-500,#5b6675);
  font-weight:600;
  margin-bottom:.35rem;
}
.tl-name{
  font-size:1rem;
  font-weight:600;
  color:var(--navy-900);
  line-height:1.3;
  margin-bottom:.25rem;
}
.tl-desc{
  font-size:.85rem;
  color:var(--slate-600);
  line-height:1.4;
}
.tl-foot{
  margin-top:2.4rem;
  font-size:.95rem;
  color:var(--slate-600);
  font-style:italic;
}

/* Two-phase variant of the timeline — used on the 90-day slide */
.tl-grid.two-phase{grid-template-columns:1fr 2.5fr}
.tl-grid.two-phase .tl-name{font-size:1.1rem}

/* "Beyond the first pilot" block */
.post-90{
  margin-top:2.2rem;
  padding-top:1.5rem;
  border-top:1px solid var(--slate-200);
}
.post-90-head{
  display:flex;align-items:baseline;gap:.9rem;flex-wrap:wrap;
  margin-bottom:.9rem;
}
.post-90-tag{
  font-size:.74rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  color:var(--slate-600);
  font-weight:700;
}
.post-90-note{
  font-size:.92rem;
  color:var(--slate-600);
  margin:0;
  font-style:italic;
}
.phase-chips{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:.7rem;
}
.phase-chip{
  display:flex;
  flex-direction:column;
  gap:.25rem;
  padding:.85rem 1rem;
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius);
  border-left:3px solid var(--teal-500);
  box-shadow:var(--shadow-sm);
}
.phase-chip:nth-child(1){border-left-color:var(--coral-500)}
.phase-chip-tag{
  font-size:.7rem;
  letter-spacing:.14em;
  text-transform:uppercase;
  font-weight:700;
  color:var(--teal-500);
}
.phase-chip:nth-child(1) .phase-chip-tag{color:var(--coral-500)}
.phase-chip-name{
  font-size:.95rem;
  font-weight:600;
  color:var(--navy-900);
  line-height:1.25;
}
.phase-chip-desc{
  font-size:.82rem;
  color:var(--slate-600);
  line-height:1.35;
}

/* ============================================================
   Slide 9 — pilot choice
   ============================================================ */
.pilot-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:1.5rem;
  margin-top:2.2rem;
}
.pilot-card{
  background:var(--white);
  border-radius:var(--radius-lg);
  padding:1.8rem;
  border:1px solid var(--slate-200);
  box-shadow:var(--shadow-sm);
  position:relative;
  display:flex;flex-direction:column;
}
.pilot-card .badge{
  position:absolute;
  top:-12px;left:1.8rem;
  font-size:.74rem;
  font-weight:700;
  letter-spacing:.14em;
  text-transform:uppercase;
  padding:.35rem .75rem;
  border-radius:999px;
  background:var(--white);
  border:1px solid var(--slate-200);
  box-shadow:var(--shadow-sm);
}
.pilot-card.a .badge{color:var(--coral-500);border-color:var(--coral-300)}
.pilot-card.b .badge{color:var(--teal-500);border-color:var(--teal-300)}
.pilot-card h3{font-size:1.4rem;margin:0 0 .35rem}
.pilot-card .audience{
  font-size:.88rem;color:var(--slate-600);
  margin-bottom:1rem;font-weight:500;
}
.pilot-card p{font-size:.96rem;color:var(--slate-700);margin-bottom:1rem}
.pilot-card .ms{
  display:flex;flex-wrap:wrap;gap:.4rem;
  margin-top:auto;
  padding-top:1rem;
  border-top:1px solid var(--slate-200);
}
.cta-line{
  margin-top:1.8rem;
  text-align:center;
  font-size:1.05rem;
  font-weight:500;
  color:var(--navy-900);
}
.cta-line em{color:var(--teal-500);font-weight:600}

/* ============================================================
   Slides 10-11 — pilot detail
   ============================================================ */
.pilot-detail{
  display:grid;
  grid-template-columns:1.05fr 1fr;
  gap:2.2rem;
  margin-top:1.8rem;
  align-items:start;
}
.pilot-problem h3,.pilot-solution h3{
  font-size:.78rem;
  letter-spacing:.16em;
  text-transform:uppercase;
  margin-bottom:.85rem;
  font-weight:600;
}
.pilot-problem h3{color:var(--slate-600)}
.pilot-solution h3{color:var(--coral-500)}
.pilot-detail.b .pilot-solution h3{color:var(--teal-500)}
.pilot-problem ul li{
  display:flex;gap:.7rem;
  margin-bottom:.85rem;
  font-size:1rem;color:var(--slate-700);line-height:1.5;
}
.pilot-problem ul li::before{
  content:'';
  flex:0 0 6px;height:6px;width:6px;
  margin-top:.6rem;
  border-radius:50%;
  background:var(--slate-400);
}
.metrics-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:1rem;
  margin-bottom:1.4rem;
}
.metric-card{
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius);
  padding:1.1rem 1.2rem;
  box-shadow:var(--shadow-sm);
}
.pilot-detail .stat-num{font-size:clamp(2rem,3.4vw,2.8rem)}
.sources-line{
  margin-top:1.2rem;
  padding-top:1rem;
  border-top:1px solid var(--slate-200);
  font-size:.86rem;
  color:var(--slate-600);
}
.sources-line strong{display:block;font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--slate-500,#5b6675);margin-bottom:.4rem;font-weight:600}
.sources-line code{
  display:inline-block;
  background:var(--paper-2);
  color:var(--navy-700);
  padding:.18rem .5rem;
  border-radius:6px;
  font-family:'Inter',inherit;
  font-size:.84rem;
  font-weight:500;
  margin:.15rem .3rem .15rem 0;
}

/* ============================================================
   Slide 12 — Dr. Baker workflow
   ============================================================ */
.workflow{
  margin-top:1.8rem;
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:.6rem 1.2rem;
}
.wf-step{
  display:grid;
  grid-template-columns:36px 1fr;
  gap:.85rem;
  align-items:start;
  padding:.7rem .85rem;
  border-radius:var(--radius);
  border:1px solid var(--slate-200);
  background:var(--white);
}
.wf-num{
  width:30px;height:30px;
  background:var(--navy-900);
  color:var(--white);
  border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:.88rem;font-weight:700;
  font-variant-numeric:tabular-nums;
}
.wf-step:nth-child(7) .wf-num,
.wf-step:nth-child(8) .wf-num{background:var(--coral-500)}
.wf-step:nth-child(10) .wf-num{background:var(--teal-500)}
.wf-text{font-size:.94rem;color:var(--slate-700);line-height:1.4}
.wf-text strong{font-weight:600}

/* ============================================================
   Slide 13 — architecture
   ============================================================ */
.arch{
  margin-top:1.8rem;
  display:grid;
  grid-template-columns:1fr;
  gap:.55rem;
}
.layer{
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius);
  padding:1.05rem 1.4rem;
  display:grid;
  grid-template-columns:200px 1fr;
  gap:1.5rem;
  align-items:center;
  box-shadow:var(--shadow-sm);
  position:relative;
}
.layer-name{
  display:flex;align-items:center;gap:.7rem;
  font-size:1rem;font-weight:600;color:var(--navy-900);
  letter-spacing:-.005em;
}
.layer-icon{
  width:34px;height:34px;
  border-radius:8px;
  background:var(--paper-2);
  display:flex;align-items:center;justify-content:center;
  flex:0 0 34px;
}
.layer-icon svg{width:18px;height:18px;color:var(--navy-700)}
.layer.action .layer-icon{background:rgba(242,107,91,.12)}
.layer.action .layer-icon svg{color:var(--coral-500)}
.layer.workflow .layer-icon{background:rgba(26,192,198,.14)}
.layer.workflow .layer-icon svg{color:var(--teal-500)}
.layer-detail{
  font-size:.92rem;color:var(--slate-700);line-height:1.4;
  display:flex;flex-wrap:wrap;gap:.35rem;
}
.layer-pill{
  font-size:.8rem;
  background:var(--paper);
  color:var(--navy-700);
  padding:.25rem .55rem;
  border-radius:6px;
  border:1px solid var(--slate-200);
  font-weight:500;
}

/* ============================================================
   Slide 14 — risk pillars
   ============================================================ */
.pillar-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:1rem;
  margin-top:1.8rem;
}
.pillar{
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius);
  padding:1.3rem 1.4rem;
  box-shadow:var(--shadow-sm);
  display:flex;flex-direction:column;gap:.6rem;
}
.pillar-icon{
  width:38px;height:38px;
  border-radius:10px;
  background:linear-gradient(135deg,var(--paper-2) 0%,var(--paper) 100%);
  display:flex;align-items:center;justify-content:center;
  color:var(--teal-500);
}
.pillar-icon svg{width:20px;height:20px}
.pillar h3{font-size:1rem;color:var(--navy-900);margin:0}
.pillar p{font-size:.9rem;color:var(--slate-600);margin:0;line-height:1.4}

/* ============================================================
   Slide 15 — metrics + ops
   ============================================================ */
.split{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:2rem;
  margin-top:1.8rem;
}
.split-card{
  background:var(--white);
  border:1px solid var(--slate-200);
  border-radius:var(--radius-lg);
  padding:1.7rem;
  box-shadow:var(--shadow-sm);
}
.split-card h3{
  font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;
  margin-bottom:1rem;font-weight:600;
}
.split-card.metrics h3{color:var(--coral-500)}
.split-card.ops h3{color:var(--teal-500)}
.split-card ul li{
  display:flex;gap:.7rem;
  margin-bottom:.7rem;
  font-size:.96rem;color:var(--slate-700);line-height:1.4;
}
.split-card ul li svg{flex:0 0 18px;width:18px;height:18px;margin-top:2px;color:inherit}
.split-card.metrics ul li svg{color:var(--coral-500)}
.split-card.ops ul li svg{color:var(--teal-500)}

/* ============================================================
   Slide 16 — closing
   ============================================================ */
.closing-quote{
  font-size:clamp(1.6rem,2.8vw,2.4rem);
  font-weight:500;
  line-height:1.3;
  color:var(--white);
  letter-spacing:-.012em;
  max-width:980px;
  border-left:4px solid var(--coral-500);
  padding:1rem 0 1rem 2.2rem;
  margin:0 0 1.5rem;
}
.closing-sub{
  font-size:1.05rem;
  color:#C9D3E0;
  max-width:880px;
  margin:0 0 3rem 2.4rem;
  line-height:1.55;
}
.next-steps{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:1rem;
  margin-top:1.5rem;
}
.step{
  background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.12);
  border-radius:var(--radius-lg);
  padding:1.4rem 1.5rem;
  backdrop-filter:blur(8px);
}
.step-num{
  font-size:.74rem;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:var(--teal-300);
  font-weight:700;
  margin-bottom:.5rem;
}
.step h4{font-size:1.1rem;color:var(--white);margin:0 0 .35rem;font-weight:600}
.step p{font-size:.92rem;color:#C9D3E0;margin:0;line-height:1.45}
.signoff{
  margin-top:3rem;
  padding-top:1.6rem;
  border-top:1px solid rgba(255,255,255,.12);
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:1rem;
  font-size:.9rem;
  color:#9DB1C8;
}
.signoff .brand{font-size:1rem}

/* ============================================================
   Responsive — keep readable on smaller laptops
   ============================================================ */
/* Scope to `screen`: Letter @96dpi (816px) is below 980px, so a bare query
   would fire during print and collapse every grid to one column. */
@media screen and (max-width:980px){
  .cols-2,.tracks,.pilot-grid,.pilot-detail,.split,.next-steps,.metrics-grid,.workflow,.check-grid{grid-template-columns:1fr}
  .pillar-grid{grid-template-columns:repeat(2,1fr)}
  .tl-grid{grid-template-columns:repeat(3,1fr);gap:1rem 1rem}
  .tl-grid.two-phase{grid-template-columns:1fr;gap:1rem}
  .timeline::before{display:none}
  .tl-item{padding-top:0;padding-left:1.2rem;border-left:2px solid var(--teal-500)}
  .tl-dot{display:none}
  .layer{grid-template-columns:1fr;gap:.6rem}
  .phase-chips{grid-template-columns:repeat(2,1fr)}
}
@media screen and (max-width:640px){
  .pillar-grid{grid-template-columns:1fr}
  .tl-grid{grid-template-columns:1fr}
  .phase-chips{grid-template-columns:1fr}
  .compare th,.compare td{font-size:.92rem;padding:.8rem .9rem}
  #counter{top:.7rem;right:.7rem;font-size:.7rem;padding:.35rem .65rem}
  #print-btn{bottom:.7rem;left:.7rem}
}

/* ============================================================
   Print rules — clean PDF export
   ============================================================ */
@media print{
  html{scroll-snap-type:none;scroll-behavior:auto}
  #progress,#counter,#print-btn,.scroll-hint,.slide-num{display:none !important}
  .slide{
    min-height:auto;
    page-break-after:always;
    break-after:page;
    padding:2.2cm 1.8cm;
    background:var(--white) !important;
    color:var(--slate-900) !important;
  }
  .slide.dark{
    background:var(--white) !important;
    color:var(--slate-900) !important;
  }
  .slide.dark h1,.slide.dark h2,.slide.dark h3,.slide.dark .hero-title,.slide.dark strong,
  .slide.dark .pullquote,.slide.dark .closing-quote{color:var(--navy-900) !important}
  .slide.dark .lede,.slide.dark .hero-sub,.slide.dark .closing-sub,.slide.dark .step p{color:var(--slate-700) !important}
  .slide.dark .hero-meta,.slide.dark .signoff,.slide.dark .step{
    background:var(--paper) !important;
    border:1px solid var(--slate-300) !important;
    color:var(--slate-700) !important;
  }
  .slide.dark .pullquote{border-left-color:var(--coral-500) !important}
  .slide.dark .closing-quote{border-left-color:var(--coral-500) !important}
  .slide.dark .eyebrow{color:var(--teal-500) !important}
  .slide.dark .hero-tag,.slide.dark .attribution-tag,.slide.dark .step-num{color:var(--coral-500) !important}
  .slide.dark .tj-logo{color:var(--navy-900) !important}
  .signoff-tagline{color:var(--slate-700) !important;border-left-color:var(--slate-300) !important}
  .card,.pilot-card,.track,.metric-card,.split-card,.layer,.pillar,.critique,.wf-step{
    box-shadow:none !important;
    break-inside:avoid;
  }
  .compare{box-shadow:none !important}
  body{font-size:12pt}
  h1,.h-hero,.hero-title{font-size:30pt !important}
  h2,.h-section{font-size:20pt !important}
  .lede,.hero-sub{font-size:13pt !important}
  @page{margin:0;size:auto}
}
```

### Techjays wordmark `<symbol>`

Paste this once, just inside `<body>`, before any visible content. Then reference with `<svg class="tj-logo"><use href="#tj-logo"/></svg>` anywhere in the deck. The wordmark paths use `currentColor` (with two `#6872FF` accent paths kept literal so the orange-purple T-shape always shows through).

```html
<svg aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">
  <defs>
    <symbol id="tj-logo" viewBox="0 0 223 41">
      <!-- 12 path elements forming the Techjays wordmark.
           Verbatim source: docs/ValleyRAA/valleyraa-techjays-proposal.html:1068–1080.
           Copy that block directly — the paths are tuned for the 223×41 viewBox. -->
    </symbol>
  </defs>
</svg>
```

### Persistent UI markup

Paste these three nodes immediately after the `<symbol>` block. They are wired up by the script in §5.

```html
<div id="progress" aria-hidden="true"></div>
<div id="counter" aria-live="polite">01 / 16</div>
<button id="print-btn" type="button" onclick="window.print()" aria-label="Print or save as PDF">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"></polyline>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
    <rect x="6" y="14" width="12" height="8"></rect>
  </svg>
  Print / Save PDF
</button>
```

### Script

The full script from §5 (50 lines) goes just before `</body>`. Verbatim source: `docs/ValleyRAA/valleyraa-techjays-proposal.html:1747–1816`.

---

_Canonical reference: `docs/ValleyRAA/valleyraa-techjays-proposal.html`. Update this guide alongside the reference any time the proposal design system evolves._
