#!/usr/bin/env node
/*
  lint-plugins.js — refuse a commit when two files disagree.

  The plugin set is ~130 markdown files stating the same rules in several
  places: a command says it, a skill says it, a schema defines it, an agent
  description repeats it. Change one and the others silently keep saying the
  old thing, which is how a bug gets announced as fixed while still live.

  Nothing was checking that they agree except a person reading them. This is
  that check.

  Six checks, each one earned by a real defect:

    paths     a cited file does not exist     (TL wrote tl/ while the tree said tl-reviews/)
    refs      a §N points at no such section  (53 broke when /jetrix:init renumbered)
    struct    fences or frontmatter broken    (a sweep destroyed every fence in 136 files)
    schema    one doc_type, two shapes        (gates said per-repo in prose, flat in the schema)
    writers   two files both claim to write X (the scaffold spec lived in three places)
    blocks    a required block nobody writes  (Stage 4 demanded a field Stage 2 stopped writing)

  Exit 1 on any ERROR. WARN never fails the build — the heuristic checks
  (writers, blocks) report for a human to judge.

    node scripts/lint-plugins.js [--warnings] [--json]
*/

"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "plugins");
const SHOW_WARN = process.argv.includes("--warnings");
const AS_JSON = process.argv.includes("--json");

// Files whose job is to record what was REMOVED keep old names on purpose.
const HISTORY = [
  "delivery-os-conventions/SKILL.md",   // the changelog
  "references/init/migrate.md",         // describes the old layout it migrates from
  "dev-context-templates.md",           // "what these replaced" table
  "feature-file-templates.md",          // "files that no longer exist"
];
const SKIP_DIR = ["_to_delete", "node_modules"];

const problems = [];
const add = (level, check, file, line, msg, detail) =>
  problems.push({ level, check, file, line, msg, detail });

// ---------------------------------------------------------------- collect
const seen = new Set();
function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    // statSync, not dirent.isDirectory(): a symlinked directory reports
    // isDirectory() === false, and 36 paths here are symlinks including whole
    // skill folders. Walking by dirent skipped 41 files.
    let st;
    try { st = fs.statSync(p); } catch (err) { continue; }
    if (st.isDirectory()) {
      if (SKIP_DIR.some((k) => p.includes(k))) continue;
      let real;
      try { real = fs.realpathSync(p); } catch (err) { real = p; }
      if (seen.has(real)) continue;   // a symlink loop would never terminate
      seen.add(real);
      walk(p, out);
    } else if (/\.(md|js|html)$/.test(e.name)) {
      out.push(p);
    }
  }
  return out;
}

const files = walk(SRC);
const rel = (p) => path.relative(ROOT, p).split(path.sep).join("/");
const onDisk = new Set(files.map(rel));
const md = files.filter((f) => f.endsWith(".md"));
const text = new Map(files.map((f) => [rel(f), fs.readFileSync(f, "utf8").replace(/\r\n/g, "\n")]));
const isHistory = (f) => HISTORY.some((h) => f.includes(h));

// ---------------------------------------------------------- 1. paths exist
// A backticked `plugins/.../x.md` is a claim that the file is there.
for (const f of md.map(rel)) {
  const lines = text.get(f).split("\n");
  lines.forEach((l, i) => {
    for (const m of l.matchAll(/`(plugins\/[A-Za-z0-9_./&-]+\.(?:md|js|html))`/g)) {
      const t = m[1];
      if (t.includes("<") || t.includes("*")) continue;
      if (!onDisk.has(t)) add("ERROR", "paths", f, i + 1, "cited file does not exist", t);
    }
  });
}

// ------------------------------------------- 2. cross-file section refs
// § is overloaded here: a section of this file, a section of another file, a
// Stage number, a section of the user's scope document. Only one of those is
// mechanically checkable -- "<file>.md §N" -- and it is the one that actually
// broke: renumbering /jetrix:init orphaned 53 refs in other files.
const WORKSPACE_ARTIFACT = new Set([
  "implementation.md", "status.md", "analysis.md", "findings.md", "pr-summary.md",
  "description.md", "discussion.md", "scope.md", "scope.html", "feature.md",
  "ledger.md", "sources.md", "quality-gates.md", "plan-blockers.md",
  "acceptance-criteria.md", "business-rules.md", "nfrs.md", "test-scenarios.md",
  "dependencies.md", "connection-map.md", "decision-log.md", "coding-standards.md",
]);
const sectionsOf = new Map();
for (const f of md.map(rel)) {
  const set = new Set();
  for (const m of text.get(f).matchAll(/^#{1,4}\s*(\d+(?:\.\d+)*[a-z]?)(?=[.)\s])/gm)) set.add(m[1]);
  sectionsOf.set(f, set);
}
const byName = new Map();
for (const f of md.map(rel)) {
  const base = f.split("/").pop();
  if (!byName.has(base)) byName.set(base, []);
  byName.get(base).push(f);
}
for (const f of md.map(rel)) {
  text.get(f).split("\n").forEach((l, i) => {
    for (const m of l.matchAll(/`?([A-Za-z0-9_./-]+\.md)`?\s*§\s*(\d+(?:\.\d+)*[a-z]?)/g)) {
      const base = m[1].split("/").pop();
      const want = m[2];
      // Files the SYSTEM generates in a workspace, not files in this repo.
      // `implementation.md §1` means section 1 of the one /dev:plan writes.
      if (WORKSPACE_ARTIFACT.has(base)) continue;
      const cands = byName.get(base);
      if (!cands || cands.length !== 1) continue;      // ambiguous or unknown: not our business
      const have = sectionsOf.get(cands[0]);
      if (!have || !have.size) continue;               // that file has no numbered sections
      if (!have.has(want)) {
        add("ERROR", "refs", f, i + 1,
            `§${want} does not exist in ${base}`,
            `${base} has: ${[...have].slice(0, 14).join(" ")}`);
      }
    }
  });
}

// ------------------------------------------------- 3. structural validity
for (const f of md.map(rel)) {
  const lines = text.get(f).split("\n");
  const fences = lines.filter((l) => l.startsWith("```")).length;
  if (fences % 2) add("ERROR", "struct", f, 0, "odd number of code fences — a block is never closed", `${fences} fences`);

  lines.forEach((l, i) => {
    if (/^``(?!`)/.test(l)) add("ERROR", "struct", f, i + 1, "line starts with two backticks — a destroyed fence", l.slice(0, 40));
  });

  if (lines[0] === "---") {
    const end = lines.indexOf("---", 1);
    if (end < 0) add("ERROR", "struct", f, 1, "frontmatter is never closed", "");
    else for (let i = 1; i < end; i++) {
      const l = lines[i];
      if (l.trim() && !/^\s/.test(l) && !/^[A-Za-z0-9_-]+\s*:/.test(l)) {
        add("ERROR", "struct", f, i + 1, "frontmatter line is not `key: value`", l.slice(0, 50));
      }
    }
  }
}

// ----------------------------------------------- 4. one shape per doc_type
// Two files defining `doc_type: X` with different top-level key sets means a
// writer following one produces a file the other's reader cannot parse.
const shapes = new Map();
for (const f of md.map(rel)) {
  if (isHistory(f)) continue;
  for (const m of text.get(f).matchAll(/```ya?ml\n([\s\S]*?)```/g)) {
    const block = m[1];
    const dt = /^doc_type:\s*([a-z0-9-]+)/m.exec(block);
    if (!dt) continue;
    const keys = [...block.matchAll(/^([a-z0-9_]+)\s*:/gm)].map((k) => k[1]).sort();
    if (!shapes.has(dt[1])) shapes.set(dt[1], []);
    shapes.get(dt[1]).push({ f, keys });
  }
}
for (const [dt, defs] of shapes) {
  if (defs.length < 2) continue;
  // A SUPERSET is a legitimate variant -- a non-feature carries task_type, a
  // feature does not. A genuine disagreement is two shapes that each have a
  // key the other lacks: a writer following one produces a file the other's
  // reader cannot parse.
  let conflict = false;
  for (let i = 0; i < defs.length && !conflict; i++) {
    for (let j = i + 1; j < defs.length && !conflict; j++) {
      const A = new Set(defs[i].keys), B = new Set(defs[j].keys);
      const aOnly = [...A].filter((k) => !B.has(k));
      const bOnly = [...B].filter((k) => !A.has(k));
      if (aOnly.length && bOnly.length) conflict = true;
    }
  }
  if (conflict) {
    add("ERROR", "schema", defs[0].f, 0,
        `doc_type \`${dt}\` is defined with different shapes in ${defs.length} places`,
        defs.map((d) => `${d.f.split("/").slice(-2).join("/")} [${d.keys.join(" ")}]`).join("  |  "));
  }
}

// ------------------------------------------------- 5. one writer per file
// Heuristic, so WARN. Two places both instructing "write X" is how a spec
// comes to exist in three copies that drift.
const writers = new Map();
const WRITE = /\b(?:writes?|authors?|creates?|emits?)\s+`([a-z0-9_<>/.-]+\.md)`/gi;
for (const f of md.map(rel)) {
  if (isHistory(f)) continue;
  for (const m of text.get(f).matchAll(WRITE)) {
    const t = m[1];
    if (!writers.has(t)) writers.set(t, new Set());
    writers.get(t).add(f);
  }
}
for (const [t, set] of writers) {
  if (set.size > 2) {
    add("WARN", "writers", [...set][0], 0,
        `\`${t}\` is claimed as written by ${set.size} files`,
        [...set].map((x) => x.split("/").slice(-2).join("/")).join("  |  "));
  }
}

// --------------------------------------- 6. required blocks have a producer
// "non-empty `foo`, `bar` blocks" as a precondition means something must write
// them. A required block nobody writes halts every run that reaches it.
const REQUIRE = /non-empty\s+((?:`[a-z0-9_]+`(?:,?\s*(?:and\s*)?)?)+)\s+blocks?/gi;
for (const f of md.map(rel)) {
  for (const m of text.get(f).matchAll(REQUIRE)) {
    for (const b of m[1].matchAll(/`([a-z0-9_]+)`/g)) {
      const name = b[1];
      const written = md.map(rel).some((g) =>
        g !== f && new RegExp("^##+\\s*" + name + "\\b", "m").test(text.get(g)));
      if (!written) {
        add("WARN", "blocks", f, 0, `requires block \`${name}\` but no file writes a \`## ${name}\` section`, "");
      }
    }
  }
}

// ------------------------------- 7. next steps naming a command that is gone
// Conventions 1.f: a next-step block may only name a command that exists.
// DERIVED from plugins/*/commands/*.md rather than hardcoded -- the previous
// version watched one literal that had already stopped existing, so it
// reported green regardless of what the corpus said.
const REAL = new Set(
  md.map(rel)
    .map((f) => /^plugins\/([^/]+)\/commands\/([^/]+)\.md$/.exec(f))
    .filter(Boolean)
    .map((m) => "/" + m[1] + ":" + m[2])
);
const CMD_RE = /\/(?:ba|tl|qa|dev|doc|jetrix|delivery-os-core):[a-z][a-z-]*/g;
const gone = (l) => (l.match(CMD_RE) || []).filter((c) => !REAL.has(c));
// a line ABOUT a retired command is documentation, not an instruction
const ABOUT = /retired|replaced|was folded|no longer|used to|formerly|never print|auto-run|invoke|slash command/i;

for (const f of md.map(rel)) {
  if (f.includes("delivery-os-conventions")) continue;   // where the rule is stated
  if (/_readme\.md$/.test(f)) continue;                  // documents what was retired
  const L = text.get(f).split("\n");
  let inBlock = false, blockStart = 0, block = [];

  const flush = () => {
    if (block.some((l) => /^\s*Next\b/.test(l))) {       // only a next-step block
      block.forEach((l, i) => {
        if (ABOUT.test(l)) return;
        for (const cmd of gone(l)) {
          add("ERROR", "internal", f, blockStart + i + 1,
              cmd + " is offered as a next step \u2014 no such command (conventions \u00a71.f)",
              l.trim().slice(0, 90));
        }
      });
    }
    block = [];
  };

  L.forEach((l, i) => {
    if (l.startsWith("```")) {
      if (inBlock) { flush(); inBlock = false; } else { inBlock = true; blockStart = i + 1; }
      return;
    }
    if (inBlock) block.push(l);
  });

  // and as a prose instruction: "then run /tl:plan"
  L.forEach((l, i) => {
    if (ABOUT.test(l)) return;
    for (const cmd of gone(l)) {
      const before = l.slice(0, l.indexOf(cmd));
      if (/\b(then|re-run|next step)\b[^.]{0,24}$|\brun \`?$/i.test(before)) {
        add("ERROR", "internal", f, i + 1,
            cmd + " is instructed as a step \u2014 no such command (conventions \u00a71.f)",
            l.trim().slice(0, 90));
      }
    }
  });
}


// ------------------------------------ 8. task status outside the vocabulary
// conventions 5: status: holds MC's seven values, locally and on every
// tracker. The eleven old local names are what split the system in two, and
// status_map was written for five of them -- which is how a Jira workspace
// lost a task mid-build. Retired names must not come back.
const RETIRED = [
  "PLANNED", "READY_FOR_DEV", "IN_PLANNING", "BLOCKED_ON_PLAN",
  "IN_DEVELOPMENT", "TESTING", "IN_PROGRESS", "REVIEW", "MERGE_CONFLICT",
];
const RETIRED_RE = /\b(PLANNED|READY_FOR_DEV|IN_PLANNING|BLOCKED_ON_PLAN|IN_DEVELOPMENT|TESTING|IN_PROGRESS|REVIEW|MERGE_CONFLICT)\b/g;
// the same words, legitimately, for something that is not a task status:
//   stage-7.status: DONE | final_status: COMPLETE | a REVIEW heading | QA verdicts
const NOT_A_STATUS =
  /\.status:|final_status|stage-\d|\bQAF?-|severity|verdict|## |# |\|\s*Tier|coverage/i;

for (const f of md.map(rel)) {
  if (f.includes("delivery-os-conventions")) continue;   // defines the vocabulary
  const L = text.get(f).split("\n");
  L.forEach((l, i) => {
    if (NOT_A_STATUS.test(l)) return;
    const hit = l.match(RETIRED_RE);
    if (!hit) return;
    add("ERROR", "status", f, i + 1,
        "retired task status " + [...new Set(hit)].join(", ") +
          " \u2014 use the shared vocabulary (conventions \u00a75)",
        l.trim().slice(0, 90));
  });
}


// ------------------------------ 9. injection tokens must exist in an asset
// A rename sweep turned __REVIEW_DATA__ into __devReview_DATA__ across nine
// files while the HTML kept the real token, so every report build would have
// injected into nothing. No other check could see it: the replacement was a
// valid word in the vocabulary that sweep was enforcing. This one ignores
// meaning and just compares the two sets.
const TOKEN = /__[A-Za-z][A-Za-z0-9_]*__/g;
const IGNORE = new Set(["__pycache__", "__tests__", "__init__", "__main__", "__ENT__"]);

const assetTokens = new Set();
for (const f of files.map(rel)) {
  if (!/\/assets\/.*\.html$/.test(f)) continue;
  for (const t of (text.get(f) || "").match(TOKEN) || []) assetTokens.add(t);
}

if (assetTokens.size) {
  for (const f of md.map(rel)) {
    (text.get(f) || "").split("\n").forEach((l, i) => {
      for (const t of l.match(TOKEN) || []) {
        if (IGNORE.has(t) || assetTokens.has(t)) continue;
        add("ERROR", "tokens", f, i + 1,
            t + " is named as an injection token but no assets/*.html contains it",
            l.trim().slice(0, 90));
      }
    });
  }
}


// --------------------------------- 10. a blank target means the set, not one
// The bug this exists for: /dev:plan's blank form selected "the next feature at
// readyForDev" -- its own OUTPUT value -- so it hunted for work it had already
// done and skipped every todo feature. Same shape in build and commit: "next",
// "first", "most recent" all quietly turn a batch command into a single-item
// one, and the user who typed no target gets one task planned out of nineteen.
// Scope belongs to the invocation; nothing downstream narrows it.
const BLANK_LINE = /blank\s*(=|:|\bfor\b)|unless blank/i;
const NARROWS = /\b(next|first|most recent(ly)?|one at a time)\b/i;
const WHOLE_SET = /\b(every|all|whole|entire|each)\b/i;
for (const f of md.map(rel).filter((x) => /^plugins\/[^/]+\/commands\/[^/]+\.md$/.test(x))) {
  (text.get(f) || "").split("\n").forEach((l, i) => {
    if (!BLANK_LINE.test(l)) return;
    // Judge the DECLARATION, not the rationale that follows it. The first cut of
    // this check tested the whole line, so a line that said "pick next feature"
    // and then explained the rule using the word "whole" vetoed its own hit --
    // it could not fail, which is the one thing a check must be able to do.
    const decl = l.split(/\u2014|\. |\(/)[0];
    if (!NARROWS.test(decl) || WHOLE_SET.test(decl)) return;
    add("ERROR", "scope", f, i + 1,
        "a blank target is described as a single item; it must resolve to every task the gate admits",
        l.trim().slice(0, 110));
  });
}

// ---------------------------------------------------------------- report
const errors = problems.filter((p) => p.level === "ERROR");
const warns = problems.filter((p) => p.level === "WARN");

if (AS_JSON) {
  console.log(JSON.stringify({ errors, warns }, null, 2));
  process.exit(errors.length ? 1 : 0);
}

const byCheck = {};
for (const p of problems) (byCheck[p.check] ||= []).push(p);

console.log(`\nlint-plugins — ${md.length} markdown files, ${files.length} total\n`);
for (const check of ["paths", "refs", "struct", "schema", "internal", "status", "tokens", "scope", "writers", "blocks"]) {
  const rows = (byCheck[check] || []).filter((p) => p.level === "ERROR" || SHOW_WARN);
  const nE = (byCheck[check] || []).filter((p) => p.level === "ERROR").length;
  const nW = (byCheck[check] || []).filter((p) => p.level === "WARN").length;
  const tag = nE ? "FAIL" : nW ? "warn" : " ok ";
  console.log(`  [${tag}] ${check.padEnd(8)} ${nE} error${nE === 1 ? "" : "s"}` + (nW ? `, ${nW} warning${nW === 1 ? "" : "s"}` : ""));
  for (const p of rows.slice(0, 12)) {
    console.log(`         ${p.file}${p.line ? ":" + p.line : ""}`);
    console.log(`           ${p.msg}`);
    if (p.detail) console.log(`           ${p.detail.slice(0, 150)}`);
  }
  if (rows.length > 12) console.log(`         … and ${rows.length - 12} more`);
}

console.log(`\n${errors.length} error(s), ${warns.length} warning(s)`);
if (!SHOW_WARN && warns.length) console.log(`run with --warnings to see them`);
console.log();
process.exit(errors.length ? 1 : 0);
