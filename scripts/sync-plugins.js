#!/usr/bin/env node
/*
  sync-plugins.js — push the working tree into the installed plugin cache.

  Why this exists:

  The marketplace is registered as a `directory` source pointing at this repo,
  which makes it tempting to assume the repo IS the running plugin. It is not.
  Each plugin's installPath is

      ~/.claude/plugins/cache/techjays-delivery-os/<plugin>/<version>/

  so Claude Code SNAPSHOTS the directory at install time and loads from the
  snapshot. Editing a command here changes nothing in a live session until the
  snapshot is refreshed — which is how a command came to reference five files
  that existed in the repo and had never been installed, and halted a run.

  Two rules, both learned the hard way:

    Copy, never reinstall.  Deleting the cache loses the install; a reinstall
    rebuilds nothing. Copying is the thing that actually works.

    Every text file lands as LF.  CRLF in a command's frontmatter makes it fail
    to register SILENTLY — the command simply is not there, with no error. That
    is worse than a crash, so the conversion is not optional.

    node scripts/sync-plugins.js            # dry run — says what would change
    node scripts/sync-plugins.js --apply    # writes
*/

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const REPO = path.resolve(__dirname, "..");
const SRC = path.join(REPO, "plugins");
const CACHE = path.join(os.homedir(), ".claude", "plugins", "cache", "techjays-delivery-os");
const APPLY = process.argv.includes("--apply");

// repo folder -> installed plugin name (delivery-os-core ships as delivery-os)
const MAP = {
  "delivery-os-core": "delivery-os",
  ba: "ba", tl: "tl", dev: "dev", qa: "qa", doc: "doc", jetrix: "jetrix",
};
const SKIP = ["_to_delete", "node_modules", ".git"];
const TEXT = [".md", ".js", ".json", ".html", ".yml", ".yaml", ".txt"];

const isText = (f) => TEXT.includes(path.extname(f).toLowerCase());

function tree(root) {
  const out = new Map();
  if (!fs.existsSync(root)) return out;
  (function walk(dir) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (SKIP.some((k) => p.includes(k))) continue;
      // statSync, not the dirent: several plugin folders here are symlinks,
      // and a dirent reports a symlinked directory as "not a directory".
      let st;
      try { st = fs.statSync(p); } catch { continue; }
      if (st.isDirectory()) walk(p);
      else out.set(path.relative(root, p).split(path.sep).join("/"), p);
    }
  })(root);
  return out;
}

if (!fs.existsSync(CACHE)) {
  console.error(`\nNo installed plugin cache at:\n  ${CACHE}\n\nInstall the plugins once from the marketplace, then re-run this.\n`);
  process.exit(1);
}

let nNew = 0, nUpd = 0, nSame = 0;
const changes = [];

for (const [repoName, instName] of Object.entries(MAP)) {
  const srcRoot = path.join(SRC, repoName);
  const base = path.join(CACHE, instName);
  if (!fs.existsSync(srcRoot)) continue;
  if (!fs.existsSync(base)) {
    console.log(`  !! ${instName} is not installed — skipping`);
    continue;
  }
  const versions = fs.readdirSync(base).filter((d) => fs.statSync(path.join(base, d)).isDirectory());
  if (!versions.length) { console.log(`  !! ${instName} has no version folder`); continue; }
  const dstRoot = path.join(base, versions.sort().pop());

  const S = tree(srcRoot), D = tree(dstRoot);

  for (const [relp, srcPath] of S) {
    const dstPath = path.join(dstRoot, relp.split("/").join(path.sep));
    const exists = D.has(relp);
    let same = false, body = null;

    if (isText(srcPath)) {
      body = fs.readFileSync(srcPath, "utf8").replace(/\r\n/g, "\n");
      if (exists) same = fs.readFileSync(dstPath, "utf8").replace(/\r\n/g, "\n") === body;
    } else if (exists) {
      same = fs.statSync(srcPath).size === fs.statSync(dstPath).size &&
             Buffer.compare(fs.readFileSync(srcPath), fs.readFileSync(dstPath)) === 0;
    }

    if (same) { nSame++; continue; }
    exists ? nUpd++ : nNew++;
    changes.push((exists ? "~ " : "+ ") + instName + "/" + relp);
    if (!APPLY) continue;

    fs.mkdirSync(path.dirname(dstPath), { recursive: true });
    if (body !== null) fs.writeFileSync(dstPath, body, { encoding: "utf8" });
    else fs.copyFileSync(srcPath, dstPath);
  }

  // A command removed from the repo but left in the cache stays registered and
  // stays runnable — strictly worse than one that is missing.
  for (const relp of D.keys()) {
    if (S.has(relp)) continue;
    changes.push("- " + instName + "/" + relp);
    if (APPLY) fs.rmSync(path.join(dstRoot, relp.split("/").join(path.sep)), { force: true });
  }
}

const removed = changes.filter((c) => c.startsWith("- ")).length;
console.log(`\n${APPLY ? "APPLIED" : "DRY RUN"} — ${nNew} new, ${nUpd} updated, ${removed} removed, ${nSame} unchanged`);
for (const c of changes.slice(0, 25)) console.log("   " + c);
if (changes.length > 25) console.log(`   … and ${changes.length - 25} more`);

if (!APPLY && changes.length) console.log(`\nrun with --apply to write\n`);
else if (APPLY) console.log(`\nRestart Claude Code for the changes to load.\n`);
else console.log(`\nthe installed plugin already matches this repo\n`);
