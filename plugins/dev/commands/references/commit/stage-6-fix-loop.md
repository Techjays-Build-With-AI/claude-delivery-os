## Stage 6 — Bounded fix loop

**Purpose.** When Stages 3–5 surface blocking findings, delegate fixes to `dev-stack-adaptive-implementation` in **fix-mode**, then re-run every upstream stage. Bounded per finding + per whole-stage re-run — never spin forever.

**Invoked by:** Stages 3 (security), 4 (code review), 5 (acceptance regression). NOT a standalone stage. Each entry into Stage 6 targets a specific set of findings.

**On completion:** every finding that entered the loop is either resolved (fixed) or escalated (bounds exceeded → `units/<repo>/status.md § ## Run history (a BLOCKED entry)` + halt).

---

### 6a. Preconditions

- One of Stages 3-5 produced findings that block at commit-time threshold
- The findings file (`security-findings-commit.md`, `code-review-findings.md`, `status.md` § `## Acceptance`) has been written and is readable
- Stack + inferred patterns are still available in `units/<repo>/status.md § ## Run history`

### 6a.i. Non-skippable execution (v2.3.27 — closes the "findings surfaced but agent didn't invoke fix loop" gap)

**Whenever any of Stages 3, 4, or 5 produces one or more BLOCKING findings, the origin stage MUST invoke the fix loop in this file via the Skill / Agent tool (delegating to `dev-stack-adaptive-implementation` in fix-mode). Internal reasoning that "the finding is small, I'll just fix it inline" or "the agent will pick it up later" is NOT sufficient evidence of execution — the skill's own invocation log is the evidence. Skip = spec violation.**

Same class of "spec exists but subagent doesn't execute it" bug as v2.3.21 (compose mechanical fix pass) and v2.3.25 (Stage 7 semantic merge). Findings surface, the agent reports them, and the agent moves to Stage 8 push without invoking Stage 6. Push then lands broken code because the review said "block" and nobody acted on it.

Every entry into Stage 6 — even trivial ones with a single Critical finding — records an invocation trace in `status.md` § `## Run history`. Recording format (Stage 8 §8a's precondition check reads this):

```yaml
stage-3:                       # or stage-4 / stage-5 depending on origin
  status: DONE
  findings:
    critical: 0                # after fix loop; must be zero to advance
    high:     0                # after fix loop; must be zero to advance
    medium:   1                # non-blocking
    low:      1
  fix_loop_invocation:         # REQUIRED whenever ANY finding at ANY severity was > 0 BEFORE the loop ran
                               # — blocking (critical/high/blocker/major/regression) drives §6c;
                               # non-blocking (medium/low/minor/nit) drives §6e.i's rounds. Both are recorded here
    invoked_at: <ISO>          # required — presence proves invocation
    invocation: <subagent id | "inline">   # required — an id when the skill ran as a subagent,
                                           # the literal "inline" when the Skill tool returned none.
                                           # Never blank, never invented
    origin_findings: [SR-C-001, SR-C-004]   # what fed the loop
    fix_attempts:              # copy of §6c per-finding outcomes
      - finding: SR-C-001
        attempts_used: 1
        resolved: true
      - finding: SR-C-004
        attempts_used: 2
        resolved: true
    broad_reruns_used: 1
    nonblocking_rounds:        # REQUIRED when any medium/low/minor/nit finding existed (§6e.i)
      rounds_used: 1           # 1 or 2; 0 is only valid when there were none
      findings:                # EVERY non-blocking finding, with its individual re-check
        - finding: CR-M-001
          round: 1
          reverified: true     # the targeted re-check passed — this is what permits `fixed`
          disposition: fixed
        - finding: CR-M-002
          round: 2
          reverified: false
          disposition: escalated   # bound reached — never silently `deferred`
          reason: "fix requires removing the legacy export; scope decision"
      cascade_rerun: true      # the single 3→4→5 re-run after the rounds
    exit_state: CLEAN | ESCALATED
    escalation_file: null | units/<repo>/status.md § ## Run history (a BLOCKED entry)
```

If a stage completes with BLOCKING findings resolved but no `fix_loop_invocation:` block written → Stage 8 refuses to push (see stage-8-9-push-pr.md §8a). No workaround. No "I checked and applied the fix inline" bypass.

**Zero-finding runs skip Stage 6 entirely and do NOT record `fix_loop_invocation:`.** The absence of the block on a stage that had zero blocking findings is fine and Stage 8 accepts it. The gate is: findings.blocking > 0 IMPLIES fix_loop_invocation MUST be present.

---

### 6b. Bounds

| Origin stage | Focused fix attempts per finding | Broad re-runs of the whole stage |
|---|---|---|
| Stage 3 (security) | 3 per finding | 1 (whole security re-scan) |
| Stage 4 (code review) | 3 per finding | 1 (whole review re-scan) |
| Stage 5 (acceptance regression) | 3 per failing row | 2 (whole acceptance re-verification) |
| Non-blocking findings (Medium/Low/Minor/Nit) | batched per round, re-verified per finding | 2 rounds, then 1 cascade (§6e.i) |

A "focused fix attempt" = one delegation to `dev-stack-adaptive-implementation` in fix-mode scoped to the finding, plus one localized re-verify of that finding.

A "broad re-run" = full re-execution of the originating stage over the current branch state.

---

### 6b.i. Freeze this unit's tests for the duration of the loop

Before the first fix-mode invocation, set `deny.write_paths` on this run's
`.jetrix/cache/session.json` row to the test paths in scope — the files whose
failures fed the loop, plus the directory the repo keeps tests in. The guard
hook then refuses an `Edit` or `Write` to any of them.

**A failing test is fixed in the code, never in the test.** That rule already
exists in prose here and in `--tests-only`'s hard limits; this makes it a
refusal instead of a hope. A test that is genuinely wrong is an escalation —
record it and halt, do not edit it.

**Empty `deny.write_paths` on every exit from the loop**, including the
bounds-exceeded escalation in §6f. A frozen path left frozen blocks the human
who was just asked to fix it by hand.

### 6b.ii. One repair agent at a time, and a new one each round

| | |
|---|---|
| **Serial per repository** | two repair agents in one working tree overwrite each other, and a fix in one can invalidate the other's premise. Never parallel, even for findings that look orthogonal |
| **A fresh agent per round** | round N+1 gets a new agent with only the finding and `allowed_files`. Reusing the agent carries round N's rationalisation — *"I already looked at this and it seemed fine"* — into the round that was supposed to re-examine it |
| **Scoped to `allowed_files`** | the finding's file plus its test. A repair that needs a file outside that set is a scope escalation, not a wider edit |

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
to the build half — `dev-stack-adaptive-implementation` in fix-mode — which is the
skill that wrote the code in the first place and knows the repo's conventions,
`coding-standards.md` and the stack.

```
  Stage 3 security  ┐
  Stage 4 code review ├─ finding ──▶ build repair (fix-mode)
  Stage 5 tests     ┘                      │  minimal change, allowed_files only
                                            │  + a regression test for the finding
          ◀────── re-review ─────────────┘
          recompute the snapshot, re-run 3 → 4 → 5 in order
```

**The repair writes a regression test for the finding**, not only a fix. A defect
that was found once and has no test can return silently; `/dev:build`'s own rule
for a bug fix is the same, and it applies here.

**After a test failure specifically, re-run that scenario's own `Run it` command
from the test map** before re-running the stage — the fastest signal is the one row
that failed, and it costs one command rather than a suite.

**Order matters on the re-run: 3 → 4 → 5.** A security fix can break a test; a code
fix can open a security hole. Never re-run only the originating stage.

### 6c. Fix-mode invocation

For each blocking finding, invoke `dev-stack-adaptive-implementation` in fix-mode:

```
Prompt to skill:
  Fix mode.
  Finding: <full finding entry from security-findings-commit.md OR code-review-findings.md OR status.md § ## Acceptance row>
  Suggested fix: <fix_suggestion field if present, or "diagnose from failure_scenario">
  Constraint: minimal-surface change; do NOT expand scope; do NOT refactor unrelated code.
  Persist per-finding decision to dev/decisions.md as DEC-###.
```

The skill:
1. Reads the finding
2. Locates the relevant file + line
3. Applies the smallest correct change
4. Runs the localized re-verify (the specific test that failed, or a re-lint/re-typecheck if the finding was from a static check)
5. Reports fixed | still-failing

---

### 6d. Ordering

Fix findings in the order they blocked. Within a stage:

- Stage 3 findings: highest-severity first (Critical before High). Within severity, by first-listed order.
- Stage 4 findings: Blocker before Major. Within severity, by first-listed order.
- Stage 5 findings: highest-priority AC/BR/NFR row first (from parent's `acceptance-criteria.md` ordering).

If a fix in one dimension breaks another dimension's test (rare but possible), the broken test surfaces at the next stage's broad re-run — not inside the current fix attempt.

---

### 6d.i. Re-run only what the repair could have affected

Re-running all three reviewers after every fix is correct and wasteful. Re-run on
this rule, computed from the repair's actual diff:

| Reviewer | Re-runs when |
|---|---|
| **security** | any source file changed. Always — a fix anywhere can open a hole, and this is the cheapest place to be paranoid |
| **test verification** | always. The repair changed code that tests assert on |
| **code review** | only when the repair touched a file in its finding set, or a file it cited as evidence |

**Recompute the snapshot first and record the new sha.** Findings from the
previous round cite the old one; a reviewer that is not re-run keeps its earlier
verdict, and that verdict must still name the snapshot it was formed against.
Stage 8 checks all three agree (§8a).

**A reviewer that is skipped is recorded as skipped**, with the reason — not left
to look like it ran.

### 6e. Re-run cascade

After ALL blocking findings for the origin stage are fixed:

1. Broad re-run of the origin stage on the current branch state
2. If origin stage now clean → re-run every earlier stage in order:
   - If origin = Stage 5: re-run Stage 3, then Stage 4, then Stage 5
   - If origin = Stage 4: re-run Stage 3, then Stage 4
   - If origin = Stage 3: re-run Stage 3 only
3. Any of those re-runs surfaces new blocking findings → re-enter Stage 6 with the new findings
4. Loop exits ONLY when all of Stages 3-5 pass at commit-time thresholds

Order matters: fixing a code-review Major may introduce a security concern; fixing a security issue may break an acceptance test. Never assume "just re-run the origin stage" is enough.

---

### 6e.i. Disposition every finding, then the batched cheap-fix pass

The loop exits when nothing **blocks**. It is not finished until nothing is
**undispositioned**.

| Severity | Blocks the PR | Default disposition |
|---|---|---|
| Critical · High · Blocker · Major | **yes** | `fixed` — the only accepted outcome |
| Medium · Low · Minor · Nit | no | **`fixed`**, via the batched pass below |

**`fixed` is the default at every severity.** `accepted` and `deferred` are
exceptions that must be argued for, not the cheap path taken by default. Each
carries a named reason — and `deferred` a real tracker id — and each appears in
the Stage 10 report. "We'll get to it" is not a disposition.

A Minor left unfixed every sprint is how a codebase degrades: naming drift, a
file in the wrong folder, a second way of doing something that already had one.
Those are exactly the findings that look safe to defer and compound fastest.

Stage 8 refuses to push while any is missing (`blocker: findings-undispositioned`).
It costs nothing on a clean run and makes *"we'll get to it"* impossible to leave
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

**Bound: 2 rounds.** Then one full 3→4→5 cascade re-run to catch anything the fixes
disturbed.

**Why rounds rather than the per-finding loop.** Routing forty findings through the
per-finding loop at three attempts each would be 120 fix cycles, each re-triggering the
full cascade — a real regression risk traded for cosmetic gain. Batching the *fix* while
keeping the *verification* per-finding gets the same guarantee at a fraction of the cost:
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
    - finding: CR-B-002
      attempts_used: 2
      resolved: true
  broad_reruns_used: 1
  new_findings_surfaced: []
  finished_at: <ISO>
```

Multiple Stage 6 invocations across a single `/dev:commit` run each get their own `-loop-N` block.

---

### 6h. Skills / agents invoked

- `dev-stack-adaptive-implementation` (fix-mode) — the sole executor of fixes
- Re-invokes Stages 3+4+5 stage refs after each fix — those in turn invoke `security-review` + `dev-stack-adaptive-code-review` + test runners

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
