# Module / Feature Sections

After the overview, the spec is broken into its modules/features, one section
each. A module section teaches one building block three ways at once: a compact
**workflow diagram** (its steps as a flow), a **numbered step list** (the same
steps in words), and a **worked example** (a concrete run-through from the spec).
Diagram, list, and example must agree.

## Section layout

Two columns inside `.module-grid`: the workflow diagram on the left, the step
list + example card stacked on the right. On narrow screens it collapses to one
column (see page-structure CSS).

```html
<section id="sec-mod-3" class="section">
  <p class="eyebrow">Module 03</p>
  <h2 class="section-heading">Brownfield Workflow</h2>
  <p class="section-sub">How an existing project moves a feature from scope to merged context.</p>
  <div class="module-grid">
    <div class="module-flow"><!-- compact vertical flow SVG, prefix m3- --></div>
    <div class="module-side">
      <ol class="step-list">
        <li><strong>Onboard.</strong> JETRIX imports pages, APIs, database, entities, relationships, existing features. A canonical architecture context is created.</li>
        <li><strong>Plan scope.</strong> BA uploads scope; <code>scope-plan</code> breaks it into features and creates epics.</li>
        <!-- … one li per step … -->
      </ol>
      <div class="example-card">
        <div class="ex-label">Worked example</div>
        <div class="ex-figure">FT-1024</div>
        <div class="ex-row"><span class="k">Feature</span><span>Login with MFA</span></div>
        <div class="ex-row"><span class="k">Command</span><code>feature-plan FT-1024</code></div>
        <div class="ex-row"><span class="k">Plan adds</span><span>Login page, MFA endpoint, MFA Secret + Recovery Codes tables</span></div>
        <div class="ex-row"><span class="k">Status</span><span>Development &rarr; Merged to DEV</span></div>
      </div>
    </div>
  </div>
</section>
```

## Compact workflow diagram (per module)

A small **vertical** flow of the module's steps: a stack of step nodes joined by
downward arrows, with any branch shown to the side. Keep it narrow (one column
of nodes) so it sits beside the step list.

- viewBox roughly `0 0 260 [90 * n_steps]`. Node ~200 wide, ~46 tall, centred.
- Node styling matches the state table (light fill + coloured border). Use the
  automated tint (`#e6f7ed`/`#1e8449`) for steps the spec says the platform does
  automatically, the manual tint (`#e8f0fb`/`#2471a3`) for developer/BA actions.
- **Unique marker id per module** (`m3-arr`, not `arr`). Duplicate ids across
  the page break arrowheads.
- Steps can carry the same `data-title`/`data-desc` hover tooltip as overview
  states if extra detail helps; keep the on-node label short.

```svg
<svg viewBox="0 0 260 430" xmlns="http://www.w3.org/2000/svg" width="260">
  <defs>
    <marker id="m3-arr" markerWidth="9" markerHeight="9" refX="7.5" refY="3"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L7.5,3 L0,6 Z" fill="#5a6a85"/>
    </marker>
  </defs>
  <g class="step" data-title="Onboard" data-desc="Import pages, APIs, DB, entities||Canonical context created">
    <rect x="30" y="14" width="200" height="46" rx="8" fill="#e8f0fb" stroke="#2471a3" stroke-width="1.5"/>
    <text x="130" y="42" text-anchor="middle" font-size="12" font-weight="600" fill="#12314d">1 · Onboard project</text>
  </g>
  <line x1="130" y1="60" x2="130" y2="88" stroke="#5a6a85" stroke-width="1.6" marker-end="url(#m3-arr)"/>
  <!-- … more nodes + connectors … -->
</svg>
```

## Worked-example card

The most important trust signal: a concrete instance from the spec. Rules:

- Use the spec's **real** identifiers and values (e.g. `FT-1024`, the sample
  generated plan, the exact command names). Never a made-up placeholder.
- Lead with the headline figure (`.ex-figure`, e.g. the feature ID) then rows of
  `key: value`. Wrap commands in `<code>`.
- If the module has no example in the spec, either omit the card or show a
  `<span class="needs">[[NEEDS: example]]</span>` — do not invent one.
- Multiple small examples (e.g. brownfield vs greenfield) can be two example
  cards stacked in `.module-side`.

## Choosing the modules

Map the spec's structure to sections. Typical sources of a module:

- A "Core Objects" section → one module per object (Scope, Feature, Plan, Task),
  or a single "Core Objects" section with a small relationship flow.
- Each numbered workflow (Brownfield, Greenfield, CI Reconciliation, Environment
  Promotion) → its own module section with its steps.
- Cross-cutting explainers ("Why feature-owned context?") → a short section with
  the benefits as a list (no diagram needed if there are no steps).

Order sections to match the spec's own flow so the sidebar reads like a table of
contents. Aim for 4-8 module sections; if the spec is huge, group related
sub-sections rather than making 15 tiny ones.

## Catalog strip (commands / objects)

When the spec has a command or object table, render it as `.catalog-grid` cards
(command in mono, purpose beneath). This gives the reader a quick reference
without hunting through the sections.

## Success-criteria strip

Render the spec's success criteria / core principles as `.criteria-card`s, each
with a green tick. Use the spec's wording. This closes the page on outcomes.
