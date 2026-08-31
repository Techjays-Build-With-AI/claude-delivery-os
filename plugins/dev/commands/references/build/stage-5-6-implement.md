## Stages 5 + 6 — Implementation + Test Writing

**Purpose.** Write feature code AND its tests for every ordered step in `implementation.md`. Combined into one document because in practice both happen interleaved — code first, tests immediately after, per step.

**Runs after Stage 4 (QA gate) succeeds.** State: `IN_PLANNING → IN_DEVELOPMENT`. MC: `inProgress` (unchanged).

**On completion:** every dev-plan step has code + tests written; ready for Stage 7 execution.

---

### 5-6a. Preconditions

- `dev/build-run.md` `stage-4.status: DONE`
- `qa/quality-gates.md` has `harness_status: Active`
- Detected stack recorded in `dev/implementation-log.md` (from Stage 4's qa-greenfield-harness OR from an explicit stack-detection pass here)
- Branch is checked out and clean (`git status` clean in the target repo)
- Every `PB-###` blocker (if any) is `RESOLVED` per `dev/plan-blockers.md`

Missing → halt cleanly and route to the appropriate remediation.

---

### 5-6b. Delegate to `dev-stack-adaptive-implementation` skill

Invoke the **`dev-stack-adaptive-implementation`** skill (see `plugins/dev/skills/dev-stack-adaptive-implementation/SKILL.md`).

**What the skill does (three phases, per its own spec):**

- **Phase 1** — Stack detection (if not already done in Stage 4). Reads `references/stack-detection.md` and records to `dev/implementation-log.md` `detected_stack:` block.
- **Phase 2** — Pattern inference. Reads ≤ 10 existing files per `references/pattern-inference.md` to establish the 8 conventions the repo uses (folder structure, imports, error handling, DI, config, logging, testing, naming). Records to `dev/implementation-log.md` `inferred_patterns:` block.
- **Phase 3** — Code + test writing. For each ordered step in `implementation.md`:
  1. Read the TL unit files this step references (endpoints, entities, pages)
  2. Write the code idiomatically per Phase 2's inferred patterns
  3. Write the tests immediately per `references/test-patterns.md`
  4. Log each step + material technical choices as `DEC-###` in `shared-context/decision-log.md`

**All runs in the dev-agent's own context.** Repo mental state (file tree, existing patterns, in-progress edits) must persist across many reads and writes — subagent delegation would lose that.

---

### 5-6c. Per-step completion tracking

For each dev-plan step, append to `dev/implementation-log.md`:

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

- Write `dev/escalation-<n>.md` naming the file, why it needs to be touched, and how it changes the plan
- Halt Stage 5-6 (do NOT silently touch the file)
- State: `IN_DEVELOPMENT → BLOCKED`

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

→ Halt the step. Write `dev/escalation-<n>.md` framing this as *"the plan says do X but the codebase requires Y first, which the plan didn't provision."* Route back to `/dev:plan --resume` — this is a case the plan-blocker system should have caught but didn't (v2.3 could add a "missing infrastructure" blocker category).

For v2.2: escalate cleanly. `/dev:build` doesn't invent new dependencies mid-run.

---

### 5-6g. Progress log format (Stage-level)

Append to `dev/build-run.md`:

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
- Read `dev/implementation-log.md` — find the last `step_N: status: RUNNING` or `BLOCKED`
- Resume from that step (skip completed ones)
- Re-run the skill's Phase 3 loop from the resume point

---

### Skills / agents invoked

- **`dev-stack-adaptive-implementation` skill** — the primary work of Stages 5-6
- No subagents (Phase 3's repo mental state must persist across many operations)

Never invoke `security-review` from Stages 5-6 — that's Stage 9. Never invoke `dev-stack-adaptive-code-review` — that's `/dev:commit` Stage 4.
