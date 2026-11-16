## Stage 6 — Bounded fix loop

**Purpose.** When Stage 4, 5R or 5X surfaces blocking findings, delegate fixes to `dev-stack-adaptive-implementation` in **fix-mode**, then re-run what the repair could have affected. Bounded per finding + per whole-stage re-run — never spin forever.

<!-- rule: fix-loop-rerun-scope
     phrases: "re-run every upstream stage" | "computed from the repair's actual diff" -->

**What re-runs is computed from the repair's diff, never assumed total** — §6d.i is
the rule, §6e applies it either side of the single execution. This sentence used to
say *"re-run every upstream stage"*, which §6d.i twenty lines below already
contradicted; the broad reading won at runtime and cost a full test map after every
repair.

**Invoked by:** Stages 4 (code review) and 5 (acceptance regression). NOT a standalone stage. Each entry into Stage 6 targets a specific set of findings.

**On completion:** every finding that entered the loop is either resolved (fixed) or escalated (bounds exceeded → `units/<repo>/status.md § ## Run history (a BLOCKED entry)` + halt).

---

### 6a. Preconditions

- Stage 4 or Stage 5 produced findings that block at commit-time threshold
- The findings file (`units/<repo>/findings.md` § `## Code review`, `status.md` § `## Acceptance`) has been written and is readable
- Stack + inferred patterns are still available in `units/<repo>/status.md § ## Run history`

### 6a.i. Non-skippable execution (v2.3.27 — closes the "findings surfaced but agent didn't invoke fix loop" gap)

**Whenever Stage 4 or Stage 5 produces one or more BLOCKING findings, the origin stage MUST invoke the fix loop in this file via the Skill / Agent tool (delegating to `dev-stack-adaptive-implementation` in fix-mode). Internal reasoning that "the finding is small, I'll just fix it inline" or "the agent will pick it up later" is NOT sufficient evidence of execution — the skill's own invocation log is the evidence. Skip = spec violation.**

Same class of "spec exists but subagent doesn't execute it" bug as v2.3.21 (compose mechanical fix pass) and v2.3.25 (Stage 7 semantic merge). Findings surface, the agent reports them, and the agent moves to Stage 8 push without invoking Stage 6. Push then lands broken code because the review said "block" and nobody acted on it.

Every entry into Stage 6 — even trivial ones with a single Critical finding — records an invocation trace in `status.md` § `## Run history`. Recording format (Stage 8 §8a's precondition check reads this):

```yaml
stage-4: # or stage-5 depending on origin
  status: DONE
  findings:
    critical: 0 # after fix loop; must be zero to advance
    high: 0 # after fix loop; must be zero to advance
    medium: 1 # non-blocking
    low: 1
  fix_loop_invocation: # REQUIRED whenever ANY finding at ANY severity was > 0 BEFORE the loop ran
    # — blocking (critical/high/blocker/major/regression) drives §6c;
    # non-blocking (medium/low/minor/nit) drives §6e.i's rounds. Both are recorded here
    invoked_at: <ISO> # required — presence proves invocation
    invocation:
      <subagent id | "inline"> # required — an id when the skill ran as a subagent,
      # the literal "inline" when the Skill tool returned none.
      # Never blank, never invented
    origin_findings: [SR-C-001, SR-C-004] # what fed the loop
    fix_attempts: # copy of §6c per-finding outcomes
      - finding: SR-C-001
        attempts_used: 1
        resolved: true
        self_check: clean          # REQUIRED -- §6c step 5, the repair agent's own
                                   # read of its diff against the nine dimensions.
                                   # `clean`, or the dimension it flagged on itself.
                                   # Absent => Stage 8 HALTS: an instruction with no
                                   # trace is one nothing can tell was followed
      - finding: SR-C-004
        attempts_used: 2
        resolved: true
        self_check: clean
    broad_reruns_used: 1
    nonblocking_rounds: # REQUIRED when any medium/low/minor/nit finding existed (§6e.i)
      rounds_used: 1 # 1 or 2; 0 is only valid when there were none
      findings: # EVERY non-blocking finding, with its individual re-check
        - finding: CR-M-001
          round: 1
          reverified: true # the targeted re-check passed — this is what permits `fixed`
          disposition: fixed
        - finding: CR-M-002
          round: 2
          reverified: false
          disposition: escalated # bound reached — never silently `deferred`
          reason: "fix requires removing the legacy export; scope decision"
      cascade_rerun: true # the single re-run after the rounds (§6e)
      ran_before_5x:
        true # true = the rounds landed before the execution,
        # so the fixes were covered by it rather than
        # costing a second one
    exit_state: CLEAN | ESCALATED
    escalation_file: null | units/<repo>/status.md § ## Run history (a BLOCKED entry)
```

If a stage completes with BLOCKING findings resolved but no `fix_loop_invocation:` block written → Stage 8 refuses to push (see stage-8-9-push-pr.md §8a). No workaround. No "I checked and applied the fix inline" bypass.

**Zero-finding runs skip Stage 6 entirely and do NOT record `fix_loop_invocation:`.** The absence of the block on a stage that had zero blocking findings is fine and Stage 8 accepts it. The gate is: findings.blocking > 0 IMPLIES fix_loop_invocation MUST be present.

### 6a.ii. A red test row is classified before it may become a finding

**No red row enters this loop unclassified.** Run
`references/build/stage-7-test-execute.md` §7f.i over it first and route on the
verdict:

| Verdict                    | Goes to                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------- |
| `defect`                   | this loop                                                                             |
| `flaky` · `harness-config` | the PR body — `stage-5-acceptance.md` §5b.i, which says **do not enter the fix loop** |

§7f.i opens with the reason: _"A failing gate is not automatically a code defect,
and treating it as one burns the repair budget on a test that is correct."_

**The classifier applies wherever the row first went red** — carried over from
build, or first seen on a re-run inside this loop. `stage-5-acceptance.md` §5b.i
used to read as though only a `PARTIAL_HARNESS` handover reached it; a timeout
discovered in round 2 is the same kind of fact as one discovered in round 1, and
gets the same verdict.

A real case: a lazy-route cold import exceeding a `findBy` timeout is
`harness-config` by §7f.i's own wording — _a timeout at the tool default under
instrumentation_. Admitted as a Blocker instead, it consumed a whole round and
drew an invented "three sequential runs green" requirement that exists in no
spec file.

---

### 6b. Bounds

| Origin stage                                 | Focused fix attempts per finding           | Broad re-runs of the whole stage     |
| -------------------------------------------- | ------------------------------------------ | ------------------------------------ |
| Stage 4 (code review)                        | 3 per finding                              | 1 (whole review re-scan)             |
| Stage 5 (acceptance regression)              | 3 per failing row                          | 2 (whole acceptance re-verification) |
| Non-blocking findings (Medium/Low/Minor/Nit) | batched per round, re-verified per finding | 2 rounds, then 1 cascade (§6e.i)     |
| **The loop as a whole, any origin**          | —                                          | **2 re-entries** (§6e steps 2 and 4) |

A "focused fix attempt" = one delegation to `dev-stack-adaptive-implementation` in fix-mode scoped to the finding, plus one localized re-verify of that finding.

A "broad re-run" = full re-execution of the originating stage over the current branch state.

A "re-entry" = Stage 6 entered again carrying findings a cascade re-run surfaced (§6e steps 2 and 4).
Every other bound here is per finding or per stage, so a finding first seen on a re-run arrives with a
full budget of its own and nothing counts how often that happens: a repair whose own code draws the
next finding can circle while every individual bound is still respected. Record `reentries_used` (§6g)
and escalate the third per §6f. **Escalation is a halt for a human, never a disposition** — no finding
becomes `deferred` by reaching this ceiling (§6e.i).

---

### 6b.i. Freeze the tests that failed — after 5X, and only those

**The freeze exists to stop one move: a test goes red, and the repair edits the
test instead of the code.** It therefore applies only where a test has gone red,
which is only after 5X has run.

| Phase                                | `deny.write_paths`                                                                                                                                                                           |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pre-5X** — origin is Stage 4 or 5R | **empty.** Nothing has run, so nothing is red, so there is no failure to cheat on                                                                                                            |
| **post-5X** — origin is 5X           | the specific test files whose rows failed. Set before the first fix-mode invocation on this run's `.jetrix/cache/session.json` row; the guard hook then refuses an `Edit` or `Write` to them |

**Not the whole test directory.** §6b.iv requires every repair to add a regression
test, and 5R's findings are _about the tests_ — a scenario with no test at all, an
assertion that mocks away its own subject. Freezing the directory would refuse the
exact writes those findings ask for. Freeze the files that failed; leave the rest
writable.

**A failing test is fixed in the code, never in the test.** That rule already
exists in prose here and in `--tests-only`'s hard limits; the freeze makes it a
refusal instead of a hope. A test that is genuinely wrong is an escalation —
record it and halt, do not edit it.

**Writing a missing test is not editing a failing one.** A 5R finding that says
_AC-5 has no test_ is closed by writing that test, and often by building the
behaviour it turns out nobody implemented. That is the repair, not a way around
the rule above.

**Empty `deny.write_paths` on every exit from the loop**, including the
bounds-exceeded escalation in §6f. A frozen path left frozen blocks the human
who was just asked to fix it by hand.

### 6b.ii. One repair agent at a time, and a new one each round

|                               |                                                                                                                                                                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Serial per repository**     | two repair agents in one working tree overwrite each other, and a fix in one can invalidate the other's premise. Never parallel, even for findings that look orthogonal                                                         |
| **A fresh agent per round**   | round N+1 gets a new agent with only the finding and `allowed_files`. Reusing the agent carries round N's rationalisation — _"I already looked at this and it seemed fine"_ — into the round that was supposed to re-examine it |
| **Scoped to `allowed_files`** | the finding's file plus its test. A repair that needs a file outside that set is a scope escalation, not a wider edit                                                                                                           |

The repair agent is a **writer**. The reviewers are readers and run in parallel
(`commit.md` §5a); this is the other half of that rule.

### 6b.iii. A reviewer that returns no verdict gets exactly one retry

A reviewer agent can die, time out, or return without a usable verdict. That is
not a finding and not a defect, so neither the fix loop nor a halt is right.

**Re-dispatch the same reviewer once, with the same inputs**, and record
`retry: 1`. A second failure is `blocker: reviewer-no-verdict` — halt that unit,
name the reviewer, and let siblings continue.

**A reviewer that returns findings you cannot parse** — no severity, no file, a
malformed table — is `blocker: reviewer-malformed-findings`. Keep its raw output
verbatim in `findings.md § ## Raw` and halt that unit; do not guess at what it
meant, and do not drop it. Siblings continue.

**Never infer a verdict from a reviewer that did not give one.** An absent verdict
is not a pass; recording one would be the same class of error as reporting a
review that inspected nothing.

### 6b.iv. A finding goes back to build — commit never implements

**`/dev:commit` validates; it does not write features.** Every repair is delegated
to the build half — `dev-stack-adaptive-implementation` in **fix mode** (that skill's
`## Two modes` § defines it) — the skill that wrote the code in the first place.

**Fix mode is the build contract, scoped to one finding.** The repair agent detects the
stack, infers patterns from the neighbours of `allowed_files`, and holds to
`coding-standards.md` on every line, exactly as a build does. `minimal-surface` bounds
_which files_ it touches, never _how well_ it writes them — the repair diff is reviewed
<!-- governed-by: code-review-dimension-count -->
against the same nine dimensions as the original, so a repair written below standard
does not close the loop, it adds a round to it. §6c passes it what it needs to meet that
contract; a repair invoked without those inputs is a spec violation, not a shortcut.

```
  Stage 4 code review ┐─ finding ──▶ build repair (fix-mode)
  Stage 5R map review ┘                    │  minimal change, allowed_files only
          ▲                                 │  + a regression test for the finding
          └────── re-review ────────────────┘
          recompute the snapshot, re-run 4 and 5R — reads, no executions

  both clean ──▶ 5X executes the map ONCE
                      │
                      └─ red + classified `defect` ──▶ repair ──▶ re-run the
                         failed rows + the suite gate (§6d.i), not the map
```

**The repair writes a regression test for the finding**, not only a fix. A defect
that was found once and has no test can return silently; `/dev:build`'s own rule
for a bug fix is the same, and it applies here.

**After a test failure specifically, re-run that scenario's own `Run it` command
from the test map** — the fastest signal is the one row that failed, and it costs
one command rather than a suite. This is the mid-loop rule, not an optimisation
available on it: §6d.i scopes every mid-loop re-run the same way.

**Order matters on the re-run: 4 and 5R together, then 5X.** A code fix can break a
test and a test fix can break the review, so neither reviewer is skipped on the
strength of the repair's intent — §6d.i decides from its diff. Never re-run only the
originating stage.

### 6c. Fix-mode invocation

For each blocking finding, invoke `dev-stack-adaptive-implementation` in fix-mode:

```
Prompt to skill:
  Fix mode.
  Finding: <full finding entry from units/<repo>/findings.md § ## Code review OR status.md § ## Acceptance row>
  Suggested fix: <fix_suggestion field if present, or "diagnose from failure_scenario">
  allowed_files: <the finding's file + its test>
  detected_stack: <the `detected_stack:` block from units/<repo>/status.md § ## Run history>
  Standards: shared-context/coding-standards.md § <repo> — §§6-12 are hard limits on
    every line you write, identical to a build.
  Constraint: minimal-surface change; do NOT expand scope; do NOT refactor unrelated code.
    This bounds WHICH files you touch, not how well you write them.
  Self-check before reporting `fixed`: read your own diff against the nine review
    dimensions — correctness, convention adherence, error handling, testability,
    BR enforcement, naming, reuse, engineering standards, API design. A repair that
    closes this finding and opens a new one has moved the finding, not resolved it.
  Persist per-finding decision to dev/decisions.md as DEC-###.
```

The skill:

1. Reads the finding
2. Locates the relevant file + line
3. Applies the smallest correct change, written to `coding-standards.md`
4. Runs the localized re-verify (the specific test that failed, or a re-lint/re-typecheck if the finding was from a static check)
5. Self-checks the diff against the nine dimensions above
6. Reports fixed | still-failing

---

### 6d. Ordering

Fix findings in the order they blocked. Within a stage:

- Stage 4 findings: Blocker before Major. Within severity, by first-listed order.
- Stage 5 findings: highest-priority AC/BR/NFR row first (from parent's `acceptance-criteria.md` ordering).

If a fix in one dimension breaks another dimension's test (rare but possible), the broken test surfaces at the next stage's broad re-run — not inside the current fix attempt.

---

### 6d.i. Re-run only what the repair could have affected

Re-running both reviewers after every fix is correct and wasteful. Re-run on
this rule, computed from the repair's actual diff:

| Reviewer                | Re-runs when                                                                           | Over what                                                |
| ----------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Stage 4 code review** | only when the repair touched a file in its finding set, or a file it cited as evidence | the new snapshot                                         |
| **5R map review**       | only when the repair added a test or changed the map                                   | the new snapshot                                         |
| **5X execution**        | only after 5X has run at least once                                                    | **the failed rows + the suite gate — not the whole map** |

**Which rows.** The map has no column recording the source files a row covers, so
"the rows the repair could have broken" is not computable from it. It does not need
to be — §6b.ii already pins the repair to `allowed_files`, _the finding's file plus
its test_:

```
re-run = the rows that failed
       ∪ rows whose `Test` path ∈ allowed_files
       ∪ the regression test the repair wrote (§6b.iv requires one)
       ∪ the suite gate, twice (stage-5-acceptance.md §5b)
```

An exact match on a column that already exists. Nothing is inferred.

**Why the suite gate is always in that set.** The per-row commands prove the rows;
the suite gate is what proves them _together_, and §5b records a green only after
two agreeing runs. A repair landed after the last gate run means the recorded green
describes code that no longer exists.

**A repair can still break a row outside that set** — the §6e exit check is what
holds the line, and the loop does not exit until Stage 4, 5R and 5X are all clean.
Narrowing which rows re-run and letting the loop exit dirty are different things,
and the second is never allowed.

Fourteen rows plus a coverage run, re-executed after each of three repairs, is
where an hour went. Under §5.0 most of those repairs now land before 5X has run at
all, so this rule has nothing to re-run for them.

**Recompute the snapshot first and record the new sha.** Findings from the
previous round cite the old one; a reviewer that is not re-run keeps its earlier
verdict, and that verdict must still name the snapshot it was formed against.
Stage 8 checks both agree (§8a).

**A reviewer that is skipped is recorded as skipped**, with the reason — not left
to look like it ran.

### 6e. Re-run cascade

**The cascade differs either side of the single execution** (`stage-5-acceptance.md`
§5.0). Before 5X, re-running costs nothing but reading; after it, re-running costs
the map.

**Pre-execution — origin is Stage 4 or 5R.** After ALL blocking findings are fixed:

1. Recompute the snapshot, then re-run **Stage 4 and 5R** over it
2. New blocking findings → re-enter Stage 6 with them — bounded, §6b
3. Both clean → **run 5X once.** This is the first and normally the only execution
   of the run

These rounds are where repair-written code gets re-read, and they are free of test
executions by construction. Repairing twelve review findings over three rounds costs
three reads here — against three full maps under the old ordering, two of which were
invalidated by the repair that followed them.

**Post-execution — origin is 5X.** A red row that classified `defect` (§6a.ii):

1. Repair it, scoped to `allowed_files`
2. Re-run the failed rows + the suite gate twice (`stage-5-acceptance.md` §5e)
3. Re-run **Stage 4** only if the repair touched a file it reviewed (§6d.i); **5R**
   only if the repair added a test or changed the map
4. New blocking findings → re-enter Stage 6 — bounded, §6b
5. Loop exits ONLY when Stage 4, 5R and 5X are all clean at commit-time thresholds

**A code fix can still break a test, and a test fix can still break the review.**
That is why step 3 exists rather than trusting the repair's scope. What changed is
that the re-run is computed from the repair's diff instead of being assumed total.

---

### 6e.i. Disposition every finding, then the batched cheap-fix pass

The loop exits when nothing **blocks**. It is not finished until nothing is
**undispositioned**.

| Severity                          | Blocks the PR | Default disposition                     |
| --------------------------------- | ------------- | --------------------------------------- |
| Critical · High · Blocker · Major | **yes**       | `fixed` — the only accepted outcome     |
| Medium · Low · Minor · Nit        | no            | **`fixed`**, via the batched pass below |

**`fixed` is the default at every severity.** `accepted` and `deferred` are
exceptions that must be argued for, not the cheap path taken by default. Each
carries a named reason — and `deferred` a real tracker id — and each appears in
the Stage 10 report. "We'll get to it" is not a disposition.

A Minor left unfixed every sprint is how a codebase degrades: naming drift, a
file in the wrong folder, a second way of doing something that already had one.
Those are exactly the findings that look safe to defer and compound fastest.

Stage 8 refuses to push while any is missing (`blocker: findings-undispositioned`).
It costs nothing on a clean run and makes _"we'll get to it"_ impossible to leave
implicit.

**The non-blocking fix rounds.** Once the blocking loop is clean, every remaining
finding — Medium, Low, Minor and Nit alike — goes through the **same fix-then-verify
discipline as a Blocker**. What differs is the batching, not the rigour.

The round takes any finding that carries a concrete fix suggestion and whose fix
neither removes existing behaviour nor needs a product decision. That is wider
than "mechanically safe": a misplaced file, an inconsistent field name, a
duplicated helper, an ad-hoc error shape — all qualify, and the reviewer has
already said how to fix each one.

Each round is:

1. **Fix every open non-blocking finding in one delegation** to
   `dev-stack-adaptive-implementation` in fix-mode — one batch, not one call per finding.
2. **Re-verify each finding individually.** A targeted re-check per finding, against the
   thing the reviewer actually reported — not a stage re-run. A finding may be marked
   `fixed` **only** on a passing re-check. Marking it `fixed` because it was in the batch
   is a spec violation; the re-check is the evidence.
3. **Any finding that did not clear carries into the next round**, with what was tried
   recorded against it.

**Bound: 2 rounds.** Then one cascade re-run to catch anything the fixes disturbed —
per §6e, which side of 5X you are on decides what that costs. Run the non-blocking
rounds **before** 5X wherever the findings allow it: the batch is then re-reviewed by
two readers rather than re-executed by the map, and the single execution covers the
fixes as well as the original code.

**Why rounds rather than the per-finding loop.** Routing forty findings through the
per-finding loop at three attempts each would be 120 fix cycles, each re-triggering the
full cascade — a real regression risk traded for cosmetic gain. Batching the _fix_ while
keeping the _verification_ per-finding gets the same guarantee at a fraction of the cost:
every finding is individually proven resolved, and the cascade runs twice, not 120 times.

**A finding still open after round 2 escalates per §6f**, named, with its attempts
listed. It does not quietly become `deferred` — the bound being reached is a
reportable outcome, not a disposition.

**Only two things stay out of the rounds**: a fix that would remove existing
behaviour, and one that needs a product decision nobody has made. Those are
escalated — `accepted` or `deferred` with a named reason — because they are
scope questions, not code questions. Cost is never a reason to leave a finding
unfixed.

**An agent may not `accept` its own finding.** Acceptance carries a name and a
reason and is asked at the pre-fan-out checkpoint, or carried from `## Settled`
(`references/common/findings-contract.md` §3).

### 6f. Bounds exceeded

If a per-finding attempt count reaches its bound OR a broad re-run count reaches its bound, escalate:

1. Write `units/<repo>/status.md § ## Run history (a BLOCKED entry)` (n = next sequential integer):

```yaml
---
doc_type: escalation
schema_version: 1.0
produced_by: dev-commit
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: <ISO>
origin_stage: 4
severity: bounds_exceeded
---

# Escalation — code review fix loop exceeded bounds

## Chain of findings
1. CR-B-002 (Major, br_enforcement) — BR-3 pre-write check missing
   - Fix attempt 1: added pre-write findOneBy check
   - Broad re-run: introduced regression on AC-4 (extra DB query changes ordering)
2. CR-B-004 (Major, testability) — pre-write check tightly couples to a specific ORM API
   - Fix attempt 1: extracted to repo method
   - Broad re-run: SR-C-003 (High) — new repo method missing param validation
3. SR-C-003 (High, injection) — SQL injection surface via unvalidated country param
   - Fix attempt 1-3: parameterized; still failing (fixture inconsistency)
   - Broad re-run: STILL failing

## Last known state
- Branch: feature/FEAT-SUP-001-supplier-onboarding-backend
- Local state: BLOCKED
- MC status: blocked
- Files modified in fix loop: [<paths>]

## Requires human action
1. Review the finding chain in this doc
2. Decide the underlying design fix (may span multiple files)
3. Apply manually, run `/dev:commit --resume` to continue
```

2. Local state: `devReview → BLOCKED`
3. MC status: `devReview → blocked` via `task-mcp.update_task_status`
4. `status.md`: `status: blocked` · `phase: escalated`, `blocked_reason: fix-loop-bounds-exceeded`, `escalation_file: units/<repo>/status.md § ## Run history (a BLOCKED entry)`
5. Halt. Print terminal message pointing at the escalation file.

Never partial-push. Never continue past a bounds exceeded escalation.

---

### 6g. Progress log

Append to `units/<repo>/status.md § ## Run history` for each fix-loop invocation:

```yaml
stage-6-loop-<invocation-n>:
  status: DONE | ESCALATED
  origin_stage: 4
  entered_with_findings: [CR-B-001, CR-B-002]
  fix_attempts:
    - finding: CR-B-001
      attempts_used: 1
      resolved: true
      self_check: clean          # REQUIRED -- same field as §6a.i. Stage 8 §8a
                                 # HALTS on `fix-not-self-checked` without it
    - finding: CR-B-002
      attempts_used: 2
      resolved: true
      self_check: clean
  broad_reruns_used: 1
  reentries_used: 0          # §6b ceiling is 2; the third escalates per §6f
  new_findings_surfaced: []
  finished_at: <ISO>
```

Multiple Stage 6 invocations across a single `/dev:commit` run each get their own `-loop-N` block.

---

### 6h. Skills / agents invoked

- `dev-stack-adaptive-implementation` (fix-mode) — the sole executor of fixes
- Re-invokes Stage 4, 5R and 5X stage refs per §6d.i and §6e — Stage 4 and 5R invoke `dev-stack-adaptive-code-review` and `dev-test-verifier` (readers, no executions); 5X invokes the test runners

Never spawn parallel fix agents on distinct findings — findings often interact; serial fixing is the safer default. If two findings are provably orthogonal (e.g. one is a comment fix in file A, the other a type fix in file B) parallel fixing is fine, but the default is serial.

---

### 6i. On `--resume`

Stage 6 doesn't have a persistent "state" — it's just a fix-execution routine invoked by the origin stage's routing. On `--resume` after a bounds-exceeded halt, the origin stage re-runs; if it produces the same set of findings, Stage 6 re-enters with the loop counters RESET (human presumably fixed something manually; give it a fresh budget). If the human's manual fix wasn't committed, or wasn't sufficient, Stage 6 will again exceed bounds and escalate — no infinite loop.

---

### 6j. Never

- Never bypass the fix loop (`--skip-fix-loop` is not a supported flag)
- Never expand scope during a fix (only the minimal-surface change to the finding)
- Never let one finding's fix silently disable another test (broad re-run catches this)
- Never fix a finding without persisting the DEC-### to `dev/decisions.md` — audit trail
