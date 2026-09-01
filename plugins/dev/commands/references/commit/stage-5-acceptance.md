## Stage 5 — Final acceptance-map verification (commit-time)

**Purpose.** Re-verify every row in `dev/acceptance-map.md` is still green. `/dev:build` built the map; between build and commit the developer may have hand-edited code (typo fix, refactor, additional cleanup) that could have broken tests. Never push a branch on stale test evidence.

Also: if this task is the LAST sub-task to land under the parent (all sibling sub-tasks are DONE in MC), run any `⏸ deferred-to-e2e` rows now.

**Runs after Stage 4 (code review passed).** State: `REVIEW` (unchanged); MC: `devReview` (unchanged). On any regression, fix loop kicks in.

**On completion:** every row in `acceptance-map.md` is `✅ pass` OR `⏸ deferred-to-e2e` (with clear reason).

---

### 5a. Preconditions

- Stages 3+4 done, zero commit-time-blocking findings
- `dev/acceptance-map.md` exists (from `/dev:build` Stage 8)
- Test runner env is set up locally the same way `/dev:build` ran it

---

### 5b. Re-verification loop

For every row in `acceptance-map.md`:

1. Read the `Verified by` column — the exact test spec + test id (e.g. `test/supplier/service.spec.ts::create rejects duplicate`)
2. Execute ONLY that test (framework-native filter: `pnpm test -t "create rejects duplicate"`, `pytest -k`, `go test -run`, `dotnet test --filter`, etc.)
3. Capture stdout + exit code
4. Set the `Commit-time verification` column to `✅ pass`, `❌ fail`, `⏸ deferred-to-e2e`, or `⚠ regression`

If step 2 fails to execute (test framework changed, spec renamed) → treat as `❌ fail` with `unrunnable: true` metadata.

---

### 5c. Deferred-to-e2e resolution

For each row in the map with `⏸ deferred-to-e2e`:

1. Determine if this task is the LAST sub-task landing:
   - Read parent's `subtasks-summary.md` (rollup Sub-tasks table)
   - Count sub-tasks with MC status NOT `done`
   - If this task is the ONLY one remaining (count == 1, this is it) → run E2E now
   - Else → keep `⏸ deferred-to-e2e`; log `deferred_reason: <N> sibling sub-tasks still open` in the map

2. To run E2E now:
   - Framework: Playwright, Cypress, Selenium, WebDriver.io — from `qa/quality-gates.md`
   - Command: `pnpm test:e2e -- --grep <scenario-id>` (or framework equivalent)
   - Capture result → set the row to `✅ pass` or `❌ fail`

3. On E2E fail → treat like any other regression (route to fix loop).

---

### 5d. Rebuild the map

Rewrite `dev/acceptance-map.md` with the new column:

```markdown
| ID | Source | Description | Verified by | Build-time | Commit-time |
|----|--------|-------------|-------------|------------|-------------|
| AC-1 | acceptance-criteria.md#AC-1 | Supplier onboarding form validates tax_id | test/supplier/service.spec.ts::validates tax_id | ✅ pass | ✅ pass |
| AC-2 | acceptance-criteria.md#AC-2 | Duplicate suppliers rejected with 409 | test/supplier/service.spec.ts::rejects duplicate | ✅ pass | ⚠ regression |
| BR-3 | business-rules.md#BR-3 | tax_id unique per country | test/db/supplier.migration.spec.ts | ✅ pass | ✅ pass |
| NFR-1 | nfrs.md#perf | POST /supplier < 200ms p95 | perf/supplier.bench.ts | ⏸ deferred-to-e2e | ✅ pass |
| TS-4 | test-scenarios.md#TS-4 | 3-tab flow end-to-end | e2e/supplier.spec.ts | ⏸ deferred-to-e2e | ⏸ deferred-to-e2e (2 sub-tasks remaining) |
```

Preserve the build-time column. Add the commit-time column. Never delete or overwrite build-time evidence.

---

### 5e. Route to fix loop or advance

**Every row `✅ pass` or acceptably `⏸ deferred-to-e2e`** → mark Stage 5 done. Advance to Stage 7 (semantic merge).

**One or more `⚠ regression` or `❌ fail`** → jump to `stage-6-fix-loop.md`. After fix loop, Stages 3+4+5 all re-run from the top.

---

### 5f. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-5:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  rows_total: 12
  rows_pass_commit_time: 8
  rows_deferred_to_e2e: 3
  rows_regressed: 1
  rows_fixed_in_loop: 1
  e2e_run_this_task: false
  parent_last_subtask: false
  acceptance_map: dev/acceptance-map.md
```

---

### 5g. Skills / agents invoked

- No skill invocation — inline test-execution logic (same runners as `/dev:build` Stage 7)
- Reuses stack-detection from `dev/implementation-log.md` for the correct test-runner command

---

### 5h. On `--resume`

If `--resume` finds `stage-5.status: DONE` AND no new commits since `finished_at`, skip. Otherwise re-run the whole verification loop — regression could have been introduced by any post-Stage-5 edit.

---

### 5i. Never

- Never mark a row `✅ pass` without actually running the test
- Never assume the build-time result still holds (that's the entire reason this stage exists)
- Never remove a deferred-to-e2e row's deferral without checking parent's sub-task count
- Never write a row you can't verify — better to halt than to fake evidence
