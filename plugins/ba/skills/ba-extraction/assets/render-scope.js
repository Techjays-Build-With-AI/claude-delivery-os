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
         [--questions ba/client-questions.md]   append as a section
         [--review ba/reviews/scope-review-<ts>.json]   header score

  Mermaid blocks are shown as labelled source, not rendered: rendering them
  would mean loading a library from a CDN, and a scope that only works online
  is not self-contained. The diagram text stays readable and copy-pasteable.
*/

"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- args
function parseArgs(argv) {
  const out = { src: null, out: null, questions: null, review: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") out.out = argv[++i];
    else if (a === "--questions") out.questions = argv[++i];
    else if (a === "--review") out.review = argv[++i];
    else if (!a.startsWith("--") && !out.src) out.src = a;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
if (!args.src) {
  console.error("usage: node render-scope.js <scope.md> [--out <file>] [--questions <file>] [--review <json>]");
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
      html +=
        '<figure class="code' + (isDiagram ? " diagram" : "") + '">' +
        (isDiagram ? '<figcaption>Flow diagram — Mermaid source</figcaption>' : lang ? `<figcaption>${esc(lang)}</figcaption>` : "") +
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

let extra = "";
if (args.questions && fs.existsSync(args.questions)) {
  const q = frontMatter(fs.readFileSync(args.questions, "utf8")).body;
  const r = render(q);
  main.toc.push({ lvl: 2, id: "client-questions", text: "Open questions for the client" });
  extra =
    '<section class="qsection"><h2 id="client-questions">Open questions for the client</h2>' +
    '<p class="lede">Everything below is still unanswered. Each one changes what gets built, so the sooner it is settled the less it costs.</p>' +
    r.html + "</section>";
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
  :root {
    --bg:#f6f8fa; --surface:#fff; --surface-2:#f6f8fa; --border:#d0d7de;
    --text:#1f2328; --muted:#636c76; --accent:#0969da;
    --ok:#1a7f37; --mid:#bf8700; --draft:#636c76;
    --shadow:0 1px 3px rgba(31,35,40,.08),0 1px 2px rgba(31,35,40,.06); --radius:10px;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#0d1117; --surface:#161b22; --surface-2:#21262d; --border:#30363d;
    --text:#e6edf3; --muted:#8b949e; --accent:#4493f8;
    --ok:#3fb950; --mid:#d29922; --draft:#8b949e; --shadow:none;}}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font-size:15.5px;line-height:1.65;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}

  header.band{background:var(--surface);border-bottom:1px solid var(--border);box-shadow:var(--shadow)}
  .band-in{max-width:1180px;margin:0 auto;padding:26px 24px 20px}
  .eyebrow{font-size:11.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:700}
  h1{margin:6px 0 12px;font-size:30px;line-height:1.2}
  .facts{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
  .chip{font-size:12px;padding:2px 9px;border-radius:999px;border:1px solid var(--border);color:var(--muted)}
  .chip.status{border-color:var(--c);color:var(--c);font-weight:700}
  .chip.score{border-color:var(--accent);color:var(--accent);font-weight:700}

  .shell{max-width:1180px;margin:0 auto;padding:0 24px 90px;display:grid;
    grid-template-columns:232px minmax(0,1fr);gap:40px;align-items:start}
  nav.toc{position:sticky;top:20px;margin-top:28px;max-height:calc(100vh - 48px);overflow:auto;
    border-left:1px solid var(--border);padding-left:14px}
  nav.toc a{display:block;font-size:13px;color:var(--muted);padding:3px 0;line-height:1.4}
  nav.toc a:hover{color:var(--accent);text-decoration:none}
  nav.toc a.l3{padding-left:13px;font-size:12.5px}

  main{min-width:0;margin-top:28px}
  main h2{margin:38px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--border);font-size:21px}
  main h3{margin:26px 0 8px;font-size:17px}
  main h4{margin:20px 0 6px;font-size:15px;color:var(--muted);
    text-transform:uppercase;letter-spacing:.04em}
  main h2:first-child{margin-top:0}
  p{margin:11px 0} ul,ol{margin:11px 0;padding-left:24px} li{margin:4px 0}
  li.task{list-style:none;margin-left:-20px} li.task input{margin-right:7px}
  code{background:var(--surface-2);border:1px solid var(--border);padding:.08em .38em;
    border-radius:5px;font-size:.87em;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
  figure.code{margin:14px 0;background:var(--surface);border:1px solid var(--border);
    border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
  figure.code figcaption{font-size:11px;text-transform:uppercase;letter-spacing:.05em;
    color:var(--muted);padding:7px 13px;border-bottom:1px solid var(--border);background:var(--surface-2)}
  figure.code pre{margin:0;padding:13px;overflow:auto}
  figure.code code{background:none;border:0;padding:0;font-size:12.6px;line-height:1.55}
  figure.diagram figcaption{color:var(--accent)}
  blockquote{margin:14px 0;padding:2px 16px;border-left:3px solid var(--border);color:var(--muted)}
  hr{border:0;border-top:1px solid var(--border);margin:30px 0}
  .tablewrap{overflow-x:auto;margin:14px 0;background:var(--surface);
    border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
  table{border-collapse:collapse;width:100%;font-size:14px}
  th,td{padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}
  th{background:var(--surface-2);font-size:12px;text-transform:uppercase;
    letter-spacing:.03em;color:var(--muted);white-space:nowrap}
  tbody tr:last-child td{border-bottom:0}
  img{max-width:100%;height:auto;border-radius:8px}

  .qsection{margin-top:46px;padding:22px 24px;background:var(--surface);
    border:1px solid var(--border);border-left:3px solid var(--mid);
    border-radius:var(--radius);box-shadow:var(--shadow)}
  .qsection h2{margin-top:0;border-bottom:0}
  .lede{color:var(--muted);font-size:14px;margin-top:0}

  footer{max-width:1180px;margin:0 auto;padding:22px 24px 40px;color:var(--muted);
    font-size:12.5px;border-top:1px solid var(--border)}

  @media (max-width:900px){
    .shell{grid-template-columns:1fr;gap:0}
    nav.toc{position:static;max-height:none;border-left:0;border-bottom:1px solid var(--border);
      padding:0 0 14px;margin-bottom:6px;columns:2;column-gap:20px}
    nav.toc a.l3{display:none}
  }
  @media print{
    body{background:#fff;font-size:11pt}
    nav.toc,header.band{position:static}
    .shell{display:block;max-width:none;padding:0}
    figure.code,.tablewrap,.qsection{break-inside:avoid;box-shadow:none}
    h2,h3{break-after:avoid}
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
${main.html}${extra}
  </main>
</div>

<footer>Generated by the Techjays BA Agent from ${esc(path.basename(args.src))} · ${esc(updated)}</footer>

</body>
</html>
`;

fs.mkdirSync(path.dirname(path.resolve(OUT)), { recursive: true });
fs.writeFileSync(OUT, html, "utf8");
console.log(`  rendered  ${OUT}  (${main.toc.length} sections, ${(html.length / 1024).toFixed(1)} KB)`);
