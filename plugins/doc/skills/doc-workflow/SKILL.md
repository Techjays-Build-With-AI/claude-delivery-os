---
name: doc-workflow
description: >
  Generate a polished, interactive HTML workflow document following the
  Techjays standard: dark-navy header, gold accent, fixed left sidebar
  navigation, an interactive phased SVG swimlane flow diagram with hover-over
  tooltips, a per-phase value panel showing before/after state (current pain →
  AI solution) and the efficiency gain (hours saved), metric KPI cards, and a
  systems retained/retired grid. Use this skill whenever the user wants to
  walk through the scope of a project as a phased flow, or asks to create,
  build, or update a workflow document, process flow, future-state document,
  or AI automation flow. Triggers: "workflow document", "workflow generation",
  "process flow", "swimlane", "future-state doc", "walk through the workflow".
  Part of the Techjays Documentation Agent; invoked by /doc:workflow.
---

# Workflow Document Skill

This skill produces a single self-contained `.html` file following the
Techjays workflow-document standard: an interactive, phased **Process Flow**
walkthrough of a project's scope — SVG swimlane with hover tooltips, a
per-phase before/after value panel with the efficiency gain, KPI cards, and a
systems retained/retired grid. No tabs, no calculator, no milestone, no vision
pages.

---

## Operating contract (Delivery OS)

This skill is part of the Techjays **Documentation Agent**. It produces one
**self-contained, offline-portable HTML file** — no external CSS/JS/CDN/webfont.

- **Read `delivery-os-conventions`** if a Delivery OS workspace is present (not required) — including **§8**, which makes the scope's **Mermaid flows the living source** for this branded SVG swimlane. Your job here is to *render* those flows into the Techjays swimlane, not to invent a new flow; the swimlane is the client-facing **projection** of the same journey.
- **Source content from the workspace when it exists.** Draft the phases, actors,
  swimlane steps, and the before/after value panels from `ba-output/scope.md`
  (the module Current→Future state, business rules, exceptions), and in particular
  its **§3.x.3 Master Flow** and **§3.x.4 Use Cases** — the Mermaid `flowchart`
  blocks are the authoritative node/branch structure: the **master flow** maps to a
  phase's decision skeleton (each labelled branch is a route to a use case), and
  each **use case's own flow** provides that route's steps, its decision/exit nodes,
  and the worked example behind a node's tooltip. Also use
  `ba-output/workflow-register.md` (WF steps, actors, systems, exceptions) and
  `shared-context/` (stakeholders, system landscape). Preserve the Mermaid branch
  **labels and decision points** faithfully (a `{…}` diamond becomes a Decision
  node; each labelled edge becomes an arrow with that condition) so the SVG and the
  scope can't drift. Use real names and the client's real numbers for KPIs and
  hours-saved; **never fabricate** — mark any unknown metric `[[NEEDS: …]]` and list
  it back to the user.
- **Write the output to `doc-output/`** (create it on first use), keeping the
  naming convention below: `doc-output/[CLIENT]-[TOPIC]-[DDMonYYYY].html`. If
  there's no workspace, write beside the working directory and note it.
  **Save the HTML as UTF-8 (no BOM); don't route it through a shell/editor that
  re-encodes it** — non-ASCII glyphs (§, ×, →, …) double-encode into mojibake
  (`§`→`Â§`) on a Windows code page despite `<meta charset="utf-8">`. After
  writing, verify the file has no `Â`/`â€`/`Ã` sequences before returning.
- **Voice:** no em-dashes (—) in on-page text; no "not X but Y" contrastive
  negation; address the client by name. (En-dashes in ranges are fine.)

---

## Step 1 - Gather content from the user

Ask (or infer from context) these items before writing any HTML:

1. **Project name** - e.g. 'Acme Corp - Employee Onboarding'
2. **Client / org name** - shown in the header overline
3. **Document subtitle** - one sentence describing scope
4. **Meta pills** - 2-4 key facts (Client, Phase, Scope, Date)
5. **Phases / steps** - ordered list, each with: phase name, actor type (ai/human/system/vendor), 2-3 bullet points
6. **Actors / swimlane columns** - who appears as columns in the SVG (e.g. HR Manager, AI Platform, IT & Vendors)
7. **KPI metrics** - 3-6 headline numbers with labels and sub-labels
8. **Systems retained / retired** - names and brief descriptions

If the user provides a BRD, process document, or existing content, extract all of the above from it. **When a Delivery OS workspace exists, prefer sourcing from `ba-output/scope.md`, `ba-output/workflow-register.md`, and `shared-context/`** — map each scope module or workflow to a phase, its actors to swimlane columns, its Current→Future state to the value panel (current pain → AI solution), and its stated numbers to KPIs and hours-saved. For a module whose scope has a **§3.x.3 master flow and §3.x.4 use cases**, drive the swimlane straight off the Mermaid: the master-flow branch point becomes the phase's Decision node, and each use case becomes the branch it leads to (with that use case's own flow supplying the downstream nodes). Never invent metrics; mark unknowns `[[NEEDS: …]]`.

---

## Step 2 - Build the HTML file

Read these reference files **in order** before writing:

1. `references/design-tokens.md` - CSS variables, colour palette, typography, actor colour table
2. `references/page-structure.md` - HTML skeleton, header, sidebar nav, sticky col header, footer, core CSS
3. `references/components.md` - metric KPI cards, systems grid, swimlane legend
4. `references/svg-swimlane.md` - SVG orientation, coordinate system, defs, node types, arrows, value panel
5. `references/javascript.md` - scroll-spy, swimlane tooltip, KPI tooltip

Produce **one single `.html` file**. No external CSS or JS files. No CDN calls.

### File naming convention

Write to `doc-output/` (create it if absent): `doc-output/[CLIENT-ABBREV]-[TOPIC]-[DDMonYYYY].html`

Example: `doc-output/Acme-Onboarding-19Jun2026.html`

---

## Step 3 - Content substitution rules

| Template element | What to replace with |
|---|---|
| Header overline | Client name in ALL CAPS |
| h1 title | Project + document type |
| Meta pills | Client, phase, date, scope |
| Sidebar nav | One nav-item per phase/section |
| Swimlane actor columns | Actual actor names for this project |
| Swimlane node colours | Map actor types to standard palette (design-tokens.md) |
| KPI numbers | Actual project metrics |
| Systems retained/retired | Actual systems for this client |
| Footer text | Project name, version, date, confidentiality notice |

---

## Step 4 - Quality checklist

### SVG swimlane (CRITICAL)
- [ ] SVG is **VERTICAL** - phases flow top-to-bottom as horizontal band rows; actors are **columns** left-to-right
- [ ] Do NOT create a horizontal flowchart with phases as columns - that is wrong
- [ ] viewBox is `0 0 {total_width} {total_height}` - width = 140 + (N_actors x 184) + 14 + 258
- [ ] `<defs>` includes: `filter id='ns'` (drop shadow), `marker id='arr'` (arrow), `linearGradient id='ghdr'`
- [ ] Phase band backgrounds alternate `#f4f7ff` / `#f7fafd`; column header bar uses `fill='url(#ghdr)'`
- [ ] Value panel is a **right-side column** (last 258px of viewBox width) - NOT a bottom strip

### Node fill colours (CRITICAL)
- [ ] All nodes use **LIGHT fills** with coloured borders - NOT dark or solid fills
  - Human/Action: `fill='#e8f0fb'` `stroke='#2471a3'`
  - AI/Automation: `fill='#e6f7ed'` `stroke='#1e8449'`
  - Decision: `fill='#fdf3d9'` `stroke='#c9a84c'`
  - Exit/Hold: `fill='#fdeaea'` `stroke='#c0392b'` `stroke-dasharray='5 3'`
  - START/END pill only: `fill='#0e7a4f'` dark green, white text
- [ ] Every node has `filter='url(#ns)'` (drop shadow)

### Arrow routing (CRITICAL)
- [ ] Every `<line>` has either constant x (vertical) OR constant y (horizontal) - **never both changing**
- [ ] Only the **last segment** of a multi-line path has `marker-end='url(#arr)'`
- [ ] 'No' branches: horizontal first across the band, then vertical up/down to target node edge
- [ ] 'Yes' branches: vertical first to target row, then horizontal across to target column
- [ ] Cross-phase transitions use a 3-segment path through the phase gap (down -> across -> into next phase)

### Tooltip data attributes (CRITICAL)
- [ ] Swimlane nodes: `data-phase='N'` `data-title='...'` `data-desc='bullet 1||bullet 2||bullet 3'`
- [ ] Do NOT use JSON in `data-tip` on swimlane nodes - JS reads `n.dataset.title` and `n.dataset.desc.split('||')`
- [ ] KPI cards: `data-kpi='Label'` and `data-tip='<HTML string>'` - hover (mouseenter), not onclick

### Value panel (per-phase right column)
- [ ] Each phase has a value panel card in the right-side SVG column
- [ ] 3 sections per card: **CURRENT PAIN** (red bullets) / **AI SOLUTION** (green bullets) / **HRS SAVED** (large gold number)
- [ ] Use exact y-coordinate offsets from `references/svg-swimlane.md` Section 11

### Page structure
- [ ] `<div id='swim-tip'></div>` and `<div id='kpi-tip'></div>` are first elements after `<body>`
- [ ] `body { padding-left: 180px }` - never remove
- [ ] Header uses `margin-left: -180px; padding-left: calc(180px + 48px)` to bleed behind sidebar
- [ ] Sticky col header `#sticky-col-hdr` `data-svgw` values match exact SVG pixel column widths
- [ ] No external dependencies - system-ui font, no CDN

### General
- [ ] File name follows `[CLIENT]-[TOPIC]-[DDMonYYYY].html` convention
- [ ] Metric numbers are gold `#c9a84c`
- [ ] Systems grid has `.retained` (green header) and `.retired` (red header)
- [ ] Footer has project name, date, confidentiality line

---

## Common mistakes to avoid

- Do NOT omit `body { padding-left: 180px }` - the sidebar breaks without it
- Do NOT make the SVG horizontal (phases as columns) - it must be VERTICAL (phases as rows)
- Do NOT use dark fills on nodes - all nodes use LIGHT background fills with coloured borders
- Do NOT put swimlane tooltip data in a JSON blob - use `data-title` and `data-desc` with `||` separators
- Do NOT use onclick for KPI tooltips - use mouseenter/mouseleave
- Do NOT put the value panel at the bottom of the SVG - it is a right-side column inside the SVG
- Do NOT draw diagonal arrow lines - all arrows must be horizontal or vertical segments only
- Do NOT put `marker-end` on intermediate arrow segments - only on the final segment hitting the target node
- Do NOT hardcode client-specific content from any sample document - replace all placeholder names, metrics, and labels with actual project content

---

## Reference files

| File | Contents |
|---|---|
| references/design-tokens.md | CSS variables, colour swatches, typography scale, actor colour table |
| references/page-structure.md | HTML skeleton, header, sidebar nav, sticky col header, footer, core CSS |
| references/components.md | Metric KPI cards, systems grid, swimlane legend, swimlane note |
| references/svg-swimlane.md | SVG orientation, coordinate system, defs, all node types, arrows, value panel, arrow routing rules |
| references/javascript.md | Scroll-spy, sticky header, swimlane tooltip (data-title/data-desc), KPI tooltip (mouseenter) |
