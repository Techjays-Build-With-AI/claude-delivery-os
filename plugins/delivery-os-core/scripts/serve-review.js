#!/usr/bin/env node
/*
  serve-review.js — serve a reports folder and let the page save back into it.

  A browser cannot write to disk. `npx serve` is static, so the report's Save
  button could only ever trigger a download into ~/Downloads, leaving the BA to
  move the file by hand every round — the one step people skip. This server
  closes that: it serves the folder AND accepts the responses file back, so
  Save writes straight to ba/reviews/ and the page can report the real path.

    node serve-review.js [folder] [--port 4100] [--open]

  Defaults to .jetrix/ba/reviews. Also serves qa/reviews and tl-reviews — every
  report is the same shape, so one script covers them all.

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
  // open defaults to FALSE: the run is usually still printing when this binds,
  // and launching a browser there steals focus mid-summary. Print the URL and
  // let the reader choose the moment.
  const out = { folder: ".jetrix/ba/reviews", port: 4100, open: false, portCeiling: 4120 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--port") out.port = parseInt(argv[++i], 10);
    else if (a === "--open") out.open = true;
    else if (a === "--no-open") out.open = false;   // accepted, already the default
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

// Only loopback. A report served on 4100 may need to save through an instance
// on 4101 -- a different origin -- but "*" would also hand POST /save to every
// site in the user's browser.
const LOOPBACK = /^http:\/\/(127\.0\.0\.1|localhost|\[::1\]):\d+$/;
function corsHeaders(req) {
  const origin = req.headers.origin;
  if (!origin) return {};
  // A report opened straight off disk has the origin "null", which fails the
  // loopback test -- so the page could not even see that a server was running
  // and every Save fell to the file dialog. Let that origin read /__whoami
  // only: a fixed blob naming this script and its folder, enough for the page
  // to find the server and hop onto it, after which it is on a loopback origin
  // like any other. POST /save stays loopback-only.
  const probeOnly =
    origin === "null" &&
    req.method === "GET" &&
    String(req.url || "").split("?")[0] === "/__whoami";
  if (!probeOnly && !LOOPBACK.test(origin)) return {};
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function send(res, code, body, type, req) {
  res.writeHead(code, Object.assign({
    "Content-Type": type || "text/plain; charset=utf-8",
    "Cache-Control": "no-store",
  }, req ? corsHeaders(req) : {}));
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

    // The report carries the folder it belongs to, so it no longer matters
    // which folder this server was started on -- the page nominates the
    // destination and any instance can honour it. That is what removes the
    // port/folder matching entirely.
    //
    // Bounded on purpose: a page that could nominate any path on disk would be
    // a worse problem than the one this solves. The target must sit inside a
    // .jetrix workspace, and the resolved path must still be inside it after
    // normalisation, which is what stops `../` climbing out.
    let destDir = ROOT;
    if (payload.dir) {
      const want = path.resolve(String(payload.dir));
      const parts = want.split(path.sep);
      const idx = parts.lastIndexOf(".jetrix");
      if (idx === -1) {
        return send(res, 400, JSON.stringify({
          ok: false,
          error: `Refused folder "${payload.dir}" \u2014 not inside a .jetrix workspace.`,
        }), MIME[".json"], req);
      }
      const workspace = parts.slice(0, idx + 1).join(path.sep);
      if (want !== workspace && !want.startsWith(workspace + path.sep)) {
        return send(res, 400, JSON.stringify({
          ok: false, error: "Refused folder \u2014 path escapes the workspace.",
        }), MIME[".json"], req);
      }
      if (!fs.existsSync(want) || !fs.statSync(want).isDirectory()) {
        return send(res, 400, JSON.stringify({
          ok: false, error: `Refused folder "${payload.dir}" \u2014 no such directory.`,
        }), MIME[".json"], req);
      }
      destDir = want;
    }

    if (!SAFE_NAME.test(name)) {
      return send(
        res,
        400,
        JSON.stringify({ ok: false, error: `Refused filename "${name}" — expected a plain *.md basename.` }),
        MIME[".json"],
        req
      );
    }

    const dest = path.join(destDir, name);
    // Belt and braces: SAFE_NAME already forbids separators, but never trust one check.
    if (path.dirname(path.resolve(dest)) !== destDir) {
      return send(res, 400, JSON.stringify({ ok: false, error: "Refused: path escapes the target folder." }), MIME[".json"], req);
    }

    try {
      fs.writeFileSync(dest, content, "utf8");
    } catch (err) {
      return send(res, 500, JSON.stringify({ ok: false, error: String(err.message || err) }), MIME[".json"], req);
    }

    // Show the workspace-relative path when there is one; a "../../.." chain
    // is worse than the absolute path for someone trying to find the file.
    const rel = path.relative(process.cwd(), dest).split(path.sep).join("/");
    const shown = rel.startsWith("..") ? dest : rel;
    console.log(`  saved  ${shown}`);
    send(res, 200, JSON.stringify({ ok: true, path: shown, absolute: dest }), MIME[".json"], req);
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");

  // Preflight for the cross-port save below.
  if (req.method === "OPTIONS") {
    res.writeHead(204, corsHeaders(req));
    return res.end();
  }

  if (req.method === "POST" && url.pathname === "/save") return handleSave(req, res);

  // Lets a later run recognise an instance of THIS script already serving THIS
  // folder, instead of assuming a busy port is someone else's and starting a
  // duplicate beside it.
  if (url.pathname === "/__whoami") {
    return send(res, 200, JSON.stringify({ app: "serve-review", root: ROOT }),
                "application/json; charset=utf-8", req);
  }

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

// Is one of our own servers already serving this exact folder? Ask each port
// in range who it is. Anything that is not this script -- or is this script on
// a different folder -- is simply skipped.
function whoami(port) {
  return new Promise((resolve) => {
    const req = http.get(
      { host: "127.0.0.1", port, path: "/__whoami", timeout: 300 },
      (res) => {
        let b = "";
        res.on("data", (d) => (b += d));
        res.on("end", () => {
          try {
            const j = JSON.parse(b);
            resolve(j && j.app === "serve-review" ? j.root : null);
          } catch { resolve(null); }
        });
      }
    );
    req.on("timeout", () => { req.destroy(); resolve(null); });
    req.on("error", () => resolve(null));
  });
}

async function findExisting() {
  for (let p = args.port; p <= args.portCeiling; p++) {
    if ((await whoami(p)) === ROOT) return p;
  }
  return null;
}

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

findExisting().then((existing) => {
  if (existing !== null) {
    // Reuse it. Two servers over one folder is how a report ends up able to
    // save through only one of them, and the other page silently downloads.
    const url = `http://127.0.0.1:${existing}/`;
    const newest = newestReport();
    console.log(`\n  Serving  ${ROOT}   (already running \u2014 reusing it)`);
    console.log(`  Open     ${url}${newest ? "  \u2192 " + newest : ""}`);
    console.log(`  Save     writes straight into that folder \u2014 leave that one running\n`);
    console.log(`DELIVERY_OS_SERVE_READY ${url}`);
    return;
  }
  startListening();
});

function startListening() {
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
}
