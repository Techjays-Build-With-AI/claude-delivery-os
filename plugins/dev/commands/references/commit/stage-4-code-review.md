## Stage 4 — Dynamic code review (commit-time)

**Purpose.** Delegate the feature-diff code review to `dev-stack-adaptive-code-review` skill. Reviews the diff against the repo's own conventions + parent's Business Rules. Reports findings in 4 severity tiers: `Blocker` / `Major` / `Minor` / `Nit`. At commit-time, blocks on `Blocker` and `Major`. `Minor` + `Nit` do not block — they are fixed in Stage 6's single batched pass (`stage-6-fix-loop.md` §6e.i), not deferred.

**Runs after Stage 3 (security review passed).** State: `devReview` (unchanged); MC: `devReview` (unchanged). On any Blocker/Major finding, fix loop kicks in.

**On completion:** `units/<repo>/findings.md § ## Code review` written (or `ReportFindings` emitted); zero Blocker + zero Major.

---

### 4a. Preconditions

- Stage 3 done, zero Critical + zero High security findings
- Branch still up-to-date with base (`git fetch <remote>` before invocation)
- `units/<repo>/status.md § ## Run history` present with `detected_stack:` + `inferred_patterns:` blocks from `/dev:build`

---

### 4b. Skill invocation

**The scope is the review snapshot, not a branch diff.** `/dev:build` commits
nothing, so `<base>...HEAD` is empty on a freshly-built task and this stage would
review zero bytes while reporting a clean result. `$SNAP` is built at Stage 0 from
the working tree — see `references/common/review-snapshot.md`.

Invoke `dev-stack-adaptive-code-review` inline (no subagent per the skill's Rule 9). Pass:

- The feature diff — `git diff <base>..$SNAP`, the review snapshot Stage 0 built. **Under `tests_only`** it is the same snapshot; the product-code dimensions with nothing to read are skipped rather than reported empty (`commit.md` §2). If the review skill refuses to run, follow `commit.md` → *When a required tool cannot run*
- The target repo path
- `units/<repo>/status.md § ## Run history` — for the detected stack + inferred patterns (avoid re-detecting)
- Parent's `business-rules.md` — for BR enforcement checks
- Parent's `nfrs.md` — for NFR-declared perf/rate targets

The skill emits findings via `ReportFindings` tool if available, or writes directly to `units/<repo>/findings.md § ## Code review`.

---

### 4b.i. Second opinion — the built-in `code-review`, advisory

Run Claude Code's built-in `code-review` skill against the same snapshot, in its
own agent, **at the same time** as the adaptive reviewer.

| | `dev-stack-adaptive-code-review` | built-in `code-review` |
|---|---|---|
| Knows | this repo's conventions, the parent's Business Rules, `coding-standards.md` | general correctness, reuse, simplification, efficiency |
| Class | adversarial — **the blocking gate** | **advisory** — never blocks |

**Report the union, labelled by source.** Two reviewers find different things —
that is the entire reason for the second one, and a planted-defect run where one
skill found five and ours found three is the evidence.

**Never swap the adaptive reviewer for the built-in.** It enforces Dimension 5
(the parent's Business Rules) and Dimension 8 (`coding-standards.md`, which
`/dev:build` Stage 0 hard-gates on). Replacing it would leave that gate protecting
nothing.

Deduplicate by finding id (`findings-contract.md` §1): the same defect found by
both reviewers is one row, `sources: [adaptive, builtin]`.

### 4c. Findings file

`units/<repo>/findings.md § ## Code review` structure:

```yaml
---
doc_type: code-review-findings
schema_version: 1.0
produced_by: dev-stack-adaptive-code-review
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: 2026-08-31T15:42:00Z
diff_base: develop
snapshot_sha: <sha>              # the exact bytes these findings cite
severity_threshold: Major
---

# Commit-time code review findings

**Findings follow `references/common/findings-contract.md`**: a stable id derived
from repo + path + enclosing symbol (never a line number), a `disposition` on every
row, and `## Settled` carried in so a decision made last run is not re-raised.


## Blocking (Blocker + Major)

- CR-B-001 (Major, error_handling) — src/supplier/service.ts:78
  New code throws plain `Error`; repo pattern is custom errors inheriting from `ApplicationError`.
  Failure scenario: `AppErrorFilter` bypasses; caller sees 500 with generic message; consumers retry.
  Fix: introduce `DuplicateSupplierError extends ApplicationError` (see src/order/errors/DuplicateOrderError.ts).

- CR-B-002 (Major, br_enforcement) — src/supplier/service.ts:110
  BR-3 (tax_id unique per country) has DB unique constraint but no pre-write service-level check.
  Failure scenario: two concurrent POSTs pass service validation, both attempt insert, DB rejects one with 500 (not 409).
  Fix: add pre-write `findOneBy({taxId, country})` check → throw `DuplicateSupplierError` before insert.

## Minor (surface in PR body under "Follow-up suggestions" — non-blocking)

- CR-M-001 (Minor, naming) — src/supplier/service.ts:180
  Function `getSupplierWithDuplicates` combines fetch + de-dup; naming leaks impl detail.
  Fix suggestion: split into `getSupplier` + `withDuplicateChecks`.

## Nit (logged only)

- CR-N-001 (Nit, comment) — src/supplier/dto/create.dto.ts:15
  TODO comment without owner or issue link.
```

---

### 4c.i. Report found-but-downgraded separately from not-found

A Minor is **found**. It does not block, so it does not appear in the blocking
list — and a reader comparing "defects I planted" against "findings that blocked"
concludes it was missed. That is how a run that found four of five was read as
finding three.

Report three counts, always, in this order:

```
Code review · snapshot 0f50921291d9 · 18 files
  Blocking      2   (1 Blocker, 1 Major)        → fix loop
  Found, below threshold   5   (3 Minor, 2 Nit) → dispositioned, in the PR body
  Not reviewed  0 files    (scope stated above)
```

**"Found, below threshold" is not a footnote.** It is the difference between a
reviewer that missed something and one that saw it and ranked it low — and only
one of those is a recall problem.

### 4d. Route to fix loop or advance

**Zero Blocker + Zero Major** → mark Stage 4 done. Minor + Nit findings persist in the findings file and carry into Stage 6's batched fix pass, where `fixed` is the default disposition. Advance to Stage 5.

**One or more Blocker/Major** → invoke the fix loop per `stage-6-fix-loop.md` §6a.i (v2.3.27). The fix loop is **MANDATORY and VERIFIABLE** — this stage MUST invoke `dev-stack-adaptive-implementation` in fix-mode via the Skill / Agent tool and record a `stage-4.fix_loop_invocation:` block in `status.md` § `## Run history` (fields per §6a.i). Applying the fix inline without recording the invocation trace is a spec violation and Stage 8 §8a will refuse to push. After fix loop, Stage 3 (security) + Stage 4 (code review) both re-run from the top — code fixes may introduce new security concerns.

---

### 4e. Interaction with build-time deferred findings

Not applicable — `/dev:build` doesn't run code review; only security. Code review is exclusively a commit-time stage.

---

### 4f. Progress log

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-4:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  snapshot_sha: 0f50921291d9
  scope: "snapshot vs develop (18 files, +624/-12)"
  dimensions_reviewed: [correctness, conventions, error_handling, testability, br_enforcement, naming, reuse]
  findings:
    blocker: 0
    major: 0
    minor: 3
    nit: 2
  fix_loop_invocation:                  # REQUIRED when the pre-loop blocking count was > 0
    invoked_at: <ISO>                   # absent + blocking findings => Stage 8 halts
    invocation: <subagent id | "inline">
    origin_findings: [REV-error_handling-9b7d1e03]
    fix_attempts: [{finding: REV-error_handling-9b7d1e03, attempts_used: 1, resolved: true}]
    broad_reruns_used: 0
    exit_state: CLEAN                   # CLEAN | ESCALATED
  findings_file: units/<repo>/findings.md § ## Code review
```

---

### 4g. Skills / agents invoked

- `dev-stack-adaptive-code-review` (inline; no subagent)
- No secondary skills — this stage is the review, findings go to fix loop or PR body

---

### 4h. On `--resume`

If `--resume` finds `stage-4.status: DONE`, **recompute the review snapshot and compare its sha** with the recorded `stage-4.snapshot_sha`. Same → skip. Different → re-run.

**Not commit history.** Nothing is committed until Stage 7.5, so a commit-based test would skip a stage whose input had changed.

---

### 4i. Never

- Never bikeshed style (lint / format catches these — the code-review skill's Rule 9)
- Never emit findings without the pattern-grounding evidence (code-review skill's Rule 10)
- Never merge follow-up-issue creation into this stage — Minor + Nit findings surface in PR body ONLY; the developer decides if they file separate issues after PR
