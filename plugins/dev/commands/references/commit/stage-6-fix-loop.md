## Stage 6 — Bounded fix loop

**Purpose.** When Stages 3–5 surface blocking findings, delegate fixes to `dev-stack-adaptive-implementation` in **fix-mode**, then re-run every upstream stage. Bounded per finding + per whole-stage re-run — never spin forever.

**Invoked by:** Stages 3 (security), 4 (code review), 5 (acceptance regression). NOT a standalone stage. Each entry into Stage 6 targets a specific set of findings.

**On completion:** every finding that entered the loop is either resolved (fixed) or escalated (bounds exceeded → `dev/escalation-<n>.md` + halt).

---

### 6a. Preconditions

- One of Stages 3-5 produced findings that block at commit-time threshold
- The findings file (`security-findings-commit.md`, `code-review-findings.md`, `acceptance-map.md`) has been written and is readable
- Stack + inferred patterns are still available in `dev/implementation-log.md`

---

### 6b. Bounds

| Origin stage | Focused fix attempts per finding | Broad re-runs of the whole stage |
|---|---|---|
| Stage 3 (security) | 3 per finding | 1 (whole security re-scan) |
| Stage 4 (code review) | 3 per finding | 1 (whole review re-scan) |
| Stage 5 (acceptance regression) | 3 per failing row | 2 (whole acceptance re-verification) |

A "focused fix attempt" = one delegation to `dev-stack-adaptive-implementation` in fix-mode scoped to the finding, plus one localized re-verify of that finding.

A "broad re-run" = full re-execution of the originating stage over the current branch state.

---

### 6c. Fix-mode invocation

For each blocking finding, invoke `dev-stack-adaptive-implementation` in fix-mode:

```
Prompt to skill:
  Fix mode.
  Finding: <full finding entry from security-findings-commit.md OR code-review-findings.md OR acceptance-map.md row>
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

### 6f. Bounds exceeded

If a per-finding attempt count reaches its bound OR a broad re-run count reaches its bound, escalate:

1. Write `dev/escalation-<n>.md` (n = next sequential integer):

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

2. Local state: `REVIEW → BLOCKED`
3. MC status: `devReview → blocked` via `task-mcp.update_task_status`
4. `dev/delivery-status.md`: `current_state: BLOCKED`, `blocked_reason: fix-loop-bounds-exceeded`, `escalation_file: dev/escalation-<n>.md`
5. Halt. Print terminal message pointing at the escalation file.

Never partial-push. Never continue past a bounds exceeded escalation.

---

### 6g. Progress log

Append to `dev/commit-run.md` for each fix-loop invocation:

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
