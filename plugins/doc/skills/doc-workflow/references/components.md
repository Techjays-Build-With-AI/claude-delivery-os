# Components

## Metric / KPI Cards

Cards sit in a 3-column grid. Each card shows a dark tooltip on **hover** (`mouseenter`).
Two data attributes required: `data-kpi` (label) and `data-tip` (pre-built HTML string).

```css
.metrics-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
/* Second row (overflow) — centred flex row */
.metrics-row-bottom { display:flex; justify-content:center; gap:18px; margin-top:18px; }
.metrics-row-bottom .metric-card { flex: 0 0 calc(33.33% - 9px); max-width: calc(33.33% - 9px); }

.metric-card {
  background: #fff; border-radius: 8px; padding: 24px 20px 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07); text-align: center; cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 6px 24px rgba(27,63,138,0.13); }
.metric-number { font-size: 36px; font-weight: 800; color: #c9a84c; line-height: 1; margin-bottom: 8px; letter-spacing: -0.5px; }
.metric-label  { font-size: 13px; font-weight: 700; color: #0d1b2a; margin-bottom: 4px; }
.metric-sub    { font-size: 11.5px; color: #6a7a8a; }
```

```html
<div class="metrics-row">
  <div class="metric-card"
    data-kpi="Hours Freed per Hire"
    data-tip="
      <div class='kt-section'>What manual hours are freed?</div>
      <div class='kt-row'><div class='kt-dot'></div><div>Recruiter manually calls candidates per language — 40 min each.</div></div>
      <hr class='kt-divider'>
      <div class='kt-future'>Future: AI sends multilingual outreach. Recruiter handles escalations only.</div>
    ">
    <div class="metric-number">~2.4 hrs</div>
    <div class="metric-label">Hours Freed per Hire</div>
    <div class="metric-sub">Across all phases</div>
  </div>
  <!-- repeat for each KPI; use .metrics-row-bottom for a second row of 3 -->
</div>
```

To link a metric number to dynamic JS updates, add an `id` to `.metric-number`:
```html
<div class="metric-number" id="cnt-per-hire">~2.4 hrs</div>
```

---

## Systems Grid (Retained vs Retired)

```css
.systems-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.systems-card { background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); overflow: hidden; }
.systems-card-header { padding: 14px 20px; font-size: 13px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
.systems-card-header.retained { background: #d4f0e3; color: #0e5c38; }
.systems-card-header.retired  { background: #fde8e8; color: #8a1a1a; }
.systems-card-body { padding: 16px 20px; }
.system-item { display: flex; align-items: flex-start; gap: 10px; padding: 7px 0; border-bottom: 1px solid #f0f2f5; font-size: 13px; color: #1a2a3a; }
.system-item:last-child { border-bottom: none; }
.system-mark { font-size: 13px; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
.system-mark.check { color: #0e7a4f; }
.system-mark.cross { color: #b02020; }
.system-item strong { font-weight: 600; }
.system-item span { color: #6a7a8a; font-size: 12.5px; }
```

```html
<div class="systems-grid">
  <div class="systems-card">
    <div class="systems-card-header retained">Systems Retained</div>
    <div class="systems-card-body">
      <div class="system-item">
        <span class="system-mark check">&#10003;</span>
        <div><strong>HRIS (Core)</strong> <span>— remains system of record; Hub writes back via SFTP on approval</span></div>
      </div>
    </div>
  </div>
  <div class="systems-card">
    <div class="systems-card-header retired">Systems Retired / Replaced</div>
    <div class="systems-card-body">
      <div class="system-item">
        <span class="system-mark cross">&#10007;</span>
        <div><strong>Excel Tracker</strong> <span>— replaced by real-time pipeline view in HR Hub</span></div>
      </div>
    </div>
  </div>
</div>
```

---

## Assumptions Cards

2-column grid of cards, each with a gold-underline heading. Use to document methodology, data sources, or key assumptions.

```css
.assumptions-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 20px; margin-top: 20px; }
.assumption-card { background: #fff; border-radius: 10px; border: 1px solid #e2e8f4; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.assumption-heading { font-size: 14px; font-weight: 700; color: #1a2a4a; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 2px solid #c9a84c; }
.assumption-body p { font-size: 13px; color: #3a4a5a; line-height: 1.65; margin-bottom: 8px; }
.assumption-body p:last-child { margin-bottom: 0; }
```

```html
<div class="assumptions-grid">
  <div class="assumption-card">
    <div class="assumption-heading">Volume Basis</div>
    <div class="assumption-body">
      <p>Based on [X] hires/month and [Y] candidates/month from discovery sessions.</p>
      <p>All figures subject to confirmation during implementation planning.</p>
    </div>
  </div>
</div>
```

---

## Swimlane Legend (above SVG)

Use LIGHT FILL swatches matching the actual SVG node colours — not dark solid colours.

```html
<div class="swimlane-legend">
  <span class="legend-label">Key:</span>
  <span class="legend-item">
    <span class="legend-swatch" style="background:#e6f7ed;border:1.5px solid #1e8449"></span>
    Automated by platform
  </span>
  <span class="legend-item">
    <span class="legend-swatch" style="background:#e8f0fb;border:1.5px solid #2471a3"></span>
    Human action required
  </span>
  <span class="legend-item">
    <span class="legend-swatch" style="background:#fdf3d9;border:1.5px solid #c9a84c"></span>
    Decision / conditional
  </span>
  <span class="legend-item">
    <span class="legend-swatch" style="background:#fdeaea;border:1.5px solid #c0392b;border-style:dashed"></span>
    Exit / adverse action
  </span>
</div>
```

```css
.swimlane-legend { margin-bottom: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 18px; font-size: 12px; color: #4a5a6a; }
.swimlane-legend .legend-label { font-weight: 600; color: #0d1b2a; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-swatch { width: 18px; height: 13px; border-radius: 3px; flex-shrink: 0; }
```

---

## Swimlane Note (below SVG)

```html
<p class="swimlane-note">Hover any node for detail &middot; [Key clarification about gates or compliance]</p>
```

```css
.swimlane-note { margin-top: 10px; font-size: 11.5px; color: #6a7a8a; font-style: italic; padding: 0 2px; }
```

---

## Section heading variants

Standard heading + sub:
```html
<h2 class="section-heading">Section Title</h2>
<p class="section-sub">One sentence description of what this section shows.</p>
```

Hero heading (larger visual weight, used on the Process Flow section):
```html
<h2 class="section-heading section-heading-hero">End-to-End Process Flow</h2>
```

```css
.section-heading-hero {
  font-size: 18px !important; font-weight: 700 !important;
  letter-spacing: normal !important; text-transform: none !important;
  color: #1a2a4a !important; margin-bottom: 16px !important;
}
.no-top-border { border-top: none !important; }
```
