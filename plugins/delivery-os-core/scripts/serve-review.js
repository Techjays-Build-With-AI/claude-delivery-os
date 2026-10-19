#!/usr/bin/env node
/*
  serve-review.js — serve a reports folder and let the page save back into it.

  A browser cannot write to disk. `npx serve` is static, so the report's Save
  button could only ever trigger a download into ~/Downloads, leaving the BA to
  move the file by hand every round — the one step people skip. This server
  closes that: it serves the folder AND accepts the responses file back, so
  Save writes straight to ba/reviews/ and the page can report the real path.

    node serve-review.js [folder] [--port 4100] [--no-open]

  Defaults to .jetrix/ba/reviews. Also serves qa/audits — the audit report is
  the same shape, so one script covers both.

  Writes are deliberately narrow: POST /save only, only into the served folder,
  only a plain `*.md` basename. Path traversal is rejected, not sanitised.
*/

"use strict";

const http = require("http");
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
};

// A responses file, and nothing else. No separators, no dots-dot, no extension games.
const SAFE_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]*\.md$/;

function parseArgs(argv) {
  const out = { folder: ".jetrix/ba/reviews", port: 4100, open: true, portCeiling: 4120 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--port") out.port = parseInt(argv[++i], 10);
    else if (a === "--no-open") out.open = false;
    else if (!a.startsWith("--")) out.folder = a;
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const ROOT = path.resolve(args.folder);

if (!fs.existsSync(ROOT) || !fs.statSync(ROOT).isDirectory()) {
  console.error(`No such folder: ${ROOT}`);
  console.error(`Run /ba:review first, or pass the folder: node serve-review.js <folder>`);
  process.exit(1);
}

function send(res, code, body, type) {
  res.writeHead(code, {
    "Content-Type": type || "text/plain; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(body);
}

function newestReport() {
  const html = fs
    .readdirSync(ROOT)
    .filter((f) => f.endsWith(".html"))
    .map((f) => ({ f, m: fs.statSync(path.join(ROOT, f)).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  return html.length ? html[0].f : null;
}

function handleSave(req, res) {
  let raw = "";
  req.on("data", (c) => {
    raw += c;
    if (raw.length > 8 * 1024 * 1024) req.destroy(); // a responses file is kilobytes
  });
  req.on("end", () => {
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      return send(res, 400, JSON.stringify({ ok: false, error: "Body was not JSON." }), MIME[".json"]);
    }

    const name = String(payload.filename || "");
    const content = String(payload.content || "");

    if (!SAFE_NAME.test(name)) {
      return send(
        res,
        400,
        JSON.stringify({ ok: false, error: `Refused filename "${name}" — expected a plain *.md basename.` }),
        MIME[".json"]
      );
    }

    const dest = path.join(ROOT, name);
    // Belt and braces: SAFE_NAME already forbids separators, but never trust one check.
    if (path.dirname(path.resolve(dest)) !== ROOT) {
      return send(res, 400, JSON.stringify({ ok: false, error: "Refused: path escapes the served folder." }), MIME[".json"]);
    }

    try {
      fs.writeFileSync(dest, content, "utf8");
    } catch (err) {
      return send(res, 500, JSON.stringify({ ok: false, error: String(err.message || err) }), MIME[".json"]);
    }

    // Show the workspace-relative path when there is one; a "../../.." chain
    // is worse than the absolute path for someone trying to find the file.
    const rel = path.relative(process.cwd(), dest).split(path.sep).join("/");
    const shown = rel.startsWith("..") ? dest : rel;
    console.log(`  saved  ${shown}`);
    send(res, 200, JSON.stringify({ ok: true, path: shown, absolute: dest }), MIME[".json"]);
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");

  if (req.method === "POST" && url.pathname === "/save") return handleSave(req, res);

  if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, "Method not allowed.");

  let rel = decodeURIComponent(url.pathname).replace(/^\/+/, "");
  if (rel === "") {
    const newest = newestReport();
    if (!newest) return send(res, 404, `No .html report in ${ROOT}. Run /ba:review first.`);
    res.writeHead(302, { Location: "/" + encodeURIComponent(newest) });
    return res.end();
  }

  const file = path.resolve(ROOT, rel);
  if (!file.startsWith(ROOT + path.sep) && file !== ROOT) return send(res, 403, "Forbidden.");
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) return send(res, 404, "Not found.");

  send(res, 200, fs.readFileSync(file), MIME[path.extname(file).toLowerCase()] || "application/octet-stream");
});

// A taken port must not be a dead end: the command that starts this script
// reads the chosen port back off stdout, and a hard crash would leave the run
// with a report nobody can save from.
server.on("error", (err) => {
  if (err.code === "EADDRINUSE" && args.port < args.portCeiling) {
    server.listen(++args.port, "127.0.0.1");
    return;
  }
  console.error(`Could not listen on port ${args.port}: ${err.message}`);
  process.exit(1);
});

server.listen(args.port, "127.0.0.1", () => {
  // 127.0.0.1, not "localhost": the server binds IPv4 loopback, and on hosts
  // where localhost resolves to ::1 first that name does not reach it.
  const url = `http://127.0.0.1:${args.port}/`;
  const newest = newestReport();
  console.log(`\n  Serving  ${ROOT}`);
  console.log(`  Open     ${url}${newest ? "  → " + newest : ""}`);
  console.log(`  Save     writes straight into that folder — leave this running\n`);
  console.log(`  Ctrl-C to stop.\n`);
  // Parsed by the command that spawned this; keep the shape stable.
  console.log(`DELIVERY_OS_SERVE_READY ${url}`);

  if (!args.open) return;
  const cmd =
    process.platform === "win32" ? ["cmd", ["/c", "start", "", url]] :
    process.platform === "darwin" ? ["open", [url]] : ["xdg-open", [url]];
  execFile(cmd[0], cmd[1], () => {}); // a browser that won't open is not an error
});
