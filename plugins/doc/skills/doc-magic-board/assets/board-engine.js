/* Magic-board interaction engine — pan, zoom, guided tour, overview.
 * Drop this into a <script> (or load as a file). It's the one piece worth not
 * reinventing; everything visual is yours to design freely.
 *
 * REQUIRED DOM:
 *   #viewport  (fixed, full-screen, overflow:hidden)  >  #canvas (transform-origin:0 0)
 *   .card elements inside #canvas, each with a unique id, positioned by inline left/top/width
 * OPTIONAL DOM (wire if present): #btn-prev #btn-next #btn-ov  #tourtitle  #counter
 * REQUIRED GLOBAL: window.tour = [{id:'card-id', t:'Bar label'}, ...]  (narrative order)
 */
(function () {
  const vp = document.getElementById('viewport');
  const canvas = document.getElementById('canvas');
  const counter = document.getElementById('counter');
  const tourTitle = document.getElementById('tourtitle');
  const tour = window.tour || [];
  let st = { x: 0, y: 0, s: 1 }, ti = -1;

  function apply(anim) {
    canvas.style.transition = anim ? 'transform .85s cubic-bezier(.45,.05,.2,1)' : 'none';
    canvas.style.transform = `translate(${st.x}px,${st.y}px) scale(${st.s})`;
  }
  function flyToEl(el, pad = 0.84, maxScale = 1.5) {
    const vw = innerWidth, vh = innerHeight;
    const cw = el.offsetWidth, ch = el.offsetHeight, cx = el.offsetLeft, cy = el.offsetTop;
    const s = Math.min(vw * pad / cw, vh * pad / ch, maxScale);
    st.s = s; st.x = vw / 2 - s * (cx + cw / 2); st.y = vh / 2 - s * (cy + ch / 2); apply(true);
  }
  function overview() {
    ti = -1;
    if (tourTitle) tourTitle.textContent = 'Overview — the whole board';
    if (counter) counter.textContent = 'overview';
    const cards = [...document.querySelectorAll('.card')];
    if (!cards.length) return;
    let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
    cards.forEach(c => {
      minX = Math.min(minX, c.offsetLeft); minY = Math.min(minY, c.offsetTop - 90);
      maxX = Math.max(maxX, c.offsetLeft + c.offsetWidth); maxY = Math.max(maxY, c.offsetTop + c.offsetHeight);
    });
    const bw = maxX - minX, bh = maxY - minY, vw = innerWidth, vh = innerHeight;
    const s = Math.min(vw * 0.9 / bw, vh * 0.86 / bh);
    st.s = s; st.x = vw / 2 - s * (minX + bw / 2); st.y = vh / 2 - s * (minY + bh / 2); apply(true);
  }
  function goto(n) {
    if (n < 0 || !tour.length) { overview(); return; }
    if (n >= tour.length) n = tour.length - 1;
    ti = n; const stop = tour[n];
    const el = document.getElementById(stop.id); if (!el) return;
    flyToEl(el);
    if (tourTitle) tourTitle.innerHTML = '<b>' + stop.t + '</b>';
    if (counter) counter.textContent = String(n + 1).padStart(2, '0') + ' / ' + String(tour.length).padStart(2, '0');
  }
  const next = () => goto(ti < 0 ? 0 : ti + 1);
  const prev = () => (ti <= 0 ? overview() : goto(ti - 1));

  const bp = document.getElementById('btn-prev'), bn = document.getElementById('btn-next'), bo = document.getElementById('btn-ov');
  if (bn) bn.onclick = e => { e.stopPropagation(); next(); };
  if (bp) bp.onclick = e => { e.stopPropagation(); prev(); };
  if (bo) bo.onclick = e => { e.stopPropagation(); overview(); };
  addEventListener('keydown', e => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'o' || e.key === 'O' || e.key === 'Home') overview();
  });

  let panning = false, sx = 0, sy = 0, ox = 0, oy = 0;
  vp.addEventListener('pointerdown', e => { panning = true; sx = e.clientX; sy = e.clientY; ox = st.x; oy = st.y; vp.classList.add('drag'); vp.setPointerCapture(e.pointerId); });
  vp.addEventListener('pointermove', e => { if (!panning) return; st.x = ox + (e.clientX - sx); st.y = oy + (e.clientY - sy); apply(false); });
  vp.addEventListener('pointerup', () => { panning = false; vp.classList.remove('drag'); });
  vp.addEventListener('wheel', e => {
    e.preventDefault();
    const f = e.deltaY < 0 ? 1.12 : 1 / 1.12, ns = Math.max(0.12, Math.min(2.6, st.s * f)), mx = e.clientX, my = e.clientY;
    st.x = mx - (mx - st.x) * (ns / st.s); st.y = my - (my - st.y) * (ns / st.s); st.s = ns; apply(false);
  }, { passive: false });
  addEventListener('resize', () => (ti < 0 ? overview() : goto(ti)));
  let tx = 0; addEventListener('touchstart', e => tx = e.touches[0].clientX, { passive: true });
  addEventListener('touchend', e => { const dx = e.changedTouches[0].clientX - tx; if (Math.abs(dx) > 50) dx < 0 ? next() : prev(); }, { passive: true });

  // expose for custom buttons / deep links if wanted
  window.board = { goto, next, prev, overview };
  overview();
})();
