/* ============================================================================
 * Techjays deck — reference generator (pptxgenjs)
 * ----------------------------------------------------------------------------
 * This is a WORKING template. To build a new deck:
 *   1. Copy this file + the skill's assets/*.png into your working dir.
 *   2. Edit CONFIG (names, date, font, accent colours if the brand differs).
 *   3. Edit the CONTENT blocks (marked ► CONTENT) — that's where all the words live.
 *   4. Add/remove slides by copying a slide block; keep to the patterns.
 *   5. node build_deck.js  → then validate + render with the pptx skill's tools.
 *
 * Layout is 13.33 × 7.5. Read references/design-system.md for the full spec.
 * pptxgenjs gotchas that bite: hex has NO '#'; never share an options object
 * across two add* calls; shadow offset ≥ 0; bullets via {bullet:true} not "•".
 * ========================================================================== */
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";

/* ==== CONFIG ============================================================== */
const CFG = {
  vendor: "Techjays",
  client: "Harvard Maintenance",
  date: "July 2026",
  outfile: "Deck.pptx",
  // ONE font is used for everything (headlines, body, and labels).
  //   "Google Sans" is the Techjays choice, but it is a proprietary Google font:
  //   it renders correctly only where installed (and is NOT in the Google Slides
  //   font picker). For guaranteed identical rendering everywhere, set this to a
  //   widely-available near-match ("Poppins") or a universal safe font ("Arial").
  font: "Google Sans",
  // asset paths (copy from the skill's assets/ into the working dir)
  logo: "logo.png", logoWhite: "logo_white.png",
  bird: "bird.png", birdWhite: "bird_white.png",
  clientLogo: null,        // e.g. "client_logo.png" (dark/brand mark on transparent) or null
};
const FOOTER = "Confidential    ·    " + CFG.vendor + " × " + CFG.client;

/* ==== PALETTE + TYPE (see design-system.md §2–3) ========================= */
const INK="141414", MUT="6B7280", FAINT="9AA0AA", LINE="E7E7EC", WHITE="FFFFFF", DARK="141B2E";
const LBL="424B5B";                                           // dark slate — small labels/subtext, legible on white
const C1="6870F8", C2="E3A03C", C3="1FA98A", PAL=[C1,C2,C3];  // brand + 2 supporting
const C1L="C3C7FB", C3L="AEE4D7", SG="9098A6";                // light tints for Gantt
const SANS=CFG.font, MONO=CFG.font;                           // single typeface
const W=13.33, LX=0.75, RX=12.58, CW=11.83;

/* ==== ENGINE: page furniture + helpers =================================== */
function base(s, dark){
  s.background = { color: dark ? DARK : WHITE };
  const mark = dark ? CFG.birdWhite : CFG.bird;
  s.addImage({ path: mark, x: 11.25, y: -0.62, w: 3.1, h: 2.816, transparency: 90 }); // watermark
  s.addImage({ path: mark, x: LX, y: 7.06, w: 0.17, h: 0.154 });                      // footer mark
  s.addText(FOOTER, { x: LX+0.28, y: 7.02, w: 9, h: 0.3, fontFace: MONO, fontSize: 9.5,
    color: dark ? "8891A6" : "7A828E", charSpacing: 0.3, margin: 0 });
  return s;
}
const slide     = () => base(p.addSlide(), false);
const darkSlide = () => base(p.addSlide(), true);

// label helper. Subtext must stay legible: keep small labels dark (LBL) and ≥11.5pt.
function mono(s, o){
  s.addText(o.t, { x:o.x, y:o.y, w:o.w, h:o.h||0.34, fontFace:MONO, fontSize:o.sz||11.5,
    color:o.c||LBL, bold:o.b||false, align:o.a||"left",
    charSpacing:o.cs!=null?o.cs:0.4, margin:0, valign:o.v||"top" });
}
function topbar(s, label, marker){
  mono(s, { t:label, x:LX, y:0.6, w:8, sz:13, c:INK, cs:0.8 });
  mono(s, { t:marker, x:RX-4, y:0.62, w:4, sz:11.5, c:MUT, a:"right" });
}
// square + single legible line
function bullet(s, x, y, w, text, col){
  s.addShape(p.ShapeType.rect, { x, y:y+0.06, w:0.1, h:0.1, fill:{color:col||C1}, line:{type:"none"} });
  s.addText(text, { x:x+0.26, y, w:w-0.26, h:0.6, fontFace:SANS, fontSize:14, color:LBL,
    margin:0, lineSpacingMultiple:1.18, valign:"top" });
}
// square + "bold lead — muted description"
function drow(s, x, y, w, lead, desc, col){
  s.addShape(p.ShapeType.rect, { x, y:y+0.06, w:0.1, h:0.1, fill:{color:col}, line:{type:"none"} });
  s.addText([{text:lead,options:{bold:true,color:INK}},
             {text:desc?"  —  "+desc:"",options:{color:MUT}}],
    { x:x+0.26, y, w:w-0.26, h:0.7, fontFace:SANS, fontSize:12.5, margin:0,
      lineSpacingMultiple:1.15, valign:"top" });
}

/* ======================================================================== */
/* ► CONTENT starts here — edit freely, follow the patterns.                 */
/* ======================================================================== */

/* --- 1. COVER ----------------------------------------------------------- */
let s = slide();
s.addImage({ path: CFG.logo, x: LX, y: 0.55, w: 1.5, h: 0.328 });
if (CFG.clientLogo){                                   // co-brand lockup
  s.addShape(p.ShapeType.line, { x:2.5, y:0.52, w:0, h:0.31, line:{color:"D3D8E0", width:1} });
  s.addImage({ path: CFG.clientLogo, x:2.72, y:0.565, w:1.6, h:0.295 });
}
mono(s, { t: CFG.date, x: RX-6, y: 0.6, w: 6, sz: 12.5, c: LBL, a: "right" });
mono(s, { t: "90-DAY ENGAGEMENT   ·   " + CFG.vendor.toUpperCase() + " × " + CFG.client.toUpperCase(),
  x: LX, y: 3.55, w: 11, sz: 12, c: C1, cs: 1 });
s.addText("Work Order\nAutomation", { x: LX-0.04, y: 3.95, w: 10.5, h: 2.2, fontFace: SANS,
  fontSize: 62, bold: true, color: INK, margin: 0, lineSpacing: 62 });

/* --- 2. EXECUTIVE SUMMARY ---------------------------------------------- */
s = slide();
topbar(s, "Executive Summary", "02  /  06");
s.addText("Automate the highest-volume\nwork orders.", { x: LX-0.02, y: 1.55, w: 11.4, h: 1.6,
  fontFace: SANS, fontSize: 36, bold: true, color: INK, margin: 0, lineSpacing: 42 });
s.addText([
  { text: "We automate ", options:{} },
  { text: "intake", options:{ color:C1, bold:true } },
  { text: " and ", options:{} },
  { text: "day-to-day oversight", options:{ color:C1, bold:true } },
  { text: " — the two parts of the process that carry the most volume — inside the platform the client already runs. The largest share of the benefit lands first.", options:{} },
], { x: LX, y: 3.35, w: 9.6, h: 1.1, fontFace: SANS, fontSize: 15.5, color: MUT, margin: 0, lineSpacingMultiple: 1.3 });
s.addShape(p.ShapeType.line, { x: LX, y: 5.05, w: CW, h: 0, line: { color: LINE, width: 1 } });
const kpis = [["$225K","Total investment"],["12 weeks","To go-live"],["2","Modules"],["16–20K","Hours returned / yr"]];
const kw = (CW - 3*0.4) / 4;
kpis.forEach((k,i) => {
  const x = LX + i*(kw+0.4);
  s.addText(k[0], { x, y:5.35, w:kw, h:0.7, fontFace:SANS, fontSize:34, bold:true, color:INK, margin:0 });
  s.addShape(p.ShapeType.rect, { x, y:6.2, w:0.1, h:0.1, fill:{color:PAL[i%3]}, line:{type:"none"} });
  mono(s, { t:k[1], x:x+0.24, y:6.12, w:kw-0.24, sz:12, c:LBL, b:true, cs:0.2 });   // KPI label: dark + semibold
});

/* --- 3. SOLUTION SUMMARY (detail is in the appendix) ------------------- */
s = slide();
topbar(s, "The Solution", "03  /  06");
s.addText("Two modules", { x: LX-0.02, y: 1.5, w: 11, h: 0.7, fontFace: SANS, fontSize: 34, bold: true, color: INK, margin: 0 });
mono(s, { t: "At a glance — full detail in the appendix", x: LX, y: 2.26, w: 9, sz: 12.5, c: LBL, cs: 0.2 });
const mods = [
  { n:"01", name:"Intake", tag:"One queue for everything that arrives.", col:C1,
    sum:"Every client channel arrives in one validated queue, so the routine volume never reaches a coordinator.",
    gain:"4–5× FASTER THAN TODAY" },
  { n:"02", name:"Mission Control", tag:"See risk before it becomes a breach.", col:C3,
    sum:"SLA, pause and extension risk is surfaced early — one role-based list in place of the daily email pile.",
    gain:"2–3× FASTER THAN TODAY" },
];
const colw=5.35, cy=3.0, gap=0.75;
s.addShape(p.ShapeType.line, { x: LX+colw+gap/2, y: cy, w: 0, h: 3.1, line: { color: LINE, width: 1 } });
mods.forEach((m,i) => {
  const x = LX + i*(colw+gap);
  s.addText(m.n, { x:x-0.03, y:cy, w:2, h:0.6, fontFace:SANS, fontSize:30, bold:true, color:m.col, margin:0 });
  s.addText(m.name, { x, y:cy+0.75, w:colw, h:0.55, fontFace:SANS, fontSize:22, bold:true, color:INK, margin:0 });
  s.addText(m.tag, { x, y:cy+1.32, w:colw, h:0.4, fontFace:SANS, fontSize:14.5, color:INK, margin:0 });
  s.addText(m.sum, { x, y:cy+1.85, w:colw-0.1, h:1.0, fontFace:SANS, fontSize:13.5, color:MUT, margin:0, lineSpacingMultiple:1.25 });
  mono(s, { t:m.gain, x, y:cy+2.95, w:colw, sz:12, c:m.col, b:true, cs:0.8 });
});

/* --- 4. TIMELINE (high level) ----------------------------------------- */
s = slide();
topbar(s, "Timeline", "04  /  06");
s.addText("Go live in 12 weeks", { x: LX-0.02, y: 1.5, w: 11, h: 0.9, fontFace: SANS, fontSize: 34, bold: true, color: INK, margin: 0 });
const phases = [
  ["01","WEEKS 1–2","Technical audit","Plan confirmed before any build begins"],
  ["02","WEEKS 3–4","Foundation","Cloud setup, data access, monitoring"],
  ["03","WEEKS 4–10","Build · 2 modules","Both modules, built and tested"],
  ["04","WEEKS 11–12","UAT & go-live","Signed off with the client; live at week 12"],
];
const pw=(CW-3*0.5)/4, py=3.05;
s.addShape(p.ShapeType.line, { x: LX+0.15, y: py+0.22, w: CW-1.2, h: 0, line: { color: LINE, width: 1.5 } });
phases.forEach((ph,i) => {
  const x=LX+i*(pw+0.5), pc=PAL[i%3];
  s.addShape(p.ShapeType.rect, { x:x+0.02, y:py+0.13, w:0.18, h:0.18, fill:{color:pc}, line:{type:"none"} });
  s.addText(ph[0], { x:x+0.34, y:py, w:pw, h:0.45, fontFace:SANS, fontSize:22, bold:true, color:pc, margin:0 });
  mono(s, { t:ph[1], x, y:py+0.72, w:pw, sz:11.5, c:LBL, b:true, cs:0.3 });          // week tag: dark + semibold
  s.addText(ph[2], { x, y:py+1.08, w:pw, h:0.5, fontFace:SANS, fontSize:16.5, bold:true, color:INK, margin:0 });
  s.addText(ph[3], { x, y:py+1.6, w:pw-0.15, h:0.9, fontFace:SANS, fontSize:13, color:LBL, margin:0, lineSpacingMultiple:1.15 }); // desc: dark slate
});
mono(s, { t: "The first two weeks need access to the client's codebase.", x: LX, y: 6.35, w: 11, sz: 11.5, c: MUT });

/* --- 5. INVESTMENT ---------------------------------------------------- */
s = slide();
topbar(s, "Investment", "05  /  06");
s.addText("$225,000", { x: LX-0.04, y: 2.05, w: 6, h: 1.3, fontFace: SANS, fontSize: 60, bold: true, color: C1, margin: 0 });
mono(s, { t: "$75,000 / MONTH   ·   3 MONTHS", x: LX, y: 3.35, w: 6, sz: 13, c: INK, cs: 0.5 });
mono(s, { t: "12 WEEKS   ·   AUDIT → BUILD → GO LIVE", x: LX, y: 3.75, w: 6, sz: 12, c: LBL, cs: 0.4 });
s.addShape(p.ShapeType.line, { x: LX, y: 4.55, w: 5.0, h: 0, line: { color: LINE, width: 1 } });
s.addText("16,000–20,000", { x: LX-0.03, y: 4.8, w: 6, h: 0.7, fontFace: SANS, fontSize: 30, bold: true, color: INK, margin: 0 });
mono(s, { t: "HOURS RETURNED / YEAR", x: LX, y: 5.5, w: 6, sz: 11.5, c: C3, cs: 0.5 });
s.addText("once both modules are live", { x: LX, y: 5.82, w: 6, h: 0.4, fontFace: SANS, fontSize: 12.5, color: MUT, margin: 0 });
s.addShape(p.ShapeType.line, { x: 6.85, y: 2.05, w: 0, h: 4.05, line: { color: LINE, width: 1 } });
const rx=7.4, rw=RX-rx;
mono(s, { t: "What's Included", x: rx, y: 2.05, w: rw, sz: 14.5, c: INK, b: true, cs: 0.4 });   // section label: bold + larger
["A two-week technical audit up front — the plan confirmed before any build",
 "Both modules built, tested and shipped inside the client's platform",
 "UAT with the client's team through to go-live at week 12"
].forEach((t,j) => bullet(s, rx, 2.7+j*0.92, rw, t, PAL[j%3]));
mono(s, { t: "Priced as a single engagement.", x: rx, y: 5.7, w: rw, sz: 11.5, c: LBL });

/* --- 6. CLOSING / CTA ------------------------------------------------- */
s = slide();
s.addImage({ path: CFG.logo, x: LX, y: 0.55, w: 1.5, h: 0.328 });
mono(s, { t: "LET'S BEGIN", x: LX, y: 3.15, w: 8, sz: 13, c: C1, cs: 1.2 });
s.addText("In 90 days, you'll\nsee the value.", { x: LX-0.04, y: 3.55, w: 11, h: 1.9, fontFace: SANS, fontSize: 54, bold: true, color: INK, margin: 0, lineSpacing: 56 });
s.addText("Two modules, live and delivering inside three months. Let's get started.", { x: LX, y: 5.55, w: 10, h: 0.9, fontFace: SANS, fontSize: 16, color: MUT, margin: 0, lineSpacingMultiple: 1.25 });

/* --- 7. APPENDIX DIVIDER (dark separator) ----------------------------- */
s = darkSlide();
mono(s, { t: "END OF CORE DECK   ·   PAGES 1–6", x: LX, y: 2.55, w: 9, sz: 11.5, c: "8A93A8", cs: 1 });
mono(s, { t: "APPENDIX", x: LX, y: 3.2, w: 8, sz: 14, c: "9AA6FF", cs: 1.6 });
s.addText("The detail behind\nthe summary.", { x: LX-0.04, y: 3.6, w: 11, h: 1.9, fontFace: SANS, fontSize: 48, bold: true, color: WHITE, margin: 0, lineSpacing: 50 });
mono(s, { t: "Module scope   ·   what the client gets   ·   timeline breakdown", x: LX, y: 5.65, w: 11, sz: 12, c: "B7C0D4", cs: 0.4 });

/* --- 8/9. APPENDIX — module detail ------------------------------------ */
const detail = [
  { n:"01", name:"Intake", col:C1, marker:"APPENDIX  ·  A1 / A3",
    build:[["One queue for everything that arrives","every channel in a single place"],
           ["Wrong vendor code caught early","checked on the order before it moves"],
           ["Billable orders marked at intake","separated from recurring placeholders"]],
    gets:[["Everything lands in one queue","no backup inbox, no portal worked on its own"],
          ["Routine volume never reaches a coordinator",""],
          ["The re-invoice loop stops","vendor code and customer checked at intake"]],
    note:"Edge cases will be decided in the technical audit." },
  { n:"02", name:"Mission Control", col:C3, marker:"APPENDIX  ·  A2 / A3",
    build:[["SLA breaches predicted","warned ahead of the deadline, from past patterns"],
           ["Pauses & extensions predicted","flagged ahead of the request"],
           ["Role-based dashboard","each team gets its own view"],
           ["Agentic search & filtering","ask for what is needed and the list narrows"]],
    gets:[["Nobody runs the near-due report",""],
          ["At-risk orders raised to the owner","while there is still time to act"],
          ["One list per role","in place of 80–100 daily emails"],
          ["Finding work takes a few clicks","not a dozen"]],
    note:"" },
];
detail.forEach(d => {
  s = slide();
  topbar(s, "Module scope", d.marker);
  s.addText([{text:d.n+"   ",options:{color:d.col}},{text:d.name,options:{color:INK}}],
    { x: LX-0.02, y: 1.45, w: 11, h: 0.7, fontFace: SANS, fontSize: 32, bold: true, margin: 0 });
  const cw2=5.5, x2=6.85;
  mono(s, { t:"WHAT WE BUILD", x:LX, y:2.5, w:cw2, sz:12, c:d.col, b:true, cs:0.7 });
  let yy=3.0; d.build.forEach(b => { drow(s, LX, yy, cw2, b[0], b[1], d.col); yy += (b[1]&&b[1].length>40)?0.82:0.62; });
  if (d.note) mono(s, { t:d.note, x:LX, y:6.5, w:cw2, sz:10.5, c:LBL });
  mono(s, { t:"WHAT THE CLIENT GETS", x:x2, y:2.5, w:cw2, sz:12, c:d.col, b:true, cs:0.7 });
  yy=3.0; d.gets.forEach(g => { drow(s, x2, yy, cw2, g[0], g[1], d.col); yy += (g[1]&&g[1].length>40)?0.82:0.62; });
  s.addShape(p.ShapeType.line, { x:6.55, y:2.5, w:0, h:3.7, line:{color:LINE, width:1} });
});

/* --- 10. APPENDIX — GANTT --------------------------------------------- */
s = slide();
topbar(s, "Timeline breakdown", "APPENDIX  ·  A3 / A3");
s.addText("Week by week", { x: LX-0.02, y: 1.4, w: 11, h: 0.7, fontFace: SANS, fontSize: 32, bold: true, color: INK, margin: 0 });
const gantt = [   // {t: task, c: bar colour, b:[startWeek,endWeek], qa?: week, qc?: light tint}
  { t:"Technical audit",         c:SG, b:[1,2] },
  { t:"Foundation",              c:SG, b:[3,4] },
  { t:"Intake parsing & scoring", c:C1, b:[4,9], qa:10, qc:C1L },
  { t:"Vendor code validation",  c:C1, b:[8,9], qa:10, qc:C1L },
  { t:"Billable vs placeholder", c:C1, b:[8,9], qa:10, qc:C1L },
  { t:"Human review queue",      c:C1, b:[7,9], qa:10, qc:C1L },
  { t:"SLA breach prediction",   c:C3, b:[4,6], qa:7,  qc:C3L },
  { t:"Pause / extension pred.",  c:C3, b:[5,7], qa:8,  qc:C3L },
  { t:"Role-based views",        c:C3, b:[4,8], qa:9,  qc:C3L },
  { t:"Agentic search & filter", c:C3, b:[7,9], qa:10, qc:C3L },
  { t:"UAT & go-live",           c:C2, b:[11,12] },
];
const WEEKS=12, gx=4.35, gw=RX-gx, colW=gw/WEEKS, gy0=2.7, pitch=0.33, barH=0.19;
for (let k=0;k<WEEKS;k++){
  const cx=gx+k*colW;
  s.addShape(p.ShapeType.line, { x:cx, y:gy0-0.05, w:0, h:gantt.length*pitch+0.05, line:{color:"F0F1F5", width:1} });
  mono(s, { t:String(k+1), x:cx, y:gy0-0.42, w:colW, sz:10.5, c:LBL, b:true, a:"center", cs:0 });
}
mono(s, { t:"WEEK", x:gx-1.0, y:gy0-0.42, w:0.9, sz:9.5, c:MUT, a:"right" });
s.addShape(p.ShapeType.line, { x:gx+WEEKS*colW, y:gy0-0.05, w:0, h:gantt.length*pitch+0.05, line:{color:"F0F1F5", width:1} });
gantt.forEach((r,i) => {
  const ry=gy0+i*pitch;
  s.addText(r.t, { x:LX, y:ry-0.05, w:gx-LX-0.15, h:0.3, fontFace:SANS, fontSize:11, color:INK, align:"right", margin:0, valign:"middle" });
  s.addShape(p.ShapeType.roundRect, { x:gx+(r.b[0]-1)*colW, y:ry, w:(r.b[1]-r.b[0]+1)*colW, h:barH, rectRadius:0.03, fill:{color:r.c}, line:{type:"none"} });
  if (r.qa) s.addShape(p.ShapeType.roundRect, { x:gx+(r.qa-1)*colW, y:ry, w:colW, h:barH, rectRadius:0.03, fill:{color:r.qc}, line:{type:"none"} });
});
const leg=[["Intake build",C1],["Mission Control build",C3],["Setup / launch",SG],["QA",C1L]];
let lx=LX; const ly=6.62;
leg.forEach(g => {
  s.addShape(p.ShapeType.rect, { x:lx, y:ly+0.02, w:0.16, h:0.16, fill:{color:g[1]}, line:{type:"none"} });
  s.addText(g[0], { x:lx+0.26, y:ly-0.03, w:2.6, h:0.3, fontFace:SANS, fontSize:11, color:MUT, margin:0, valign:"middle" });
  lx += 0.55 + g[0].length*0.087 + 0.35;
});

/* --- 11. THANK YOU (dark separator) ----------------------------------- */
s = darkSlide();
s.addImage({ path: CFG.logoWhite, x: LX, y: 3.0, w: 2.1, h: 0.459 });
s.addText("Thank you.", { x: LX-0.06, y: 3.75, w: 11, h: 1.3, fontFace: SANS, fontSize: 60, bold: true, color: WHITE, margin: 0 });
mono(s, { t: "Let's build it together.", x: LX, y: 5.15, w: 10, sz: 14, c: "B7C0D4", cs: 0.5 });

/* ======================================================================== */
p.writeFile({ fileName: CFG.outfile }).then(f => console.log("WROTE", f));
