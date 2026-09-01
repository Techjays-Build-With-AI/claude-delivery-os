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

### 7b.i. Pre-start required external services (v2.3.23 — REQUIRED for integration/contract/concurrency/e2e tiers)

For every test file the `dev-stack-adaptive-implementation` skill wrote in Stages 5-6, read its `# tier:` and `# requires:` header (Rule 7.ii in the dev-implementation SKILL). If the test file's tier is `integration` / `contract` / `concurrency` / `e2e`, the required external services MUST be started BEFORE the test runs.

**Steps per required service:**

1. **Resolve the start command** from the service's own repo:
   - Backend (Node): `package.json` `scripts.dev` or `scripts.start`
   - Backend (Python): `manage.py runserver` or `uvicorn app:app --reload`
   - Backend (Go): `go run ./cmd/server` per the repo's convention
   - Database: check for `docker-compose.yml`, `podman-compose.yml`, or platform-specific test-container config; else use ambient (already-running) service
2. **Read the required env vars** from the service's `.env.example` — every var listed must be present in the runtime env. If ANY is missing → **HALT Stage 7 with `blocker: required-env-vars-missing`**, listing which vars for which service. Do NOT run tests with partial env — that's how the "Bearer null / mocked-integration passes" bug propagates.
3. **Start the service** with a health-check probe (max 30s wait). Health check per service type:
   - HTTP service: `curl -f http://localhost:<port>/health` or `curl -f http://localhost:<port>/` returns 2xx/3xx
   - Database: framework-native ping (e.g. `pg_isready`, `mongosh --eval "db.runCommand({ping:1})"`)
   - Custom: probe defined in service's `.env.example` `HEALTH_CHECK_CMD` if present
4. **Log started service** to `dev/implementation-log.md` under a new `external_services_started:` block:

   ```yaml
   external_services_started:
     - name: backend
       command: npm run dev
       pid: 12456
       port: 8080
       env_vars_verified: [DATABASE_URL, SECRET, FIREBASE_SERVICE_ACCOUNT]
       health_check: "curl -f http://localhost:8080/health"
       started_at: 2026-09-01T14:22:03Z
       status: healthy
     - name: postgres-test
       command: docker compose up -d postgres-test
       port: 5433
       health_check: "pg_isready -h localhost -p 5433"
       started_at: 2026-09-01T14:22:07Z
       status: healthy
   ```

5. **If a service fails to start** (missing env var, port conflict, DB unreachable) → HALT Stage 7 with a specific error naming the service + missing prerequisite + the exact env var / port. Do NOT continue to run tests without the required service. Stage 8's `real-service-not-run` detection would catch this AFTER the fact, but halting HERE surfaces the true blocker earlier.
6. **Tear down services** at end of Stage 7 (after test-run block completes or on halt), regardless of pass/fail. Log `stopped_at` per service.

**Env var resolution — where they come from at Stage 7 time:**

For `/dev:build` runs, env vars are resolved in this order:
1. Explicit `dev/build-env.local` (user-provided secrets for local dev — gitignored)
2. `.env.local` in the target repo (developer's own)
3. `.env` in the target repo
4. `.env.example` (last resort — but any placeholder value there triggers a warning)

If `.env.example` requires `FIREBASE_SERVICE_ACCOUNT` and no non-placeholder value is found anywhere, HALT with:

```
✗ Stage 7 requires backend to start, but FIREBASE_SERVICE_ACCOUNT is not set.

  Backend won't authenticate incoming requests without it — so any integration
  test that hits a gated endpoint would either fail or (worse) pass because
  auth was mocked.

  Add the value to dev/build-env.local (gitignored) OR .env.local, then re-run:
    /dev:build <task-ref> --resume

  Where to get the value:
    - Firebase Console → Project Settings → Service Accounts → Generate new private key
    - Paste the JSON body into FIREBASE_SERVICE_ACCOUNT= (single-line, escaped)
    - OR set GOOGLE_APPLICATION_CREDENTIALS=<path to the file>
```

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
