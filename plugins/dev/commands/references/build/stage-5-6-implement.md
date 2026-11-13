## Stages 5 + 6 — Implementation + Test Writing

**Purpose.** Write feature code AND its tests for every ordered step in `implementation.md`. Combined into one document because in practice both happen interleaved — code first, tests immediately after, per step.

**Runs after Stage 4 (QA gate) succeeds.** status `agentExecuting` · phase `planning` → `implementing`

**On completion:** every dev-plan step has code + tests written; ready for Stage 7 execution.

---

### 5-6a0. `--tests-only` — run the test half against existing code

Under `--tests-only` the implementation half does not run. There is no `implementation.md` build sequence to follow because the code is already written; the source on disk is the input instead.

**What replaces the build sequence.** Enumerate the units in scope — the path/module given, the ticket's touched files, or the whole repo ranked by risk. For each, derive its concern class the same way a build step would, against **the full table in `dev-stack-adaptive-implementation`** — all of it, not a remembered subset. A route or handler is an operation contract; a consumer, job or webhook is idempotency/retry; an entity with a status field that moves between values is lifecycle; a refusal path (400/403/404/409/500) is its own class and is the one most often missed when reading code rather than a plan. Then intersect with the Required tiers exactly as normal and write a test at every tier in the intersection.

**Ranking.** Business logic and branch-heavy code first; boundaries and error paths before happy paths; getters, DTOs and generated code last. A file already at full branch coverage is skipped and reported as such.

**Re-run safety — a second pass must converge, not duplicate.** Full branch coverage is the only skip condition, which is not enough on its own: a partially-covered unit would be enumerated again and re-authored, so running tests-only twice on the same repo produces overlapping tests.

*Stamp what you write.* Every file generated here carries a header naming the run and the unit it covers:

```
// generated-by: dev:build --tests-only
// run-id: TO-2026-10-01-1432
// covers: src/services/payment.js
// tier: integration
// requires: backend-running, real-db
```

**Rule 7.ii applies here in full.** Stage 7b.i starts external services by reading each test's `# tier:` and `# requires:` header — a file written without them gets no backend, no database and no dev server, and then runs green against nothing. Writing them is not optional for an `integration`, `contract`, `concurrency` or `e2e` test.

*Read the stamps before enumerating.* Then per unit:

| Unit state | Action |
|---|---|
| Full branch coverage | skip; report as already covered |
| Covered by a **stamped** test from an earlier run | **extend only the uncovered branches** — never re-author the file |
| Covered by a **hand-written** test | leave it alone; add only at tiers it does not cover |
| Uncovered | write as normal |

*Record the manifest.* List every generated file in `units/<repo>/status.md § ## Run history` under `tests_only_generated:` with its run id, so the next run reads a manifest rather than inferring intent from filenames.

The hand-written case matters most: a developer's test is never re-authored or replaced, only supplemented at tiers it does not reach.

**Hard limits — these are what make the flag safe:**

- **Never edit a source file.** Not to add a seam, not to make something injectable, not to fix a bug the test exposes. A failing test over real behaviour is a *finding*: record it and keep the test. Changing product code here would silently turn a test-writing run into an unreviewed refactor.
- **Never delete, disable, skip or loosen an existing test** — including one that was already failing. Report it; leave it.
- Where a unit cannot be tested without a seam that does not exist, write the highest tier that *is* reachable, and record `not-verified` with the reason rather than forcing it.

**Then continue unchanged** into Stage 7 (verify the map — it runs nothing) and Stage 8 (`## Acceptance` table, every row `⏳ pending`). Where a task ref was given, its Acceptance Criteria or Expected Result supply the map's rows; without one, rows come from the observable behaviour asserted, and anything that cannot be settled reads `not-verified`.

---

### 5-6a. Preconditions

- `units/<repo>/status.md § ## Run history` `stage-4.status` is **`DONE` or `SKIPPED`**
- `qa/quality-gates.md` has `harness_status: Active` — **required only when `stage-4.status: DONE`**

  **`SKIPPED` is a valid state to enter this stage in, and must not be treated as a missing precondition.** `--skip-qa` short-circuits Stage 4 at §4a0, which records `status: SKIPPED` and `qa_gate_state: skipped-by-user` and never bootstraps a harness — so demanding `DONE` plus an `Active` gate here halts the one flow Stage 4 deliberately sent us. Under `SKIPPED`, write no tests and let Stage 8 mark every acceptance row `verified: manually`.
- Detected stack recorded in `units/<repo>/status.md § ## Run history` (from Stage 4's qa-greenfield-harness OR from an explicit stack-detection pass here)
- Branch is checked out and clean (`git status` clean in the target repo)
- Every `PB-###` blocker (if any) is `RESOLVED` per `units/<repo>/plan-blockers.md`

Missing → halt cleanly and route to the appropriate remediation.

---

### 5-6b. Delegate to `dev-stack-adaptive-implementation` skill

Invoke the **`dev-stack-adaptive-implementation`** skill (see `plugins/dev/skills/dev-stack-adaptive-implementation/SKILL.md`).

**What the skill does (three phases, per its own spec):**

- **Phase 1** — Stack detection (if not already done in Stage 4). Reads `references/stack-detection.md` and records to `units/<repo>/status.md § ## Run history` `detected_stack:` block.
- **Phase 2** — Pattern inference. Reads ≤ 10 existing files per `references/pattern-inference.md` to establish the 8 conventions the repo uses (folder structure, imports, error handling, DI, config, logging, testing, naming). Records to `units/<repo>/status.md § ## Run history` `inferred_patterns:` block.
- **Phase 3** — Code + test writing. For each ordered step in `implementation.md`:
  1. Read the TL unit files this step references (endpoints, entities, pages)
  2. Write the code idiomatically per Phase 2's inferred patterns
  3. Write the tests immediately per `references/test-patterns.md`
  4. Hold each step's material technical choices in memory as a pending `DEC-###`

  **Write the decision log once, at the end of Phase 3** — append every pending `DEC-###` to `shared-context/decision-log.md` in step order, in one edit. A write per step interrupts the repo mental state this phase depends on, and the log reads the same either way. A halt mid-phase writes what it has before it exits.

**All runs in the dev-agent's own context.** Repo mental state (file tree, existing patterns, in-progress edits) must persist across many reads and writes — subagent delegation would lose that.

---

### 5-6b.i. Write the test map — in the repo, as the tests are written

`.jetrix/` is **entirely gitignored**, so `status.md § ## Acceptance` exists only on
the machine that ran the build. A teammate who clones the repo sees none of it, and
the PR body is a snapshot frozen at PR time. The thing a person opens to ask *"is
this tested?"* has to travel with the code.

Split by how often it changes:

| | Lives | Changes | Committed |
|---|---|---|---|
| **The map** — scenario → test → tier → fixtures | `<repo>/context/test-map/<feature-slug>.md` | only when tests change | **yes** |
| **The results** — pass/fail/flaky, per run | `units/<repo>/status.md § ## Acceptance` | every run | no |

Same Model B split the code-context graph uses: durable structure in the repo,
per-run state in `.jetrix/`. Committing results would churn the repo on every build
and make the diff unreadable.

```markdown
<!-- <repo>/context/test-map/holiday-calendar-management.md -->
---
doc_type: test-map
feature_id: FEAT-HCAL-01
produced_by: dev
generated_at: 2026-11-04
---

# Test map — Holiday calendar management

Every row is runnable on its own. Copy the command.

| Kind | ID | Scenario | Tier | Test | Run it | Needs | Fixtures |
|---|---|---|---|---|---|---|---|
| AC | AC-1 | Adding a holiday on a free date succeeds | integration | `tests/holidays/create.spec.ts::adds` | `npm test -- tests/holidays/create.spec.ts -t "adds"` | `real-db` | `holidayFactory`, `seedCalendar` |
| AC | AC-2 | A date already held refuses with a distinct message | integration | `tests/holidays/create.spec.ts::duplicate` | `npm test -- tests/holidays/create.spec.ts -t "duplicate"` | `real-db` | `holidayFactory` |
| BR | BR-1 | One holiday per date, active rows only | unit | `tests/holidays/rules.spec.ts::uniqueness` | `npm test -- tests/holidays/rules.spec.ts -t "uniqueness"` | — | — |
| TS | TS-4 | Full add → list → remove journey | e2e | `tests/e2e/holiday.spec.ts` | `npm run test:e2e -- --grep "holiday"` | `backend-running`, `frontend-running` | `seedCalendar` |

## Run everything for this feature

```bash
npm test -- tests/holidays            # unit + integration
npm run test:e2e -- --grep "holiday"  # browser journeys
npm run coverage                      # floor: 70% lines
```

## Mock data and fixtures

| Fixture | Lives | Gives you |
|---|---|---|
| `holidayFactory` | `tests/support/factories/holiday.ts` | a valid holiday; override any field |
| `seedCalendar` | `tests/holidays/fixtures/seedCalendar.ts` | three years of holidays for the e2e journey |

## Not automated
| ID | Scenario | Why | How to check by hand |
|---|---|---|---|
| NFR-2 | Calendar renders under 200ms on a 3-year dataset | needs production-scale data | runbook in the PR summary |
```

**The `Run it` column is the point of the document.** A map that names a test
but not how to run it makes the reader reconstruct the invocation — the runner,
the path syntax, the name-filter flag — which differs per stack and is exactly
the thing they came here to avoid. **A human or an agent copies one cell and
runs one scenario.**

**`Needs` is what `/dev:commit` reads to decide what to start.** `real-db`,
`backend-running`, `frontend-running`, `real-auth`, or `—` for a test that needs
nothing. These are the tokens `stage-7-test-execute.md` §7b.i knows how to start;
anything else is not startable and will halt there.
Build knows this because build wrote the test; commit must not have to infer it.


**Write it as each test is written, not afterwards.** A map composed at the end is
a summary of what happened; one written alongside is the thing that makes a missing
scenario visible while there is still time to write it.

It lands in the diff, so it is reviewed like any other file. `/dev:commit` Stage 5
verifies it against the tests that actually exist.

The `## Not automated` block is where `NOT AUTOMATED` and `INCONCLUSIVE` scenarios
get a home instead of vanishing into a status value nobody reads.

### 5-6b.iii. Point `CLAUDE.md` at the map

The map is only useful if the next reader finds it without being told. Add this
to the repo's `CLAUDE.md` once, under its testing section — idempotent, never
duplicated:

```markdown
## Tests

Coverage per feature lives in `context/test-map/<feature-slug>.md`. Each row is a
scenario with the exact command to run it on its own, what it needs running, and
which fixtures it uses. Read the map before writing a new test — the fixture you
need probably exists.
```

**Why `CLAUDE.md` and not only the map:** `CLAUDE.md` is what an agent reads on
entering the repo. A map nobody is pointed at is a map nobody opens, and the next
agent writes a second `holidayFactory`.

### 5-6b.ii. Fixtures — two owners, three rules

| Scope | Owner | Lives |
|---|---|---|
| **Harness-level** — factories, builders, test DB/container setup, shared mocks | `/qa:setup`, recorded in `quality-gates.md § <repo> → ## Conventions` | the repo's own test tree |
| **Feature-level** — what this feature's tests need | this stage | beside those tests |

1. **Reuse before creating.** Read `## Conventions` first. A second factory for an
   entity that already has one is a code-review Major (Dimension 7, reuse).
2. **Every fixture a scenario depends on is named in the test map** — that is the
   `Fixtures` column. A fixture nobody can trace to a scenario is dead weight; a
   scenario whose fixture is missing is why a test passes against nothing.
3. **A fixture that mocks the behaviour under test is a finding, not a fixture.**
   Stage 8c catches the mechanical case (`vi.mock` at `tier: integration`); the
   commit test-verifier catches the case where the mock is legal at that tier but
   returns a canned answer that makes the assertion vacuous.

### 5-6c. Per-step completion tracking

For each dev-plan step, append to `units/<repo>/status.md § ## Run history`:

```yaml
step_1:
  from_plan:       "Add migration for supplier table + composite (tax_id, country) unique index"
  status:          DONE                            # RUNNING | DONE | BLOCKED
  files_written:
    - src/db/migrations/20260831142400_add_supplier_table.ts    # +42 lines
    - src/db/migrations/20260831142400_add_supplier_table.spec.ts  # +28 lines
  tests_written:
    - migrations.spec.ts::supplier-table-and-index               # asserts on BR-1, AC-B2 (schema level)
  dec_logged:      [DEC-101, DEC-102]
  started_at:      2026-08-31T14:23:15Z
  finished_at:     2026-08-31T14:24:47Z

step_2:
  from_plan:       "..."
  ...
```

Every step must land at `status: DONE` for Stage 5-6 to be complete. `BLOCKED` on a step routes to Stage 8's repair loop preemptively (see §5-6f below).

---

### 5-6d. Scope discipline

**The dev-plan lists every file to touch.** Touching a file NOT in the plan requires a scope escalation:

- Write `units/<repo>/status.md § ## Run history (a BLOCKED entry)` naming the file, why it needs to be touched, and how it changes the plan
- Halt Stage 5-6 (do NOT silently touch the file)
- State: `agentExecuting → BLOCKED`

Exception: **routine imports and module registrations** (e.g. registering a new module in `AppModule` for NestJS, registering a URL in Django's `urls.py`, adding a new file to `sys.modules` in Python) are NOT scope escalations — they're the framework's plumbing for the new code. The plan should mention them; if it doesn't, do them anyway but log a `DEC-###`.

---

### 5-6e. Rules the skill enforces (12 hard rules, see the skill's SKILL.md)

The full rule set lives in `dev-stack-adaptive-implementation/SKILL.md`. Summary:

1. Read before writing (Phase 2 pattern inference)
2. Reuse over parallel abstractions
3. Match error handling
4. Match config style
5. Match test framework (from `qa/quality-gates.md`)
6. No framework leakage in identifiers or comments
7. Every dev-plan step gets tests
8. Tests assert on behaviour, not on hardcoded responses
9. Honour `DEC-###` from `plan-blockers.md`
10. No secrets in code or tests
11. Stay in scope (§5-6d)
12. Log every material technical choice as `DEC-###`

Enforced at Phase 3 write time. Violations invalidate the step; the skill halts and asks for re-run.

---

### 5-6f. Preemptive blocking (if the plan is decidable but the code isn't buildable)

If, during Phase 3, the skill hits a step where:
- The dev-plan says "call `POST /compliance/dedupe`"
- The target repo has NO HTTP client library and no config for making external calls
- Adding one would require adding a dependency, which requires updating `technology-stack.md`, which…

→ Halt the step. Write `units/<repo>/status.md § ## Run history (a BLOCKED entry)` framing this as *"the plan says do X but the codebase requires Y first, which the plan didn't provision."* Route back to `/dev:plan --resume` — this is a case the plan-blocker system should have caught but didn't (v2.3 could add a "missing infrastructure" blocker category).

For v2.2: escalate cleanly. `/dev:build` doesn't invent new dependencies mid-run.

---

### 5-6g. Progress log format (Stage-level)

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-5-6:
  status: DONE                          # DONE | BLOCKED
  started_at: 2026-08-31T14:23:14Z
  phases:
    stack_detection:   DONE
    pattern_inference: DONE
    code_and_tests:    DONE
  steps_from_plan:   12
  steps_completed:   12
  files_written:     18
  tests_written:     34
  decs_logged:       23
  finished_at:       2026-08-31T15:07:22Z
```

---

### 5-6h. On `--resume`

If `--resume` finds `stage-5-6.status: DONE`, skip Stages 5-6 entirely.

If `stage-5-6.status: RUNNING` (partial completion, e.g. previous run crashed):
- Read `units/<repo>/status.md § ## Run history` — find the last `step_N: status: RUNNING` or `BLOCKED`
- Resume from that step (skip completed ones)
- Re-run the skill's Phase 3 loop from the resume point

---

### Skills / agents invoked

- **`dev-stack-adaptive-implementation` skill** — the primary work of Stages 5-6
- No subagents (Phase 3's repo mental state must persist across many operations)

Never invoke `dev-stack-adaptive-code-review` from Stages 5-6 — that's `/dev:commit` Stage 4.
