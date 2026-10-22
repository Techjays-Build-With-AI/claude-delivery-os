#!/usr/bin/env node
/*
  render-scope.js — ba/scope.md  ->  ba/scope.html

  The scope is the client-facing artifact: it is what gets published to
  Dashboard -> Reports and handed to someone who will never open a .md file.
  So the conversion happens HERE, at build time, and the page ships as plain
  HTML — no client-side renderer, no CDN, no fetch. It opens from a file://
  double-click, from a share link, and from a printer, identically.

    node render-scope.js ba/scope.md
         [--out ba/scope.html]
         [--ledger   ba/ledger.md]              open questions as a section
                                                (INTERNAL copies only -- see below)
         [--sources  ba/sources.md]             source-coverage block
         [--features ba/features]               the feature roll-up
         [--review requirements/<slug>/reviews/<ts>.json]  header score

  Mermaid blocks are shown as labelled source, not rendered: rendering them
  would mean loading a library from a CDN, and a scope that only works online
  is not self-contained. The diagram text stays readable and copy-pasteable.
*/

"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- args
function parseArgs(argv) {
  const out = { src: null, out: null, ledger: null, review: null, sources: null, features: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") out.out = argv[++i];
    else if (a === "--ledger") out.ledger = argv[++i];
    else if (a === "--sources") out.sources = argv[++i];
    else if (a === "--features") out.features = argv[++i];
    else if (a === "--review") out.review = argv[++i];
    else if (!a.startsWith("--") && !out.src) out.src = a;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
if (!args.src) {
  console.error("usage: node render-scope.js <scope.md> [--out <file>] [--ledger <f>] [--sources <f>] [--features <dir>] [--review <json>]");
  process.exit(1);
}
if (!fs.existsSync(args.src)) {
  console.error(`No such file: ${args.src}`);
  process.exit(1);
}
const OUT = args.out || args.src.replace(/\.md$/i, "") + ".html";

// ---------------------------------------------------------------- helpers
const esc = (v) =>
  String(v == null ? "" : v).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const slug = (t) =>
  String(t).toLowerCase().replace(/[^\w\s.-]/g, "").trim().replace(/[\s.]+/g, "-").replace(/^-+|-+$/g, "") || "s";

/** Front matter -> object. Deliberately shallow: the scope header needs five
 *  scalars, and a real YAML parser would be a dependency for nothing. */
function frontMatter(text) {
  const m = /^---\n([\s\S]*?)\n---\n?/.exec(text);
  if (!m) return { meta: {}, body: text };
  const meta = {};
  for (const line of m[1].split("\n")) {
    const kv = /^([A-Za-z0-9_ -]+):\s*(.*)$/.exec(line);
    if (kv) meta[kv[1].trim()] = kv[2].trim().replace(/^["']|["']$/g, "");
  }
  return { meta, body: text.slice(m[0].length) };
}

// ---------------------------------------------------------------- inline md
function inline(s) {
  // Code spans are extracted first so nothing inside them gets styled.
  const spans = [];
  let t = String(s).replace(/`([^`]+)`/g, (_, c) => {
    spans.push("<code>" + esc(c) + "</code>");
    return "\u0000" + (spans.length - 1) + "\u0000";
  });

  t = esc(t);
  t = t.replace(/!\[([^\]]*)\]\(([^)\s]+)[^)]*\)/g, (_, alt, src) => `<img src="${src}" alt="${alt}">`);
  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)[^)]*\)/g, (_, txt, href) => `<a href="${href}">${txt}</a>`);
  t = t.replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[^*\w])\*([^*\n]+)\*(?=[^*\w]|$)/g, "$1<em>$2</em>");
  t = t.replace(/(^|[\s(])_([^_\n]+)_(?=[\s).,;:!?]|$)/g, "$1<em>$2</em>");
  t = t.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  t = t.replace(/\u0000(\d+)\u0000/g, (_, i) => spans[+i]);
  return t;
}

// ---------------------------------------------------------------- block md
// ---------------------------------------------------------------------------
// Mermaid `flowchart TD` -> inline SVG.
//
// The scope's diagrams use four constructs: [box], ([stadium]), {diamond} and
// -->|label|. Small enough to lay out here, which keeps the page
// self-contained -- the same rule that keeps this renderer off a CDN, so a
// client opens the file offline and still sees the flows.
//
// Not a general Mermaid implementation: anything it cannot parse falls back to
// labelled source.
// ---------------------------------------------------------------------------
const SHAPE = {
  round: /^\(\[(.*)\]\)$/, // ([text])  terminal
  diamond: /^\{(.*)\}$/, //  {text}    decision
  box: /^\[(.*)\]$/, //      [text]    step
};

// Every internal id shape we mint: CLR-001, CON-002, ASM-013, DEC-014,
// SQ-001, EX-009, DATA-001, INT-001, QAF-001, PB-001, plus the area forms
// ROLE-UC-01, EP-AUTH-01, PAGE-TEAM-01, ENT-TEAM-01, FEAT-SUP-001.
const ID_RE =
  /\b(?:[A-Z]{2,6}-[A-Z]{2,6}-\d{1,3}|(?:CLR|CON|ASM|DEC|SQ|EX|DATA|INT|QAF|PB|OQ|BR|AC|TS|NFR|MAT|FND|QG)-\d{1,3})(?:\.\.\d{1,3})?/g;

/** Drop internal ids from client-facing prose.
 *
 *  They are our traceability markers -- the scope.md and the registers keep
 *  them, and /ba:review needs them. In the document a client reads they are
 *  noise at best: "(CON-002, CON-004)" hands over our filing system.
 *
 *  Order matters. Ids usually sit inside parentheses, so a token-level strip
 *  leaves "( , )" behind. Take whole id-only parentheticals first. */
function stripIds(html) {
  return html
    // (CON-002, CON-004)  /  (see CLR-030)  /  (EP-TEAM-01..06, EP-PROJ-02)
    .replace(/\s*\((?:\s*(?:see|also|and|per|ref\.?)?\s*(?:[A-Z]{2,6}-[A-Z]{2,6}-\d{1,3}|(?:CLR|CON|ASM|DEC|SQ|EX|DATA|INT|QAF|PB|OQ|BR|AC|TS|NFR|MAT|FND|QG)-\d{1,3})(?:\.\.\d{1,3})?[,;\s]*)+\)/g, "")
    // "; see CLR-030" / ", per CON-002" left mid-sentence
    .replace(/[;,]\s*(?:see|per|ref\.?)\s+(?:[A-Z]{2,6}-[A-Z]{2,6}-\d{1,3}|(?:CLR|CON|ASM|DEC|SQ|EX|DATA|INT|QAF|PB|OQ|BR|AC|TS|NFR|MAT|FND|QG)-\d{1,3})(?:\.\.\d{1,3})?/g, "")
    // any straggler, including the `ID: ` label form
    .replace(new RegExp(ID_RE.source + "\\s*[:\\u2014-]\\s*", "g"), "")
    .replace(ID_RE, "")
    // tidy what the removals left
    .replace(/\(\s*[,;]?\s*\)/g, "")
    .replace(/\s+([,.;:])/g, "$1")
    .replace(/([(\[])\s+/g, "$1")
    .replace(/ {2,}/g, " ");
}

/** `ROLE-UC-01: Assign roles` -> `Assign roles`. Internal ids are for the
 *  markdown and the registers, not for the client reading the diagram. */
function stripId(s) {
  return s
    .replace(/^[A-Z]{2,6}-[A-Z]{2,6}-\d{1,3}\s*[:—-]\s*/, "")
    .replace(/^[A-Z]{2,6}-\d{1,3}\s*[:—-]\s*/, "")
    .trim();
}

function parseFlow(src) {
  const nodes = new Map(); // id -> {id,label,shape}
  const edges = []; // {from,to,label}
  let sawHeader = false;

  for (const raw of src.split("\n")) {
    const line = raw.trim();
    if (!line || line.startsWith("%%")) continue;
    if (/^(flowchart|graph)\s+(TD|TB)\b/i.test(line)) { sawHeader = true; continue; }
    if (/^(flowchart|graph)\b/i.test(line)) return null; // LR etc -- not ours

    // A -->|label| B   /   A --> B
    // Split on the arrow rather than regex-matching the whole line: a node
    // token like `A([Trigger: people data changes])` contains spaces, so \S+
    // cannot stand in for it.
    const arrow = line.indexOf("-->");
    if (arrow > 0) {
      const lhs = line.slice(0, arrow);
      let rhs = line.slice(arrow + 3).trim();
      let elabel = "";
      const lbl = /^\|([^|]*)\|\s*(.*)$/.exec(rhs);
      if (lbl) { elabel = lbl[1].trim(); rhs = lbl[2].trim(); }
      const from = nodeRef(lhs, nodes);
      const to = nodeRef(rhs, nodes);
      if (!from || !to) return null;
      edges.push({ from, to, label: elabel });
      continue;
    }
    // a bare node declaration on its own line
    if (nodeRef(line, nodes)) continue;
    return null; // something we do not model -- fall back
  }
  if (!sawHeader || !nodes.size) return null;
  return { nodes, edges };
}

/** `ID[text]` -> registers and returns the id; `ID` alone -> the id. */
function nodeRef(token, nodes) {
  const m = /^([A-Za-z0-9_]+)\s*(.*)$/.exec(token.trim());
  if (!m) return null;
  const id = m[1];
  const rest = m[2].trim();
  if (rest) {
    let label = null, shape = "box";
    for (const [name, re] of Object.entries(SHAPE)) {
      const hit = re.exec(rest);
      if (hit) { label = hit[1]; shape = name; break; }
    }
    if (label === null) return null;
    nodes.set(id, { id, label: stripId(label.replace(/^["']|["']$/g, "")), shape });
  } else if (!nodes.has(id)) {
    nodes.set(id, { id, label: id, shape: "box" });
  }
  return id;
}

/** Longest-path layering: a node sits one row below its deepest parent. */
function layer(g) {
  const incoming = new Map([...g.nodes.keys()].map((k) => [k, 0]));
  for (const e of g.edges) incoming.set(e.to, (incoming.get(e.to) || 0) + 1);

  const depth = new Map([...g.nodes.keys()].map((k) => [k, 0]));
  const q = [...g.nodes.keys()].filter((k) => !incoming.get(k));
  if (!q.length) q.push(g.nodes.keys().next().value); // a cycle: start anywhere
  const seen = new Set(q);
  let guard = 0;
  while (q.length && guard++ < 5000) {
    const n = q.shift();
    for (const e of g.edges.filter((x) => x.from === n)) {
      if (depth.get(e.to) < depth.get(n) + 1) depth.set(e.to, depth.get(n) + 1);
      if (!seen.has(e.to)) { seen.add(e.to); q.push(e.to); }
      else q.push(e.to); // re-settle on a longer path
      if (guard++ > 5000) break;
    }
  }
  const rows = [];
  for (const [id, d] of depth) (rows[d] ||= []).push(id);
  return rows;
}

const CH = 6.2; // mean advance at 12px in the UI stack

function wrap(text, max) {
  const words = text.split(/\s+/);
  const out = [];
  let line = "";
  for (const w of words) {
    const t = line ? line + " " + w : w;
    if (t.length > max && line) { out.push(line); line = w; } else line = t;
  }
  if (line) out.push(line);
  return out.slice(0, 4);
}

function renderFlow(src) {
  const g = parseFlow(src);
  if (!g) return null;
  const rows = layer(g);
  if (!rows.length) return null;

  const PADX = 13, LINEH = 15, GAPY = 40, GAPX = 20, TOP = 10;
  const boxes = new Map();

  rows.forEach((row, r) => {
    row.forEach((id) => {
      const n = g.nodes.get(id);
      const lines = wrap(n.label, 26);
      const w = Math.max(84, Math.round(Math.max(...lines.map((l) => l.length)) * CH) + PADX * 2 + (n.shape === "diamond" ? 22 : 0));
      const h = lines.length * LINEH + 16 + (n.shape === "diamond" ? 10 : 0);
      boxes.set(id, { ...n, lines, w, h, r });
    });
  });

  // centre each row
  let width = 0;
  rows.forEach((row) => {
    const w = row.reduce((a, id) => a + boxes.get(id).w, 0) + GAPX * (row.length - 1);
    width = Math.max(width, w);
  });
  width += 40;

  let y = TOP;
  rows.forEach((row) => {
    const rowW = row.reduce((a, id) => a + boxes.get(id).w, 0) + GAPX * (row.length - 1);
    let x = (width - rowW) / 2;
    const rowH = Math.max(...row.map((id) => boxes.get(id).h));
    row.forEach((id) => {
      const b = boxes.get(id);
      b.x = x; b.y = y + (rowH - b.h) / 2;
      x += b.w + GAPX;
    });
    y += rowH + GAPY;
  });
  const height = y - GAPY + TOP;

  const parts = [];
  parts.push(
    `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" xmlns="http://www.w3.org/2000/svg" class="flow">`,
    `<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">` +
      `<path d="M0 0 L10 5 L0 10 z" fill="var(--flow-line)"/></marker></defs>`
  );

  // edges first, so nodes sit on top
  for (const e of g.edges) {
    const a = boxes.get(e.from), b = boxes.get(e.to);
    if (!a || !b) continue;
    const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
    const my = (y1 + y2) / 2;
    const d = Math.abs(x1 - x2) < 2
      ? `M${x1} ${y1} L${x2} ${y2 - 6}`
      : `M${x1} ${y1} L${x1} ${my} L${x2} ${my} L${x2} ${y2 - 6}`;
    parts.push(`<path d="${d}" fill="none" stroke="var(--flow-line)" stroke-width="1.4" marker-end="url(#ah)"/>`);
    if (e.label) {
      const lw = e.label.length * 6.1 + 12;
      const lx = Math.abs(x1 - x2) < 2 ? x1 : (x1 + x2) / 2;
      parts.push(
        `<rect x="${lx - lw / 2}" y="${my - 9}" width="${lw}" height="18" rx="9" fill="var(--flow-chip)"/>`,
        `<text x="${lx}" y="${my + 4}" text-anchor="middle" class="flow-edge">${esc(e.label)}</text>`
      );
    }
  }

  for (const b of boxes.values()) {
    if (b.shape === "diamond") {
      const cx = b.x + b.w / 2, cy = b.y + b.h / 2;
      parts.push(
        `<path d="M${cx} ${b.y} L${b.x + b.w} ${cy} L${cx} ${b.y + b.h} L${b.x} ${cy} z" ` +
          `fill="var(--flow-dec)" stroke="var(--flow-dec-s)" stroke-width="1.3"/>`
      );
    } else {
      const rx = b.shape === "round" ? b.h / 2 : 7;
      parts.push(
        `<rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="${rx}" ` +
          `fill="var(--flow-${b.shape})" stroke="var(--flow-${b.shape}-s)" stroke-width="1.3"/>`
      );
    }
    const startY = b.y + b.h / 2 - ((b.lines.length - 1) * LINEH) / 2 + 4;
    b.lines.forEach((ln, i) => {
      parts.push(
        `<text x="${b.x + b.w / 2}" y="${startY + i * LINEH}" text-anchor="middle" ` +
          `class="flow-t${b.shape === "round" ? " flow-term" : ""}">${esc(ln)}</text>`
      );
    });
  }

  parts.push("</svg>");
  return parts.join("");
}

function render(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const toc = [];
  let html = "";
  let i = 0;

  const listStack = []; // {tag, indent}
  function closeLists(toIndent) {
    while (listStack.length && listStack[listStack.length - 1].indent >= toIndent) {
      html += "</" + listStack.pop().tag + ">\n";
    }
  }
  function closeAllLists() {
    while (listStack.length) html += "</" + listStack.pop().tag + ">\n";
  }

  while (i < lines.length) {
    const line = lines[i];

    // fenced code
    const fence = /^\s*```+\s*([\w-]*)\s*$/.exec(line);
    if (fence) {
      closeAllLists();
      const lang = fence[1] || "";
      const buf = [];
      i++;
      while (i < lines.length && !/^\s*```+\s*$/.test(lines[i])) buf.push(lines[i++]);
      i++;
      const isDiagram = /^(mermaid|sequence|graph|flow)/i.test(lang);
      // Draw it where we can. The page stays self-contained -- the SVG is
      // inline, no CDN, no library -- and anything the parser cannot model
      // degrades to labelled source rather than breaking the page.
      const drawn = isDiagram ? renderFlow(buf.join("\n")) : null;
      if (drawn) {
        html += '<figure class="diagram">' + drawn + "</figure>\n";
        continue;
      }
      html +=
        '<figure class="code' + (isDiagram ? " diagram" : "") + '">' +
        (isDiagram ? '<figcaption>Flow diagram — source</figcaption>' : lang ? `<figcaption>${esc(lang)}</figcaption>` : "") +
        "<pre><code>" + esc(buf.join("\n")) + "</code></pre></figure>\n";
      continue;
    }

    // heading
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      closeAllLists();
      const lvl = h[1].length;
      const text = h[2].replace(/\s*#+\s*$/, "");
      const id = slug(text);
      if (lvl === 2 || lvl === 3) toc.push({ lvl, id, text });
      html += `<h${lvl} id="${id}">${inline(text)}</h${lvl}>\n`;
      i++;
      continue;
    }

    // table — a header row followed by a separator row
    if (/\|/.test(line) && i + 1 < lines.length && /^\s*\|?[\s:-]*\|[\s|:-]*$/.test(lines[i + 1])) {
      closeAllLists();
      const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const head = cells(line);
      const align = cells(lines[i + 1]).map((a) =>
        /^:-+:$/.test(a) ? "center" : /-+:$/.test(a) ? "right" : "left"
      );
      i += 2;
      let body = "";
      while (i < lines.length && /\|/.test(lines[i]) && lines[i].trim()) {
        const row = cells(lines[i++]);
        body +=
          "<tr>" +
          head.map((_, k) => `<td style="text-align:${align[k] || "left"}">${inline(row[k] || "")}</td>`).join("") +
          "</tr>\n";
      }
      html +=
        '<div class="tablewrap"><table><thead><tr>' +
        head.map((c, k) => `<th style="text-align:${align[k] || "left"}">${inline(c)}</th>`).join("") +
        "</tr></thead><tbody>" + body + "</tbody></table></div>\n";
      continue;
    }

    // blockquote
    if (/^\s*>\s?/.test(line)) {
      closeAllLists();
      const buf = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^\s*>\s?/, ""));
      html += "<blockquote>" + render(buf.join("\n")).html + "</blockquote>\n";
      continue;
    }

    // hr
    if (/^\s*([-*_])\s*(\1\s*){2,}$/.test(line)) {
      closeAllLists();
      html += "<hr>\n";
      i++;
      continue;
    }

    // list item
    const li = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/.exec(line);
    if (li) {
      const indent = li[1].replace(/\t/g, "    ").length;
      const ordered = /\d/.test(li[2]);
      const tag = ordered ? "ol" : "ul";
      closeLists(indent + 1);
      const top = listStack[listStack.length - 1];
      if (!top || top.indent < indent) {
        html += "<" + tag + ">\n";
        listStack.push({ tag, indent });
      }
      // checkbox items read as a list of states, not as literal "[x]"
      let body = li[3];
      const box = /^\[([ xX])\]\s+(.*)$/.exec(body);
      html += box
        ? `<li class="task"><input type="checkbox" disabled${/[xX]/.test(box[1]) ? " checked" : ""}> ${inline(box[2])}</li>\n`
        : `<li>${inline(body)}</li>\n`;
      i++;
      continue;
    }

    // blank
    if (!line.trim()) {
      closeAllLists();
      i++;
      continue;
    }

    // paragraph — gather until a blank line or the start of another block
    const buf = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,6})\s/.test(lines[i]) &&
      !/^\s*```/.test(lines[i]) &&
      !/^\s*>/.test(lines[i]) &&
      !/^(\s*)([-*+]|\d+[.)])\s+/.test(lines[i])
    ) {
      buf.push(lines[i++]);
    }
    if (buf.length) {
      closeAllLists();
      html += "<p>" + inline(buf.join(" ")) + "</p>\n";
    } else {
      i++;
    }
  }
  closeAllLists();
  return { html, toc };
}

// ---------------------------------------------------------------- assemble
const srcText = fs.readFileSync(args.src, "utf8");
const { meta, body } = frontMatter(srcText);
const main = render(body);
// scope.html is what the CLIENT reads: strip our traceability ids from the
// prose and from the TOC. scope.md and the registers keep every one of them,
// and /ba:review needs them -- this only affects the rendered page.
main.html = stripIds(main.html);
main.toc = main.toc.map((t) => ({ ...t, text: stripIds(t.text) }));

/** Rows of the first markdown table in ledger.md, keyed by lower-cased header. */
function readLedger(file) {
  const lines = fs.readFileSync(file, "utf8").replace(/\r\n/g, "\n").split("\n");
  const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  for (let i = 0; i < lines.length - 1; i++) {
    if (!/\|/.test(lines[i]) || !/^\s*\|?[\s:-]*\|[\s|:-]*$/.test(lines[i + 1])) continue;
    const head = cells(lines[i]).map((h) => h.toLowerCase());
    const rows = [];
    for (let j = i + 2; j < lines.length && /\|/.test(lines[j]) && lines[j].trim(); j++) {
      const c = cells(lines[j]);
      const row = {};
      head.forEach((h, k) => { row[h] = (c[k] || "").replace(/^`|`$/g, ""); });
      rows.push(row);
    }
    return rows;
  }
  return [];
}

const col = (row, ...names) => {
  for (const n of names) {
    const k = Object.keys(row).find((h) => h.includes(n));
    if (k && row[k]) return row[k];
  }
  return "";
};

// scope.html is what the CLIENT reads. Open questions belong to /ba:review,
// whose report has a tab for answering them in place; thirty-four unanswered
// questions at the end of a scope document is the BA's working surface pasted
// into the deliverable. Source coverage is QA on our own extraction. Both are
// opt-in now, and /ba:scope no longer asks for either.
let extra = "";
if (args.ledger && !fs.existsSync(args.ledger)) {
  console.warn(`  warning   --ledger ${args.ledger} does not exist; no questions section`);
}
if (args.ledger && fs.existsSync(args.ledger)) {
  const all = readLedger(args.ledger);
  if (!all.length) {
    console.warn(`  warning   no markdown table found in ${args.ledger}; no questions section`);
  }
  // Only open questions. A closed one is history, and an assumption or a
  // contradiction is not something to put in front of a client.
  const open = all.filter(
    (r) => /question/i.test(col(r, "kind")) && /^open$/i.test(col(r, "status"))
  );
  if (open.length) {
    main.toc.push({ lvl: 2, id: "client-questions", text: "Open questions" });
    extra =
      '<section class="qsection"><h2 id="client-questions">Open questions</h2>' +
      '<p class="lede">' + open.length + " still unanswered. Each one changes what gets built, " +
      "so the sooner it is settled the less it costs.</p>";
    for (const r of open) {
      const id = col(r, "id"), topic = col(r, "topic");
      const q = col(r, "statement", "question");
      const checked = col(r, "already checked", "checked");
      const owner = col(r, "owner");
      extra += '<div class="q">' +
        '<div class="qh"><span class="qid">' + esc(id) + "</span>" +
        (topic ? '<span class="qtopic">' + esc(topic) + "</span>" : "") + "</div>" +
        "<p>" + inline(q) + "</p>" +
        (checked ? '<p class="qmeta">Already checked: ' + inline(checked) + "</p>" : "") +
        (owner ? '<p class="qmeta">Owner: ' + esc(owner) + "</p>" : "") +
        "</div>";
    }
    extra += "</section>";
  }
}

/** Source coverage -- what contributed, what did not, and what we could not read.
 *  This is the content intake-runs/run-###.md used to hold: a file nobody opened,
 *  describing work the reader of the scope most wants to sanity-check. */
let coverage = "";
if (args.sources && fs.existsSync(args.sources)) {
  const rows = readLedger(args.sources);
  if (!rows.length) {
    console.warn(`  warning   no markdown table found in ${args.sources}; no source coverage`);
  } else {
    const st = (r) => col(r, "status").toLowerCase();
    const contributed = rows.filter((r) => /process|contribut|indexed/.test(st(r)));
    const blocked = rows.filter((r) => /access|guidance|required|fail/.test(st(r)));
    main.toc.push({ lvl: 2, id: "source-coverage", text: "Source coverage" });
    coverage =
      '<section class="cov"><h2 id="source-coverage">Source coverage</h2>' +
      '<p class="lede">' + contributed.length + " of " + rows.length +
      " sources contributed to this scope." +
      (blocked.length ? " <b>" + blocked.length + " could not be read.</b>" : "") + "</p>" +
      '<div class="tablewrap"><table><thead><tr><th>Source</th><th>Mode</th><th>Status</th><th>Notes</th></tr></thead><tbody>';
    for (const r of rows) {
      const bad = blocked.includes(r);
      coverage +=
        '<tr' + (bad ? ' class="bad"' : "") + ">" +
        "<td>" + inline(col(r, "source", "name") || col(r, "id")) + "</td>" +
        "<td>" + esc(col(r, "mode")) + "</td>" +
        "<td>" + esc(col(r, "status")) + "</td>" +
        "<td>" + inline(col(r, "why", "note")) + "</td></tr>";
    }
    coverage += "</tbody></table></div>";
    // A source that could not be read is a hole in the scope, not a footnote.
    if (blocked.length) {
      coverage += '<p class="lede"><b>Nothing below was derived from those ' + blocked.length +
        ".</b> Anything they would have covered is absent from this scope, not assumed.</p>";
    }
    coverage += "</section>";
  }
}

/** The feature roll-up -- what feature-index.md cached. Read live from each
 *  status.md, so it cannot go stale the way the cached index did. */
let features = "";
if (args.features && fs.existsSync(args.features)) {
  const dirs = fs.readdirSync(args.features, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
  const rows = [];
  for (const slug of dirs) {
    const st = path.join(args.features, slug, "status.md");
    if (!fs.existsSync(st)) { rows.push({ slug }); continue; }
    const meta = frontMatter(fs.readFileSync(st, "utf8")).meta;
    rows.push({
      slug,
      id: meta["feature_id"] || meta["id"] || "",
      title: meta["title"] || meta["feature"] || slug,
      status: meta["status"] || "",
      priority: meta["priority"] || "",
    });
  }
  if (rows.length) {
    main.toc.push({ lvl: 2, id: "features", text: "Features" });
    features =
      '<section class="cov"><h2 id="features">Features</h2>' +
      '<p class="lede">' + rows.length + " features, read from each folder\u2019s own status \u2014 " +
      "not a cached list.</p>" +
      '<div class="tablewrap"><table><thead><tr><th>ID</th><th>Feature</th><th>Status</th><th>Priority</th></tr></thead><tbody>';
    for (const r of rows) {
      features += "<tr><td>" + esc(r.id) + "</td><td>" + esc(r.title) +
        "</td><td>" + esc(r.status || "\u2014") + "</td><td>" + esc(r.priority || "\u2014") + "</td></tr>";
    }
    features += "</tbody></table></div></section>";
  }
}

let score = null;
if (args.review && fs.existsSync(args.review)) {
  try {
    const rev = JSON.parse(fs.readFileSync(args.review, "utf8"));
    if (rev && rev.overallScore != null) score = { n: rev.overallScore, verdict: rev.verdict || "" };
  } catch {
    /* a malformed review must not take the scope down with it */
  }
}

const title =
  meta["Requirement"] || meta["requirement"] || meta["title"] || meta["name"] ||
  (/^#\s+(.+)$/m.exec(body) || [])[1] || path.basename(args.src, ".md");
const status = meta["Status"] || meta["status"] || "Draft";
const version = meta["Version"] || meta["version"] || "";
const updated = meta["Updated"] || meta["updated"] || meta["Last Updated"] ||
  new Date(fs.statSync(args.src).mtime).toISOString().slice(0, 10);

const statusClass = /approved/i.test(status) ? "ok" : /review/i.test(status) ? "mid" : "draft";

const tocHtml = main.toc
  .map((t) => `<a class="l${t.lvl}" href="#${t.id}">${esc(t.text)}</a>`)
  .join("\n");

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} — Scope</title>
<style>
  /* Techjays house style -- tokens from doc-deck/references/design-system.md.
     Laid out as a DOCUMENT: a fixed contents rail and a wide content column,
     because this is eleven numbered sections of tables that a reader jumps
     around in, not an essay read top to bottom. */
  :root {
    --ink:#141414; --lbl:#424B5B; --mut:#6B7280; --faint:#9AA0AA;
    --line:#E7E7EC; --bg:#FFFFFF; --surface:#FBFBFD; --surface2:#F4F4F8;
    --c1:#6870F8; --c1l:#C3C7FB; --c2:#E3A03C; --c3:#1FA98A;
    --rail:272px; --content:1080px; --radius:8px;
    /* flow diagrams: terminals teal, steps indigo-tinted, decisions amber */
    --flow-line:#9AA0AA; --flow-chip:#F4F4F8;
    --flow-box:#F3F4FE;   --flow-box-s:#C3C7FB;
    --flow-round:#E8F7F3; --flow-round-s:#AEE4D7;
    --flow-dec:#FDF4E7;   --flow-dec-s:#E3A03C;
  }
  @media (prefers-color-scheme:dark){:root{
    --ink:#ECECEF; --lbl:#AEB6C4; --mut:#9098A6; --faint:#6B7280;
    --line:#242B3D; --bg:#0F1524; --surface:#19223A; --surface2:#141B2E;
    --c1:#8E95FF; --c1l:#3B4280;
    --flow-line:#6B7280; --flow-chip:#1E2742;
    --flow-box:#1E2742;   --flow-box-s:#3B4280;
    --flow-round:#13302B; --flow-round-s:#1FA98A;
    --flow-dec:#2E2516;   --flow-dec-s:#E3A03C;}}

  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
  body{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:"Google Sans","Product Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:15px; line-height:1.6;
    font-feature-settings:"kern" 1,"liga" 1; text-rendering:optimizeLegibility;
  }
  a{color:var(--c1);text-decoration:none}
  a:hover{text-decoration:underline}

  /* ---- cover band ------------------------------------------------------- */
  header.band{background:#141B2E;color:#fff;border:0}
  .band-in{max-width:var(--content);margin:0 auto;padding:38px 56px 30px}
  .eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.15em;
    color:#8A93A8;font-weight:600}
  header.band h1{margin:12px 0 16px;font-size:36px;line-height:1.1;
    letter-spacing:-.02em;font-weight:600;color:#fff;max-width:22ch}
  .chips{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
  .chip{font-size:12px;padding:3px 11px;border-radius:999px;
    border:1px solid rgba(255,255,255,.24);color:#B7C0D4}
  .chip.status,.chip.score{border-color:var(--c1);color:#C3C7FB;font-weight:600}

  /* ---- document shell: rail + column ------------------------------------ */
  .shell{max-width:calc(var(--content) + var(--rail));margin:0 auto;
    padding:0 56px 90px;display:grid;grid-template-columns:var(--rail) minmax(0,1fr);
    gap:56px;align-items:start}

  nav.toc{position:sticky;top:0;max-height:100vh;overflow-y:auto;
    padding:30px 0 30px;border:0}
  nav.toc::before{content:"Contents";display:block;font-size:11px;
    text-transform:uppercase;letter-spacing:.14em;color:var(--lbl);
    font-weight:600;margin-bottom:14px}
  nav.toc a{display:block;font-size:15px;color:var(--mut);padding:7px 0 7px 14px;
    border-left:2px solid var(--line);line-height:1.45;
    transition:color .12s,border-color .12s}
  nav.toc a:hover{color:var(--ink);border-left-color:var(--c1l);text-decoration:none}
  nav.toc a.l3{padding-left:26px;font-size:13.5px}
  /* where you are. Without it an eleven-section rail is a list, not a map. */
  nav.toc a.active{color:var(--c1);border-left-color:var(--c1);font-weight:600}
  nav.toc a.l3.active{font-weight:500}

  main{padding-top:30px;min-width:0}

  /* ---- type: numbered-section document ---------------------------------- */
  h2{font-size:23px;line-height:1.25;letter-spacing:-.012em;font-weight:600;
    margin:38px 0 8px;padding-top:18px;border-top:2px solid var(--ink)}
  h2:first-of-type{margin-top:0;padding-top:0;border-top:0}
  h3{font-size:17px;line-height:1.32;font-weight:600;margin:24px 0 5px}
  h4{font-size:14px;font-weight:600;color:var(--lbl);margin:18px 0 3px;
    text-transform:none;letter-spacing:0}
  p{margin:0 0 .85em;max-width:78ch}
  ul,ol{max-width:78ch;margin:.5em 0} li{margin:.18em 0}
  blockquote{margin:1em 0;padding:10px 16px;background:var(--surface);
    border-left:3px solid var(--c1);border-radius:0 var(--radius) var(--radius) 0;
    color:var(--ink)}
  blockquote p:last-child{margin-bottom:0}

  /* ---- tables get the full column --------------------------------------- */
  table{border-collapse:collapse;width:100%;margin:1.1em 0;font-size:13.5px;
    line-height:1.45}
  th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;
    color:var(--lbl);font-weight:600;background:var(--surface2);
    border-bottom:1px solid var(--line);padding:7px 12px;white-space:nowrap}
  td{padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
  tr:last-child td{border-bottom:1px solid var(--line)}
  tbody tr:hover td{background:var(--surface)}

  code{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
    font-size:.86em;background:var(--surface2);border-radius:4px;padding:1.5px 5px}
  pre{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
    padding:16px 18px;overflow:auto;font-size:13px;line-height:1.55}
  pre code{background:none;padding:0}

  /* ---- toolbar ---------------------------------------------------------- */
  figure.diagram{margin:1.2em 0;padding:12px 10px;background:var(--surface);
    border:1px solid var(--line);border-radius:var(--radius);overflow-x:auto}
  figure.diagram svg{display:block;margin:0 auto;max-width:100%;height:auto}
  figure.diagram{text-align:center}
  .flow-t{font-size:12px;fill:var(--ink);font-weight:500}
  .flow-term{font-weight:600}
  .flow-edge{font-size:11.5px;fill:var(--mut)}

  .tools{position:fixed;right:24px;bottom:24px;display:flex;gap:8px;z-index:50}
  .tools button{font:inherit;font-size:13px;font-weight:500;cursor:pointer;
    padding:9px 17px;border-radius:999px;border:1px solid var(--line);
    background:var(--bg);color:var(--ink);box-shadow:0 2px 12px rgba(20,27,46,.12)}
  .tools button:hover{border-color:var(--c1);color:var(--c1)}
  .tools button.primary{background:var(--c1);border-color:var(--c1);color:#fff}
  .tools button.primary:hover{background:#565EE8;color:#fff}

  @media print{
    .tools,nav.toc{display:none}
    .shell{display:block;max-width:none;padding:0}
    main{padding-top:0}
    header.band{background:none;color:var(--ink);border-bottom:2px solid var(--ink)}
    header.band h1{color:var(--ink);font-size:30px} .band-in{padding:0 0 18px}
    .eyebrow,.chip{color:var(--mut);border-color:var(--line)}
    body{font-size:10.5pt;line-height:1.45}
    h2{page-break-after:avoid;font-size:17pt;border-top-width:1.5px}
    h3{page-break-after:avoid;font-size:13pt}
    table,pre,blockquote{page-break-inside:avoid}
    th{background:#F4F4F8}
  }
  @media (max-width:1100px){
    .shell{grid-template-columns:1fr;gap:0;padding:0 32px 100px}
    nav.toc{position:static;max-height:none;padding:28px 0 0;
      display:flex;flex-wrap:wrap;gap:2px 16px;
      border-bottom:1px solid var(--line);margin-bottom:8px}
    nav.toc::before{width:100%}
    nav.toc a{border-left:0;padding:3px 0} nav.toc a.l3{display:none}
    .band-in{padding:40px 32px 32px}
    header.band h1{font-size:34px}
  }
  @media (max-width:640px){
    .shell,.band-in{padding-left:20px;padding-right:20px}
    header.band h1{font-size:28px} h2{font-size:22px}
    table{font-size:13.5px} th,td{padding:9px 10px}
    .tools{right:12px;bottom:12px}
  }
</style>
</head>
<body>

<header class="band">
  <div class="band-in">
    <div class="eyebrow">Project scope</div>
    <h1>${esc(title)}</h1>
    <div class="facts">
      <span class="chip status" style="--c:var(--${statusClass})">${esc(status)}</span>
      ${version ? `<span class="chip">${esc(version)}</span>` : ""}
      <span class="chip">Updated ${esc(updated)}</span>
      ${score ? `<span class="chip score">Readiness ${esc(score.n)}/10${score.verdict ? " · " + esc(score.verdict) : ""}</span>` : ""}
    </div>
  </div>
</header>

<div class="shell">
  <nav class="toc">
${tocHtml}
  </nav>
  <main>
${main.html}${coverage}${features}${extra}
  </main>
</div>

<footer>Generated by the Techjays BA Agent from ${esc(path.basename(args.src))} · ${esc(updated)}</footer>

<div class="tools">
  <button class="primary" onclick="exportDoc()">Export as .doc</button>
  <button onclick="window.print()">Print / PDF</button>
</div>
<script>
// Light the contents entry for whatever section you are reading. No library --
// IntersectionObserver is in every browser this page targets, and the page
// stays self-contained.
(function () {
  var links = [].slice.call(document.querySelectorAll("nav.toc a[href^='#']"));
  if (!links.length || !window.IntersectionObserver) return;
  var byId = {};
  links.forEach(function (a) { byId[decodeURIComponent(a.hash.slice(1))] = a; });
  var targets = Object.keys(byId)
    .map(function (id) { return document.getElementById(id); })
    .filter(Boolean);
  if (!targets.length) return;

  var current = null;
  function mark(id) {
    if (id === current) return;
    current = id;
    links.forEach(function (a) { a.classList.remove("active"); });
    var a = byId[id];
    if (!a) return;
    a.classList.add("active");
    // keep it in view when the rail is taller than the viewport
    var nav = a.closest("nav.toc");
    if (nav && nav.scrollHeight > nav.clientHeight) {
      var top = a.offsetTop - nav.clientHeight / 2;
      nav.scrollTo({ top: top, behavior: "smooth" });
    }
  }

  var visible = {};
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      visible[e.target.id] = e.isIntersecting ? e.intersectionRatio : 0;
    });
    // the highest heading still on screen wins; ties go to document order
    var best = null, bestTop = Infinity;
    targets.forEach(function (t) {
      if (!visible[t.id]) return;
      var top = t.getBoundingClientRect().top;
      if (top < bestTop) { bestTop = top; best = t.id; }
    });
    if (best) mark(best);
  }, { rootMargin: "0px 0px -62% 0px", threshold: [0, 1] });

  targets.forEach(function (t) { io.observe(t); });
})();

// A .doc Word opens is HTML plus the Office namespace and the right MIME type.
// No library, no CDN -- the page stays self-contained, which is the same rule
// that keeps Mermaid rendered as labelled source here.
function exportDoc() {
  var page = document.documentElement.cloneNode(true);
  var tools = page.querySelector(".tools"); if (tools) tools.remove();
  page.querySelectorAll("script").forEach(function (n) { n.remove(); });
  var nav = page.querySelector("nav.toc"); if (nav) nav.remove();

  // Word ignores most of the stylesheet; give it the few rules it does honour
  // so the export is a readable document rather than unstyled text.
  var wordCss =
    "<style>" +
    "body{font-family:Calibri,Arial,sans-serif;font-size:11pt;line-height:1.5;color:#141414}" +
    "h1{font-size:22pt;color:#141414} h2{font-size:16pt;border-bottom:1px solid #E7E7EC;padding-bottom:4pt}" +
    "h3{font-size:13pt} h4{font-size:11pt;color:#424B5B}" +
    "table{border-collapse:collapse;width:100%}" +
    "th{background:#F2F2F7;text-align:left;border:1px solid #E7E7EC;padding:6pt;font-size:9pt}" +
    "td{border:1px solid #E7E7EC;padding:6pt;vertical-align:top}" +
    "code,pre{font-family:Consolas,monospace;font-size:9.5pt;background:#FBFBFD}" +
    "blockquote{border-left:3px solid #C3C7FB;padding-left:10pt;color:#6B7280}" +
    "a{color:#6870F8}" +
    "</style>";

  var head = page.querySelector("head");
  if (head) { head.querySelectorAll("style").forEach(function (n) { n.remove(); }); }

  var html =
    '<html xmlns:o="urn:schemas-microsoft-com:office:office" ' +
    'xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">' +
    '<head><meta charset="utf-8">' + wordCss + "</head>" +
    "<body>" + page.querySelector("body").innerHTML + "</body></html>";

  var name = (document.title || "scope").replace(/[^A-Za-z0-9._ -]+/g, "-").trim() + ".doc";
  var blob = new Blob(["﻿", html], { type: "application/msword" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
}
</script>
</body>
</html>
`;

fs.mkdirSync(path.dirname(path.resolve(OUT)), { recursive: true });
fs.writeFileSync(OUT, html, "utf8");
console.log(`  rendered  ${OUT}  (${main.toc.length} sections, ${(html.length / 1024).toFixed(1)} KB)`);
