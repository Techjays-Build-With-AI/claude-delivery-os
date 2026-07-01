---
name: doc-magic-board
description: >
  Design a "magic board" — a self-contained, pannable & zoomable infinite-canvas HTML
  presentation with a smooth guided fly-through tour and an overview. Use when the user
  wants to turn a system, architecture, concept, workflow, plan, process, user journey,
  strategy, or roadmap into a spatial board they can present from, walk through page by
  page (next / next / next, each stop framed full-screen), or zoom around like a Miro
  board. Triggers: "magic board", "create a board", "walkthrough board", "workflow board",
  "infinite canvas", "Figma/Miro/Excalidraw-style", "spatial deck", "zoomable diagram
  board". Also use to improve or extend an existing magic board.
---

# Magic Board

A magic board is one self-contained HTML file: an **infinite canvas** of cards laid out
in space, with **pan** (drag), **zoom** (scroll toward cursor), a **guided tour** that
smoothly flies and frames each card full-screen in narrative order (click next / next /
next), and an **overview** that fits the whole board. It is the best of a Miro board
(spatial overview) and a slide deck (guided walkthrough) at once — perfect for showing a
workflow or "our understanding" of a system to a client or team.

**You are the designer.** This skill gives you the design language, the method, the
interaction engine, and a playbook of ideas — then trust your judgement. Invent card
types, diagrams, and layouts that fit the content. Don't fill a fixed template.

## Operating contract (Delivery OS)

This skill is part of the Techjays **Documentation Agent**. It produces one **self-contained,
offline-portable HTML file** — no external CSS/JS/CDN/webfont, so it opens from an email
attachment with the network unplugged.

- **Read `delivery-os-conventions`** if a Delivery OS workspace is present (it isn't required).
- **Source content from the workspace when it exists.** For a workflow/understanding board,
  draft the spine and cards from `ba-output/scope.md`, `ba-output/workflow-register.md`, and
  `shared-context/` (the modules, workflows, actors, systems). Use real names and the
  client's real numbers; never fabricate — mark unknowns as `[[NEEDS: …]]` and list them back.
- **Write the output to `doc-output/`** (create it on first use), timestamped so runs never
  collide: `doc-output/board-<topic>-<timestamp>.html`. If there's no workspace, write beside
  the working directory and note it.
- **Voice:** no em-dashes (—) in on-card text; no "not X but Y" contrastive negation; address
  the client by name where relevant. (En-dashes in ranges are fine.)

## The only fixed part: the interaction engine

Reliable pan/zoom/tour is fiddly, so reuse **`assets/board-engine.js`** from this skill dir
(copy its contents into a `<script>` so the file stays single-and-self-contained). It needs:

- `#viewport` (fixed, full-screen, `overflow:hidden`) → `#canvas` (`transform-origin:0 0`)
- `.card` elements inside `#canvas`, each with a **unique id**, positioned by inline
  `left/top/width` in canvas px (let height be natural — the engine frames by `offset*`)
- a global `window.tour = [{id, t}, …]` in narrative order
- optional chrome it wires if present: `#btn-prev #btn-next #btn-ov #tourtitle #counter`

Everything else — the visual design, the cards, the diagrams — is yours.

## Design language (the house style — adapt freely)

- **Warm editorial, not corporate.** Light paper canvas with a faint dot grid; cards are
  white with a soft shadow, a title bar, and a thin top accent stripe in the card's color.
- **Type:** Fraunces (serif) for headlines/titles, Archivo (sans) for body, JetBrains
  Mono for labels, code, and captions. Serif italics for emphasis and "quotes". (If you must
  stay fully offline with no webfont fetch, fall back to a system serif + system sans and keep
  the same hierarchy.)
- **Palette:** a warm ink on paper, with five accents used to *theme clusters* — amber,
  teal, sage, violet, coral. One accent per "part" reads cleanly. Muted/faint greys for
  secondary text. High contrast — it's projected.
- **A dark title card** to open (warm near-black gradient, glowing amber accent word) —
  it anchors the start and adds drama.
- **Generous space.** Few words per card; let diagrams and one-line takeaways carry it.
- **Honesty chips** (built / wip / gap) in card headers so an audience reads maturity at
  a glance.
- You may reskin (swap the palette in `:root`, go dark, change fonts) when the brand or
  mood calls for it — keep contrast and restraint. To echo the Techjays proposal system,
  you may theme with teal/coral and the client's accent.

## Method

1. **Find the spine.** What's the narrative? Order the pieces like a talk: a hook/problem,
   the how, the payoff. The **tour is the story** — design that order first.
2. **Cluster into parts.** Group cards into 3–6 "parts" that read **left-to-right** across
   the canvas, each under a big faded `PART N · Name` label. Parts are the chapters.
3. **Design each card to its content** (see the idea library). Title + one diagram, or a
   tight table, or a two-column "every step", or two mini-cards + a key line.
4. **Place without overlap.** Compute each card's footprint before the next (a tall SVG or
   step list can be 400–550px; wide step-cards ~1000px). Stack a cluster in a column,
   ~40–80px gaps; ~600–900px between clusters. Correct positions matter — the tour and the
   overview both frame by real geometry.
5. **Wire the tour**, save to `doc-output/board-<topic>-<timestamp>.html`, then **offer a
   browser QA pass** (overview fits, every stop frames cleanly, no overlaps) and ask about
   enhancements.

## Shape it to the use case

The board's *content and arc* should change with intent — ask or infer which this is:

- **Workflow / "our understanding"** (the common Delivery OS case) → cards are the **steps of
  the workflow** in order (inbox → processing → decision → system-of-record), one card per
  step or subsystem, laid left-to-right; call out what's automated vs human, the systems each
  step touches, and the exceptions. Tour = the workflow start to finish. Draft it from the BA
  scope's modules and `workflow-register` when a workspace exists.
- **User journey** → cards are **moments in time** (persona's steps), laid left-to-right as a
  timeline; show what the user does, sees, feels, and what the system does behind it.
- **Comprehensive system / architecture deep-dive** → cluster by subsystem; one card per
  major mechanic; turn key flows into two-column "every step" cards; add a runtime
  architecture card and a data-model card. Tour = problem → design → each subsystem → payoff.
- **Concept / "how it works" explainer** → fewer cards, each one idea, building intuition;
  lean on one strong diagram per concept and a memorable one-liner; light on tables.
- **Strategy / decisions** → cards are choices and tradeoffs ("chose X over Y, because Z"),
  principles/tenets, and the payoff; a flywheel or 2×2 as the centerpiece.
- **Roadmap / phases** → cards are phases with gates; a timeline spine across the top; each
  phase card lists what ships and the gate; close on the end-state.
- **Comparison / before-after** → paired columns, a migration arc, a "what changed / what
  stayed" card.

When unsure which, ask one question: *"Is this a workflow/understanding board, a user journey,
a system deep-dive, a concept explainer, a strategy/decision story, or a roadmap?"* — then
shape accordingly.

## Idea library (inspiration, not rules — invent beyond these)

- **Diagram card** — inline SVG: boxes + arrows for a flow, an architecture, a pipeline.
  (Define each `<marker>` with a **unique id per card**.)
- **Table card** — key → description rows for data models, tables, edge types, glossaries.
- **Two-column "every step"** — a compact vertical SVG flow + a numbered step list. The way
  to make a flow *comprehensive*: zoom from overview into full detail.
- **Mini-cards** — two or three small framed ideas side by side, plus a key formula/line.
- **Knowledge / relationship graph** — a node-link SVG with **labelled, color-coded edges**
  (solid/dashed/dotted): shows relationships concretely instead of abstractly. High impact.
- **3D isometric "layers in space"** — stacked translucent parallelogram planes (rhombi at
  descending y-centers), nodes on each, lines climbing between them. Conveys hierarchy
  spatially; use isometric SVG (not CSS-3D) so it survives the canvas transform. A "wow".
- **Chart / curve** — a small plotted SVG (a sigmoid, a growth curve, a comparison) when a
  number tells the story.
- **Flywheel / cycle** — a ring of arrows for compounding/loops; great as a closer.
- **Closer card** — a payoff / "what it becomes" / call-to-action as the final tour stop.

## Make it sing

- A clear arc across clusters — problem → how → payoff. Order the tour like a talk.
- One or two **wow cards** (the 3D layers, a relationship graph, a flywheel) near the
  spatial center — they reward zooming out.
- Be **comprehensive where it counts** (two-column step cards) and **spare elsewhere**.
- **Honesty chips** for maturity; a strong **closer** to land the point.
- Short, numbered tour labels (`01 · …`) so the audience tracks progress.

## Gotchas

- **Unique SVG `<marker>` ids per card** (prefix them) — duplicate ids across cards make
  arrowheads vanish.
- Position cards via inline `left/top/width`; never transform a card individually — the
  engine frames by `offsetLeft/Top/Width/Height`.
- Size each SVG to its card so nothing clips; let card height be natural.
- Keep the engine intact — only `window.tour` and your cards/labels are yours to write.
- Keep it **single-file** — inline the engine, the CSS, and any SVG. No external fetches.
- After building, verify in a browser: the overview spans all clusters, the tour frames
  each card, and no two cards overlap.
