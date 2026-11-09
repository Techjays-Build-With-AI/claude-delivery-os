#!/usr/bin/env node
/**
 * Delivery OS guard hook.
 *
 * Registered on PreToolUse (see hooks/hooks.json). Claude Code streams a JSON
 * event payload on stdin; this script decides whether the tool call may run.
 *
 * It enforces three invariants that the plugin previously only stated in prose:
 *
 *   1. /dev:build never commits      — git commit is refused while a build session is live
 *   2. No push before the gates pass — git push is refused while a commit session has not passed them
 *   3. A fix loop may not edit tests — writes to the loop's test paths are refused
 *
 * The contract it reads is `.jetrix/cache/session.json`; its schema lives in
 * commands/references/common/session-marker.md.
 *
 * Design rules:
 *   - FAIL OPEN. No marker, unreadable marker, odd payload, unexpected error:
 *     exit 0 and say nothing. A developer with no Delivery OS session running
 *     must never notice this hook exists. Enforcement that breaks a normal
 *     `git commit` gets uninstalled within a day, and then enforces nothing.
 *   - Exit 2 ONLY for an explicit, matched refusal, with a message on stderr
 *     that names what blocked it, why, and the command that proceeds.
 *   - Never write to stdout. Exit 2 messages go to stderr.
 */

'use strict';

const fs = require('fs');
const path = require('path');

// A row older than this stops restricting anything. See session-marker.md §4.
const STALE_AFTER_MS = 4 * 60 * 60 * 1000;

// How far up from the tool call's cwd to look for .jetrix/. A product repo
// normally sits one level under the workspace; 4 is slack for monorepos.
const MAX_WALK_UP = 4;

let raw = '';
process.stdin.on('data', (c) => {
  raw += c;
  if (raw.length > 2 * 1024 * 1024) raw = raw.slice(0, 2 * 1024 * 1024);
});
process.stdin.on('end', () => {
  try {
    main();
  } catch (_) {
    // Any unexpected failure allows the call. See the fail-open rule above.
  }
  process.exit(0);
});
// Some environments never emit 'end' on a closed stdin.
setTimeout(() => process.exit(0), 5000).unref();

function main() {
  if (!raw.trim()) return;

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (_) {
    return; // malformed payload — allow
  }
  if (!payload || typeof payload !== 'object') return;

  const toolName = payload.tool_name || payload.toolName || '';
  const toolInput = payload.tool_input || payload.toolInput || {};
  const cwd = payload.cwd || process.cwd();

  // What is this call trying to do, and to which path?
  const op = classify(toolName, toolInput, cwd);
  if (!op) return; // not an operation we guard — allow

  const workspace = findWorkspace(op.target || cwd);
  if (!workspace) return; // not inside a bound workspace — allow

  const markerFile = path.join(workspace, '.jetrix', 'cache', 'session.json');
  const sessions = readSessions(markerFile);
  if (!sessions.length) return;

  const now = Date.now();
  const live = [];
  const stale = [];
  for (const s of sessions) {
    if (!s || typeof s !== 'object' || !s.repo) continue;
    if (!covers(s.repo, op.target || cwd)) continue;
    (isStale(s, now) ? stale : live).push(s);
  }

  const blocker = live.find((s) => forbids(s, op));
  if (!blocker) {
    // Nothing live forbids this. Mention a stale row once so a crashed session
    // is visible rather than mysterious, then allow.
    if (stale.length) {
      process.stderr.write(
        'Delivery OS: ignoring a stale ' + stale[0].kind + ' session from ' +
        shortTime(stale[0].started_at) + ' — /dev:' + stale[0].kind +
        ' --clear-locks to remove it.\n'
      );
    }
    return;
  }

  if (process.env.DELIVERY_OS_HOOK_BYPASS === '1') {
    logBypass(workspace, op, blocker);
    process.stderr.write(
      'Delivery OS: hook bypassed (DELIVERY_OS_HOOK_BYPASS=1). Logged to ' +
      '.jetrix/cache/bypass.log and reported in the run summary.\n'
    );
    return;
  }

  process.stderr.write(refusal(op, blocker));
  process.exit(2);
}

/**
 * Decide what this tool call is, and the path it acts on.
 * Returns null for anything we do not guard.
 */
function classify(toolName, input, cwd) {
  if (toolName === 'Bash') {
    const cmd = String(input.command || '');
    if (!/\bgit\b/.test(cmd)) return null;

    // `git -C <path> ...` relocates the repo the command acts on.
    const dirMatch = cmd.match(/\bgit\s+(?:--git-dir=\S+\s+|--work-tree=\S+\s+)*-C\s+("[^"]+"|'[^']+'|\S+)/);
    const target = dirMatch ? resolveMaybeRelative(unquote(dirMatch[1]), cwd) : cwd;

    // Match the subcommand, skipping global flags and any -C <path>.
    const sub = cmd.match(/\bgit\s+(?:(?:-[cC]\s+\S+|--\S+)\s+)*([a-z-]+)/);
    const verb = sub ? sub[1] : '';

    if (verb === 'commit') return { kind: 'git_commit', label: 'git commit', target };
    if (verb === 'push') return { kind: 'git_push', label: 'git push', target };
    return null;
  }

  if (toolName === 'Edit' || toolName === 'Write' || toolName === 'NotebookEdit') {
    const f = input.file_path || input.filePath || input.notebook_path;
    if (!f) return null;
    return { kind: 'write', label: toolName, target: resolveMaybeRelative(String(f), cwd) };
  }

  return null;
}

function forbids(session, op) {
  const deny = session.deny || {};
  if (op.kind === 'git_commit') return deny.git_commit === true;
  if (op.kind === 'git_push') {
    // A commit session stops forbidding the push once its gates have passed.
    return deny.git_push === true && session.gates_passed !== true;
  }
  if (op.kind === 'write') {
    const paths = Array.isArray(deny.write_paths) ? deny.write_paths : [];
    if (!paths.length) return false;
    const rel = relFrom(session.repo, op.target);
    if (rel === null) return false;
    return paths.some((p) => {
      const d = normRel(p);
      if (!d) return false;
      return rel === d || rel.startsWith(d + '/');
    });
  }
  return false;
}

function refusal(op, s) {
  const where = s.task ? s.task + ' in ' + path.basename(s.repo) : path.basename(s.repo);
  const when = shortTime(s.started_at);
  const L = [];
  L.push('Blocked: ' + op.label + '\n\n');

  if (op.kind === 'git_commit') {
    L.push('  A /dev:build session is live on ' + where + ' (started ' + when + ').\n');
    L.push('  /dev:build never commits — /dev:commit gathers the working tree once\n');
    L.push('  its gates pass. That boundary is what keeps unreviewed code off the branch.\n\n');
    L.push('  If the build is finished:   /dev:commit ' + (s.task || '') + '\n');
    L.push('  If it crashed:              /dev:build --clear-locks\n');
  } else if (op.kind === 'git_push') {
    L.push('  A /dev:commit session is live on ' + where + ' (started ' + when + ')\n');
    L.push('  and its gates have not passed. Findings are still open or undispositioned.\n\n');
    L.push('  Let it finish, or:          /dev:commit --resume ' + (s.task || '') + '\n');
    L.push('  If it crashed:              /dev:commit --clear-locks\n');
  } else {
    L.push('  A fix loop is running on ' + where + ' and this path is one of its tests.\n');
    L.push('  A failing test is fixed in the code, never in the test.\n\n');
    L.push('  If the test itself is wrong, say so — that is an escalation, not an edit.\n');
    L.push('  If the loop crashed:        /dev:commit --clear-locks\n');
  }

  L.push('  If you need this anyway:    DELIVERY_OS_HOOK_BYPASS=1 <your command>\n');
  L.push('                              (logged, and shown in the run summary)\n');
  return L.join('');
}

function readSessions(file) {
  try {
    const j = JSON.parse(fs.readFileSync(file, 'utf8'));
    return Array.isArray(j && j.sessions) ? j.sessions : [];
  } catch (_) {
    return []; // missing or corrupt — allow everything
  }
}

function isStale(s, now) {
  const t = Date.parse(s.started_at || '');
  if (!t) return true; // no usable timestamp — treat as stale, never as live
  return now - t > STALE_AFTER_MS;
}

/** Does `repo` contain `target` (or equal it)? */
function covers(repo, target) {
  const r = norm(repo);
  const t = norm(target);
  return t === r || t.startsWith(r.replace(/\/*$/, '/'));
}

/** `target` relative to `repo`, or null when outside it. */
function relFrom(repo, target) {
  const r = norm(repo).replace(/\/*$/, '/');
  const t = norm(target);
  if (!t.startsWith(r)) return null;
  return t.slice(r.length);
}

function findWorkspace(start) {
  let dir = path.resolve(start);
  // A file path resolves to its directory.
  try {
    if (fs.existsSync(dir) && fs.statSync(dir).isFile()) dir = path.dirname(dir);
  } catch (_) {
    dir = path.dirname(dir);
  }
  for (let i = 0; i <= MAX_WALK_UP; i++) {
    if (fs.existsSync(path.join(dir, '.jetrix'))) return dir;
    const up = path.dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  return null;
}

function logBypass(workspace, op, s) {
  try {
    const line = [
      new Date().toISOString(),
      op.label,
      s.id || s.kind,
      s.repo,
    ].join('\t') + '\n';
    fs.appendFileSync(path.join(workspace, '.jetrix', 'cache', 'bypass.log'), line);
  } catch (_) {
    // Logging must never turn an allowed call into a failed one.
  }
}

function norm(p) {
  return path.resolve(String(p)).replace(/\\/g, '/').replace(/\/+$/, '');
}

/**
 * Normalize a REPO-RELATIVE path. Unlike norm() this must not resolve against
 * the process cwd — `deny.write_paths` holds entries like `tests/`, and
 * resolving those would produce an absolute path somewhere else entirely.
 */
function normRel(p) {
  return String(p).replace(/\\/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');
}

function resolveMaybeRelative(p, cwd) {
  return path.isAbsolute(p) ? p : path.resolve(cwd, p);
}

function unquote(s) {
  return String(s).replace(/^["']|["']$/g, '');
}

function shortTime(iso) {
  const t = Date.parse(iso || '');
  if (!t) return 'an unknown time';
  const d = new Date(t);
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
}
