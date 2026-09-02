## Stage 4 — Dynamic code review (commit-time)

**Purpose.** Delegate the feature-diff code review to `dev-stack-adaptive-code-review` skill. Reviews the diff against the repo's own conventions + parent's Business Rules. Reports findings in 4 severity tiers: `Blocker` / `Major` / `Minor` / `Nit`. At commit-time, blocks on `Blocker` and `Major`; `Minor` + `Nit` surface as follow-up suggestions in the PR body.

**Runs after Stage 3 (security review passed).** State: `REVIEW` (unchanged); MC: `devReview` (unchanged). On any Blocker/Major finding, fix loop kicks in.

**On completion:** `dev/code-review-findings.md` written (or `ReportFindings` emitted); zero Blocker + zero Major.

---

### 4a. Preconditions

- Stage 3 done, zero Critical + zero High security findings
- Branch still up-to-date with base (`git fetch <remote>` before invocation)
- `dev/implementation-log.md` present with `detected_stack:` + `inferred_patterns:` blocks from `/dev:build`

---

### 4b. Skill invocation

Invoke `dev-stack-adaptive-code-review` inline (no subagent per the skill's Rule 9). Pass:

- The feature diff — `git diff <base>...HEAD`
- The target repo path
- `dev/implementation-log.md` — for the detected stack + inferred patterns (avoid re-detecting)
- Parent's `business-rules.md` — for BR enforcement checks
- Parent's `nfrs.md` — for NFR-declared perf/rate targets

The skill emits findings via `ReportFindings` tool if available, or writes directly to `dev/code-review-findings.md`.

---

### 4c. Findings file

`dev/code-review-findings.md` structure:

```yaml
---
doc_type: code-review-findings
schema_version: 1.0
produced_by: dev-stack-adaptive-code-review
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: 2026-08-31T15:42:00Z
diff_base: develop
diff_head: <sha>
severity_threshold: Major
---

# Commit-time code review findings

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

### 4d. Route to fix loop or advance

**Zero Blocker + Zero Major** → mark Stage 4 done. Minor + Nit findings persist in the findings file for PR body integration + follow-up. Advance to Stage 5.

**One or more Blocker/Major** → invoke the fix loop per `stage-6-fix-loop.md` §6a.i (v2.3.27). The fix loop is **MANDATORY and VERIFIABLE** — this stage MUST invoke `dev-stack-adaptive-implementation` in fix-mode via the Skill / Agent tool and record a `stage-4.fix_loop_invocation:` block in `commit-run.md` (fields per §6a.i). Applying the fix inline without recording the invocation trace is a spec violation and Stage 8 §8a will refuse to push. After fix loop, Stage 3 (security) + Stage 4 (code review) both re-run from the top — code fixes may introduce new security concerns.

---

### 4e. Interaction with build-time deferred findings

Not applicable — `/dev:build` doesn't run code review; only security. Code review is exclusively a commit-time stage.

---

### 4f. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-4:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  scope: "git diff develop...HEAD (18 files, +624/-12)"
  dimensions_reviewed: [correctness, conventions, error_handling, testability, br_enforcement, naming, reuse]
  findings:
    blocker: 0
    major: 0
    minor: 3
    nit: 2
  findings_file: dev/code-review-findings.md
```

---

### 4g. Skills / agents invoked

- `dev-stack-adaptive-code-review` (inline; no subagent)
- No secondary skills — this stage is the review, findings go to fix loop or PR body

---

### 4h. On `--resume`

If `--resume` finds `stage-4.status: DONE`, skip re-running UNLESS the branch has new commits since `finished_at`. New commits → re-run.

---

### 4i. Never

- Never bikeshed style (lint / format catches these — the code-review skill's Rule 9)
- Never emit findings without the pattern-grounding evidence (code-review skill's Rule 10)
- Never merge follow-up-issue creation into this stage — Minor + Nit findings surface in PR body ONLY; the developer decides if they file separate issues after PR
