---
name: doc-spec-walkthrough
description: >
  Turn a specification, scope, or engineering-spec document into a polished,
  interactive HTML walkthrough that explains the whole system at a glance and
  then in depth. Produces one self-contained HTML file in the Techjays house
  style (dark-navy header, gold accent, fixed left sidebar nav): a top
  OVERVIEW STATE DIAGRAM showing the phases/states the system moves through
  (an interactive SVG state machine with hover detail and click-to-highlight
  transitions), followed by a drill-down SECTION PER FEATURE / MODULE, each
  with its own interactive workflow diagram and worked examples. Use whenever
  the user wants to "present a spec", "walk through the specification", turn a
  scope or spec doc into an interactive page, explain a system's phases and
  modules, or give stakeholders the full picture of how a system flows and
  breaks down. Triggers: "spec walkthrough", "walk through the spec",
  "present the specification", "spec presentation", "state diagram of the
  system", "explain the modules", "feature breakdown page", "interactive spec".
  Part of the Techjays Documentation Agent; invoked by /doc:walkthrough.
---

# Spec Walkthrough Skill

This skill turns a **specification / scope / engineering-spec document** into
one self-contained, interactive **HTML walkthrough** that lets a reader
understand the whole picture and then drill into the detail. It is the doc
agent's tool for *presenting a spec* rather than authoring one.

The output has three layers, top to bottom:

1. **Overview state diagram** — one interactive SVG that shows the **phases /
   states the system (or a unit of work) passes through** and the transitions
   between them. This is the "full picture" the reader sees first. Hovering a
   state reveals its detail; clicking a state highlights its inbound/outbound
   transitions.
2. **Module / feature sections** — the spec broken into its features and
   modules, one navigable section each. Every section carries its own compact
   **interactive workflow diagram** (the steps inside that module) plus one or
   more **worked examples** (a concrete run-through, e.g. a real feature ID
   moving through the steps).
3. **Reference strips** — a command/API catalog, a systems or object model, and
   the success criteria, rendered as scannable cards.

It is NOT the single-page swimlane of `doc-workflow` (one phased actor grid),
and NOT the infinite canvas of `doc-magic-board`. Reach for this skill when the
source is a **written spec** and the reader needs both a **state overview** and
a **module-by-module breakdown with examples** on one scrollable, sidebar-
navigated page. When the user wants an actor swimlane, use `doc-workflow`; when
they want a spatial fly-through, use `doc-magic-board`.

---

## Operating contract (Delivery OS)

Part of the Techjays **Documentation Agent**. It produces one **self-contained,
offline-portable HTML file** — no external CSS/JS/CDN/webfont, so it opens from
an email attachment with the network unplugged.

- **Read `delivery-os-conventions`** if a Delivery OS workspace is present (not
  required).
- **The source is the spec.** Draft every state, module, workflow step, command,
  and example from the supplied document (a `.md`, `.docx`, `.pdf`, or pasted
  text) or, when a Delivery OS workspace exists, from `ba-output/scope.md` and
  `shared-context/`. Use the spec's real names, IDs, and numbers. **Never
  fabricate.** If the spec states a fact, use it verbatim; if a number or detail
  the page needs is absent, mark it `[[NEEDS: …]]` and list it back to the user.
- **Do not invent metrics or outcomes.** This page explains what the spec says.
  Where the spec has no KPI, omit the KPI strip rather than inventing figures.
- **Write the output to `doc-output/`** (create it on first use), timestamped so
  runs never collide: `doc-output/walkthrough-<topic>-<timestamp>.html`. If
  there's no workspace, write beside the working directory and note it.
- **Encoding:** Save the HTML as **UTF-8 (no BOM)**; don't route it through a
  shell/editor that re-encodes it — non-ASCII glyphs (§, ×, →, …) double-encode
  into mojibake (`§`→`Â§`) on a Windows code page despite `<meta
  charset="utf-8">`. After writing, verify the file has no `Â`/`â€`/`Ã`
  sequences before returning. Prefer ASCII in copy where practical.
- **Voice:** no em-dashes (—) in on-page text; no "not X but Y" contrastive
  negation; write plainly and specifically. (En-dashes in numeric ranges are
  fine.)

---

## Step 1 — Read and model the spec

Before writing any HTML, read the whole source and extract this model. Write it
down (even as a scratch outline) so the page is faithful:

1. **Title, subtitle, audience, version/status** — for the header.
2. **The state machine.** Find the lifecycle the system (or a unit of work such
   as a feature, request, or record) moves through. List the **states in order**
   and the **transitions** between them, including any branch/failure edges
   (e.g. "if mismatch → blocked"). This becomes the overview state diagram. Most
   specs state this explicitly (a "Lifecycle", "Workflow", "Phases", or
   "Promotion" section); if several candidate lifecycles exist, pick the spine
   that best explains the whole system and note the others as module workflows.
3. **The modules / features.** The spec's major building blocks: core objects,
   subsystems, workflows, or numbered spec sections. Each becomes one page
   section. For each capture: name, one-line purpose, the **ordered steps**
   inside it (its mini-workflow), and any **example** the spec gives (an ID, a
   sample plan, a command run).
4. **The catalog.** Any table of commands/APIs/objects, and the success criteria
   or principles. These become reference strips.
5. **Open questions** — anything the page would want but the spec doesn't state,
   captured as `[[NEEDS: …]]`.

If the user passed a document, extract all of the above from it. If a Delivery
OS workspace exists, prefer `ba-output/scope.md` (modules, workflows) and
`shared-context/`. Ask the user only for what you truly cannot infer (usually
just: which lifecycle is the spine, or confirmation of the title).

---

## Step 2 — Build the HTML file

Read these reference files **in order** before writing:

1. `references/design-tokens.md` — CSS variables, colour palette, typography,
   state/actor colour table.
2. `references/page-structure.md` — HTML skeleton, header, sidebar nav,
   scroll-spy sections, footer, core CSS.
3. `references/state-diagram.md` — the overview state-machine SVG: node types,
   layout, transition edges, hover/click interactivity, the legend.
4. `references/module-sections.md` — the per-module section: the compact
   workflow diagram, the step list, the worked-example card, the catalog and
   criteria strips.
5. `references/javascript.md` — scroll-spy nav, node tooltips, click-to-
   highlight transitions, example toggles.

Produce **one single `.html` file**. All CSS and JS inline. No external files,
no CDN calls, no webfonts.

### File naming convention

Write to `doc-output/` (create it if absent):
`doc-output/walkthrough-<topic>-<DDMonYYYY>.html`

Example: `doc-output/walkthrough-jetrix-14Jul2026.html`

---

## Step 3 — Content mapping

| Page element | Sourced from the spec |
|---|---|
| Header overline | Product / system name in ALL CAPS |
| h1 title | Spec title + "Walkthrough" |
| Meta pills | Version, status, audience, date |
| Overview state diagram | The lifecycle states + transitions (Step 1.2) |
| State hover detail | What happens in that state (2-3 lines from the spec) |
| Sidebar nav | Overview + one item per module section + catalog |
| Module section title | Module / feature / spec-section name |
| Module workflow diagram | The ordered steps inside that module |
| Worked example card | The concrete example the spec gives (ID, plan, command) |
| Command / object catalog | The spec's command or object table |
| Success criteria strip | The spec's success criteria / principles |
| Footer | System name, version, date, "prepared by Techjays" |

---

## Step 4 — Quality checklist

### Overview state diagram (CRITICAL)
- [ ] Renders the actual states from the spec, in order, with **every
      transition** including branch/failure edges (dashed red for failure/exit).
- [ ] Each state node has `data-state`, `data-title`, `data-desc` (bullets
      joined by `||`) so hover shows detail. No JSON blobs in data attributes.
- [ ] Clicking a state highlights its inbound + outbound edges and dims the rest
      (see `references/javascript.md`).
- [ ] Nodes use **LIGHT fills with coloured borders** (per design-tokens). Start
      and terminal states use the filled pill style. No dark node fills.
- [ ] Edges are orthogonal (horizontal/vertical segments) or clean curves;
      `marker-end` only on the final segment reaching a node.
- [ ] Every `<marker>` / gradient / filter id is unique on the page.

### Module sections
- [ ] One section per module/feature, each reachable from the sidebar nav.
- [ ] Each has a compact workflow diagram (its ordered steps) AND at least one
      worked example, both drawn from the spec (or marked `[[NEEDS: …]]`).
- [ ] Worked examples use the spec's real IDs/values (e.g. `FT-1024`), not
      placeholders.
- [ ] Step lists and diagrams agree with each other and with the spec.

### Page structure & behaviour
- [ ] Fixed left sidebar; `body { padding-left: 180px }` present (never removed).
- [ ] Header/footer use the `margin-left: -180px` bleed so they span behind the
      sidebar.
- [ ] Tooltip overlay divs are the first elements after `<body>`.
- [ ] Scroll-spy: the active nav item updates as sections scroll into view.
- [ ] No external dependencies; system-ui font; opens offline.

### Fidelity & voice
- [ ] Nothing on the page contradicts or invents beyond the spec.
- [ ] Every unknown the page wanted is a visible `[[NEEDS: …]]`, also listed
      back to the user.
- [ ] No em-dashes, no contrastive negation, gold `#c9a84c` for accents/numbers.
- [ ] File saved UTF-8, no mojibake (`Â`/`â€`/`Ã`), name follows convention.

---

## Common mistakes to avoid

- Do NOT reproduce the `doc-workflow` actor swimlane — this page leads with a
  **state machine**, then module sections. Different shape.
- Do NOT invent states, metrics, or examples the spec doesn't contain. Mark
  gaps `[[NEEDS: …]]`.
- Do NOT drop the failure/branch transitions — the "if mismatch → blocked" edges
  are the interesting part of a state diagram.
- Do NOT use dark node fills or diagonal edges without markers on intermediate
  segments.
- Do NOT split into multiple files or fetch a CDN/webfont — one offline HTML.
- Do NOT remove `body { padding-left: 180px }` or the header/footer bleed.
- Do NOT reuse SVG marker/gradient ids across the overview and module diagrams —
  prefix them (`ov-arr`, `m1-arr`, …) or arrowheads vanish.

---

## Reference files

| File | Contents |
|---|---|
| references/design-tokens.md | CSS variables, colour swatches, typography, state/node colour table |
| references/page-structure.md | HTML skeleton, header, sidebar nav, scroll-spy sections, footer, core CSS |
| references/state-diagram.md | Overview state-machine SVG: node types, layout, transitions, hover/click interactivity, legend |
| references/module-sections.md | Per-module section: workflow diagram, step list, worked-example card, catalog + criteria strips |
| references/javascript.md | Scroll-spy nav, node tooltips, click-to-highlight transitions, example toggles |
