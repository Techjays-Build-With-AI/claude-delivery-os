## Stage 8 — Validate against parent AC + BR + TS + NFRs

**Purpose.** Build the acceptance-map. Every parent-owned assertion (Acceptance Criteria, Business Rules, Test Scenarios, NFRs) gets a row that maps to a validation method, result, and evidence. This is the definition of "done at build-time" — green tests alone are not enough; the acceptance-map is.

**Runs after Stage 7 tests pass.** State: `TESTING` (unchanged). MC: `inProgress`.

**On completion:** `dev/acceptance-map.md` contains one row per applicable AC/BR/TS/NFR, either `✅ pass` (with evidence) or `⏸ deferred-to-e2e` (cross-sub-task E2E, closed by last sub-task).

---

### 8a. Preconditions

- `dev/build-run.md` `stage-7.status: DONE`
- All Required gates from `qa/quality-gates.md` passed (no `FAIL` results in `test_runs:`)

If any Required gate is `FAIL` → jump to Stage 8's repair loop (§8f) BEFORE trying to build the acceptance-map.

---

### 8a0. When `/dev:build` ran with `--skip-qa`

No tests were written, so there is no test evidence to map to. Build the acceptance-map anyway — every assertion still gets a row — but each row's evidence is what you inspected, not what executed:

```
| AC-1 | <assertion> | verified: manually | <what you read, and what it now says> |
```

Rules for a manual row: name the file and value you actually changed, never "looks correct". If an assertion cannot be settled by reading the code — anything about runtime behaviour, timing, or integration — mark it `verified: not-verified` and list it in the Stage 11 summary under a heading the user cannot miss. A `--skip-qa` run may finish with unverified rows; it may never finish with rows that *claim* verification it didn't do.

Stage 8 does not fail a run for missing test evidence under this flag. It fails for a missing row.

### 8b. Extract every parent-owned assertion

**Non-feature targets (bug / story / task / epic) — read `tasks/<slug>.md` instead.** These have no BA folder; their assertions come from the tabs their type owns, per MC's `TASK_TYPE_TAB_CONFIG`:

- **`bug`** — the type has only Description, Steps to Reproduce, Actual Result, Expected Result. Build the map from:
  - `Expected Result` — every distinct expected behaviour → one map row. This is the bug's acceptance criteria; a fix is done when each one holds.
  - `Steps to Reproduce` — one `repro` row whose evidence is a test that follows those steps and now passes. This is the regression test; without it the fix has no proof it addressed *this* defect.
  - `Actual Result` is the pre-fix observation, not an assertion — never a map row. Use it to word the regression test's failing case.
  - An empty `Expected Result` is a halt, not an empty map — `/dev:plan` §2f should already have blocked it.
- **`story` · `task` · `epic`** — same sources as a feature below, minus any tab the type lacks. Absent tabs contribute no rows; they are not failures.

A non-feature target is never split, so the sub-task scoping rule below does not apply to it.

**Feature targets** — read the parent's BA files (parent-alone → `features/<slug>/*.md`; sub-task → same, since sub-task inherits parent's validation contract):

- `acceptance-criteria.md` — every `AC-N` bullet or row → one map row
- `business-rules.md` — every `BR-N` bullet or row → one map row (only if the BR requires enforcement in code, not "informational" business context)
- `test-scenarios.md` — every `TS-N` scenario → one map row
- `nfrs.md` — every `NFR-N` with a measurable threshold → one map row (informational NFRs like "should be maintainable" are excluded)

**For a sub-task target:** apply the sub-task scoping rule — an AC that references an endpoint this sub-task owns is validatable here; an AC that spans layers (UI + backend + mobile) is marked `deferred-to-e2e` for the LAST sub-task to close.

---

### 8c. Map each assertion to test evidence — WITH REAL-SERVICE VALIDATION (v2.3.23)

For each map row, grep the test source files (`step_N.tests_written` from `dev/implementation-log.md`) for the assertion's ID.

**Match rules:**

- Test file contains a describe/it/test block citing the assertion ID (e.g. `it('should reject duplicate — AC-B2', ...)`)
- Match on word-boundary — `AC-B2` matches but `AC-B22` doesn't
- Multiple IDs per test — a single test covering `AC-B1, AC-B2 · BR-1` counts as evidence for all three

**Tier + mock detection per test file (v2.3.23 — closes the "tests pass but real endpoint 401s" gap):**

For each matching test file, read the top of the file:
1. Extract the `// tier:` (or `# tier:`) header — expected: `unit` / `component` / `integration` / `contract` / `concurrency` / `e2e`
2. Scan the file body for mock indicators:
   - `jest.mock(`, `vi.mock(`, `vitest.mock(`, `sinon.stub(`, `sinon.mock(`
   - `nock(`, `msw.setupServer(`, `axios-mock-adapter`
   - `unittest.mock`, `MagicMock`, `pytest.MonkeyPatch`, `mockery`
   - `mockery.replaceAll(`, `td.replace(`
3. **Apply Rule 7.iv from `dev-stack-adaptive-implementation`:** if `tier: integration` (or higher) AND ANY mock indicator hit → the tier claim is CONTRADICTED. Record row as `❌ mock-contradicts-tier` — do NOT mark ✅ pass even if the test itself ran green.

**Real-service run requirement per tier (v2.3.23):**

Before marking a row ✅ pass for tiers `integration` / `contract` / `concurrency` / `e2e`, verify Stage 7 ran the test file against a REAL backend process:

- Read Stage 7's `test_runs.<file>.external_services_started` list
- For each service in the test file's `# requires:` header, the service must appear in `external_services_started` with `status: healthy`
- If required services aren't in `external_services_started` → row is `❌ real-service-not-run` — the test can't have actually validated integration behavior

**Common cause of `❌ real-service-not-run`:** the backend needs env vars that aren't set in the test environment. Example: `FIREBASE_SERVICE_ACCOUNT` missing → backend fails to start → test with `# requires: backend-running` skipped or hit an unreachable localhost:8080 → test "passed" only because axios call was mocked.

Result mapping (v2.3.23 tightened):

| Test file result | tier declared | mocks used | real service ran | Map row status |
|---|---|---|---|---|
| PASS | unit | any | N/A | ✅ pass |
| PASS | component | any (mocking axios OK at component tier) | N/A | ✅ pass |
| PASS | integration/contract/concurrency/e2e | none | yes | ✅ pass |
| PASS | integration/contract/concurrency/e2e | some | any | ❌ mock-contradicts-tier |
| PASS | integration/contract/concurrency/e2e | none | no | ❌ real-service-not-run |
| PASS_FLAKY_ONE_RETRY | (any) | (per above) | (per above) | ✅ pass with `flaky: 1-retry` |
| FAIL | (any) | (any) | (any) | ❌ fail (repair via §8f) |
| No test found | — | — | — | ❌ missing-test (fail) |

**Never mark ✅ pass on `mock-contradicts-tier` or `real-service-not-run`** — those failures are treated the same as ❌ fail from Stage 8's downstream perspective. The repair loop (§8f) either fixes the test (replaces mock with real fixture) or splits it (unit test at unit tier + integration test at integration tier).

---

### 8d. Deferred-to-e2e for cross-sub-task ACs

An AC is `deferred-to-e2e` when:

1. This task is a sub-task (not parent-alone)
2. The AC spans multiple layers (e.g. "user submits form and sees success toast and record in list" — touches frontend + backend + DB)
3. This sub-task doesn't own the LAYER that closes the AC's user-visible outcome

**Rule for who closes:** the last sub-task to reach `REVIEW` locally (MC `devReview`) at `/dev:commit` time runs the E2E validation and closes the deferred ACs. Check the parent's rollup Sub-tasks table (from `tl-plan.md`) — the sub-tasks NOT-YET at `REVIEW`/`DONE` count; deferring lives in the acceptance-map. The E2E execution itself happens in `/dev:commit` Stage 5, not here at build-time Stage 8.

Row format:

```markdown
| AC | AC-1 | (E2E) user submits valid form → success toast → record in list | E2E — parent Feature-4 close | ⏸ deferred-to-e2e | last sub-task closes; parent's Sub-tasks table: backend done, this=frontend running, mobile pending |
```

---

### 8e. Assemble `dev/acceptance-map.md`

Frontmatter:

```yaml
---
doc_type: acceptance-map
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>            # OMIT for parent-alone
subtask_repo: <repo-slug>
generated_at: <ISO>
build_run_id: <build-run-timestamp>
status: COMPLETE               # COMPLETE | PARTIAL_FAILURES | PARTIAL_DEFERRED
---
```

Body table:

```markdown
| Kind | ID | Statement | Verified by | Result | Evidence |
|---|---|---|---|---|---|
| AC | AC-B1 | POST /supplier returns 201 with created record | tests/endpoint.spec.ts::create-happy | ✅ pass | test_runs: QG-006, exit 0 |
| AC | AC-B2 | POST /supplier returns 409 with DUPLICATE_TAX_ID on repeat | tests/endpoint.spec.ts::duplicate | ✅ pass | test_runs: QG-006, exit 0 |
| AC | AC-1 | (E2E) submit valid form → success toast → record in list | E2E — cross-sub-task | ⏸ deferred-to-e2e | last sub-task closes; parent rollup: backend done |
| BR | BR-1 | (tax_id, country) uniqueness | DB constraint + integration test | ✅ pass | code:migrations/…, test:supplier.spec.ts::duplicate |
| TS | TS-U-1 | Happy path — new supplier submission | tests/supplier.spec.ts::happy | ✅ pass | test_runs: QG-001 |
| NFR | NFR-B1 | Endpoint responds < 300ms p95 | tests/perf.spec.ts::latency | ✅ pass | test_runs: QG-BENCH, p95=142ms |
```

**Status field:**

- `COMPLETE` — every applicable row is `✅ pass` or `⏸ deferred-to-e2e`, **and the test-suite gate was green on both runs** (§7f). A `PASS_FLAKY` gate is never `COMPLETE`: it is `PARTIAL_HARNESS`, carrying both run results
- `PARTIAL_FAILURES` — one or more rows are `❌ fail` from a **`defect`** verdict, post-repair → task can't advance
- `PARTIAL_HARNESS` — rows are red, but **none is a defect**: every failure is `flaky` or `harness-config` → **task advances**, carrying the remedies and flaky rows forward
- `PARTIAL_DEFERRED` — no failures, but some deferred rows exist (normal for non-last sub-tasks)

**Why the split.** A `defect` means the code is wrong — advancing would commit a known-broken state. A `flaky` or `harness-config` failure means the tests are right and the runner is not, and the remedy is a separate human change to the harness; blocking there strands good tests over a config default.

Advancing is not the same as passing. A `PARTIAL_HARNESS` run must carry into the summary, the acceptance-map and the PR body:

- every `flaky` row with **both** run results
- every `harness_config_remedy` block, verbatim, with its `requires: human DEC-###`
- a one-line statement that a Required gate is red and why it was not repaired

A reviewer must be able to see the red gate without opening anything else.

---

### 8.5. Terminal stage for `--tests-only` runs

A `--tests-only` run ends here, not at Stage 11. Stages 9–11 assume a product diff that does not exist: nothing to security-review, no unit to flip `designed → implemented`, no runbook for code that already shipped. Skipping them is correct — **ending without a state transition is not.**

Do all four, in order:

1. **Write the run summary.** Tests added per tier · before/after coverage with **branch and line reported separately** · every `not-verified` row with its blocker · every `tier-unavailable` · everything deliberately left untested. A behaviour pinned by a characterisation test is *recorded*, not *endorsed* — say so where the pinned behaviour looks like a defect.
   **Name every command, with its own count.** A repo usually has more than one runner, and a reader who is given a total they cannot reproduce will run the wrong one. List each separately — the command, what it runs, and how many tests it accounts for:

   | Runner | Command | Tests |
   |---|---|---|
   | Vitest (unit + component) | `npm test` | 264 |
   | Playwright (browser) | `npm run e2e` | 4 |
   | coverage gate | `npm run test:coverage` | — |
   | new-code floor | `npm run test:diff-coverage` (after coverage) | — |

   Never report one combined figure. `npm run e2e` returning 4 when the summary claims 264 reads as a broken run; it is two runners.

   **State the CI position.** Check the repo for a workflow (`.github/workflows/*.yml` or equivalent) and say which of these gates it already runs, so nobody re-wires what exists — then tell the reader to confirm the run is green on the PR rather than asserting it here. Build never watches CI. Where no workflow runs these gates, say that plainly: it means local is the only place they have ever passed.

2. **Record `tests_only: true`** in `dev/build-run.md`, so `/dev:commit` can tell "skipped by design" from "never ran" — it reads this at its Stage 0.
3. **Set local state — gated on §8e's status**, not unconditional:

   | Status | State | Why |
   |---|---|---|
   | `COMPLETE` · `PARTIAL_DEFERRED` | `IN_PROGRESS` | clean run, advance |
   | **`PARTIAL_HARNESS`** | `IN_PROGRESS` | tests are correct; the harness is misconfigured. Advance **carrying the remedy and flaky rows** into the summary and the PR body |
   | **`PARTIAL_FAILURES`** | **leave as-is — do NOT advance** | an unfixed `defect` means the suite is red for a real reason. Halt, name the failing rows, and stop |

   `/dev:commit` refuses to start on anything but `IN_PROGRESS`, so this step is what makes the work committable.

4. **Report the next step:**

   | Status | Next |
   |---|---|
   | `COMPLETE` · `PARTIAL_DEFERRED` | `/qa:health` — it writes the real gate results back to `quality-gates.md`, which **no build stage does** — then `/dev:commit` |
   | `PARTIAL_HARNESS` | the remedy first, as a `DEC-###`, then `/qa:health`, then `/dev:commit`. Say plainly that a Required gate is red |
   | `PARTIAL_FAILURES` | the failing rows and what to fix. Do not mention commit |

`/dev:commit` reads `tests_only` and `stage-8.status` at its Stage 0 and routes accordingly. Its semantic context merge still runs: with no context-unit changes it records a zero-change result, which that stage defines as legitimate, not a skip.

---

### 8f. Repair loop — fix any `❌ fail` row

Per `/dev:build` §14 bounded limits:
- 3 focused repair attempts per failing row
- 2 broad validation cycles (whole Stage 7 + Stage 8 re-run)

**Route by verdict first — only `defect` gets a repair attempt.**

Read `verdict:` from the gate's `dev/implementation-log.md` block (set at Stage 7 §7f.i). Do not re-derive it.

| Verdict | Action | Repair budget |
|---|---|---|
| `defect` | focused repair, below | **consumes an attempt** |
| `flaky` | no repair. Record both run results and carry the row as `flaky` | **none** |
| `harness-config` | no repair. Emit the remedy block below | **none** |
| `env-missing` | already halted at Stage 7 | — |

This is the rule that stops a moving target eating the budget. A failure whose cause is instrumentation or a default limit cannot be fixed by editing the test, so spending three attempts on it produces three wasted edits and a still-red gate.

**Remedy block for `harness-config`** — write to `dev/implementation-log.md` and surface in the Stage 11 summary:

```yaml
harness_config_remedy:
  gate: QG-005
  symptom: 3 tests exceed 5000ms under v8 coverage instrumentation; pass under `npm test`
  diagnosis: harness-config
  file: vite.config.js
  change: "add `testTimeout: 30000` to the `test` block"
  rationale: instrumentation adds per-test overhead; the limit is the tool default, never chosen
  requires: human DEC-### — this modifies the harness, not a test
  measured_when_applied: lines 90.02% / branches 91.17% — floors met
```

**Never apply it.** A gate or threshold change is a human `DEC-###`; this is a recommendation carrying its own evidence. Running the variant once to populate `measured_when_applied` is legitimate — label it a measurement, never a gate result.

**Acceptance-map statuses for these two verdicts:**

- A row backed by a `flaky` test is **`flaky`**, never `✅ pass` — record both results. A passing retry does not erase the failure.
- A row blocked by `harness-config` is **`blocked`**, naming the remedy.

Neither may read `pass`. When a run's only red rows are `flaky` or `harness-config`, the status is **`PARTIAL_HARNESS`** — the gate is genuinely red, the fix is a human decision rather than another repair cycle, and the task still advances carrying both forward. A single `defect` row anywhere in the run makes it `PARTIAL_FAILURES` instead, and it stops.

**Focused repair** (`defect` only):

1. Identify the failing test's file + line
2. Delegate back to `dev-stack-adaptive-implementation` in "fix mode" — give it the failure output + the test file
3. Skill applies a focused code fix (small diff)
4. Re-run JUST the failing test (`pnpm test <path>` / `pytest <path>::<name>`)
5. If pass → continue to next failing row. If fail → next attempt.

**Broad cycle:** re-run all of Stage 7 (all Required gates) after 3 focused attempts on a row hit their limit. Two broad cycles allowed.

**Limits exceeded:**
- Write `dev/escalation-<n>.md` with the failure chain (attempts, resulting states, remaining diagnosis)
- Local state: `TESTING → BLOCKED`
- MC status: `blocked`
- Halt. Report to user.

---

### 8g. Missing-test rows

An assertion with no test in the code IS a bug in Stages 5-6. Two options:

**Option A** (preferred): route back to Stages 5-6 to write the missing test, then re-run 7 + 8. Bounded by 1 broad cycle.

**Option B** (fallback): if writing the test can't be done (dependency doesn't exist, testing framework doesn't support the scenario), mark the row `❌ missing-test-cant-be-added` and escalate. The developer decides at PR review whether to accept the risk.

**Never mark `✅ pass` without a test.** The acceptance-map is the contract.

---

### 8h. Progress log format

Append to `dev/build-run.md`:

```yaml
stage-8:
  status: DONE                                # DONE | BLOCKED
  started_at: 2026-08-31T15:12:42Z
  assertions_extracted:
    ac:  4
    br:  2
    ts:  5
    nfr: 1
  map_rows: 12
  results:
    pass:                8
    deferred_to_e2e:     3
    fail:                1                    # became 0 after repair
  repair_attempts:  2                         # total attempts across all failures
  broad_cycles:     0
  final_status: COMPLETE                      # COMPLETE | PARTIAL_FAILURES | PARTIAL_DEFERRED
  finished_at: 2026-08-31T15:18:57Z
```

---

### 8i. On `--resume`

If `--resume` finds `stage-8.status: DONE` and `final_status: COMPLETE`, skip.

If `final_status: PARTIAL_FAILURES`, re-run from §8c (map assertions to evidence) — the developer might have hand-fixed something.

---

### Skills / agents invoked

- **`dev-stack-adaptive-implementation` skill** in fix-mode — only during §8f focused repair
- No subagents

Never invoke `security-review` from Stage 8 — that's Stage 9.
