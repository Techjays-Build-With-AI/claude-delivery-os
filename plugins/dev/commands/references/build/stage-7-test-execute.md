## Stage 7 — Execute tests locally

**Purpose.** Actually RUN the tests. Not a plan-mode "would run" — the exact commands from `qa/quality-gates.md` Required table execute in the target repo, and their real exit codes drive the acceptance-map at Stage 8.

**Runs after Stages 5-6.** State: `IN_DEVELOPMENT → TESTING`. MC: `inProgress` (unchanged).

**On completion:** every Required gate has a real pass/fail result captured in `dev/implementation-log.md`. Failing gates route to Stage 8's repair loop.

---

### 7a. Preconditions

- `dev/build-run.md` `stage-5-6.status: DONE`
- `qa/quality-gates.md` `harness_status: Active` (verified in Stage 4)
- Target repo working tree contains the newly-written code + tests
- Package dependencies installed (either by `qa-greenfield-harness` in Stage 4 OR pre-existing)

Missing → halt.

---

### 7b. Read the Required gates

Parse the `Required gates` table from `qa/quality-gates.md`. For each row, capture:
- `qg_id` (QG-###)
- `check` name
- `command` — the exact shell command
- `threshold` — pass/fail criteria
- `layer` — advisory; used only for parent-alone tasks that touch multiple layers

---

### 7c. Execute each gate in order

Run each `command` in the target repo's directory. Capture stdout + stderr + exit code into a run block:

```bash
cd <target-repo-path>
<command>
```

**No parallel execution.** Gates run serially in the order listed. Reason: some gates depend on artifacts from previous ones (coverage reports need unit tests to have run first).

**Timeout per gate:** 20 minutes. If a gate exceeds it, kill the process, mark as `TIMEOUT`, treat as failure. Escalate rather than retry.

---

### 7d. Parse results per framework

Framework-native output shape varies. Parse using the framework detected by `dev-stack-adaptive-implementation`'s stack-detection:

| Framework | Pass signal | Fail signal | Test count |
|---|---|---|---|
| Vitest / Jest | `passed:` in summary; exit 0 | `failed:` in summary; exit ≠ 0 | `Tests:  N passed / M total` |
| pytest | `passed` in summary; exit 0 | `failed` / `errors`; exit ≠ 0 | `N passed`, `N failed` |
| Go test | `PASS` at end; exit 0 | `FAIL` at end; exit ≠ 0 | `ok  <pkg>  <time>` or `--- FAIL:` |
| .NET test | `Passed: N` / `Failed: N`; exit 0 or 1 | `Failed: N > 0` | Same |
| Maven / Gradle test | `Tests run: N, Failures: M` | `Failures: > 0`; exit ≠ 0 | Same |
| Playwright | `N passed` in `list` reporter; exit 0 | `N failed`; exit ≠ 0 | Same |
| flutter test | `+N` (passed), `-N` (failed); exit 0 or 1 | | Same |

Coverage gates parse the coverage summary output (percentage per line/function/branch/statement) against threshold.

---

### 7e. Record each result

Append to `dev/implementation-log.md` under a `test_runs:` section:

```yaml
test_runs:
  - qg_id:       QG-001
    check:       unit tests
    command:     pnpm test
    started_at:  2026-08-31T15:07:23Z
    finished_at: 2026-08-31T15:08:12Z
    exit_code:   0
    passed:      34
    failed:      0
    skipped:     0
    result:      PASS
    stdout_excerpt: |
      Test Files  6 passed (6)
       Tests  34 passed (34)
       Duration  49.32s (in thread 48.42s)
    ac_ids_covered: [AC-B1, AC-B2, AC-B3, BR-1, TS-U-1, TS-U-2, TS-U-3]      # from grep of test source

  - qg_id:       QG-002
    check:       coverage
    command:     pnpm test:coverage
    started_at:  2026-08-31T15:08:13Z
    finished_at: 2026-08-31T15:09:44Z
    exit_code:   0
    coverage:
      lines:      72.4
      functions:  81.0
      branches:   65.3
      statements: 72.4
    threshold:  60
    result:      PASS

  - qg_id:       QG-007
    check:       e2e
    command:     pnpm test:e2e
    started_at:  2026-08-31T15:09:45Z
    finished_at: 2026-08-31T15:12:33Z
    exit_code:   1
    passed:      3
    failed:      1
    result:      FAIL
    failed_tests:
      - tests/e2e/supplier-happy-path.spec.ts::submit valid form
    stderr_excerpt: |
      Error: expect(page.getByText(/created/i)).toBeVisible()
      Timeout of 5000ms exceeded.
```

---

### 7f. Failure handling

Any Required gate returning `result: FAIL` → jump to Stage 8's repair loop for that gate. Do NOT continue to remaining gates until the failing one is fixed.

Rationale: if the unit tests fail, running coverage after is wasted time (coverage would also fail, and the fix might change coverage anyway). Fix, re-run affected gates, then continue downstream.

**Exception — flakiness detection:** if a gate fails on first run, immediately re-run it once (single retry, in-process). If second run passes → mark `result: PASS_FLAKY_ONE_RETRY` and note it. Flaky gates are legit failures at Stage 8 but the pattern is worth surfacing.

---

### 7g. Missing test command

If a gate's command fails with "command not found" / "no such option" / equivalent:
- Do NOT try to install anything (that's Stage 4's job)
- Route back to Stage 4 with an escalation: `qa/quality-gates.md` has a command that doesn't work in this repo
- Halt Stage 7

This shouldn't happen if Stage 4's `qa-greenfield-harness` bootstrap succeeded — but if `qa/quality-gates.md` was hand-edited or partially installed, catch it here.

---

### 7h. Progress log format

Append to `dev/build-run.md`:

```yaml
stage-7:
  status: DONE                          # DONE | FAILED | BLOCKED
  started_at: 2026-08-31T15:07:22Z
  gates_run: 7
  gates_passed: 7
  gates_failed: 0
  gates_flaky: 0
  finished_at: 2026-08-31T15:12:41Z
```

`FAILED` if any gate ended in `FAIL` after Stage 8's repair loop is done and still couldn't fix.

---

### 7i. On `--resume`

If `--resume` finds `stage-7.status: DONE`, skip Stage 7 entirely. Rationale: even if code was hand-edited between runs (unlikely), running Stage 8 (validate) will pick up the change through its acceptance-map rebuild.

If `stage-7.status: FAILED` on the last recorded run, re-execute Stage 7 fully — the developer might have fixed the failing gates by hand.

---

### Skills / agents invoked

- Shell tool for command execution (direct, no MCP)
- No subagents

Never invoke `dev-stack-adaptive-implementation` from Stage 7 — that's Stages 5-6. Never modify code from Stage 7 — that's Stage 8's repair job.
