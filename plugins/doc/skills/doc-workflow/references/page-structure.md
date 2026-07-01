# Page Structure

## HTML skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[CLIENT] &mdash; [TOPIC]</title>
<style>
  /* all CSS here — no external stylesheets */
</style>
</head>
<body>

<!-- TOOLTIP OVERLAYS — place first, before nav -->
<div id="swim-tip"></div>
<div id="kpi-tip"></div>

<!-- SIDEBAR NAV -->
<nav id="side-nav" aria-label="Page sections">
  <!-- PROCESS FLOW nav items — data-page="flow" -->
  <a class="nav-item active" href="#sec-flow" data-target="sec-flow" data-page="flow">
    <span class="nav-dot"></span><span class="nav-label">Process Flow</span>
  </a>
  <a class="nav-item" href="#sec-kpi" data-target="sec-kpi" data-page="flow">
    <span class="nav-dot"></span><span class="nav-label">Impact Metrics</span>
  </a>
  <a class="nav-item" href="#sec-systems" data-target="sec-systems" data-page="flow">
    <span class="nav-dot"></span><span class="nav-label">Systems Map</span>
  </a>
</nav>

<!-- STICKY SWIMLANE COL HEADER -->
<!-- data-svgw values must match the SVG viewBox column pixel widths exactly -->
<div id="sticky-col-hdr">
  <div class="sch-cell sch-left" data-svgw="140">Phases</div>
  <div class="sch-cell"          data-svgw="184">Actor 1</div>
  <div class="sch-cell"          data-svgw="184">Actor 2</div>
  <div class="sch-cell"          data-svgw="184">Actor 3</div>
  <div class="sch-cell"          data-svgw="184">Actor 4</div>
  <div class="sch-cell"          data-svgw="184">Actor 5</div>
  <div style="flex:0 0 auto;width:0" data-svgw="14"></div>
  <div class="sch-cell sch-right" data-svgw="258">Phase Value</div>
</div>

<!-- SITE HEADER (margin-left trick stretches it behind the sidebar) -->
<header class="site-header">
  <div class="left">
    <div class="overline">[CLIENT NAME IN CAPS]</div>
    <h1>[Document Title]</h1>
    <p class="subtitle">[One sentence scope description]</p>
    <div class="meta-pills">
      <span class="meta-pill"><strong>Client:</strong> [Name]</span>
      <span class="meta-pill"><strong>Phase:</strong> Future State</span>
      <span class="meta-pill"><strong>Scope:</strong> [Brief scope]</span>
      <span class="meta-pill"><strong>Date:</strong> [DDMonYYYY]</span>
    </div>
  </div>
  <div class="right">
    <span>[Version]</span>
    <span>[Date]</span>
  </div>
</header>

<!-- TAB BAR — always present; sits between </header> and first page wrapper -->

<!-- PAGE: PROCESS FLOW -->
<div class="content-wrap">

  <!-- PROCESS FLOW SECTION -->
  <div id="sec-flow" class="section">
    <h2 class="section-heading section-heading-hero">End-to-End Process Flow</h2>
    <p class="section-sub">[Future State · System · All N phases across all actors]</p>

    <!-- Legend above swimlane -->
    <div class="swimlane-legend">
      <span class="legend-label">Key:</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#e6f7ed;border:1.5px solid #1e8449"></span>Automated by platform</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#e8f0fb;border:1.5px solid #2471a3"></span>Human action required</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#fdf3d9;border:1.5px solid #c9a84c"></span>Decision / conditional</span>
      <span class="legend-item"><span class="legend-swatch" style="background:#fdeaea;border:1.5px solid #c0392b;border-style:dashed"></span>Exit / adverse action</span>
    </div>

    <!-- Swimlane SVG wrapper -->
    <div class="swimlane-wrap" id="swimlane-wrap">
      <!-- SVG here — see svg-swimlane.md -->
    </div>

    <p class="swimlane-note">Hover any node for detail &middot; [Key compliance or gate note]</p>
  </div>

  <!-- IMPACT METRICS SECTION -->
  <div id="sec-kpi" class="section">
    <h2 class="section-heading">Key Impact Metrics</h2>
    <p class="section-sub">[Projected efficiency gains at current volume. Hover any card for detail.]</p>
    <div class="metrics-row">
      <!-- metric-card × 3 — see components.md -->
    </div>
  </div>

  <!-- SYSTEMS MAP SECTION -->
  <div id="sec-systems" class="section">
    <h2 class="section-heading">Systems Landscape</h2>
    <p class="section-sub">Systems retained as the foundation vs processes retired by the new platform.</p>
    <div class="systems-grid">
      <!-- systems-card retained + systems-card retired — see components.md -->
    </div>
  </div>

</div><!-- /content-wrap -->

<!-- PAGE: IMPACT CALCULATOR -->
  <footer class="site-footer">...</footer>

<!-- FOOTER for Process Flow page (same margin trick as header) -->
<footer class="site-footer">
  <p>[Project name] &mdash; Future State [Topic] &middot; Prepared by TechJays &middot; [Month Year]</p>
  <p style="color:#3a5a7a;font-size:11.5px;margin-top:4px">All figures are estimates based on discovery sessions and are subject to confirmation during implementation planning.</p>
</footer>

<script>
  /* all JS here — see javascript.md */
</script>
</body>
</html>
```

---

## Core CSS (always include in full)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  background: #f4f6f9; color: #1a1a2e; font-size: 15px; line-height: 1.55;
  padding-left: 180px; /* sidebar offset — never remove */
}

.content-wrap { max-width: 1480px; margin: 0 auto; padding: 0 32px; }
.section { padding: 44px 0; }
.section + .section { border-top: 1px solid #dde3ec; }
.section-heading { font-size: 20px; font-weight: 700; color: #0d1b2a; margin-bottom: 6px; }
.section-sub { font-size: 13px; color: #5a6a7a; margin-bottom: 28px; }

/* HEADER — negative margin stretches behind the 180px sidebar */
.site-header {
  background: linear-gradient(160deg, #1a2a4a 0%, #243b6e 100%);
  padding: 36px 48px; display: flex; justify-content: space-between; align-items: flex-start;
  margin-left: -180px; padding-left: calc(180px + 48px);
}
.site-header .left { max-width: 860px; }
.site-header .overline {
  font-size: 11px; font-weight: 700; letter-spacing: 0.14em;
  text-transform: uppercase; color: #c9a84c; margin-bottom: 10px;
}
.site-header h1 { font-size: 26px; font-weight: 700; color: #fff; line-height: 1.25; margin-bottom: 8px; }
.site-header .subtitle { font-size: 14px; color: #9bb0c8; line-height: 1.5; }
.site-header .meta-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.site-header .meta-pill {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px; padding: 3px 12px; font-size: 11.5px; color: rgba(255,255,255,0.75);
}
.site-header .meta-pill strong { color: #c9a84c; }
.site-header .right {
  font-size: 12px; color: #c9a84c; opacity: 0.85; text-align: right;
  white-space: nowrap; padding-top: 4px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;
}

/* SIDEBAR NAV */
#side-nav {
  position: fixed; left: 0; top: 50%; transform: translateY(-50%);
  z-index: 500; display: flex; flex-direction: column; gap: 2px;
  padding: 14px 0; background: #1a2a4a; border-radius: 0 12px 12px 0;
  box-shadow: 2px 0 18px rgba(0,0,0,0.22); width: 172px;
}
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px 10px 14px;
  cursor: pointer; border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  white-space: nowrap; text-decoration: none; color: rgba(255,255,255,0.55);
  font-size: 12px; font-weight: 500; letter-spacing: 0.01em;
}
.nav-item:hover { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.88); }
.nav-item.active { border-left-color: #c9a84c; color: #fff; background: rgba(201,168,76,0.14); font-weight: 700; }
.nav-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,0.25); flex-shrink: 0; transition: background 0.15s; }
.nav-item.active .nav-dot { background: #c9a84c; }
.nav-item:hover .nav-dot { background: rgba(255,255,255,0.6); }
.nav-label { font-size: 12px; }

/* STICKY COL HEADER */
#sticky-col-hdr {
  display: none; position: fixed; top: 0; left: 180px; right: 0; z-index: 400;
  height: 44px; background: linear-gradient(160deg, #1a2a4a 0%, #243b6e 100%);
  box-shadow: 0 2px 10px rgba(0,0,0,0.28); align-items: stretch; overflow: hidden;
}
#sticky-col-hdr.visible { display: flex; }
.sch-left  { flex:0 0 10.51%; text-align:center; font-size:10px; font-weight:600; color:rgba(255,255,255,0.45); border-right:1px solid rgba(255,255,255,0.14); display:flex; align-items:center; justify-content:center; }
.sch-cell  { flex:0 0 13.81%; text-align:center; font-size:11px; font-weight:700; color:#fff; border-right:1px solid rgba(255,255,255,0.14); padding:0 4px; line-height:1.3; display:flex; align-items:center; justify-content:center; }
.sch-right { flex:1; text-align:center; font-size:11px; font-weight:700; color:#c9a84c; border-left:1px solid rgba(255,255,255,0.14); display:flex; align-items:center; justify-content:center; }

/* SWIMLANE */
.swimlane-wrap { overflow-x: auto; width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }
.swimlane-wrap svg { display: block; }

/* FOOTER */
.site-footer {
  background: linear-gradient(160deg, #1a2a4a 0%, #243b6e 100%);
  padding: 24px 48px; margin-top: 60px; margin-left: -180px; padding-left: calc(180px + 48px);
}
.site-footer p { font-size: 12px; color: #5a7a9a; line-height: 1.7; }

/* TAB BAR */
  background: #0d1b2a;
  display: flex;
  gap: 0;
  padding: 0 48px;
  border-bottom: 2px solid #c9a84c;
  margin-left: -180px;
  padding-left: calc(180px + 48px);
}
  padding: 14px 32px;
  font-size: 14px;
  font-weight: 700;
  color: rgba(255,255,255,0.55);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  letter-spacing: 0.03em;
  transition: color 0.15s, border-color 0.15s;
  margin-bottom: -2px;
}

/* RESPONSIVE */
@media (max-width: 1100px) { .metrics-row { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 720px) {
  .site-header { flex-direction: column; gap: 12px; }
  .metrics-row { grid-template-columns: repeat(2, 1fr); }
  .systems-grid { grid-template-columns: 1fr; }
}
```
