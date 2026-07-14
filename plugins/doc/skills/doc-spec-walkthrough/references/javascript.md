# JavaScript

All inline in one `<script>` at the end of `<body>`. Three behaviours:
scroll-spy nav, node tooltips (overview states + module steps), and
click-to-highlight transitions on the overview diagram. Vanilla JS, no
dependencies.

```html
<script>
(function () {
  "use strict";

  /* ---------- 1. SCROLL-SPY NAV ---------- */
  var navItems = Array.prototype.slice.call(document.querySelectorAll('.nav-item'));
  var sections = navItems
    .map(function (n) { return document.getElementById(n.dataset.target); })
    .filter(Boolean);

  navItems.forEach(function (n) {
    n.addEventListener('click', function (e) {
      e.preventDefault();
      var t = document.getElementById(n.dataset.target);
      if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  function setActive(id) {
    navItems.forEach(function (n) {
      n.classList.toggle('active', n.dataset.target === id);
    });
  }

  var spy = new IntersectionObserver(function (entries) {
    // pick the entry nearest the top that is intersecting
    var best = null;
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        if (!best || en.boundingClientRect.top < best.boundingClientRect.top) best = en;
      }
    });
    if (best) setActive(best.target.id);
  }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });
  sections.forEach(function (s) { spy.observe(s); });

  /* ---------- 2. NODE TOOLTIPS ---------- */
  var tip = document.getElementById('node-tip');
  function showTip(el, evt) {
    var title = el.dataset.title || '';
    var desc = (el.dataset.desc || '').split('||').filter(Boolean);
    var html = '';
    if (title) html += '<div class="tip-title">' + esc(title) + '</div>';
    if (desc.length) {
      html += '<ul>' + desc.map(function (d) { return '<li>' + esc(d) + '</li>'; }).join('') + '</ul>';
    }
    if (!html) return;
    tip.innerHTML = html;
    tip.classList.add('show');
    moveTip(evt);
  }
  function moveTip(evt) {
    var pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    var x = evt.clientX + pad, y = evt.clientY + pad;
    if (x + w > window.innerWidth - 8) x = evt.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = evt.clientY - h - pad;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = Math.max(8, y) + 'px';
  }
  function hideTip() { tip.classList.remove('show'); }

  Array.prototype.forEach.call(document.querySelectorAll('.state, .step'), function (el) {
    if (!el.dataset.title && !el.dataset.desc) return;
    el.addEventListener('mouseenter', function (e) { showTip(el, e); });
    el.addEventListener('mousemove', moveTip);
    el.addEventListener('mouseleave', hideTip);
  });

  /* ---------- 3. CLICK-TO-HIGHLIGHT TRANSITIONS (overview only) ---------- */
  var ovSvg = document.querySelector('#sec-overview svg');
  if (ovSvg) {
    var states = Array.prototype.slice.call(ovSvg.querySelectorAll('.state'));
    var edges  = Array.prototype.slice.call(ovSvg.querySelectorAll('.edge'));

    function clearSel() {
      ovSvg.classList.remove('has-sel');
      states.forEach(function (s) { s.classList.remove('sel', 'adj'); });
      edges.forEach(function (ed) { ed.classList.remove('lit'); });
    }

    function selectState(g) {
      var id = g.dataset.state;
      if (!id) return;
      if (g.classList.contains('sel')) { clearSel(); return; }
      clearSel();
      ovSvg.classList.add('has-sel');
      g.classList.add('sel');
      var neighbours = {};
      edges.forEach(function (ed) {
        var f = ed.dataset.from, t = ed.dataset.to;
        if (f === id || t === id) {
          ed.classList.add('lit');
          neighbours[f === id ? t : f] = true;
        }
      });
      states.forEach(function (s) {
        if (neighbours[s.dataset.state]) s.classList.add('adj');
      });
    }

    states.forEach(function (g) {
      g.style.cursor = 'pointer';
      g.addEventListener('click', function (e) { e.stopPropagation(); selectState(g); });
    });
    // click empty canvas / outside resets
    ovSvg.addEventListener('click', function (e) {
      if (!e.target.closest('.state')) clearSel();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') clearSel(); });
  }

  /* ---------- util ---------- */
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
})();
</script>
```

## Notes

- **Scroll-spy** uses `IntersectionObserver` with an asymmetric `rootMargin` so
  a section becomes active when it reaches roughly the upper third of the
  viewport. Tune the margins if sections are very short or very tall.
- **Tooltips** read `data-title` and `data-desc` (bullets split on `||`). The
  same handler serves overview `.state` nodes and module `.step` nodes, so any
  node with those attributes gets a tooltip for free.
- **Click-to-highlight** toggles `has-sel` on the overview `<svg>`, `sel` on the
  clicked state, `adj` on connected states, and `lit` on the touching edges. The
  visual is entirely in CSS (see state-diagram.md) so this stays declarative.
  The matching is by `data-state` / `data-from` / `data-to`, so those must be
  consistent between nodes and edges.
- Escape or a click on empty SVG space clears the selection.
- Everything is feature-guarded (`if (ovSvg)`, attribute checks) so a page with
  no overview diagram or a module with no tooltips still runs without errors.
