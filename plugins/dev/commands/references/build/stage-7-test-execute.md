## Stage 7 — Verify the test map · and the execution runbook

**This file holds two halves, and they run in different commands.**

| Sections | Who runs them | What they do |
|---|---|---|
| **§7a0 – §7b**, **§7i – §7l** | `/dev:build` | verify the test map against the disk. **Run no tests** |
| **§7b.i – §7h** | `/dev:commit` Stage 5 | start what the tests need, execute, parse, record, classify failures |

**`/dev:build` does not execute tests.** Build implements, writes the tests, the test map and
the fixtures, then proves the map is *runnable* without running it. `/dev:commit` Stage 5 is
the only executor, and it reads §7b.i–§7h of this file.

Build's half catches what makes a command fail for reasons unrelated to the code — a renamed
spec, a fixture nobody wrote, a `Needs` token nothing can start. Finding those costs a file
read here; finding them at commit costs a full run plus a loop back into build.

**Section numbers are historical and deliberately unchanged** — `stage-8-validate.md` points at
`§7f.i`, `stage-11-summary.md` at `§7b`, `commit/stage-5-acceptance.md` at `§7b.i`. Renumbering
would break all three.

**Runs after Stages 5-6.** status `agentExecuting` · phase `testing`

**On completion:** `context/test-map/<feature-slug>.md` is verified row by row and every row
carries `status: pending` — written, not yet run.

---

### 7a0. `--skip-qa` short-circuit

If `stage-4.qa_gate_state: skipped-by-user`, no tests and no map were written.
Record and move on:

```yaml
stage-7:
  status: SKIPPED
  reason: --skip-qa (no harness, no tests, no map written)
```

Stage 8 handles this run shape at §8a0.

---

---

### 7a1. `--tests-only` and `--vulnerable` DO execute — they are terminal

These two modes end at Stage 8 (§8.5) and never hand off to `/dev:commit`. There is
no later executor, so if they do not run the suite, nothing ever does and the mode
reports nothing it can stand behind:

| Mode | Why the run is the point |
|---|---|
| `--tests-only` | its output is before/after coverage. Coverage is measured, not read off a map |
| `--vulnerable` | it upgrades packages. The suite result is the only evidence the upgrade broke nothing |

For these two, execute **§7b.i–§7h of this file** in full, then continue
to Stage 8 with real pass/fail rows.

<!-- governed-by: build-declares-commit-executes -->
**This is not an exception to "build declares, commit executes" — it is that rule
applied.** Execution belongs wherever the diff stops moving. In the delivery flow
that is commit; in a terminal maintenance run there is no commit, so it is here.

---

---

### 7a. Preconditions

- `units/<repo>/status.md § ## Run history` `stage-5-6.status: DONE`
- `<repo>/context/test-map/<feature-slug>.md` exists

Missing map with tests written → HALT `blocker: test-map-missing`. The map is the
contract commit executes; without it commit has nothing to run and falls back to
guessing, which is the drift this architecture exists to prevent.

---

---

### 7b. Verify every row, against the disk

**Run the script; do not walk the rows yourself.**

```bash
python "$CLAUDE_PLUGIN_ROOT/scripts/verify-test-map.py"   --map  "<repo>/context/test-map/<feature-slug>.md"   --repo "<repo>"   --json "<workspace_root>/.jetrix/cache/test-map-verify.json"
```

It applies every check below to every row and exits non-zero if any fails. Reading
30 rows by hand costs 150 file reads and applies the name-matching rule 30 separate
times; the script applies it once, identically. Record `rows_total` / `rows_verified`
/ `rows_failed` and the `blockers` list from its JSON into `## Run history`.

**Exit 0** — continue to Stage 8. **Exit 1** — HALT on the blocker it names; its
`rows[]` entries carry the failing row and the reason. **Exit 2** — the map is
missing or has no table: HALT `blocker: test-map-missing`.

If the script cannot run at all (no interpreter), say so in `## Run history` with
`method: manual` and apply the table below by hand — the bar is the same, only the
evidence trail differs.

The checks it applies, one per row:

<!-- rule: test-map-blocker-ids
     phrases: "missing-test-file" | "missing-test-case" | "ambiguous-test-case"
            | "missing-fixture" | "test-map-incomplete" | "test-map-unstartable" -->

**One vocabulary, both commands.** `/dev:commit` §5a.00 re-runs these same checks
against the working tree, and emits these same ids. One defect, one name, whichever
stage happened to see it.

> Until 2.3.29 the two sides used different names for one fact —
> `test-map-dangling-test` here, `missing-test-file` there — and this side used a
> *single* id for three distinct defects, so a report could not tell "no such file"
> from "no such test" from "that name matches two tests". `ambiguous-test-case` is
> new: the condition was always detected, it just had no name of its own.

| Check | Fails when | Blocker |
|---|---|---|
| **Test file exists** | the `Test` column names a path not on disk | `missing-test-file` |
| **Named test exists** | the file exists but holds no test matching `::name` | `missing-test-case` |
| **Named test is unique** | the runner's substring filter would select more than one | `ambiguous-test-case` |
| **`Run it` is populated** | the cell is empty or `—` | `test-map-incomplete` |
| **`Needs` is startable** | a token is not `real-db`, `backend-running`, `frontend-running`, `real-auth` or `—` | `test-map-unstartable` |
| **Fixture exists** | the `Fixtures` column names a factory or seed not on disk | `missing-fixture` |

**Match the test name the way the runner does.** The runner's `-t` filter is a
substring match, so a row must name **exactly one** test. `create.spec.ts::duplicate`
against a file holding both `duplicate` and `duplicate-ignored` selects two, and the
row then runs more than it claims — a false green nobody can see. The script fails
that row as ambiguous and names the other matches.

**Do not execute anything to prove a row.** Reading the spec file settles every
check above. Running it is commit's job and would need the services started.

---

---

### 7b.i. Pre-start required external services (v2.3.23 — REQUIRED for integration/contract/concurrency/e2e tiers)

**This procedure has two callers.** `/dev:build` Stage 7 (here) and `/dev:commit`
Stage 5 §5a.0a, which re-runs gates after the fix loop and finds nothing running
because this stage tore its services down at step 6. Keep it generic enough for
both; never fork a second copy.

For every test file in this run's scope — the ones Stages 5-6 wrote **and** any pre-existing test the run will execute — read its `# tier:` and `# requires:` header (Rule 7.ii in the dev-implementation SKILL). If the tier is `integration` / `contract` / `concurrency` / `e2e`, the required **external** services MUST be started BEFORE the test runs.

**Not every `requires:` names an external service.** A header may declare an in-process dependency — `mongodb-memory-server (in-process)`, Testcontainers started by the suite itself, an embedded broker, Supertest driving the exported app without a listening port. These start themselves; there is nothing for this step to launch. Classify each entry first:

| `requires:` entry | Action |
|---|---|
| names `in-process`, `in-memory`, a Testcontainers fixture, or Supertest against the exported app | **nothing to start** — record it and move on |
| names a process this run must reach over a port (`backend-running`, `frontend-running`, `real-db`, `real-auth`) | start it per the steps below |

Treating an in-process dependency as external halts a suite that would have passed — the opposite failure to the one this step exists to prevent.

**Steps per required service:**

1. **Resolve the start command** from the service's own repo:
   - Backend (Node): `package.json` `scripts.dev` or `scripts.start`
   - Backend (Python): `manage.py runserver` or `uvicorn app:app --reload`
   - Backend (Go): `go run ./cmd/server` per the repo's convention
   - **Frontend (dev server)**: an `e2e` test drives a browser against this — without it Playwright/Cypress hits a dead port, which fails as a connection error, not as the behaviour under test. **If the e2e runner's own config declares a `webServer` block, let it own the frontend and do not start one here** — it pins the port, and a second server would either collide or serve a different one. Start it here only when that block is absent, using the pinned command from `qa-greenfield-harness/references/gates-template.md`. Never assume `3000`
   - Database: check for `docker-compose.yml`, `podman-compose.yml`, or platform-specific test-container config; else use ambient (already-running) service
2. **Read the required env vars** from the service's `.env.example` — every var listed must be present in the runtime env. If ANY is missing → **HALT Stage 7 with `blocker: required-env-vars-missing`**, listing which vars for which service. Do NOT run tests with partial env — that's how the "Bearer null / mocked-integration passes" bug propagates.
2b. **These tiers may not write to a non-local database.** Step 2 checks the vars are
   present; this checks where they point. Resolve the URI the service will actually use
   and classify its host:

   | URI | Verdict |
   |---|---|
   | `localhost` / `127.0.0.1`, or a container this run started | run |
   | in-process — `mongodb-memory-server`, Testcontainers, an embedded engine | run |
   | any remote host, any `mongodb+srv://`, any URI carrying credentials | **HALT `blocker: remote-db-in-test-run`** |

   These tiers create users and rows. Pointed at a hosted cluster they write to something
   every run and every teammate shares, and the first run that halts mid-suite leaves its
   fixtures there. Step 1's *"else use ambient (already-running) service"* resolves a
   database by what is reachable, and a remote cluster is always reachable — that is the
   hole this closes. Name the host in the halt, never the credentials, and state the
   remedy: point the service at a local database for the run.
3. **Probe the port first. Start only if nothing is there.**

   | Probe | Action |
   |---|---|
   | nothing listening | start it, then health-check as below |
   | listening, and it identifies as this build | **adopt it** — record `adopted: true`, start nothing |
   | listening, and it does not | a previous run's own service → reclaim it per below; anything else → HALT `blocker: stale-service-on-port`, naming host, port and pid |

   **Liveness is not identity.** `curl -f .../health` returning 2xx proves something is
   answering, never that it is the code under test. A server left by an earlier branch
   answers it exactly as this one does, and the suite then reports green against code the
   diff does not contain — a worse outcome than any halt. Identify by the build the
   service reports (a sha or branch on its health route), else by the pid's start time
   against the branch's newest commit. Neither available → HALT; a server that cannot say
   what it is running is a stale one.

   **Reclaim this system's own litter; never touch anything else.** A port held by a
   service a previous delivery-os run started is ours to clear, and clearing it needs no
   human. Search every `units/<repo>/status.md` in the workspace for an
   `external_services_started:` entry on this port and stop that process only when all
   three of these match:

   | Must match | Why |
   |---|---|
   | `port` | it is the port being reclaimed |
   | `pid` | it is that entry's process |
   | the pid's real start time is at or after the entry's `started_at` | pids are reused after a reboot, and without this the match is a coincidence |

   All three hold → stop it, record `reclaimed_pid` naming the entry it matched, and start
   the correct build. Any one missing, or no entry at all → HALT. **A process with no
   record is someone else's** — started by hand, or by another tool — and a run that frees
   its port by killing whatever holds it will one day kill the server the user was
   working in. The halt names the pid and the user decides.

   Health check per service type (max 30s wait):
   - HTTP service: `curl -f http://localhost:<port>/health` or `curl -f http://localhost:<port>/` returns 2xx/3xx
   - Database: framework-native ping (e.g. `pg_isready`, `mongosh --eval "db.runCommand({ping:1})"`)
   - Custom: probe defined in service's `.env.example` `HEALTH_CHECK_CMD` if present
4. **Log started service** to `units/<repo>/status.md § ## Run history` under a new `external_services_started:` block:

   ```yaml
   external_services_started:
     - name: backend
       command: npm run dev
       pid: 12456
       port: 8080
       adopted: false
       reclaimed_pid: null
       db_host: localhost
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

**A gate records what it covered, not only that it ran.** Capture `files_checked` beside
each gate's exit code, and fail `blocker: gate-scope-empty` on either signal:

| Signal | What it means |
|---|---|
| the tool reports a file count and it is **0** | the gate inspected nothing and exited 0 |
| the command resolves to a committed or staged scope — `lint-staged`, `--cached`, `--since`, `--diff-filter` | it selects from git history, and this command commits nothing |

A gate scoped to staged files is not a weak gate here, it is an absent one: the run has
written every file into the working tree and committed none of them, so the set the gate
examines is empty and the green it reports is the green of an empty set. The halt names
the gate, its command, and the unscoped equivalent to put in `qa/quality-gates.md`.

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

Append to `units/<repo>/status.md § ## Run history` under a `test_runs:` section:

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

**A green first run is not enough either.** The rule above re-runs a gate that *fails*; a gate that *passes* is never checked again, so a suite that is green by luck is reported as green by proof. Before the test-suite gate is recorded `PASS`, **run it a second time** and compare:

| Two runs | Record |
|---|---|
| both green, same count | `PASS` — the only result that may be called green |
| green then red (or red then green) | `PASS_FLAKY` — **classify the red run per §7f.i first**: a timeout at the tool default under instrumentation is `harness-config`, not `flaky`. Keep **both** results, naming the tests that differed |
| both red | `FAIL` — classify per §7f.i as normal |

The second run costs one suite execution and is the only thing separating "the tests pass" from "the tests passed that time". A single-run green has been enough to report `COMPLETE` on a suite that fails every other run.

Where the two runs disagree, say so in the summary with the next step — **the test is unreliable, not the feature**: name the differing tests, give the command to reproduce (`<test cmd> <path>` for that file alone), and say whether they pass in isolation. A test that passes alone and fails in the suite is ordering or shared state; one that fails alone is a real defect the first run happened to miss.

### 7f.i. Classify the failure BEFORE Stage 8 spends a repair attempt on it

A failing gate is not automatically a code defect, and treating it as one burns the repair budget on a test that is correct. Decide the **verdict** here; Stage 8 routes on it.

Run the diagnosis in this order, stopping at the first verdict that fits:

| Verdict | Evidence required |
|---|---|
| `env-missing` | an external service or env var is absent — already halted at §7b.i, never reaches here |
| `harness-config` | the test **passes under the plain run command** (`npm test`, `pytest`) and fails only under the gate's variant (coverage instrumentation, parallelism, a CI-only flag) — **OR** the failure is a timeout and the configured limit is the tool's default, never explicitly chosen |
| `flaky` | the single retry above produced a **different set of failing tests**, **OR** the failing test passes when run in isolation while the suite still fails |
| `defect` | fails consistently, and fails in isolation. The default when nothing above fits |

**Isolated re-run is bounded: one attempt per failing test** (`pnpm test <path>` / `pytest <path>::<name>`), its result recorded. This is diagnosis, not retry-until-green — **the original failure stays in the evidence whatever the isolated run does.**

**Why `harness-config` is checked before `flaky`:** instrumentation overhead presents *as* flakiness — a different few tests cross the limit each run. Calling it flaky stops at "unreliable test"; calling it harness-config names the fix. A timeout at exactly the tool default is the strongest signal, because no one chose that number.

**Record the verdict** in `units/<repo>/status.md § ## Run history` beside the exit code:

```yaml
- gate: QG-005
  command: npm run test:coverage
  result: FAIL
  verdict: harness-config
  evidence:
    plain_run: PASS            # npm test — same tests, no instrumentation
    gate_run_1: [EmployeesContent.test.jsx > renders list]
    gate_run_2: [EmpolyeeForm.test.jsx > submits]   # different set → not a defect
    failure_mode: timeout 5000ms
    configured_limit: default   # never explicitly set
```

Stage 8 reads `verdict:` and routes. It does not re-derive the diagnosis.

---

### 7g. Missing test command

If a gate's command fails with "command not found" / "no such option" / equivalent:
- Do NOT try to install anything (that's Stage 4's job)
- Route back to Stage 4 with an escalation: `qa/quality-gates.md` has a command that doesn't work in this repo
- Halt Stage 7

This shouldn't happen if Stage 4's `qa-greenfield-harness` bootstrap succeeded — but if `qa/quality-gates.md` was hand-edited or partially installed, catch it here.

---

### 7h. Progress log format

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-7:
  status: DONE                          # DONE | FAILED | BLOCKED
  started_at: 2026-08-31T15:07:22Z
  executed: false                       # ALWAYS false here — this stage reads, never runs
  rows_verified: 14
  rows_total: 14

  # REQUIRED, every run. Anything that EXECUTED during this build, whatever
  # stage or subagent ran it, with the command and what prompted it. `[]` is
  # the healthy value and must be written explicitly -- an absent field is a
  # missing answer, not a "no".
  unplanned_executions: []
  finished_at: 2026-08-31T15:12:41Z
```

`FAILED` if any gate ended in `FAIL` after Stage 8's repair loop is done and still couldn't fix.

**Why `unplanned_executions` exists rather than a sterner sentence.** A real run
executed 474 unit and 35 e2e tests at this stage, recorded `executed: false`
correctly, and then parked the results in an invented `builder_run_results:` key —
because the schema had nowhere to put them and the agent would not throw them away.
It was honest; **nothing was reading.** This field is that place, and `§8g` gates on
it, so an execution that happens anyway cannot be reported as a clean build:

```yaml
unplanned_executions:
  - command: "npx vitest run --coverage"
    ran_by: "builder subagent (Stage 5-6)"
    prompted_by: "superpowers:verification-before-completion"
    result: "42 files, 474 passed"
```

**Recording it is never the violation — hiding it is.** A run that declares what it
did gets a `PARTIAL_UNPLANNED_RUN` status and a line in the summary. A run that
executes and writes `[]` has falsified its own record, and the next stage cannot
tell the difference between that and a clean build.

---

---

### 7i. Verify `CLAUDE.md` points at the map

`<repo>/CLAUDE.md` has the `## Tests` pointer written at Stage 5-6 §5-6b.iii.
Missing → write it now, idempotently. A map nobody is pointed at is a map the
next agent never opens, and it writes a second `holidayFactory` instead.

---

---

### 7j. Record

```yaml
stage-7:
  status: DONE                      # DONE | SKIPPED
  started_at: <ISO>
  map_file: context/test-map/<feature-slug>.md
  rows_total: 12
  rows_verified: 12
  tiers_present: [unit, integration, e2e]
  needs_tokens: [real-db, backend-running]
  executed: false                   # ALWAYS false — build does not run tests
  finished_at: <ISO>
```

**`executed: false` is recorded deliberately**, so `/dev:commit` Stage 0 can tell
"not run yet, by design" from "a run that never happened". Commit reads this and
knows every row is still `pending`.

---

---

### 7k. Failure handling

A dangling row is a **build defect, not a test failure** — build wrote both the
test and the map, so a mismatch between them is work left unfinished. Fix it here:
rename the row to the real test, write the missing fixture, or drop the row if the
scenario was dropped. Then re-verify.

Never "fix" a dangling row by deleting the scenario it names. If a scenario in the
plan has no test, that is a coverage gap Stage 8 must report as `not-verified` —
not something to tidy away by removing the evidence that it is missing.

---

---

### 7l. On `--resume`

If `--resume` finds `stage-7.status: DONE` **or `SKIPPED`**, skip. The map is
cheap to re-verify, but re-verifying it would also re-raise blockers the user has
already resolved.
