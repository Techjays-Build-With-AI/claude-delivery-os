# JavaScript Patterns

All JS goes in a single `<script>` tag before `</body>`. No external scripts.

---

## 1. Scroll-spy nav (active state)

Keeps the sidebar nav item highlighted as the user scrolls past each section.

```js
(function(){
  var items = document.querySelectorAll('.nav-item[data-target]');
  function onScroll(){
    var threshold = 100;
    var best = 0;
    var visible = Array.from(items).filter(function(it){ return it.style.display !== 'none'; });
    visible.forEach(function(it, i){
      var s = document.getElementById(it.dataset.target);
      if(!s) return;
      var r = s.getBoundingClientRect();
      if(r.top <= threshold) best = i;
    });
    visible.forEach(function(it, i){ it.classList.toggle('active', i===best); });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
  items.forEach(function(it){
    it.addEventListener('click', function(e){
      e.preventDefault();
      var s = document.getElementById(it.dataset.target);
      if(s) s.scrollIntoView({behavior:'smooth', block:'start'});
    });
  });
})();
```

---

## 2. Sticky swimlane column header

Makes the column header bar appear (fixed, top of viewport) when the user scrolls past the swimlane.

**Key**: `svgViewW` must match the actual SVG `viewBox` width for pixel-perfect alignment.

```js
(function(){
  var wrap = document.getElementById('swimlane-wrap');
  var bar  = document.getElementById('sticky-col-hdr');
  if(!wrap || !bar) return;
  function reposition(){
    var r = wrap.getBoundingClientRect();
    bar.style.left  = r.left+'px';
    bar.style.width = r.width+'px';
    bar.style.right = 'auto';
    // Scale each column cell to match SVG proportions
    // Replace 1332 with your actual SVG viewBox width
    var scale = r.width / 1332;
    bar.querySelectorAll('[data-svgw]').forEach(function(c){
      c.style.flex  = 'none';
      c.style.width = (parseInt(c.getAttribute('data-svgw')) * scale) + 'px';
    });
  }
  reposition();
  window.addEventListener('resize', reposition, {passive:true});
  function update(){
    var r = wrap.getBoundingClientRect();
    if(r.top<=0 && r.bottom>0){ reposition(); bar.classList.add('visible'); }
    else { bar.classList.remove('visible'); }
  }
  window.addEventListener('scroll', update, {passive:true});
  update();
})();
```

**If your SVG viewBox is not 1332 wide**, replace `1332` with your actual viewBox width.

---

## 3. Swimlane tooltip

Reads `data-title` and `data-desc` (pipe-separated `||`) from each `.swimnode`. Builds HTML dynamically.
There is **no JSON parsing** — the attributes are plain strings.

```js
(function(){
  var tip = document.getElementById('swim-tip');
  if(!tip) return;
  document.querySelectorAll('.swimnode').forEach(function(n){
    n.addEventListener('mouseenter', function(){
      var t = n.dataset.title || '';
      var d = n.dataset.desc  || '';
      var b = d ? d.split('||').map(function(x){
        return '<div class="tip-row"><span class="tip-dot"></span><span>'+x+'</span></div>';
      }).join('') : '';
      tip.innerHTML = (t ? '<div class="tip-title">'+t+'</div>' : '')
                    + (b ? '<div class="tip-body">'+b+'</div>' : '');
      tip.style.display = 'block';
    });
    n.addEventListener('mousemove', function(e){
      var x = e.clientX+18, y = e.clientY-10;
      if(x+320>window.innerWidth) x = e.clientX-326;
      if(y+260>window.innerHeight) y = e.clientY-250;
      tip.style.left = x+'px'; tip.style.top = y+'px';
    });
    n.addEventListener('mouseleave', function(){ tip.style.display='none'; });
  });
})();
```

### Node attribute format

```html
<g class="swimnode"
   data-phase="P2"
   data-title="AI: Multilingual Outreach"
   data-desc="Sends SMS + WhatsApp in 6 languages||EN, ES, PL, SQ, SO, HT supported||Replaces manual recruiter dial-outs">
```

- `data-phase`: phase ID string (used only for semantic grouping, not tooltip display)
- `data-title`: tooltip heading (bold, dark)
- `data-desc`: `||`-separated bullet lines, no HTML inside

---

## 4. KPI card tooltip (hover)

KPI cards use **`mouseenter`** (not click). They have TWO data attributes:
- `data-kpi`: the label string shown in gold at the top of the tooltip
- `data-tip`: pre-built HTML string using `kt-row`, `kt-dot`, `kt-divider`, `kt-future` classes

```js
(function(){
  var kt = document.getElementById('kpi-tip');
  if(!kt) return;
  document.querySelectorAll('.metric-card[data-tip]').forEach(function(c){
    c.addEventListener('mouseenter', function(){
      kt.innerHTML = '<div class="kt-label">'+(c.dataset.kpi||'')+'</div><div>'+c.dataset.tip+'</div>';
      kt.style.display = 'block';
    });
    c.addEventListener('mousemove', function(e){
      var x = e.clientX+20, y = e.clientY-12;
      if(x+312>window.innerWidth) x = e.clientX-316;
      if(y+280>window.innerHeight) y = e.clientY-285;
      kt.style.left = x+'px'; kt.style.top = y+'px';
    });
    c.addEventListener('mouseleave', function(){ kt.style.display='none'; });
  });
})();
```

### KPI card HTML (with `data-tip` as pre-built HTML)

```html
<div class="metric-card"
  data-kpi="Hours Freed per Hire"
  data-tip="
    <div class='kt-section'>What manual hours are freed?</div>
    <div class='kt-row'><div class='kt-dot'></div><div>Detail about the manual process being replaced</div></div>
    <div class='kt-row'><div class='kt-dot'></div><div>Second detail</div></div>
    <hr class='kt-divider'>
    <div class='kt-future'>Future state: One sentence on the automated replacement</div>
  ">
  <div class="metric-number">~2.4 hrs</div>
  <div class="metric-label">Hours Freed per Hire</div>
  <div class="metric-sub">Across all phases</div>
</div>
```

### KPI tooltip CSS (include in `<style>`)

```css
#kpi-tip {
  position: fixed; background: #0d1b2a;
  border: 1.5px solid rgba(255,255,255,0.14); border-radius: 10px;
  padding: 14px 18px; box-shadow: 0 10px 36px rgba(0,0,0,0.42);
  max-width: 300px; z-index: 9998; pointer-events: none; display: none;
  font-family: system-ui,-apple-system,'Segoe UI',sans-serif;
}
#kpi-tip .kt-label   { font-size:10px; font-weight:700; color:#c9a84c; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px; }
#kpi-tip .kt-section { font-size:11.5px; font-weight:700; color:#ffffff; margin:0 0 8px; letter-spacing:0.01em; }
#kpi-tip .kt-row     { display:flex; gap:8px; align-items:flex-start; font-size:12px; color:#d0dcec; line-height:1.60; margin:4px 0; }
#kpi-tip .kt-dot     { width:7px; height:7px; border-radius:50%; background:#c9a84c; margin-top:4px; flex-shrink:0; }
#kpi-tip .kt-divider { border:none; border-top:1px solid rgba(255,255,255,0.12); margin:8px 0; }
#kpi-tip .kt-future  { color:#3dd68c; font-size:11.5px; font-weight:600; line-height:1.55; }
#kpi-tip .kt-note    { font-size:11px; color:#9bb0c8; margin-top:8px; border-top:1px solid rgba(255,255,255,0.12); padding-top:7px; }
#kpi-tip .kt-phase   { display:inline-block; min-width:118px; color:#9bb0c8; font-size:11px; }
#kpi-tip .kt-phase b { color:#c9a84c; }
```

---

## 5. Swimlane tooltip CSS (include in `<style>`)

```css
#swim-tip {
  position: fixed;
  background: #ffffff;
  border: 1.5px solid #c0cede;
  border-radius: 9px;
  padding: 14px 18px;
  box-shadow: 0 8px 32px rgba(13,27,42,0.18);
  max-width: 300px;
  z-index: 9999;
  pointer-events: none;
  display: none;
  font-family: system-ui,-apple-system,'Segoe UI',sans-serif;
}
#swim-tip .tip-title { font-size:13px; font-weight:700; color:#0d1b2a; margin-bottom:8px; }
#swim-tip .tip-body  { font-size:12.5px; }
.tip-row  { display:flex; gap:8px; align-items:flex-start; margin:3px 0; font-size:12.5px; color:#2a3a4a; line-height:1.5; }
.tip-dot  { width:5px; height:5px; border-radius:50%; background:#c9a84c; flex-shrink:0; margin-top:5px; }
.swimnode { cursor: pointer; }
.swimnode rect, .swimnode polygon { transition: filter 0.12s; }
.swimnode:hover rect, .swimnode:hover polygon {
  filter: brightness(0.90) drop-shadow(0 2px 6px rgba(0,0,0,0.14));
}
```

### DOM placement

Place both tooltip `<div>` elements **immediately after the opening `<body>` tag**, before the nav:

```html
<body>
<div id="swim-tip"></div>
<div id="kpi-tip"></div>
<nav id="side-nav">...
```

The JS builds the inner HTML dynamically — do not pre-fill these divs.

---

