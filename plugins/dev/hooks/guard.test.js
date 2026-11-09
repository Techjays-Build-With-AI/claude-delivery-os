// Standalone test for guard.js. Builds a throwaway workspace, drives the hook
// with crafted payloads, asserts exit codes. No real workspace is touched.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const GUARD = process.argv[2] || path.join(__dirname, 'guard.js');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'guard-test-'));
const repo = path.join(root, 'Inhouse-server');
const other = path.join(root, 'Inhouse-client');
fs.mkdirSync(path.join(repo, 'tests'), { recursive: true });
fs.mkdirSync(other, { recursive: true });
fs.mkdirSync(path.join(root, '.jetrix', 'cache'), { recursive: true });

const marker = path.join(root, '.jetrix', 'cache', 'session.json');
const iso = (msAgo) => new Date(Date.now() - msAgo).toISOString();

function setMarker(obj) {
  if (obj === null) { try { fs.unlinkSync(marker); } catch (_) {} return; }
  fs.writeFileSync(marker, typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2));
}

function run(payload, env) {
  const r = spawnSync(process.execPath, [GUARD], {
    input: JSON.stringify(payload),
    encoding: 'utf8',
    env: Object.assign({}, process.env, env || {}),
  });
  return { code: r.status, err: (r.stderr || '').trim(), out: (r.stdout || '').trim() };
}

const bash = (command, cwd) => ({ tool_name: 'Bash', tool_input: { command }, cwd: cwd || repo });
const write = (file_path, cwd) => ({ tool_name: 'Edit', tool_input: { file_path }, cwd: cwd || repo });

const buildSession = {
  sessions: [{
    id: 'build-test-0001', kind: 'build', repo: repo.replace(/\\/g, '/'),
    task: 'Subtask-7', started_at: iso(60 * 1000),
    deny: { git_commit: true, git_push: true, write_paths: [] },
  }],
};

let pass = 0, fail = 0;
function check(name, got, want, extra) {
  const ok = got === want && (!extra || extra());
  console.log((ok ? '  PASS  ' : '  FAIL  ') + name + '   (exit ' + got + ', wanted ' + want + ')');
  ok ? pass++ : fail++;
}

console.log('\n-- fail-open cases (must all allow) --');
setMarker(null);
check('no marker + git commit', run(bash('git commit -m x')).code, 0);
check('no marker + git push', run(bash('git push')).code, 0);
check('no marker + Edit', run(write(path.join(repo, 'src/a.js'))).code, 0);

setMarker('{ this is not json');
check('corrupt marker + git commit', run(bash('git commit -m x')).code, 0);

setMarker({ sessions: [] });
check('empty sessions + git commit', run(bash('git commit -m x')).code, 0);

setMarker(buildSession);
check('live build + unrelated bash', run(bash('npm test')).code, 0);
check('live build + git status', run(bash('git status')).code, 0);
check('live build + git commit in OTHER repo', run(bash('git commit -m x', other)).code, 0);
check('outside any workspace', run(bash('git commit -m x', os.tmpdir())).code, 0);

console.log('\n-- refusals (must block) --');
check('live build + git commit', run(bash('git commit -m x')).code, 2);
check('live build + git commit -am', run(bash('git commit -am "x"')).code, 2);
check('live build + git -C <repo> commit', run(bash('git -C "' + repo + '" commit -m x', other)).code, 2);
check('live build + git push', run(bash('git push -u origin feat')).code, 2);

const r = run(bash('git commit -m x'));
check('refusal names the command that proceeds', /dev:commit/.test(r.err) ? 1 : 0, 1);
check('refusal names --clear-locks', /--clear-locks/.test(r.err) ? 1 : 0, 1);
check('refusal names the bypass', /DELIVERY_OS_HOOK_BYPASS/.test(r.err) ? 1 : 0, 1);

console.log('\n-- staleness --');
setMarker({ sessions: [Object.assign({}, buildSession.sessions[0], { started_at: iso(5 * 60 * 60 * 1000) })] });
const st = run(bash('git commit -m x'));
check('stale build + git commit allows', st.code, 0);
check('stale build says so', /stale/.test(st.err) ? 1 : 0, 1);

setMarker({ sessions: [Object.assign({}, buildSession.sessions[0], { started_at: 'not-a-date' })] });
check('unparseable timestamp allows', run(bash('git commit -m x')).code, 0);

console.log('\n-- commit session + gates --');
const commitSession = (gates) => ({
  sessions: [{
    id: 'commit-test-0001', kind: 'commit', repo: repo.replace(/\\/g, '/'),
    task: 'Subtask-7', started_at: iso(60 * 1000), gates_passed: gates,
    deny: { git_push: true, write_paths: [] },
  }],
});
setMarker(commitSession(false));
check('gates not passed + git push blocks', run(bash('git push')).code, 2);
check('gates not passed + git commit allows', run(bash('git commit -m x')).code, 0);
setMarker(commitSession(true));
check('gates passed + git push allows', run(bash('git push')).code, 0);

console.log('\n-- fix loop write paths --');
setMarker({
  sessions: [{
    id: 'commit-test-0002', kind: 'commit', repo: repo.replace(/\\/g, '/'),
    task: 'Subtask-7', started_at: iso(60 * 1000), gates_passed: false,
    deny: { git_push: true, write_paths: ['tests/'] },
  }],
});
check('Edit inside tests/ blocks', run(write(path.join(repo, 'tests', 'a.spec.js'))).code, 2);
check('Edit in src/ allows', run(write(path.join(repo, 'src', 'a.js'))).code, 0);
check('Edit in other repo allows', run(write(path.join(other, 'tests', 'a.spec.js'), other)).code, 0);

console.log('\n-- bypass --');
setMarker(buildSession);
const by = run(bash('git commit -m x'), { DELIVERY_OS_HOOK_BYPASS: '1' });
check('bypass allows', by.code, 0);
const logPath = path.join(root, '.jetrix', 'cache', 'bypass.log');
check('bypass is logged', fs.existsSync(logPath) ? 1 : 0, 1);

console.log('\n-- stdout discipline --');
check('never writes to stdout', run(bash('git commit -m x')).out === '' ? 1 : 0, 1);

console.log('\n' + pass + ' passed, ' + fail + ' failed\n');
try { fs.rmSync(root, { recursive: true, force: true }); } catch (_) {}
process.exit(fail ? 1 : 0);
