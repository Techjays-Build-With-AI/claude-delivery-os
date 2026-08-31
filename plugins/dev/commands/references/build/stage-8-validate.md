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

### 8b. Extract every parent-owned assertion

Read the parent's BA files (parent-alone → `features/<slug>/*.md`; sub-task → same, since sub-task inherits parent's validation contract):

- `acceptance-criteria.md` — every `AC-N` bullet or row → one map row
- `business-rules.md` — every `BR-N` bullet or row → one map row (only if the BR requires enforcement in code, not "informational" business context)
- `test-scenarios.md` — every `TS-N` scenario → one map row
- `nfrs.md` — every `NFR-N` with a measurable threshold → one map row (informational NFRs like "should be maintainable" are excluded)

**For a sub-task target:** apply the sub-task scoping rule — an AC that references an endpoint this sub-task owns is validatable here; an AC that spans layers (UI + backend + mobile) is marked `deferred-to-e2e` for the LAST sub-task to close.

---

### 8c. Map each assertion to test evidence

For each map row, grep the test source files (`step_N.tests_written` from `dev/implementation-log.md`) for the assertion's ID.

**Match rules:**

- Test file contains a describe/it/test block citing the assertion ID (e.g. `it('should reject duplicate — AC-B2', ...)`)
- Match on word-boundary — `AC-B2` matches but `AC-B22` doesn't
- Multiple IDs per test — a single test covering `AC-B1, AC-B2 · BR-1` counts as evidence for all three

Look up the corresponding row in `test_runs:` (from Stage 7) — get the result.

Result mapping:

| Test file result | Map row status |
|---|---|
| Test exists AND `test_runs` shows PASS | ✅ pass |
| Test exists AND `test_runs` shows FAIL | ❌ fail (repair via §8f) |
| Test exists AND `test_runs` shows PASS_FLAKY_ONE_RETRY | ✅ pass (with `flaky: 1-retry` note) |
| No test found | See §8d — deferred-to-e2e OR ❌ missing-test (fail) |

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

- `COMPLETE` — every applicable row is `✅ pass` or `⏸ deferred-to-e2e`
- `PARTIAL_FAILURES` — one or more rows are `❌ fail` (post-repair) → task can't advance
- `PARTIAL_DEFERRED` — no failures, but some deferred rows exist (normal for non-last sub-tasks)

---

### 8f. Repair loop — fix any `❌ fail` row

Per `/dev:build` §14 bounded limits:
- 3 focused repair attempts per failing row
- 2 broad validation cycles (whole Stage 7 + Stage 8 re-run)

**Focused repair:**

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
