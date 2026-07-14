# Page Structure

The page is a single scrollable column with a fixed left sidebar. Order:
header → overview state diagram → one section per module → catalog/criteria →
footer. Nav is scroll-spy: the active item tracks the section in view.

## HTML skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[SYSTEM] &mdash; Spec Walkthrough</title>
<style>/* all CSS inline — see below */</style>
</head>
<body>

<!-- TOOLTIP OVERLAY — first element after body -->
<div id="node-tip"></div>

<!-- SIDEBAR NAV — one item per section, data-target = section id -->
<nav id="side-nav" aria-label="Sections">
  <a class="nav-item active" data-target="sec-overview"><span class="nav-dot"></span><span class="nav-label">Overview</span></a>
  <a class="nav-item" data-target="sec-mod-1"><span class="nav-dot"></span><span class="nav-label">[Module 1]</span></a>
  <a class="nav-item" data-target="sec-mod-2"><span class="nav-dot"></span><span class="nav-label">[Module 2]</span></a>
  <!-- … one per module … -->
  <a class="nav-item" data-target="sec-catalog"><span class="nav-dot"></span><span class="nav-label">Commands</span></a>
  <a class="nav-item" data-target="sec-criteria"><span class="nav-dot"></span><span class="nav-label">Success Criteria</span></a>
</nav>

<!-- HEADER (bleeds behind sidebar via negative margin) -->
<header class="site-header">
  <div class="left">
    <div class="overline">[SYSTEM NAME IN CAPS]</div>
    <h1>[Spec Title] Walkthrough</h1>
    <p class="subtitle">[One sentence describing the system]</p>
    <div class="meta-pills">
      <span class="meta-pill"><strong>Version:</strong> [x]</span>
      <span class="meta-pill"><strong>Status:</strong> [status]</span>
      <span class="meta-pill"><strong>Audience:</strong> [audience]</span>
      <span class="meta-pill"><strong>Date:</strong> [DDMonYYYY]</span>
    </div>
  </div>
  <div class="right"><span>[Version]</span><span>[Date]</span></div>
</header>

<div class="content-wrap">

  <!-- OVERVIEW STATE DIAGRAM — see state-diagram.md -->
  <section id="sec-overview" class="section">
    <p class="eyebrow">The full picture</p>
    <h2 class="section-heading">System State Overview</h2>
    <p class="section-sub">[One line: what moves through these states.] Hover a state for detail. Click a state to trace its transitions.</p>
    <div class="state-legend"><!-- legend swatches, see design-tokens --></div>
    <div class="diagram-wrap"><!-- overview SVG here --></div>
    <p class="diagram-note">[Optional gate/branch note from the spec.]</p>
  </section>

  <!-- MODULE SECTIONS — see module-sections.md -->
  <section id="sec-mod-1" class="section">
    <p class="eyebrow">Module 01</p>
    <h2 class="section-heading">[Module name]</h2>
    <p class="section-sub">[One-line purpose from the spec.]</p>
    <div class="module-grid">
      <div class="module-flow"><!-- compact workflow SVG --></div>
      <div class="module-side">
        <ol class="step-list"><!-- ordered steps --></ol>
        <div class="example-card"><!-- worked example --></div>
      </div>
    </div>
  </section>
  <!-- … repeat per module … -->

  <!-- CATALOG (commands / objects) -->
  <section id="sec-catalog" class="section">
    <p class="eyebrow">Reference</p>
    <h2 class="section-heading">[Commands / Objects]</h2>
    <p class="section-sub">[caption]</p>
    <div class="catalog-grid"><!-- catalog cards --></div>
  </section>

  <!-- SUCCESS CRITERIA -->
  <section id="sec-criteria" class="section">
    <p class="eyebrow">Outcomes</p>
    <h2 class="section-heading">Success Criteria</h2>
    <div class="criteria-grid"><!-- criteria cards --></div>
  </section>

</div><!-- /content-wrap -->

<footer class="site-footer">
  <p>[System] &mdash; Spec Walkthrough v[x] &middot; Prepared by Techjays &middot; [Month Year]</p>
  <p class="fine">Generated from the source specification. Items marked [[NEEDS: …]] await confirmation.</p>
</footer>

<script>/* all JS inline — see javascript.md */</script>
</body>
</html>
```

## Core CSS (include in full)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  background: #f4f6f9; color: #1a1a2e; font-size: 15px; line-height: 1.55;
  padding-left: 180px;             /* sidebar offset — never remove */
}

.content-wrap { max-width: 1240px; margin: 0 auto; padding: 0 32px; }
.section { padding: 44px 0; scroll-margin-top: 20px; }
.section + .section { border-top: 1px solid #dde3ec; }
.eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #c9a84c; margin-bottom: 8px; }
.section-heading { font-size: 20px; font-weight: 700; color: #0d1b2a; margin-bottom: 6px; }
.section-sub { font-size: 13px; color: #5a6a7a; margin-bottom: 24px; max-width: 820px; }
.diagram-note { font-size: 12px; color: #5a6a7a; margin-top: 14px; }

/* HEADER — negative margin stretches behind the 180px sidebar */
.site-header {
  background: linear-gradient(160deg, #1a2a4a 0%, #243b6e 100%);
  padding: 36px 48px; display: flex; justify-content: space-between; align-items: flex-start;
  margin-left: -180px; padding-left: calc(180px + 48px);
}
.site-header .left { max-width: 820px; }
.site-header .overline { font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #c9a84c; margin-bottom: 10px; }
.site-header h1 { font-size: 26px; font-weight: 700; color: #fff; line-height: 1.25; margin-bottom: 8px; }
.site-header .subtitle { font-size: 14px; color: #9bb0c8; line-height: 1.5; }
.site-header .meta-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.site-header .meta-pill { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15); border-radius: 20px; padding: 3px 12px; font-size: 11.5px; color: rgba(255,255,255,.75); }
.site-header .meta-pill strong { color: #c9a84c; }
.site-header .right { font-size: 12px; color: #c9a84c; opacity: .85; text-align: right; white-space: nowrap; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }

/* SIDEBAR */
#side-nav {
  position: fixed; left: 0; top: 50%; transform: translateY(-50%);
  z-index: 500; display: flex; flex-direction: column; gap: 2px;
  padding: 14px 0; background: #1a2a4a; border-radius: 0 12px 12px 0;
  box-shadow: 2px 0 18px rgba(0,0,0,.22); width: 172px; max-height: 92vh; overflow-y: auto;
}
.nav-item { display: flex; align-items: center; gap: 10px; padding: 9px 16px 9px 14px; cursor: pointer;
  border-left: 3px solid transparent; transition: background .15s, border-color .15s, color .15s;
  white-space: nowrap; text-decoration: none; color: rgba(255,255,255,.55); font-size: 12px; font-weight: 500; }
.nav-item:hover { background: rgba(255,255,255,.08); color: rgba(255,255,255,.88); }
.nav-item.active { border-left-color: #c9a84c; color: #fff; background: rgba(201,168,76,.14); font-weight: 700; }
.nav-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,.25); flex-shrink: 0; transition: background .15s; }
.nav-item.active .nav-dot { background: #c9a84c; }
.nav-label { font-size: 12px; overflow: hidden; text-overflow: ellipsis; }

/* DIAGRAM WRAP */
.diagram-wrap { overflow-x: auto; width: 100%; background: #fff; border: 1px solid #dde3ec; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.06); padding: 8px; }
.diagram-wrap svg { display: block; }

/* LEGEND */
.state-legend { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 16px; font-size: 12px; color: #3a4a5a; }
.state-legend .legend-item { display: flex; align-items: center; gap: 7px; }
.legend-swatch { width: 15px; height: 12px; border-radius: 3px; display: inline-block; }

/* MODULE SECTION */
.module-grid { display: grid; grid-template-columns: minmax(300px, 1.05fr) 1fr; gap: 24px; align-items: start; }
.module-flow { background: #fff; border: 1px solid #dde3ec; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.06); padding: 10px; overflow-x: auto; }
.module-flow svg { display: block; }
.module-side { display: flex; flex-direction: column; gap: 18px; }
.step-list { list-style: none; counter-reset: step; display: flex; flex-direction: column; gap: 8px; }
.step-list li { position: relative; padding: 9px 12px 9px 42px; background: #fff; border: 1px solid #dde3ec; border-radius: 8px; font-size: 13.5px; }
.step-list li::before { counter-increment: step; content: counter(step); position: absolute; left: 10px; top: 8px; width: 22px; height: 22px; border-radius: 50%; background: #1a2a4a; color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.step-list li strong { color: #0d1b2a; }

/* EXAMPLE CARD */
.example-card { background: linear-gradient(160deg, #fbfaf4 0%, #fff 60%); border: 1px solid #e7dcae; border-left: 4px solid #c9a84c; border-radius: 10px; padding: 16px 18px; }
.example-card .ex-label { font-size: 10.5px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #a5842f; margin-bottom: 8px; }
.example-card .ex-figure { font-size: 24px; font-weight: 800; color: #c9a84c; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
.example-card code, .mono { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 13px; color: #12314d; background: #eef2f8; padding: 1px 6px; border-radius: 4px; }
.example-card .ex-row { display: flex; gap: 8px; align-items: baseline; margin-top: 6px; font-size: 13.5px; }
.example-card .ex-row .k { color: #5a6a7a; min-width: 78px; }

/* CATALOG + CRITERIA */
.catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.catalog-card { background: #fff; border: 1px solid #dde3ec; border-radius: 10px; padding: 14px 16px; }
.catalog-card .cmd { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 13.5px; font-weight: 600; color: #12314d; }
.catalog-card .desc { font-size: 12.5px; color: #5a6a7a; margin-top: 4px; }
.criteria-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.criteria-card { background: #fff; border: 1px solid #dde3ec; border-left: 4px solid #1e8449; border-radius: 10px; padding: 14px 16px; font-size: 13.5px; }
.criteria-card .tick { color: #1e8449; font-weight: 800; margin-right: 6px; }

/* NEEDS marker */
.needs { background: #fdeaea; color: #8a1a1a; border-radius: 4px; padding: 0 5px; font-size: 12px; font-weight: 600; }

/* TOOLTIP */
#node-tip { position: fixed; z-index: 900; max-width: 320px; background: #0d1b2a; color: #eaf1f8; border-radius: 8px; padding: 12px 14px; font-size: 12.5px; line-height: 1.5; box-shadow: 0 8px 24px rgba(0,0,0,.35); pointer-events: none; opacity: 0; transition: opacity .12s; }
#node-tip.show { opacity: 1; }
#node-tip .tip-title { font-weight: 700; color: #c9a84c; margin-bottom: 5px; font-size: 13px; }
#node-tip ul { margin: 0; padding-left: 16px; }

/* FOOTER */
.site-footer { background: linear-gradient(160deg, #1a2a4a 0%, #243b6e 100%); padding: 24px 48px; margin-top: 50px; margin-left: -180px; padding-left: calc(180px + 48px); }
.site-footer p { font-size: 12px; color: #7d94b0; line-height: 1.7; }
.site-footer .fine { color: #55708f; font-size: 11px; margin-top: 4px; }

/* RESPONSIVE */
@media (max-width: 900px) {
  .module-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  body { padding-left: 0; }
  #side-nav { display: none; }
  .site-header, .site-footer { margin-left: 0; padding-left: 24px; }
}
```

## Notes

- **Sidebar item count** grows with the number of modules. Keep labels short so
  they don't wrap; the label cell has `text-overflow: ellipsis`.
- On very narrow screens the sidebar hides and the body padding drops to 0 so
  the page still reads (the diagrams scroll horizontally).
- `scroll-margin-top` on sections keeps a clicked nav target from hiding under
  the top edge.
