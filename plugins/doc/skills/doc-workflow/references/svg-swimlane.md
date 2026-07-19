# SVG Swimlane

> **Source of the flow (Delivery OS).** When the scope has Mermaid flows, this SVG is their **branded projection**, not a fresh flow (see `delivery-os-conventions` §8). Translate the scope's **§3.x.3 master flow** and **§3.x.4 use-case flows** node-for-node: a Mermaid `{diamond}` becomes a **Decision** node, each labelled edge becomes an arrow carrying that condition, a stadium `([…])` becomes a START/END pill, and each master-flow branch routes to the use case it names. Keep the labels and branch conditions verbatim so the swimlane and the scope stay 1:1; only the presentation (columns, phases, styling) is added here.

## 1. Orientation — VERTICAL (phases as rows, actors as columns)

**This is the canonical orientation.** Phases run top-to-bottom (each phase is a horizontal band).
Actors run left-to-right (each actor is a column).

```
|  Phase labels  | Actor col 1 | Actor col 2 | Actor col 3 | Actor col 4 | Value panel |
|─── PHASE 1 ────|             |    [node]   |    [node]   |             |  card P1   |
|─── PHASE 2 ────|   [node]   |    [gate?]  |    [node]   |             |  card P2   |
|─── PHASE 3 ────|             |    [node]   |    [node]   |   [node]    |  card P3   |
```

Do NOT rotate this to put phases as columns — that is incorrect.

---

## 2. ViewBox coordinate system

### Column widths (standard 5-actor layout)

| Zone | x start | width | x end |
|------|---------|-------|-------|
| Phase label col | 0 | 140 | 140 |
| Actor col 1 | 140 | 184 | 324 |
| Actor col 2 | 324 | 184 | 508 |
| Actor col 3 | 508 | 184 | 692 |
| Actor col 4 | 692 | 184 | 876 |
| Actor col 5 | 876 | 184 | 1060 |
| Gap | 1060 | 14 | 1074 |
| Value panel | 1074 | 258 | 1332 |
| **Total viewBox width** | | **1332** | |

For **4 actors**, use 230px columns: zones at 140, 370, 600, 830, 1060 → then gap 14px → value panel 1074-1332.

### Row heights

- Header bar: h = 55px (y=0 to y=55)
- Each phase band: h = 180–260px depending on node count in that phase
- No fixed grid — set each phase height to fit its content

### Total viewBox height

`55 (header) + sum of phase heights`

---

## 3. Required SVG `<defs>`

Always include these in every swimlane SVG:

```xml
<defs>
  <!-- Drop shadow for nodes -->
  <filter id="ns" x="-12%" y="-12%" width="124%" height="124%">
    <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#00000015"/>
  </filter>
  <!-- Arrow marker -->
  <marker id="arr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
    <path d="M0,0 L0,6 L8,3 z" fill="#8090a8"/>
  </marker>
  <!-- Gradient for phase label column and header bar -->
  <linearGradient id="ghdr" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#1a2a4a"/>
    <stop offset="100%" stop-color="#243b6e"/>
  </linearGradient>
</defs>
```

---

## 4. Background layers (draw first, in order)

### 4a. Value panel background (right column, full height)

```xml
<rect x="1074" y="0" width="258" height="{total_height}" fill="#f0f4f9"/>
```

### 4b. Phase band background rects (alternating colours, actor area only)

```xml
<!-- Odd phases: #f4f7ff, Even phases: #f7fafd -->
<rect x="140" y="{phase_y}"  width="920" height="{phase_h}" fill="#f4f7ff"/>
<rect x="140" y="{phase2_y}" width="920" height="{phase2_h}" fill="#f7fafd"/>
<!-- ...continue alternating... -->
```

### 4c. Phase label column background (left col, per phase, gradient)

```xml
<rect x="0" y="{phase_y}" width="140" height="{phase_h}" fill="url(#ghdr)"/>
<!-- ...one per phase... -->
```

### 4d. Column header bar (top, full width)

```xml
<rect x="0"    y="0" width="1060" height="55" fill="url(#ghdr)" rx="6"/>
<rect x="1074" y="0" width="258"  height="55" fill="url(#ghdr)" rx="4"/>
<rect x="0"    y="48" width="1060" height="7" fill="url(#ghdr)"/>
```

---

## 5. Separator lines

### Phase separator lines (horizontal, full width)

```xml
<line x1="0" y1="{phase_boundary_y}" x2="1332" y2="{phase_boundary_y}" stroke="#cdd5e5" stroke-width="1"/>
```

### Actor column dividers (vertical dashed, inside actor area only)

```xml
<line x1="{col_x}" y1="55" x2="{col_x}" y2="{total_h}" stroke="#dde4f0" stroke-width="0.75" stroke-dasharray="3 3"/>
```

One line per column boundary (not on outer edges).

---

## 6. Column headers (inside header bar)

```xml
<!-- Actor column headers — gold text, letter-spacing -->
<text x="{col_center}" y="31" text-anchor="middle" font-size="10.5" font-weight="700"
      fill="#c9a84c" letter-spacing="0.06em">ACTOR NAME</text>

<!-- Value panel header -->
<text x="1203" y="26" text-anchor="middle" font-size="10.5" font-weight="700"
      fill="#c9a84c" letter-spacing="0.06em">PHASE VALUE</text>
<text x="1203" y="41" text-anchor="middle" font-size="8.5"
      fill="rgba(255,255,255,0.65)">Impact at go-live</text>
```

---

## 7. Phase labels (left column)

```xml
<text text-anchor="middle" font-size="12" font-weight="700" fill="#c9a84c" letter-spacing="0.05em">
  <tspan x="70" y="{phase_mid_y - 10}" font-size="9.5">PHASE N</tspan>
  <tspan x="70" dy="14" font-size="8.5" fill="rgba(255,255,255,0.78)" letter-spacing="0.03em">PHASE</tspan>
  <tspan x="70" dy="11" font-size="8.5" fill="rgba(255,255,255,0.78)" letter-spacing="0.03em">NAME</tspan>
</text>
```

---

## 8. Node types

**CRITICAL: All nodes use `filter="url(#ns)"` for the drop shadow.**
**Text uses two `<tspan>` lines with `dominant-baseline="middle"` centering.**

### 8a. Human / Action node (light blue)

```xml
<g class="swimnode" data-phase="P1" data-title="Node Title"
   data-desc="Detail one||Detail two||What replaces the manual step">
  <rect x="{cx-74}" y="{cy-18}" width="148" height="36" rx="8"
        fill="#e8f0fb" stroke="#2471a3" stroke-width="1.5" filter="url(#ns)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-size="10.5" fill="#1a1a2e">
    <tspan x="{cx}" dy="-5" font-weight="600">Line 1</tspan>
    <tspan x="{cx}" dy="13">Line 2</tspan>
  </text>
</g>
```

### 8b. AI / Automation node (light green)

```xml
<g class="swimnode" data-phase="P2" data-title="AI Step"
   data-desc="What AI does||How it replaces manual work">
  <rect x="{cx-74}" y="{cy-18}" width="148" height="36" rx="8"
        fill="#e6f7ed" stroke="#1e8449" stroke-width="1.5" filter="url(#ns)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-size="10.5" fill="#1a1a2e">
    <tspan x="{cx}" dy="-5" font-weight="600">AI Step</tspan>
    <tspan x="{cx}" dy="13">Sub-label</tspan>
  </text>
</g>
```

### 8c. Decision diamond (gold)

Points formula: top(cx,cy-22) right(cx+38,cy) bottom(cx,cy+22) left(cx-38,cy)

```xml
<g class="swimnode" data-phase="P2" data-title="Gate: Decision?"
   data-desc="What is checked||YES path: action||NO path: action">
  <polygon points="{cx},{cy-22} {cx+38},{cy} {cx},{cy+22} {cx-38},{cy}"
           fill="#fdf3d9" stroke="#c9a84c" stroke-width="1.8" filter="url(#ns)"/>
  <text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="9.5" font-weight="700" fill="#7a5a00">Gate</text>
  <text x="{cx}" y="{cy+9}" text-anchor="middle" font-size="9"   fill="#7a5a00">Label?</text>
</g>
<!-- YES/NO branch labels -->
<text x="{cx+6}" y="{cy+36}" text-anchor="start" font-size="8.5" fill="#1e8449" font-weight="700">YES</text>
<text x="{cx-44}" y="{cy}" text-anchor="end" font-size="8.5" fill="#c0392b" font-weight="700">NO</text>
```

### 8d. Exit / Adverse node (dashed red)

```xml
<g class="swimnode" data-phase="P3" data-title="Exit: Decline"
   data-desc="What triggers this exit||FCRA or compliance note">
  <rect x="{cx-74}" y="{cy-14}" width="148" height="28" rx="8"
        fill="#fdeaea" stroke="#c0392b" stroke-width="1.5" stroke-dasharray="5 3" filter="url(#ns)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-size="10.5" font-weight="600" fill="#8a1a1a">Decline</text>
</g>
```

### 8e. START pill (green)

```xml
<g class="swimnode" data-phase="P1" data-title="Start: New Hire Request"
   data-desc="Trigger: hiring manager initiates process">
  <rect x="{cx-50}" y="{cy-13}" width="100" height="26" rx="13"
        fill="#0e7a4f" stroke="#0a5c38" stroke-width="1.5" filter="url(#ns)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-size="10" font-weight="700" fill="#ffffff" letter-spacing="0.04em">START</text>
</g>
```

### 8f. Passive / System node (grey)

```xml
<g class="swimnode" data-phase="P2" data-title="System Step"
   data-desc="What the system does automatically">
  <rect x="{cx-74}" y="{cy-18}" width="148" height="36" rx="8"
        fill="#f8f9fb" stroke="#b0bac8" stroke-width="1.5" filter="url(#ns)"/>
  <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle"
        font-size="10" font-weight="600" fill="#3a4a5a">System Step</text>
</g>
```

---

## 9. Node data attributes (`data-desc` format)

Use **double-pipe `||`** as the separator between bullet points. No JSON.

```xml
data-phase="P3"
data-title="AI: Multilingual Outreach"
data-desc="Sends SMS + WhatsApp in 6 languages on recruiter trigger||EN, ES, PL, SQ, SO, HT supported||Replaces recruiter making manual phone calls per candidate"
```

The tooltip JS splits on `||` to create individual bullet rows. Keep each segment under ~100 chars.

---

## 10. Arrows

```xml
<!-- Simple horizontal or vertical arrow -->
<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
      stroke="#5e6e82" stroke-width="1.6" marker-end="url(#arr)"/>

<!-- L-shaped path (node bottom to next phase node) -->
<path d="M{cx},{node_bottom} L{cx},{mid_y} L{next_cx},{mid_y} L{next_cx},{next_node_top}"
      fill="none" stroke="#5e6e82" stroke-width="1.6" marker-end="url(#arr)"/>

<!-- Dashed green arrow (approved / fast path) -->
<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
      stroke="#1e8449" stroke-width="1.4" stroke-dasharray="5 3" marker-end="url(#arr)"/>

<!-- Dashed red arrow (rejected / exit path) -->
<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
      stroke="#c0392b" stroke-width="1.4" marker-end="url(#arr)"/>
```

---

## 11. Value panel — RIGHT-SIDE COLUMN

The value panel is the last column of the SVG (x=1074–1332, 258px wide).
Each phase gets one white card aligned vertically with its phase band.
Each card has **three sections**: Current Pain Points → Proposed Solution → Hours Saved.

### Layout (assuming phase_h = 230px, card height = 214px)

```
Card y+8  to y+222  (214px total)
─────────────────────────────────
 Phase label          y+20  (muted uppercase, centered)
─────────────────────────────────
 CURRENT PAIN label   y+36  (red-tinted, left-aligned)
 Pain bullet 1        y+50
 Pain bullet 2        y+63
─────────────────────────────────
 AI SOLUTION label    y+81  (green, left-aligned)
 Solution bullet 1    y+95
 Solution bullet 2    y+108
─────────────────────────────────
 HRS SAVED label      y+124 (gold uppercase, left-aligned)
 Hours number         y+148 (large gold, centered)
 Hours sub-label      y+164
─────────────────────────────────
```

### Background

```xml
<!-- Full-height panel background -->
<rect x="1074" y="0" width="258" height="{total_height}" fill="#f0f4f9"/>
<!-- Panel header cell (same gradient as column headers) -->
<rect x="1074" y="0" width="258" height="55" fill="url(#ghdr)"/>
<text x="1203" y="32" text-anchor="middle" font-size="12" font-weight="700" fill="#c9a84c">Phase Value</text>
```

### One card per phase — full template

```xml
<!-- Card background -->
<rect x="1084" y="{py+8}" width="236" height="214" rx="6" fill="#ffffff" stroke="#e8edf5" stroke-width="1"/>

<!-- Phase label (centered, muted) -->
<text x="1203" y="{py+22}" text-anchor="middle" font-size="8" font-weight="700"
      fill="#8090a8" letter-spacing="0.1em">PHASE N — LABEL</text>

<!-- ── SECTION 1: CURRENT PAIN ── -->
<line x1="1090" y1="{py+29}" x2="1314" y2="{py+29}" stroke="#f0e8e8" stroke-width="1"/>
<text x="1090" y="{py+39}" font-size="8" font-weight="700" fill="#c0392b" letter-spacing="0.08em">CURRENT PAIN</text>
<!-- Bullet 1 -->
<circle cx="1094" cy="{py+51}" r="2.5" fill="#e74c3c" opacity="0.6"/>
<text x="1100" y="{py+54}" font-size="9.5" fill="#3a4a5a">[Pain point line 1a — keep to ~28 chars]</text>
<text x="1100" y="{py+65}" font-size="9.5" fill="#3a4a5a">[Pain point line 1b if needed]</text>
<!-- Bullet 2 -->
<circle cx="1094" cy="{py+76}" r="2.5" fill="#e74c3c" opacity="0.6"/>
<text x="1100" y="{py+79}" font-size="9.5" fill="#3a4a5a">[Pain point line 2]</text>

<!-- ── SECTION 2: AI SOLUTION ── -->
<line x1="1090" y1="{py+89}" x2="1314" y2="{py+89}" stroke="#e8f0e8" stroke-width="1"/>
<text x="1090" y="{py+99}" font-size="8" font-weight="700" fill="#1e8449" letter-spacing="0.08em">AI SOLUTION</text>
<!-- Bullet 1 -->
<circle cx="1094" cy="{py+111}" r="2.5" fill="#1e8449" opacity="0.6"/>
<text x="1100" y="{py+114}" font-size="9.5" fill="#3a4a5a">[Solution line 1a — ~28 chars]</text>
<text x="1100" y="{py+125}" font-size="9.5" fill="#3a4a5a">[Solution line 1b if needed]</text>
<!-- Bullet 2 -->
<circle cx="1094" cy="{py+136}" r="2.5" fill="#1e8449" opacity="0.6"/>
<text x="1100" y="{py+139}" font-size="9.5" fill="#3a4a5a">[Solution line 2]</text>

<!-- ── SECTION 3: HOURS SAVED ── -->
<line x1="1090" y1="{py+149}" x2="1314" y2="{py+149}" stroke="#f5f0e0" stroke-width="1"/>
<text x="1090" y="{py+159}" font-size="8" font-weight="700" fill="#c9a84c" letter-spacing="0.08em">HRS SAVED / HIRE</text>
<text x="1203" y="{py+187}" text-anchor="middle" font-size="28" font-weight="800" fill="#c9a84c">[X.X hrs]</text>
<text x="1203" y="{py+203}" text-anchor="middle" font-size="9" fill="#8090a8">[e.g. form chase + portal eliminated]</text>
```

### Writing rules for each section

**CURRENT PAIN — what the team does manually today:**
- 1-2 bullets, each ≤ 28 characters per line (use 2 `<text>` lines if longer)
- Concrete and specific — name the tool, action, or frequency (e.g. "Manual Sterling login 3×/day")
- Red bullet circles `fill="#e74c3c"` opacity 0.6

**AI SOLUTION — what the platform does instead:**
- 1-2 bullets, same length limit
- Action-oriented ("API submits in <60s", "OCR extracts cert data")
- Green bullet circles `fill="#1e8449"` opacity 0.6

**HRS SAVED — quantified time saving:**
- Single large number in gold (e.g. `2.5 hrs`, `0.76 hrs`, `1.8 hrs`)
- Sub-label names what's eliminated (e.g. "form chase + follow-up")
- Use discovery figures or calculated rates; note if estimated

### Adjusting for different phase heights

If `phase_h ≠ 230`:
- Scale all `py+` offsets proportionally, keeping section dividers at ~38% / ~65% / 100% of card height
- Minimum usable phase height: 190px (reduce font-size to 9px for bullets)
- For very tall phases (>300px): add a third bullet per section

---

## 12. Sticky column header widths

In the `#sticky-col-hdr` bar, add `data-svgw` equal to the SVG pixel width of each column so JavaScript can scale them:

```html
<div class="sch-left"  data-svgw="140">Phases</div>
<div class="sch-cell"  data-svgw="184">Actor 1</div>
<div class="sch-cell"  data-svgw="184">Actor 2</div>
<!-- ... -->
<div style="flex:0 0 auto;width:0" data-svgw="14"></div>  <!-- gap -->
<div class="sch-right" data-svgw="258">Phase Value</div>
```

The JS scales each cell's pixel width by `viewBoxWidth / containerPixelWidth`.

---

## 13. Arrow routing rules (CRITICAL)

Incorrect arrows are the most common SVG mistake. Follow these rules without exception.

### Rule 1 — Orthogonal paths only (no diagonals)

Every arrow must travel horizontally OR vertically. **Never change both x and y in the same `<line>` segment.**

```xml
<!-- ✅ CORRECT — L-shape: two segments -->
<line x1="599" y1="645" x2="599" y2="687" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="599" y1="687" x2="714" y2="687" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>

<!-- ❌ WRONG — diagonal: both x and y change in one line -->
<line x1="668" y1="655" x2="714" y2="680" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
```

### Rule 2 — `marker-end` on the LAST segment only

Multi-segment paths are drawn as separate `<line>` elements. Only the **final** line going into the target node gets `marker-end="url(#arr)"`. All earlier segments have no marker attribute.

```xml
<!-- 3-segment path: down → left → down into target -->
<line x1="783" y1="709" x2="783" y2="745" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="783" y1="745" x2="599" y2="745" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="599" y1="745" x2="599" y2="758" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
```

### Rule 3 — Connect to node edges, not centres

Calculate the exact edge pixel where the arrow leaves or enters a node:

| Node element | Entry/exit points |
|---|---|
| `<rect x="X" y="Y" width="W" height="H">` | Top: (X+W/2, Y) · Bottom: (X+W/2, Y+H) · Left: (X, Y+H/2) · Right: (X+W, Y+H/2) |
| `<polygon points="cx,t cx+d,my cx,b cx-d,my">` (diamond) | Top: (cx, t) · Bottom: (cx, b) · Left: (cx-d, my) · Right: (cx+d, my) |
| START/END pill `<rect rx="13">` | Same as rect: centre of each edge |

```xml
<!-- Rect at x=530 y=758 w=138 h=44 — bottom centre = (599, 802), top centre = (599, 758) -->
<!-- Arrow arrives at top centre: -->
<line x1="599" y1="745" x2="599" y2="758" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
```

### Rule 4 — "No" / back-path routing (decision to earlier node)

When the "No" branch goes back to a node in a column to the LEFT of the decision:

1. Start from the decision diamond's **left point** `(cx - d, mid_y)`
2. Draw horizontal segment all the way to the **centre-x of the target column**
3. Draw vertical segment up or down to the **target node edge**
4. `marker-end` on the vertical segment only

```xml
<!-- Decision at cx=599, left-point at x=538, y=268 -->
<!-- Target: Escalate box at x=163, width=138 → centre-x=232, bottom edge y=262 -->
<line x1="538" y1="268" x2="232" y2="268" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="232" y1="268" x2="232" y2="262" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
<text x="385" y="263" text-anchor="middle" font-size="10" fill="#c0392b">No</text>
```

### Rule 5 — "Yes" / forward-path routing (decision to next phase or cross-lane)

When the "Yes" branch goes to a node in a **different column** than the decision:

1. Start from the decision diamond's **bottom point** `(cx, bottom_y)`
2. Draw vertical segment down to the **centre-y of the target node**
3. Draw horizontal segment across to the **target node's left or right edge**
4. `marker-end` on the horizontal segment only

```xml
<!-- Decision bottom at (599, 645) — target Register Creds at x=714, centre-y=687 -->
<line x1="599" y1="645" x2="599" y2="687" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="599" y1="687" x2="714" y2="687" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
<text x="606" y="659" font-size="10" fill="#1e8449">Yes</text>
```

### Rule 6 — Cross-phase transitions

When an arrow crosses a phase boundary (horizontal band separator), use a 3-segment path with a **waypoint in the gap** between phases:

```xml
<!-- From node bottom (783, 709) → through phase gap at y=745 → left to AI col → into next phase node top (599, 758) -->
<line x1="783" y1="709" x2="783" y2="745" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="783" y1="745" x2="599" y2="745" stroke="#a0aec0" stroke-width="1.5"/>
<line x1="599" y1="745" x2="599" y2="758" stroke="#a0aec0" stroke-width="1.5" marker-end="url(#arr)"/>
```

### Rule 7 — Label placement

Place "Yes" / "No" / condition labels adjacent to the arrow, never overlapping a node:

- For a **vertical arrow** going down: label at `x = cx + 7`, `y = midpoint_y` (right of line)
- For a **horizontal arrow** going left (No path): label above the line at `y = line_y - 5`, centred between start and end x
- Font: `font-size="10"`, colour `#1e8449` for Yes, `#c0392b` for No

### Arrow routing checklist

Before finalising any SVG:

- [ ] Every `<line>` has either constant x (vertical) or constant y (horizontal) — never both changing
- [ ] Only the last segment of each multi-line path has `marker-end="url(#arr)"`
- [ ] All start/end coordinates land exactly on a node's calculated edge pixel
- [ ] "No" paths travel horizontal first (across the band), then vertical (up/down to target)
- [ ] "Yes" paths travel vertical first (down to target row), then horizontal (across to target column)
- [ ] Cross-phase arrows use a 3-segment L-Z-L path through the phase gap
- [ ] Labels do not overlap any node rect or polygon
