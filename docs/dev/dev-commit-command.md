# `/dev:commit` Command — Design & Implementation Plan (v2.2)

> **Status:** Draft · **Owner:** dev plugin · **Depends on:** `/dev:build` complete on the task's branch · **Related:** [dev-build-command.md](dev-build-command.md)
>
> This is the build-ready plan for the NEW `/dev:commit` command. Second-gate validation + semantic context merge + push + PR handoff. Every §-number is a checkable spec.

---

## 1. Purpose

Take a built + tested + security-scanned task branch (output of `/dev:build`) and:

1. **Re-validate at a stricter gate** — code review + security review with `High`-severity blocking (not just `Critical`), plus final acceptance-map verification against parent's Test Scenarios + Business Rules + Acceptance Criteria + NFRs. Catches drift if the developer hand-edited between `/dev:build` and `/dev:commit`.
2. **Semantically merge code-context with the base branch** — not a text merge; a graph-aware merge that unions consumer lists, promotes confidence, rebuilds indexes, and preserves other teammates' units on `develop`.
3. **Push the branch** to the remote — first time this task's code leaves the developer's machine.
4. **Raise the PR** against the base branch with a PR-focused summary.
5. **Update MC** — status → `devReview`.

If ANY validation fails at this gate, `/dev:commit` calls back to `dev-agent` (via `/dev:build --resume` semantics on the fix step) and loops. Never pushes or PRs a broken task.

---

## 2. Command shape

**File:** [plugins/dev/commands/commit.md](../../plugins/dev/commands/commit.md) (NEW)

```yaml
---
description: Second-gate validation and PR handoff for a task built by /dev:build. Runs a strict code review (dev-stack-adaptive-code-review skill) + strict security review (Claude Code security-review, High-blocking) + final acceptance-map verification against parent's AC + BR + TS + NFRs. Semantically merges the branch's code-context with the base branch (tl-semantic-context-merge skill) — not a text merge, a graph-aware merge that unions consumers, promotes confidence, and preserves other teammates' work. Any break calls dev-agent to fix in a bounded loop. Once clean, pushes the branch and raises the PR against the base (from project.json env_branches). Sets MC status to devReview; the PR-merge webhook later flips to done. Never merges the PR — human owns that. Accepts the same task identifiers as /dev:build.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN | (blank = current task on the current branch)> [--base=<dev|staging|master>] [--dry-run]"
---
```

**Arguments** — same task resolution as `/dev:build`. If no target given, resolve from the current branch name (`feature/FEAT-<AREA>-NN-<slug>[-<repo>]`).

**Flags:**
- `--base=<env>` — override which environment's branch to PR against. Defaults to `dev` env's branch from `project.json`. Values: `dev` / `staging` / `master`.
- `--dry-run` — run the full validation + semantic merge locally, produce the summary, **skip the actual push + PR**. Useful for previewing.

---

## 3. High-level flow (10 stages)

```
/dev:commit <task>
│
├── Stage 0 — Identity resolution + branch verification
│     (task exists; branch matches; /dev:build completed)
│
├── Stage 1 — Acquire lock + set MC status to devReview
│     Local: IN_PROGRESS → REVIEW  ·  MC: inProgress → devReview
│
├── Stage 2 — Base branch selection (project.json env_branches; default dev)
│
├── Stage 3 — Strict security review (Claude Code security-review, Critical+High blocking)
│
├── Stage 4 — Dynamic code review (dev-stack-adaptive-code-review skill)
│
├── Stage 5 — Final acceptance-map verification against parent AC+BR+TS+NFRs
│     Re-run tests, re-check every non-deferred row is still ✅ pass
│
├── Stage 6 — Fix loop (if Stages 3–5 surfaced issues)
│     Delegates back to dev-agent (invokes dev-stack-adaptive-implementation)
│     Bounded retries; re-runs Stages 3–5 after each fix
│
├── Stage 7 — Semantic context merge (tl-semantic-context-merge skill)
│     Merge <repo>/context/code-context/ branch state with base branch state
│     Not a text merge; unit-level graph merge
│
├── Stage 8 — Push the branch to origin
│
├── Stage 9 — Raise the PR against the base branch (via gh CLI)
│
└── Stage 10 — Report summary
             Local: REVIEW  ·  MC: devReview
             PR link + summary + follow-ups
```

**Loop:** Stages 3–5 form the second-gate fix loop. Fix → re-run 3–5. Bounded per §12.
**Stages 7-9 fire only when 3–5 come back 100% clean.**

**Progress log:** `dev/commit-run.md` per task — same shape as `build-run.md`.

---

## 4. Stage 0 — Identity resolution + branch verification

### 4a. Resolve target

Same 4-way resolution as `/dev:plan` / `/dev:build`. If invoked with no target, resolve from current git branch name (`feature/FEAT-<AREA>-NN-<slug>[-<repo>]`).

### 4b. Verify `/dev:build` completed on this task

Under the task folder, require:

- `dev/status.md` with `current_state: IN_PROGRESS` (the "build done, awaits commit" state per `/dev:build` §19)
- `dev/build-run.md` with Stage 11 status `DONE`
- `dev/acceptance-map.md` present, with 100% of non-deferred rows `✅ pass`
- `dev/local-runbook.md` present
- Current git branch name matches the recorded branch in `status.md`

Missing / mismatched → halt with:

```
✗ Task <target> hasn't finished /dev:build yet, or the branch doesn't match. Options:
    · Run /dev:build <target> first (fresh build)
    · Run /dev:build <target> --resume (continue an in-progress build)
    · Check out the correct branch:  git checkout <branch>
```

Never build inline. `/dev:commit` only ships what `/dev:build` produced.

---

## 5. Stage 1 — Acquire lock + set MC status to devReview

Write owner into `dev/status.md`. Transition:

- **Local:** `IN_PROGRESS → REVIEW` (broadcast)
- **MC:** `inProgress → devReview` (via `task-mcp.update_task_status`)

This is when the outside world first sees the task moving toward PR — the moment the developer commits to committing.

If MC status is currently `blocked` (someone flagged it after `/dev:build` finished) → halt cleanly, tell user to resolve the block first.

---

## 6. Stage 2 — Base branch selection

Read `.jetrix/project.json`:

```json
{
  "apps": [{
    "projectId": "...",
    "projectSlug": "acme-backend",
    "env_branches": {
      "dev":     "develop",
      "staging": "staging",
      "prod":    "master"
    }
  }]
}
```

Look up THIS task's repo (via `subtask_repo` frontmatter → matching `projectSlug`, OR the primary app for parent-alone tasks).

Resolve base branch name:

- Default: `env_branches.dev` (usually `develop`)
- Override: `--base=<env>` flag → `env_branches[<env>]`

**Do NOT prompt the user** (per your "no prompts in /dev:build" rule — same for `/dev:commit`; if they want a different base they pass `--base`). Log the choice in `commit-run.md`.

If `env_branches` is missing or the resolved key doesn't exist → halt with a clear error pointing at `/jetrix:init` to refresh env configuration.

---

## 7. Stage 3 — Strict security review

Invoke Claude Code's built-in **`security-review`** skill on the feature diff:

- **Scope:** `git diff <base>...<current-branch>` (same scope as `/dev:build` Stage 9)
- **Threshold at commit-time:** block on `Critical` AND `High`. `Medium` surfaces as warnings; `Low` / `Info` logged only.
- **Same skill invocation as `/dev:build`, different severity config.** One skill, two thresholds. Configured via env or invocation param.
- **Full focus areas** (not the build-time subset):
  - Injection (SQL, command, path, LDAP, XPath)
  - Auth/authz on new + modified endpoints
  - Secret leaks in new code AND in `.env.example` / config files
  - Insecure deserialization
  - Input validation completeness
  - CSRF / CORS on new endpoints
  - Rate-limiting on new endpoints
  - Sensitive data logging
  - Dependency vulnerabilities on newly added packages

**Any Critical or High** → jump to Stage 6 (fix loop). Fix, re-run.

---

## 8. Stage 4 — Dynamic code review

Delegate to the new **`dev-stack-adaptive-code-review`** skill (see §14 for spec).

**What it does:**

1. Detects stack (reuses `dev-stack-adaptive-implementation`'s stack-detection reference)
2. Reads the repo's existing conventions (imports, error handling, DI, config, logging patterns)
3. Reviews the diff against those conventions AND against the parent's Business Rules
4. Reports findings in 4 severity tiers: `Blocker` / `Major` / `Minor` / `Nit`

**Threshold at commit-time:** block on `Blocker` AND `Major`. `Minor` / `Nit` surface as suggestions the developer can address in follow-up PRs (not this one).

**Review dimensions (dynamic per stack, not per-stack playbooks):**

- **Correctness** — does the code actually implement what `implementation.md` said?
- **Convention adherence** — matches the repo's existing patterns?
- **Error handling** — every exceptional path handled per the repo's style?
- **Testability** — is the code structured so tests can exercise it (no hard-coded time, DI where appropriate)?
- **Business rule enforcement** — for every parent BR, is there a code path that enforces it?
- **Naming** — matches the codebase's naming style (camelCase vs snake_case, hungarian, etc.)?
- **Reuse** — did we introduce a parallel abstraction where one exists?

**Any Blocker or Major** → jump to Stage 6 (fix loop). Fix, re-run.

---

## 9. Stage 5 — Final acceptance-map verification

`/dev:build` built the acceptance-map. `/dev:commit` re-verifies EVERY row is still green. Reason: the developer may have hand-edited code between build and commit (fixed a typo, refactored something), and that could have broken a test.

**What happens:**

1. Re-run every test from the acceptance-map's `Verified by` column
2. Compare current test results to build-time results
3. Any row that was `✅ pass` at build-time but is now `❌ fail` → surface as regression
4. Any `⏸ deferred-to-e2e` row → check if this task is the LAST sub-task to land (via parent's rollup table's remaining sub-tasks NOT-DONE count):
   - If YES → run the E2E now, add its result to the map
   - If NO → keep deferred

**Any regression** → jump to Stage 6 (fix loop).

**Update `acceptance-map.md`** with the re-verification results — write a `Commit-time verification` column alongside the build-time one.

---

## 10. Stage 6 — Fix loop (bounded)

Same bounded model as `/dev:build` §14, applied to Stages 3–5:

| Phase | Focused attempts per finding | Broad re-runs |
|---|---|---|
| Stage 3 (security) | 3 per finding | 1 (whole security pass) |
| Stage 4 (code review) | 3 per finding | 1 (whole code review) |
| Stage 5 (acceptance regression) | 3 per failing row | 2 (whole re-verification) |

**Fix strategy:**

- Delegate to `dev-agent` invoking `dev-stack-adaptive-implementation` in **fix mode** — same skill `/dev:build` uses, scoped to the finding
- After each fix: **re-run Stages 3-5 from the top** (order matters — fixing a security issue may break a test)

**Bounds exceeded** → escalate cleanly:

- Write `dev/escalation-<n>.md` with the finding chain + last state
- Local: `REVIEW → BLOCKED`
- MC: `devReview → blocked`
- Halt. Never push a broken task.

---

## 11. Stage 7 — Semantic context merge

**The single most complex stage in `/dev:commit`.** Delegate to the new **`tl-semantic-context-merge`** skill (see §15 for spec).

**Purpose:** the branch has `<repo>/context/code-context/` units marked `origin: implemented` (from `/dev:build` Stage 10). The base branch's `context/code-context/` is what OTHER teammates have merged in the meantime. When our PR merges, git's text-level merge would try to reconcile these two trees line-by-line — which fails badly for a graph structure (indexes especially).

Instead: run a **semantic merge NOW on the branch**, so the PR reviewer sees a clean, mergeable end state.

**What the skill does:**

1. Read branch's `<repo>/context/code-context/` — the current snapshot including our implemented units
2. Fetch base's `<repo>/context/code-context/` — via `git show <base>:<path>` (don't switch branches)
3. Compute the diff at the **UNIT LEVEL, not line level**
4. For each divergence, apply per-field merge rules:
   - **New unit on branch, not in base** → keep verbatim (our new work)
   - **New unit on base, not on branch** → add to our tree (other teammate's work; we didn't touch it)
   - **Same unit modified by both** → per-field merge:
     - Frontmatter `Used by Features` cell → **UNION** (both consumers keep the link)
     - Frontmatter `confidence` → take **higher** (Confirmed > Likely > Assumed > Conflicting > Needs Clarification)
     - Frontmatter `origin` → prefer `implemented > designed > reverse-mapped` (if our branch built it, ours wins; if base has reverse-mapped-with-code-citation and we have designed, base wins)
     - Body sections — additive sections (e.g. new `## Data Access` row, new `## Called by` entry) → **MERGE** (union the rows); replacement sections (e.g. `## Summary`) → LWW on identical, warn on divergent
   - **Unit removed on branch, still on base** → keep base (removals require a decision — flag as an open question)
5. Rebuild layer indexes (`frontend-index.md`, `backend-index.md`, `database-index.md`) from the merged unit set — indexes are DERIVED, never merged directly
6. Rebuild `map-coverage.md` — merge rows by row id
7. Cross-repo links — validate against workspace `.jetrix/tl/code-map-registry.md`
8. **Write the merged tree back to the branch** (`git add`, part of the commit)

**Artifact:** `<repo>/context/code-context/.merge-report-<timestamp>.md` — one row per merge decision, kept for audit. Not committed (gitignored).

**Any UNRESOLVED conflict** (e.g. same unit with two divergent `## Summary` bodies, no clear winner) → surface as an open question, halt Stage 7, tell the developer to resolve manually and re-run `/dev:commit --resume`.

---

## 12. Stage 8 — Push the branch

`git push origin <branch>` in the target repo. Set upstream on first push.

If push fails (branch protection, RBAC): surface the error, do NOT retry silently. Some pushes are legitimately denied (protected branches, missing permissions).

Log the push result to `commit-run.md`.

---

## 13. Stage 9 — Raise the PR

Use `gh pr create` in the target repo:

```bash
gh pr create \
  --base <resolved-base-branch> \
  --head <feature-branch> \
  --title "<title from parent feature.md OR sub-task title>" \
  --body "$(cat dev/pr-summary.md)"
```

**PR title format:**
- Parent-alone: `<feature title>` (e.g. `Supplier Onboarding`)
- Sub-task: `<parent title> — <repo>` (e.g. `Supplier Onboarding — backend`)

**PR body** = `dev/pr-summary.md` verbatim. This is the PR-reviewer-facing document. It NEVER includes:
- "How to run locally" (that's `local-runbook.md`, developer-facing)
- Config setup instructions (also `local-runbook.md`)
- Test-run outputs (linked to CI, not inline)

It DOES include:
- Purpose (1-2 lines)
- Scope of changes (files, endpoints, entities)
- Technical approach summary
- Test coverage summary (X tests written, all passing)
- Acceptance criteria table (parent AC → this task's evidence)
- Security review outcome (0 Critical, 0 High, N Medium warnings)
- Code review outcome (0 Blockers, 0 Majors, N Minors deferred)
- Follow-ups (E2E deferred, sub-tasks still to land)
- Reviewer instructions (what to focus on)

Log the PR URL to `commit-run.md`.

---

## 14. Stage 10 — Report summary

**In-terminal:**

```
✓ /dev:commit FEAT-SUP-001-1 complete

Branch:       feature/FEAT-SUP-001-supplier-onboarding-backend  →  develop
PR:           https://github.com/acme/acme-backend/pull/247
Security:     ✓ 0 Critical, 0 High (2 Medium warnings surfaced in PR body)
Code review:  ✓ 0 Blocker, 0 Major  (3 Minor suggestions for follow-up PRs)
Acceptance:   9/9 verified at commit-time (3 deferred-to-e2e)
Context merge: 3 units merged clean · 5 base units carried forward · 0 conflicts

Local state:  REVIEW  ·  MC status:  devReview
Local runbook: features/supplier-onboarding/subtask/backend/dev/local-runbook.md

Next:
  1. Reviewer reviews PR-247
  2. On merge, MC status flips to `done` automatically (webhook)
  3. Semantic merge on base is already reflected in this PR
```

**No new files** at this stage — everything's already written by earlier stages.

**Local state stays `REVIEW`** — human reviewer takes over. On PR merge, a webhook (out of scope for v2.2; noted for v2.3) flips MC status to `done` and updates `status.md` to `DONE`.

---

## 15. The two new skills (specs)

### 15a. `dev-stack-adaptive-code-review`

**Location:** `plugins/dev/skills/dev-stack-adaptive-code-review/SKILL.md`

**Purpose:** dynamic code review during `/dev:commit` Stage 4. Detects the stack, reads the repo's conventions, reviews the diff against those + against parent's Business Rules. NOT stack-specific playbooks — one skill, all stacks.

**Skill file structure:**

- `SKILL.md` — top-level workflow + severity model
- `references/review-dimensions.md` — the 7 dimensions (correctness / conventions / errors / testability / BR enforcement / naming / reuse)
- `references/stack-signals.md` — how to identify the stack-specific idioms to check for (imports from `axios` vs `fetch`, use of `async/await` vs `.then()`, use of `Optional` vs nullability, etc.). **Reused across stacks by pattern, not enumerated per-stack.**

**Absolute rules:**

- Review only the diff, not the whole repo
- One finding per issue — don't repeat the same critique 5 times
- Every Blocker/Major finding must include a concrete fix suggestion, not just "this is wrong"
- Findings must cite line numbers in the diff
- Never invent business rules the parent doesn't declare
- Never require patterns the repo doesn't already use ("could you use dependency injection here" — no; the codebase uses direct instantiation, follow that)

**Threshold config:**

- `severity_block: [Blocker, Major]` at commit-time (from `/dev:commit` Stage 4)
- `severity_block: [Blocker]` if reused from `/dev:build`'s draft path (not currently used; kept in the skill for future flexibility)

### 15b. `tl-semantic-context-merge`

**Location:** `plugins/tl/skills/tl-semantic-context-merge/SKILL.md`

**Purpose:** merge branch's `<repo>/context/code-context/` with base branch's — graph-aware, unit-level, per-field. Invoked from `/dev:commit` Stage 7.

**Under `tl` plugin** because the context graph is TL-owned — this skill authors the same tree `/tl:code-map` and `/tl:plan` produce.

**Skill file structure:**

- `SKILL.md` — the merge workflow + per-field rules
- `references/field-merge-rules.md` — every frontmatter field + body section, with its merge rule
- `references/index-rebuild.md` — how to derive layer indexes from a merged unit set
- `references/conflict-resolution.md` — the 5 conflict types + how to resolve or escalate

**Absolute rules:**

- Never delete a unit that exists on either side without a decision
- Confidence promotion — always take higher (never demote a `Confirmed` back to `Likely`)
- `origin` state precedence: `implemented > reverse-mapped > designed` (the more concrete wins)
- Indexes are DERIVED — never merge index files directly; regenerate from unit set
- `map-coverage.md` merges row-by-row on row id; new rows appended; status column takes `mapped > pending > skipped`
- Cross-repo links resolve against `.jetrix/tl/code-map-registry.md`; missing target → warn, not error
- Unresolved conflict → surface as an open question, halt the merge, tell developer to resolve manually

**Conflict types + resolutions:**

| Conflict | Auto-resolvable? | Rule |
|---|---|---|
| Both sides added the same unit id with different bodies | NO | Flag, halt |
| Both sides modified same body section with divergent content | NO if both non-trivial changes; YES if one is a simple confidence bump | Halt or auto-take higher confidence |
| Branch deleted a unit still on base | NO | Halt, developer confirms removal is intentional |
| Base has a link to a feature branch never merged (dangling) | YES | Preserve — later `/tl:code-map --refresh` will clean up |
| Layer index has both old + new row for same id | YES | Take the branch's row (implemented > designed) |

---

## 16. Local file layout (per task)

Additions on top of `/dev:build`'s layout:

```
.jetrix/features/<slug>/subtask/<repo>/dev/  (or parent's dev/)
├── (files from /dev:build — unchanged)
│
│  (written by /dev:commit)
├── commit-run.md                        ← stage-by-stage progress log (new)
├── pr-summary.md                        ← PR-reviewer-facing (already exists from feature-delivery-loop; /dev:commit rewrites it)
├── code-review-findings.md              ← full findings from Stage 4 (Blockers + Majors fixed; Minors kept for follow-up)
├── security-findings.md                 ← full findings from Stage 3 (Criticals + Highs fixed; Mediums surfaced in PR)
└── escalation-<n>.md                    ← if BLOCKED

<repo>/context/code-context/
└── .merge-report-<timestamp>.md         ← semantic merge audit (gitignored)
```

---

## 17. Status mapping — local + MC

| /dev:commit phase | Local state | MC status |
|---|---|---|
| Start (Stage 1 lock) | `IN_PROGRESS → REVIEW` | `inProgress → devReview` |
| Security review (Stage 3) | `REVIEW` | `devReview` |
| Code review (Stage 4) | `REVIEW` | `devReview` |
| Acceptance verification (Stage 5) | `REVIEW` | `devReview` |
| Fix loop (Stage 6) | `REVIEW → REVIEW_FIXES` | `devReview` |
| Semantic merge (Stage 7) | `REVIEW` | `devReview` |
| Push (Stage 8) | `REVIEW` | `devReview` |
| PR raised (Stage 9) | `REVIEW` (unchanged; human takes over) | `devReview` (unchanged) |
| Escalation | `BLOCKED` | `blocked` |
| PR merged (later, via webhook) | `REVIEW → DONE` | `devReview → done` |

**Parent's status derived** from sub-tasks (per `/dev:plan` §10). When all sub-tasks reach `REVIEW`, parent's status reflects that.

---

## 18. Files to create / modify / delete

### Create

| Path | Purpose |
|---|---|
| [plugins/dev/commands/commit.md](../../plugins/dev/commands/commit.md) | The NEW `/dev:commit` orchestrator |
| [plugins/dev/commands/references/commit/stage-3-security.md](../../plugins/dev/commands/references/commit/) | Strict security review runbook |
| [plugins/dev/commands/references/commit/stage-4-code-review.md](../../plugins/dev/commands/references/commit/) | Code review runbook |
| [plugins/dev/commands/references/commit/stage-5-acceptance.md](../../plugins/dev/commands/references/commit/) | Final acceptance verification runbook |
| [plugins/dev/commands/references/commit/stage-6-fix-loop.md](../../plugins/dev/commands/references/commit/) | Fix loop runbook |
| [plugins/dev/commands/references/commit/stage-7-semantic-merge.md](../../plugins/dev/commands/references/commit/) | Semantic context merge orchestration |
| [plugins/dev/commands/references/commit/stage-8-9-push-pr.md](../../plugins/dev/commands/references/commit/) | Push + PR raise runbook |
| [plugins/dev/skills/dev-stack-adaptive-code-review/SKILL.md](../../plugins/dev/skills/dev-stack-adaptive-code-review/) | Dynamic code review skill (§15a) |
| [plugins/dev/skills/dev-stack-adaptive-code-review/references/review-dimensions.md](../../plugins/dev/skills/dev-stack-adaptive-code-review/references/) | The 7 dimensions |
| [plugins/dev/skills/dev-stack-adaptive-code-review/references/stack-signals.md](../../plugins/dev/skills/dev-stack-adaptive-code-review/references/) | Pattern-based stack idiom checks |
| [plugins/tl/skills/tl-semantic-context-merge/SKILL.md](../../plugins/tl/skills/tl-semantic-context-merge/) | Semantic merge skill (§15b) |
| [plugins/tl/skills/tl-semantic-context-merge/references/field-merge-rules.md](../../plugins/tl/skills/tl-semantic-context-merge/references/) | Per-field merge rules |
| [plugins/tl/skills/tl-semantic-context-merge/references/index-rebuild.md](../../plugins/tl/skills/tl-semantic-context-merge/references/) | Deriving indexes from merged units |
| [plugins/tl/skills/tl-semantic-context-merge/references/conflict-resolution.md](../../plugins/tl/skills/tl-semantic-context-merge/references/) | 5 conflict types + resolutions |

### Modify

| Path | Change |
|---|---|
| [plugins/dev/commands/pr.md](../../plugins/dev/commands/pr.md) | Retire — `/dev:commit` supersedes it. Delete or slim to a deprecation notice pointing at `/dev:commit`. |
| [plugins/dev/dev_readme.md](../../plugins/dev/dev_readme.md) | Add `/dev:commit`; retire `/dev:pr`; note the two new skills |
| [plugins/tl/tl_readme.md](../../plugins/tl/tl_readme.md) | Add `tl-semantic-context-merge` skill (invoked internally by `/dev:commit`, not a user-visible command) |
| [plugins/delivery-os-core/skills/delivery-os-conventions/SKILL.md](../../plugins/delivery-os-core/skills/delivery-os-conventions/) | v2.2 — document the two-gate model (`/dev:build`'s Critical-only vs `/dev:commit`'s Critical+High); update loop-control state model |
| [plugins/dev/skills/feature-delivery-loop/SKILL.md](../../plugins/dev/skills/feature-delivery-loop/) | Reference `/dev:commit` as the PR-handoff phase; remove old inline PR flow |
| [plugins/dev/skills/dev-pr-handoff/](../../plugins/dev/skills/dev-pr-handoff/) | Slim to just the PR-body content generator (used by `/dev:commit` Stage 9); remove the state-transition + tracker-update logic that now lives in `/dev:commit` |

### Delete

| Path | Reason |
|---|---|
| [plugins/dev/commands/pr.md](../../plugins/dev/commands/pr.md) | `/dev:pr` retired; `/dev:commit` supersedes it (or slim to deprecation shim) |

---

## 19. Order of implementation

1. **`delivery-os-conventions` v2.2 confirmed** — same bump `/dev:build` needs; do once for both commands.
2. **Create `dev-stack-adaptive-code-review` skill** — SKILL.md + 2 references. Fully local.
3. **Create `tl-semantic-context-merge` skill** — SKILL.md + 3 references. The most complex piece; test with hand-crafted merge scenarios before going live.
4. **Create the 6 stage reference files** under `plugins/dev/commands/references/commit/`.
5. **Create `plugins/dev/commands/commit.md`** — orchestrator, routes to the 6 stage files.
6. **Slim `plugins/dev/skills/dev-pr-handoff`** — remove state/tracker logic, keep PR-body generator.
7. **Retire `plugins/dev/commands/pr.md`** — delete or leave a deprecation shim.
8. **Update `dev_readme.md` + `tl_readme.md`** — new command + new skills.
9. **Update `feature-delivery-loop/SKILL.md`** — reference the two-gate flow.
10. **Smoke test end-to-end** with a real feature that spans 2+ sub-tasks — verifies semantic merge across parallel branches.

---

## 20. Success criteria

- `/dev:commit FEAT-…-1` after successful `/dev:build` → runs Stages 3-10, pushes branch, raises PR against `develop`
- Any Critical/High security or Blocker/Major code-review finding → repair loop → re-runs → clean → proceeds
- Bounds exceeded → clean escalation with `escalation-<n>.md`, task `BLOCKED`, never pushes
- Semantic merge with base — 0 conflicts on typical cases; unresolvable conflicts surface as open questions, not silent errors
- MC status: `inProgress → devReview` on Stage 1; stays `devReview` through PR raise; PR merge webhook (later) flips to `done`
- Parent's derived status updates automatically when all sub-tasks reach `REVIEW`
- `/dev:commit` before `/dev:build` finishes → clean halt with "run /dev:build first"
- `/dev:commit --dry-run` → runs everything through Stage 7 (semantic merge preview), skips push + PR
- `/dev:commit --base=staging` → PRs against the staging env branch instead of dev

---

## 21. Explicitly out of scope

- Merging the PR — human owns that (per Delivery-OS guardrail)
- Deploying — human/CI owns that
- PR-merge webhook that flips MC status to `done` — v2.3 (noted, not built now)
- Cross-repo PR coordination (e.g. "backend PR must merge before frontend PR") — captured in parent's rollup Sub-tasks table; humans coordinate via that table for v2.2
- Squashing commits before PR — the developer's git workflow, not `/dev:commit`'s responsibility
- Post-merge cleanup (branch deletion, sync-state update) — v2.3
- Re-running `/dev:code-review` as a separate user command — folded into `/dev:commit` for v2.2; can be exposed later if needed

---

## 22. Blockers / open questions

**BC-01** — Semantic merge on cross-repo scenarios (parent has 3 sub-tasks, all separately `/dev:commit`ted with their own semantic merges) — does the LAST sub-task's merge see the previous two? Answer: yes — each sub-task runs semantic merge against its OWN base branch; they don't share a base repo. Non-issue.

**BC-02** — When `dev-pr-handoff` is slimmed, does the existing `pr-summary.md` template need reshaping? Recommendation: minor tweaks — remove state transitions from the template (those move to `/dev:commit`), keep the content-generation parts (purpose, scope, test coverage, AC table). **Owner:** us. **Non-blocking.**

**BC-03** — `tl-semantic-context-merge` skill needs unit tests / merge fixtures to verify correctness before shipping. Recommendation: hand-craft 5 scenarios (new-only, both-modified-same-field, both-modified-different-field, delete-vs-modify, unrelated-additions) and verify the skill's expected output. **Owner:** us. **Non-blocking but critical for v2.2 ship confidence.**

**BC-04** — Config for security-review skill's severity threshold — does the built-in skill accept a threshold param, or do we filter its output ourselves? Verify. **Owner:** verify against Claude Code's `security-review` skill docs. Fallback: filter output client-side.

**BC-05** — `gh` CLI dependency — does every developer have it installed? If not, `/dev:commit` Stage 9 fails at push. Recommendation: check for `gh` in preflight (Stage 0) and error early with install instructions if missing. **Owner:** us. **Non-blocking; add to Stage 0.**

---

**End of `/dev:commit` plan.** Every §-number is a checkable spec. Read together with [dev-build-command.md](dev-build-command.md) for the full build→commit flow.
