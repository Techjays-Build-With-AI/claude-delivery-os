# Overview State Diagram

The hero of the page: one interactive SVG showing the **states the system (or a
unit of work) passes through** and the transitions between them. It answers
"how does the whole thing flow?" before the reader touches any module.

## Orientation and layout

- **Left-to-right main spine** for the happy path (entry → … → terminal), with
  branch/failure edges looping back or diverting off the spine. This reads as a
  state machine, not a swimlane.
- If the lifecycle is long (7+ states), wrap onto two rows (snake layout): row 1
  left-to-right, drop down, row 2 right-to-left. Keep the spine continuous.
- Pick a viewBox that fits without scaling text: about `220px` horizontal pitch
  per state, `150px` vertical between rows, `~120px` node width. A 9-state
  single row is roughly `viewBox="0 0 1600 260"`; two rows about `900 x 440`.
- Wrap the SVG in `.diagram-wrap` (scrolls horizontally on small screens).

## `<defs>` (unique ids, prefix `ov-`)

```svg
<defs>
  <marker id="ov-arr" markerWidth="9" markerHeight="9" refX="7.5" refY="3"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L7.5,3 L0,6 Z" fill="#5a6a85"/>
  </marker>
  <marker id="ov-arr-fail" markerWidth="9" markerHeight="9" refX="7.5" refY="3"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L7.5,3 L0,6 Z" fill="#c0392b"/>
  </marker>
  <filter id="ov-sh" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="1.5" stdDeviation="1.6" flood-opacity="0.16"/>
  </filter>
</defs>
```

Marker ids MUST be unique across the whole page. The module diagrams use their
own prefixes (`m1-arr`, `m2-arr`, …). Duplicate ids make arrowheads disappear.

## State node

Each state is a `<g class="state" data-state="ID" data-title="…"
data-desc="line1||line2||line3">` containing a rounded rect + centered label.
The `data-*` attributes drive the tooltip (JS reads `dataset.title` and
`dataset.desc.split('||')`) and the click-to-highlight (matched to edges by
`data-state`).

```svg
<g class="state" data-state="feature"
   data-title="Feature"
   data-desc="Small independently deliverable capability||Owns its implementation plan||Example: FT-1024 Login with MFA">
  <rect x="260" y="60" width="120" height="52" rx="9"
        fill="#e8f0fb" stroke="#2471a3" stroke-width="1.5" filter="url(#ov-sh)"/>
  <text x="320" y="90" text-anchor="middle" font-size="12.5" font-weight="600"
        fill="#12314d">Feature</text>
</g>
```

Node fills by kind (see design-tokens for the full table):

- Normal state: `fill="#e8f0fb" stroke="#2471a3"`
- Automated / CI / AI state: `fill="#e6f7ed" stroke="#1e8449"`
- Blocked / failure state: `fill="#fdeaea" stroke="#c0392b" stroke-dasharray="5 3"`
- Start / terminal pill: `fill="#0e7a4f" stroke="#0a5c38" rx="24"`, white text,
  give it `data-state` too so it participates in highlighting.

Decision gate as a diamond (`<polygon>`), `fill="#fdf3d9" stroke="#c9a84c"`,
label inside, e.g. "CI match?".

## Transition edges

Every edge is a `<path class="edge" data-from="A" data-to="B">` (or `<line>`)
with `marker-end`. Give each edge `data-from`/`data-to` so clicking a state can
light up its edges.

```svg
<!-- happy path: straight segment -->
<path class="edge" data-from="feature" data-to="plan"
      d="M380,86 H460" fill="none" stroke="#5a6a85" stroke-width="1.6"
      marker-end="url(#ov-arr)"/>

<!-- automated transition -->
<path class="edge edge-auto" data-from="merge" data-to="ci"
      d="M980,86 H1060" fill="none" stroke="#1e8449" stroke-width="1.6"
      marker-end="url(#ov-arr)"/>

<!-- failure branch back (dashed red, orthogonal 3-segment) -->
<path class="edge edge-fail" data-from="ci" data-to="plan"
      d="M1120,112 V150 H460 V112" fill="none" stroke="#c0392b" stroke-width="1.5"
      stroke-dasharray="5 4" marker-end="url(#ov-arr-fail)"/>
```

Routing rules:

- Segments are horizontal or vertical only (or a single smooth cubic if you
  prefer curves — but be consistent). No diagonal straight lines between nodes.
- `marker-end` goes on the **whole path** (it lands at the path's end), so build
  each transition as one `<path>` whose final point touches the target node's
  edge. Do not split one transition into several `<path>`s.
- Loop-back / failure edges route below the spine (drop down, travel back,
  rise into the target) so they don't cross node rows.
- The arrow tip should touch the target node border, not overlap its centre.

## Interactivity (wired in javascript.md)

- **Hover** a `.state`: show `#node-tip` with its title + desc bullets near the
  cursor. Give `.state { cursor: pointer; }` and a subtle hover via CSS:
  `.state:hover rect, .state:hover polygon { filter: url(#ov-sh); stroke-width: 2.4; }`
- **Click** a `.state`: add `.sel` to it, dim every edge whose `data-from` and
  `data-to` both differ from the selected id, and highlight (gold, thicker) the
  edges that touch it. Also dim the non-connected states. Click empty space or
  the same state again to reset. CSS classes:

```css
.edge { transition: stroke .15s, stroke-width .15s, opacity .15s; }
svg.has-sel .edge { opacity: .18; }
svg.has-sel .edge.lit { opacity: 1; stroke: #c9a84c !important; stroke-width: 2.6; }
svg.has-sel .state { opacity: .45; }
svg.has-sel .state.sel, svg.has-sel .state.adj { opacity: 1; }
.state.sel rect, .state.sel polygon { stroke: #c9a84c; stroke-width: 2.6; }
```

The JS toggles `has-sel` on the `<svg>`, `sel` on the clicked state, `adj` on
states connected to it, and `lit` on the touching edges (see javascript.md).

## Legend

Above the SVG, render the four legend swatches from design-tokens (automated,
manual, decision, blocked) so the colour code is explicit.

## Fidelity

- Use the spec's exact state names and order. Include EVERY transition the spec
  describes, especially the failure/branch ones ("if mismatch → blocked",
  "promotion blocked"). Those edges are the point of a state diagram.
- If the spec's lifecycle has a linear "then" chain plus a separate CI/promotion
  loop, show both: the linear spine and the loop that re-enters it.
- If a transition condition is unstated, do not invent it. Label the edge
  plainly (or leave it unlabelled) rather than guessing a rule.
