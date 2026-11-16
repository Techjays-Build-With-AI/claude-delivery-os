## Stage 5 — Final `## Acceptance` table verification (commit-time)

**Purpose.** Settle every row in `units/<repo>/status.md § ## Acceptance`: that the
map tells the truth, that each row's test proves what it claims, and that the code
passes it. `/dev:build` writes the map and executes nothing, so commit is where
every row moves off `⏳ pending`.

Also: if this task is the LAST sub-task to land under the parent (all sibling sub-tasks are DONE in MC), run any `⏸ deferred-to-e2e` rows now.

**On completion:** every row in `status.md` § `## Acceptance` is `✅ pass` OR `⏸ deferred-to-e2e` (with clear reason) — or, where a red row classified `flaky` / `harness-config` per §5b.i.

---

### 5.0. Two phases — review, then execute ONCE

**The expensive half of this stage runs after every known finding is fixed, not
before.** Reading the map and running the suite answer different questions and cost
three orders of magnitude apart, so they are separated:

| Phase | Sections | Asks | Test executions |
|---|---|---|---|
| **5R — review** | §5a.00 · §5a.0 · §5d.i coverage | Does the map tell the truth? Does each test prove its row? Does every ticket row have a test at all? | **zero** |
| **5X — execute** | §5a.0a · §5b · §5b.i · §5c · §5d | Do they pass? | all of them |

**5R is read-only and runs in parallel with Stage 4** (`commit.md` §5a) — neither
reviewer needs a green suite to do its reading. Their findings merge into one repair
pass.

**5X runs once, after Stage 6 has cleared every Stage 4 and 5R finding.** Executing
before those repairs lands means executing against code that is about to change: the
run is invalidated by the repair that follows it, and then repeated. A loop that
repaired twelve review findings over three rounds paid for the full map three times
to learn nothing it kept.

```
Stage 4 code review  ┐
                     ├── parallel · read-only · 0 executions
Stage 5R map review  ┘
          │
          ▼   all findings from both → ONE repair pass (Stage 6)
          │
Stage 5X  EXECUTE ─── once: every row + coverage + the suite gate twice
          │
          ▼   red? → classify §5b.i → defect → repair → re-run the failed
              rows and the suite gate. Not the whole map again.
```

**Nothing is skipped by this ordering.** Every row is still executed, and the suite
gate still runs twice before any green is recorded (§5b). What moves is *when* — one
execution after the repairs instead of one before each of them.

---

### 5a. Preconditions

**For 5R** — the same snapshot Stage 4 reads, and nothing else. It does **not** wait
on Stage 4; the two are dispatched together.

- `units/<repo>/status.md § ## Acceptance` exists (from `/dev:build` Stage 8)
- the review snapshot is built (`commit.md` Stage 0)

**For 5X** — the gate that makes the single execution worth running:

- **Stage 4 AND 5R are both done, with zero findings open at commit-time threshold.**
  A finding still open means code is still about to change; executing now buys a
  result the next repair invalidates. Open findings → Stage 6 first, then return here
- `units/<repo>/status.md § ## Acceptance` exists (from `/dev:build` Stage 8)
- **Services are started by this stage, not assumed** — §5a.0a. `/dev:build`
  Stage 7 tears its services down when it finishes, so by commit time nothing is
  running. The old wording here (*"test runner env is set up locally the same way
  `/dev:build` ran it"*) was an assumption no one satisfied

---

### 5a.0a. Execute the map — commit decides nothing

> **Phase 5X.** Runs once, and only once §5a's 5X precondition holds: Stage 4 and
> 5R both clean. Everything from here to §5d is the executing half.

<!-- governed-by: build-declares-commit-executes -->
**Build declared; commit executes.** The test map
(`<repo>/context/test-map/<feature-slug>.md`) carries, per scenario, the command
that runs it and what that command needs running. This stage runs those commands.
It does not re-derive which tiers apply, does not infer services from file paths,
and does not invent a gate selection of its own — all of that is knowledge build
had when it wrote the test, and re-deriving it here is how the two halves drift.

**1. Start exactly what the map's `Needs` column declares.** Take the union across
the rows you are about to run, then execute
`references/build/stage-7-test-execute.md` §7b.i verbatim for that set — same
classification (in-process dependencies start themselves), same env-var
verification, same 30s health probe, same `external_services_started` record. One
procedure, two callers.

A row whose `Needs` is `—` needs nothing started. A missing env var is
`blocker: required-env-vars-missing` **before any test runs**.

**Build tore its services down at Stage 7 step 6**, so nothing is running by the
time commit starts. That is why this step exists; the old precondition here just
assumed an environment nobody had set up.

**2. Run each row's `Run it` command and record what it returned.** Per row, not
per suite — the map's unit of work is a scenario, and a per-row result is what the
coverage table in §5d.i reports. Then run the feature's coverage command at the
floor `qa/quality-gates.md § <repo>` declares.

**Use the map's command verbatim.** Not a reconstruction of it. The map was written
by the agent that wrote the test; if its command is wrong, that is a
<!-- governed-by: test-map-blocker-ids -->
`missing-test-case` finding, not something to work around.

**3. Fixtures and mock data are the ones build already created.** Do not generate
new test data, do not substitute a mock for a service the map says to start. The
`Fixtures` column names what each scenario uses; a fixture that is missing is a
`missing-fixture` finding.

**4. Tear down everything you started**, pass or fail, and log `stopped_at`.

**No map on Route A** is a Major finding — Stage 5-6 was supposed to write one —
and this stage falls back to the Required gates in `qa/quality-gates.md`, reporting
that it did so. On Route B there is no map by design; the verifier infers (§5a.i).

### 5a.00. Verify the test map against reality

> **Phase 5R.** Reading only — every check below is settled by opening files. Runs
> in parallel with Stage 4, before anything executes.

`<repo>/context/test-map/<feature-slug>.md` (written at `/dev:build` Stage 5-6)
claims a scenario → test → tier → fixture mapping. Check each claim:

| Check | Failure |
|---|---|
| the test file exists | `missing-test-file` |
| the named test exists in it | `missing-test-case` |
| the tier matches what the file declares | `tier-mismatch` |
| the named fixtures exist | `missing-fixture` |
| every changed source file appears somewhere in the map | `unmapped-change` |

**A map that claims coverage it does not have is worse than no map** — it is read
as evidence. Each failure is a `## Test verification` finding at Major.

No map at all on Route A is itself a Major: Stage 5-6 was supposed to write one.
On Route B there is none by design — the verifier infers instead (§5a.i).

### 5a.0. The test-verifier — what it adds over Stage 8c

> **Phase 5R.** The verifier's judgement — *does this assertion prove its row?* — is
> formed by reading the test, not by running it. A test that proves nothing proves
> nothing whether it is green or red, so this costs no execution and happens before
> 5X.

Build and Commit must not answer the same question with different authority.

| | `/dev:build` Stage 8c | this stage |
|---|---|---|
| Check | **mechanical** — does this file import `vi.mock` while declaring `tier: integration`? | **semantic** — does the assertion actually exercise the stated behaviour? |
| Catches | a tier claim contradicted by an import | a mock that is legal at its tier but returns a canned answer, making the assertion vacuous |
| Also | — | scenarios with no test at all; tests that assert on a fixture rather than on behaviour |

Build asks *"did we write tests?"*. Commit asks *"do those tests prove it?"*.
Stating the split this way is what stops the verifier re-implementing Stage 8c and
the two disagreeing.

It runs as its own fresh-context agent (`commit.md` §5a) via the
**`dev-test-verifier`** skill, and writes `findings.md § ## Test verification`.

**Statuses:** `PASS` · `FAIL` · `BLOCKED` · `SKIPPED` · `NOT AUTOMATED` ·
`INCONCLUSIVE`. **Only `PASS` counts as verified.**

### 5a.i. On Route B there are no ticket rows to re-verify

Route A runs each row of `status.md` § `## Acceptance`, built at `/dev:build`
Stage 8 from the ticket's AC/BR/TS/NFR and left at `⏳ pending` — **build writes the
tests, commit is the first and only thing that runs them.** **Route B has no ticket and no build**, so
there is nothing to re-verify. Do this instead:

1. **Infer the scenarios** from the review snapshot, bounded by `commit.md` §2a.8's
   five ASK triggers. Every row carries `source: inferred`, the diff hunk it came
   from, the behaviour inferred, and the test that covers it — or its absence.
2. **Run the tests that exist** for the changed paths.
3. **Report the gaps**: a changed file with no test is a row reading
   `not-verified`, named in the summary and the PR body. It is not a failure and it
   does not block — but it is never silent.

**No usable harness is `BLOCKED`, never a pass.** If `qa/quality-gates.md` has no
`## <repo>` section, or its section has no runnable commands, every row reads
`BLOCKED` with the reason. Do not bootstrap one — that is `/qa:setup`'s job, and
standing up a harness mid-commit would be a far larger change than the one under
review.

**Only `PASS` counts as verified.** `BLOCKED`, `SKIPPED`, `NOT AUTOMATED` and
`INCONCLUSIVE` are all honest outcomes; none of them is a pass.

### 5b. Re-verification loop

For every row in `status.md` § `## Acceptance`:

1. Read the `Verified by` column — the exact test spec + test id (e.g. `test/supplier/service.spec.ts::create rejects duplicate`)
2. Execute ONLY that test (framework-native filter: `pnpm test -t "create rejects duplicate"`, `pytest -k`, `go test -run`, `dotnet test --filter`, etc.)
3. Capture stdout + exit code
4. Set the `Commit-time verification` column to `✅ pass`, `❌ fail`, `⏸ deferred-to-e2e`, or `⚠ regression`

If step 2 fails to execute (test framework changed, spec renamed) → treat as `❌ fail` with `unrunnable: true` metadata.

---

### 5b.i. A red row that is not a defect — wherever it first went red

A row can be red because the code is wrong, or because the test is unreliable or
the harness is misconfigured. Those are different facts with different remedies,
and only the first belongs to the fix loop. Classify every red row per
`references/build/stage-7-test-execute.md` §7f.i before routing it. A `flaky` or
`harness-config` row is red, but the code is not wrong and the remedy is a human
`DEC-###` against the harness — which this stage may not apply.

**Two sources, one rule.**

| Where the row went red | |
|---|---|
| **Carried from a `PARTIAL_HARNESS` build** | `/dev:build` Stage 8 classified it and handed it over |
| **First seen here** — on the initial §5b run, or on any re-run inside the Stage 6 fix loop | classify it now, per §7f.i |

**The second case is the one that gets missed.** A timeout that appears in fix-loop
round 2 is the same kind of fact as one that appeared at build, and takes the same
verdict. Admitting it as a Blocker because it arrived late sends a config problem
into a loop that is forbidden to fix config — see §6a.ii of
`stage-6-fix-loop.md`, which refuses an unclassified row at the loop's entrance.

Re-run such a row once, exactly as §5b does, then:

| Re-run result | Column | Route |
|---|---|---|
| passes | `✅ pass` | normal — the flake did not reproduce |
| fails for the **same** carried reason | keep the carried `⚠ flaky` / `⚠ harness-config` verdict | **do not enter the fix loop** — carry the remedy to the PR body |
| fails for a **different** reason | `⚠ regression` | normal fix loop |

Routing a harness-config failure into the fix loop makes it attempt a code change for a config problem it is forbidden to fix — it burns its bounds and halts on a misleading escalation.

---

### 5c. Deferred-to-e2e resolution — closing a row, not deciding whether e2e runs

**E2E execution is decided in §5a.0a by what the snapshot touches.** This section
is only about *closing a `⏸ deferred-to-e2e` row*, which needs every sibling
sub-task to have landed before the cross-layer journey can be asserted end to end.

Conflating the two is what made a single-repo feature skip Playwright entirely:
nothing was deferred, so the last-sub-task test never fired, so e2e never ran.

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

Rewrite `units/<repo>/status.md § ## Acceptance` with the new column:

```markdown
| ID | Source | Description | Verified by | Build-time | Commit-time |
|----|--------|-------------|-------------|------------|-------------|
| AC-1 | acceptance-criteria.md#AC-1 | Supplier onboarding form validates tax_id | test/supplier/service.spec.ts::validates tax_id | ⏳ pending | ✅ pass |
| AC-2 | acceptance-criteria.md#AC-2 | Duplicate suppliers rejected with 409 | test/supplier/service.spec.ts::rejects duplicate | ⏳ pending | ❌ fail |
| BR-3 | business-rules.md#BR-3 | tax_id unique per country | test/db/supplier.migration.spec.ts | ⏳ pending | ✅ pass |
| NFR-1 | nfrs.md#perf | POST /supplier < 200ms p95 | perf/supplier.bench.ts | ⏸ deferred-to-e2e | ✅ pass |
| TS-4 | test-scenarios.md#TS-4 | 3-tab flow end-to-end | e2e/supplier.spec.ts | ⏸ deferred-to-e2e | ⏸ deferred-to-e2e (2 sub-tasks remaining) |
```

Preserve the build-time column. Add the commit-time column. Never delete or overwrite build-time evidence.

**What each column now means.** Build runs no tests, so **build-time is a readiness
state, not a result**: `⏳ pending` says the assertion has a test, the test declares a
tier it does not contradict, and the map can run it. **Commit-time is the only column
carrying a result.**

A build-time cell is therefore never `✅ pass`. If one is, it came from a
`--tests-only` or `--vulnerable` run (§7a1), which execute because they are terminal —
and those runs never reach this stage.

**A `⏳ pending` that is still pending after this stage is a bug in this stage**, not a
deferral. Every row build left pending must leave here with a real result or an
explicit `⏸ deferred-to-e2e`.

---

### 5d.i. Show which scenarios are covered, and which passed

**Print this. It is the answer to "is this tested?" and nobody should have to open
a file to get it.** One row per scenario in the map, with the result this run
actually produced.

```
Test validation · Holiday calendar management · snapshot 0f50921291d9

  Kind  ID     Scenario                                  Tier         Result
  AC    AC-1   Adding a holiday on a free date succeeds  integration  ✅ pass
  AC    AC-2   A date already held refuses distinctly    integration  ✅ pass
  AC    AC-3   Removing a holiday frees the date         integration  ❌ FAIL
  BR    BR-1   One holiday per date, active rows only    unit         ✅ pass
  TS    TS-4   Full add → list → remove journey           e2e          ✅ pass
  NFR   NFR-2  Renders under 200ms on 3 years of data    —            ⏸ not automated

  Covered     5 of 6 scenarios have a test
  Passed      4 of 5 executed
  Failed      1  → AC-3, routed to build for repair
  Coverage    72.4% lines (floor 70)
  Services    backend @8080 healthy · real-db healthy · torn down

  Not covered by any test:
    AC-4  Bulk import rejects a malformed row   — no test in the map
```

Four rules for that block:

- **Every scenario in the map gets a row**, including the ones that did not run.
  A scenario silently absent is the thing this table exists to prevent.
- **`Covered` and `Passed` are different numbers.** Five of six having a test and
  four of five passing are two distinct facts, and collapsing them into one
  percentage hides whichever one is bad.
- **`Not covered` is listed by name**, never as a count. A gap you cannot name is a
  gap nobody will close.
- **Only `✅ pass` counts as verified.** `BLOCKED`, `SKIPPED`, `NOT AUTOMATED` and
  `INCONCLUSIVE` are honest results and none of them is a pass.

The same table goes into `units/<repo>/pr-summary.md`, so the reviewer sees what
the committer saw.

### 5e. Route to fix loop or advance

**From 5R** — findings only; no row changes verdict, because nothing has run. Every
`## Test verification` finding joins Stage 4's into the single repair pass. 5R never
advances to Stage 7 on its own, and never triggers 5X directly: Stage 6 does, once
both reviewers are clean.

**From 5X:**

**Every row `✅ pass` or acceptably `⏸ deferred-to-e2e`** → mark Stage 5 done. Advance to Stage 7 (semantic merge).

**One or more `⚠ regression` or `❌ fail`** → classify per §5b.i first, then invoke the fix loop per `stage-6-fix-loop.md` §6a.i (v2.3.27) for the rows that classified `defect`. The fix loop is **MANDATORY and VERIFIABLE** — this stage MUST invoke `dev-stack-adaptive-implementation` in fix-mode via the Skill / Agent tool and record a `stage-5.fix_loop_invocation:` block in `status.md` § `## Run history` (fields per §6a.i). Applying the fix inline without recording the invocation trace is a spec violation and Stage 8 §8a will refuse to push.

**What re-runs after that repair — not the whole stage.** The repair is scoped to
`allowed_files`; re-executing all of 5X would run the map a second time to re-learn
rows no repair could have touched.

| | Re-runs |
|---|---|
| the failed rows | always |
| the suite gate, twice (§5b) | always — the recorded green must reflect the final code |
| other map rows | no — the §6e exit check covers them |
| Stage 4 | only if the repair touched a file it reviewed (`stage-6-fix-loop.md` §6d.i) |
| 5R | only if the repair added a test or changed the map |

---

### 5f. Progress log

Append to `units/<repo>/status.md § ## Run history`:

**This block is the canonical record. Stage 8 §8a gates on it**, so a field named
here and not written is a halt on every run; a field written elsewhere in this
file and absent here does not exist as far as the gate is concerned.

**Both phases are recorded.** Stage 8 §8a gates on `phase_execute.executed` specifically,
because 5R alone settles no row — a run that reviewed, repaired and advanced would
otherwise present an Acceptance table of claims nothing executed.

```yaml
stage-5:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  snapshot_sha: 0f50921291d9            # the scope these results cite

  phase_review:                             # the read — parallel with Stage 4
    finished_at: <ISO>
    snapshot_sha: 0f50921291d9
    findings: {blocker: 0, major: 0, minor: 2, nit: 1}
    executions: 0                       # ALWAYS zero. Non-zero is a spec violation

  phase_execute:                             # the single execution
    executed: true                      # Stage 8 HALTS on false or missing
    started_at: <ISO>
    finished_at: <ISO>
    snapshot_sha: 0f50921291d9          # post-repair; must equal 5R's by exit (§8a)
    full_map_runs: 1                    # 1 on a healthy run; each extra is a
                                        # repair that landed after the execution
    rescoped_runs: 0                    # §6d.i re-runs: failed rows + suite gate

  # what actually executed - Stage 8 refuses to push without this
  external_services_started:
    - {name: backend, port: 8080, env_vars_verified: [DATABASE_URL], status: healthy, stopped_at: <ISO>}
    - {name: real-db, port: 5433, status: healthy, stopped_at: <ISO>}
  gates_run:
    - {id: AC-1,  command: 'npm test -- tests/holidays/create.spec.ts -t "adds"', result: PASS}
    - {id: TS-4,  command: 'npm run test:e2e -- --grep "holiday"',                result: PASS}
    - {id: QG-002, check: coverage, command: npm run coverage, result: PASS, threshold: 70}
  gates_skipped:
    - {id: QG-00X, reason: no row in the test map requires it}

  # coverage, as reported in 5d.i
  scenarios_in_map: 6
  scenarios_with_a_test: 5
  scenarios_executed: 5
  scenarios_passed: 4
  scenarios_uncovered: [AC-4]

  # row outcomes - BOTH names, Stage 8 reads both
  rows_total: 12
  rows_pass_commit_time: 8
  rows_deferred_to_e2e: 3
  rows_regressed: 1                     # a row that passed at build and fails now
  rows_failed: 0                        # a row that fails and did not pass at build
  rows_fixed_in_loop: 1
  fix_loop_invocation:                  # REQUIRED when rows_regressed or rows_failed was > 0
    invoked_at: <ISO>
    invocation: <subagent id | "inline">
    origin_findings: [AC-3]
    exit_state: CLEAN

  e2e_run_this_task: true
  e2e_reason: the test map has an e2e row for this feature
  parent_last_subtask: false
  acceptance_map: units/<repo>/status.md § ## Acceptance
```

`rows_regressed` and `rows_failed` are **different questions** and Stage 8 reads
both: a regression passed at build and fails now (something changed under it);
a failure never passed (the build advanced carrying it). Collapsing them loses
which of those happened.

---

### 5g. Skills / agents invoked

- No skill invocation — inline test-execution logic (same runners as `/dev:build` Stage 7)
- Reuses stack-detection from `units/<repo>/status.md § ## Run history` for the correct test-runner command

---

### 5h. On `--resume`

If `--resume` finds `stage-5.status: DONE` AND no new commits since `finished_at`, skip. Otherwise re-run the whole verification loop — regression could have been introduced by any post-Stage-5 edit.

---

### 5i. Never

- Never mark a row `✅ pass` without actually running the test
- Never assume the build-time result still holds (that's the entire reason this stage exists)
- Never remove a deferred-to-e2e row's deferral without checking parent's sub-task count
- Never write a row you can't verify — better to halt than to fake evidence
