---
description: Commit a built task through the full 10-stage commit loop — strict security review (Critical + High blocking, vs /dev:build's Critical-only), dynamic code review via dev-stack-adaptive-code-review (Blocker + Major blocking), final `## Acceptance` table re-verification (regression + last-sub-task E2E), bounded fix loop, semantic-context-merge against baseline via tl-semantic-context-merge (unit-level merge, not text-level), push branch, raise PR with units/<repo>/pr-summary.md, print terminal summary. Flips status to devReview (phase pr-open) on start and stays there on success; the PR-merge webhook flips it to done. Sub-task commits work in the sub-task's repo only. Refuses to run without a completed /dev:build.
argument-hint: "<task-number | Task-N | slug | features/<slug> | tasks/<slug>.md | FEAT-<AREA>-NN | list=<name> | requirement=<slug> | --all | (blank = every task /dev:build finished)> [requirement=<slug>] [--concurrency=N] [--resume] [--skip-security] [--force-context-merge=ours] [--force-push]"
---

# /dev:commit

You are the entry point for the 10-stage commit loop. **Orchestrator only** — parses args, resolves identity, verifies `/dev:build` completed, then routes each stage to its reference file under `plugins/dev/commands/references/commit/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's `units/<repo>/status.md § ## Run history`.

**The single invariant:** `/dev:commit` runs on a completed `/dev:build` or refuses. `status` must be `inProgress` **and** `phase` must be `built` when this command starts — `agentExecuting` means a build is still running.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "every built task"):
- **Task number** — `11` (bare) or `Task-11` / `Feature-11` / `Subtask-11`. A bare integer is accepted wherever a target is, and means `Task-<n>`. This is the normal form — it is what Mission Control shows, and it needs no knowledge of where anything sits on disk.
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/units/backend`
- **Non-feature ticket**: `tasks/<slug>.md` — run state lives at `tasks/<slug>/dev/` (`status.md` § `## Run history`, `status.md`). Every stage is unchanged: same security review, same code review, same acceptance re-verify, same PR. Only the path to the run files differs.
- Internal id: `FEAT-<AREA>-NN`
- Blank: **every task `/dev:build` has finished** — `status: inProgress` · `phase: built` · `ready_for_dev_commit: true`, across `features/*/units/<repo>/status.md` and `tasks/*/units/<repo>/status.md`. Same default as `/dev:plan` and `/dev:build`: blank means the whole set, a target means that one thing.
- `list=<name>` / `requirement=<slug>` / `--all` — resolved as `/dev:plan` §2a resolves them, then filtered to the gate above.

**Flags:**
- `requirement=<slug>` — scope the target set to one requirement
- `--concurrency=N` — how many tasks commit at once. Default `5`, matching `/dev:plan` and `/dev:build`.
- `--resume` — continue from last completed stage per `units/<repo>/status.md § ## Run history`
- `--skip-security` — bypass Stage 3 (requires `SECURITY_REVIEW_OVERRIDE` env + audited reason)
- `--force-context-merge=ours` — auto-resolve Stage 7 conflicts to our-side (emergency)
- `--force-push` — allow `git push --force-with-lease` (rare)

## 1a. Batch semantics

A resolved set of more than one task runs the same ten stages per task, independently.

- **One worker per task**, bounded by `--concurrency=N` (default 5). Each task owns its own repo
  checkout, its own branch, and its own `## Run history`, so workers do not contend.
- **One task's failure never halts the batch.** A blocked security finding, a failed acceptance
  re-verify or a merge conflict stops THAT task at its stage; siblings run on. Failures report
  together at the end, each naming its stage and what the human has to decide.
- **One PR per task**, exactly as a single-target run raises one. A batch of N tasks raises N pull
  requests — say so in the run summary, with every PR URL, so the set is reviewable as a set.
- **`--resume` applies per task**, read from each task's own `## Run history`.

**Every question is asked once, before the batch fans out.** `/dev:build` earns its
background-agent property by never prompting mid-run; a batch of commits has to earn the same one,
because N workers each stopping to ask would interleave their prompts and block the set. So Stage 2's
base-branch confirmation, the `PARTIAL_HARNESS` confirmation from §2, and the `gh` auth check from
Stage 8 all move **ahead** of fan-out, into one consolidated checkpoint:

1. Resolve the set, then group it **by repo** — a base branch is a property of a repo, not of a task,
   so a 19-task batch spanning 3 repos asks three base questions, not nineteen. Each repo's
   recommended default is still its tasks' `status.md` `base_branch:`, the value `/dev:plan`
   confirmed. Where tasks in one repo disagree on `base_branch:`, that is a real conflict — show both
   and make the user pick; never silently take one.
2. Read every task's `stage-8.final_status` from its `## Run history` **before** starting any of them, and
   put all the `PARTIAL_HARNESS` ones in a single confirmation naming each task and its red gate.
   A task the user declines is dropped from the set, not failed.
3. Check `gh` auth once for the whole run.
4. Write the answers into each task's `status.md` — `stage-2.base_confirmed_by_user: true` plus the
   chosen base — so Stage 8a's precondition finds what it requires per task.

**After this checkpoint no worker prompts.** A decision a worker discovers mid-run that would need
the user is not a prompt: it halts that task with a `BLOCKED` entry naming the decision, and the
batch reports it at the end alongside the other halts. A single-target run keeps asking inline
exactly as it does today — there is nothing to consolidate.

## 2. Stage 0 — Identity resolution + branch verification (hard gate)

Same resolution as `/dev:plan` Stage 0 / `/dev:build` Stage 0 — see `plugins/dev/commands/plan.md` §2a, including the multi-target forms. Determine `task_kind` (parent-alone or sub-task) and canonical `(feature_id, task_object_id, task_number, task_folder)` **per task in the resolved set**.

**Verify `/dev:build` completed.** Check `status.md`:
- `status: inProgress` · `phase: built`
- `ready_for_dev_commit: true`
- `branch:` field non-empty

Any missing → this task is not built. **Single target:** halt with the "run /dev:build first" message. **Batch:** skip it, keep its reason, and report it with the other skips at the end — one unbuilt task must never stop the tasks that are ready.

**Read the build verdict** from `units/<repo>/status.md § ## Run history` — the field is `stage-8.final_status`, **not** `stage-8.status`, which only ever holds `DONE` or `BLOCKED` and would match none of the rows below. `IN_PROGRESS` alone does not distinguish a clean build from one that advanced carrying a red Required gate:

| `stage-8.final_status` | Action |
|---|---|
| `COMPLETE` · `PARTIAL_DEFERRED` | proceed |
| `PARTIAL_HARNESS` | a Required gate is red for a **harness** reason, not a defect. Proceed only after `AskUserQuestion` confirms, and carry the `harness_config_remedy` and flaky rows into Stage 5 (§5b.i) and the PR body. Never report this run as green |
| `PARTIAL_FAILURES` | **halt** — an unfixed defect. Name the red rows; `/dev:build` should not have advanced |

**Read `tests_only`** from the same file. When `true`, build Stages 9–11 were skipped by design: expect no `context/code-context/**` changes and no `units/<repo>/pr-summary.md § ## How to verify`, and never treat their absence as a missed stage.

**`tests_only: true` scopes the review to what actually changed.** A run that may not edit product code has produced no product-code diff, so reviewing the whole branch at feature grade costs a long run and reports findings this commit did not introduce. Scope each stage to **the files this commit adds or modifies**:

| Stage | Under `tests_only` |
|---|---|
| 3 security | Scan the committed files for secrets — **always**, a test fixture is a common place to leak one. Skip the product-code review *only where no product file is in the diff*; where the branch does carry product changes, review those at the normal threshold |
| 4 code review | Review the test files — assertion strength, tier honesty, no disabled or loosened tests. Skip the product-code dimensions that have no diff to read |
| 5 acceptance | Unchanged — re-verify every row. This is the stage that catches code edited between build and commit |
| 7 context merge | Unchanged — it is cheap, and a zero-change result is the expected outcome |

**Check the diff, do not assume it.** `tests_only` says the *build* wrote no product code; it does not promise the branch carries none — earlier harness commits often do. Read `git diff <base>...HEAD`, and where product files appear, review them normally and say so. Report pre-existing findings as pre-existing, never as introduced by this commit.

**Verify branch is checked out** in the target repo: `git rev-parse --abbrev-ref HEAD` matches the branch recorded in `status.md`. Mismatch → halt with "checkout the feature branch first: `git checkout <branch>`".

**Verify no uncommitted changes** (`git status --porcelain` empty) UNLESS `--resume` and we're in Stage 7 halt state — in which case pending manual edits are allowed on `dev/context-merge-conflicts.md` and touched context files.

## 3. Stage 1 — Acquire lock + flip status

- Write owner into `status.md` (agent id)
- status `devReview` · phase `pr-open` (broadcast)
- MC: `inProgress → devReview` via `task-mcp.update_task_status`
- Read parent BA files (`feature.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`) — validation contract; passed to Stages 4 + 5
- Read `units/<repo>/status.md § ## Run history` (Stage 10's `context_units_updated:` list, Stage 9's build-time security findings)
- Read `units/<repo>/status.md § ## Acceptance` (build-time results, feeds Stage 5)
- Read `units/<repo>/status.md § ## Run history` (detected_stack + inferred_patterns, feeds Stage 4)
- Record start in `units/<repo>/status.md § ## Run history`

## 4. Stage 2 — Base branch selection + pull (v2.3.25 — user confirmation required; base branch pulled locally before Stage 7)

**Step 1 — Take the default from the plan, not from scratch:**

- **`status.md` `base_branch:`** — the value the user confirmed at `/dev:plan`'s checkpoint, and the branch
  this work was actually cut from. It is the recommended option.
- **Missing** (a plan predating that field) → fall back to `apps[].env_branches.dev` for the sub-task's repo,
  or the primary product repo's for a parent-alone run, and say in the prompt that it came from
  `project.json` rather than from a confirmed plan.

**Step 2 — Confirm with the user via `AskUserQuestion` (v2.3.25 — no more silent defaulting):**

```
Which branch is this PR merging INTO?

  [<default from project.json — highlighted as recommended>]  — e.g. develop
  [main / master]                                              — allowed only with explicit override; refuses if branch-protected
  [staging / release/*]                                        — release-train branches; typed by user
  [other]                                                      — user types the exact branch name
```

Rationale: silent defaulting hid mistakes when a repo's `env_branches.dev` was stale or pointed at a branch the user didn't actually intend. Asking once surfaces the decision.

**In a batch this question has already been answered** — §1a's pre-flight asks it per repo before fan-out and writes the result into each task's `status.md`. A worker that finds `stage-2.base_confirmed_by_user: true` already set uses that base and does not ask again. Only a single-target run reaches the prompt above.

If user picks `main` / `master` / `production` OR the branch is under branch-protection → refuse UNLESS user passes `--allow-protected-base` on the same run. Standard commit flow always targets a mutable dev branch.

**Step 3 — Fetch + pull the base branch locally (v2.3.25 — REQUIRED for Stage 7):**

```bash
cd <target-repo>
git fetch <remote>
git fetch <remote> <base>:refs/remotes/<remote>/<base>
```

Stage 7's semantic context merge needs the base branch's context units on disk to reconcile against. Without this step, Stage 7's tl-semantic-context-merge either hallucinates a diff or (as the user just observed) rationalizes itself into a no-op. This pull is what makes the merge REAL.

Verify:
- `git log HEAD..<remote>/<base>` — must be empty (this feature branch is descendant of base). If NOT empty → halt: "rebase your feature branch against <base> and re-run: `git rebase <remote>/<base>`".
- `git rev-parse <remote>/<base>` — record base's tip SHA to `status.md` § `## Run history`.
- Base build green check (best-effort: read last CI status via `gh` if available); non-green is a WARN, not a halt.

Log to `status.md` § `## Run history`:

```yaml
stage-2:
  status: DONE
  base_branch: develop
  base_confirmed_by_user: true         # from Step 2's AskUserQuestion answer
  base_remote_sha: <sha>               # recorded for Stage 7 + Stage 8 preconditions
  base_pulled_at: <ISO>
  base_ci_status: green | non-green | unknown
```

## 5. Route to Stages 3–9

Read each stage's reference file and execute verbatim. Fix loop is inline routing between Stages 3-5 (see Stage 6 file for the loop mechanics).

### When a required tool cannot run

A stage's tool may **refuse to start** rather than return findings — `security-review` needs a git repository and halts when the session's working directory is the folder *above* the repo; a skill may be unavailable in this environment. This is not a finding, so the fix loop has nothing to act on, and it is not a defect, so halting the run strands finished work over an environment condition.

Do **not** halt, and do **not** silently skip. For each stage whose tool refuses:

1. **Record the refusal verbatim** in `status.md` § `## Run history` under that stage — the exact error text, not a paraphrase:
   ```yaml
   stage-3:
     tool: security-review
     tool_status: not-invocable
     tool_error: "<the tool's exact message>"
     method: manual            # the stage's own criteria, applied by hand
   ```
2. **Do the check by hand** against that stage's own criteria and threshold, and record the result in the stage's normal fields. A manual pass is a real pass — it is the *evidence trail* that differs, not the bar.
3. **Say so in the PR body.** A reviewer must be able to see which checks were tool-run and which were manual without opening `status.md` § `## Run history`.
4. **Never record a tool run that did not happen.** `tool_status: not-invocable` with `method: manual` is honest; omitting the field and filling in the findings as though the tool produced them is a spec violation and worse than halting.

Where the refusal is fixable, name the fix in the summary rather than only reporting it — for `security-review`, that is running `/dev:commit` from inside the repository rather than from a parent folder.

### Stage 3 — Strict security review

**Read** `plugins/dev/commands/references/commit/stage-3-security.md` and execute verbatim. Invokes Claude Code's `security-review` skill at Critical+High threshold. Any finding routes to Stage 6 fix loop.

### Stage 4 — Dynamic code review

**Read** `plugins/dev/commands/references/commit/stage-4-code-review.md` and execute verbatim. Invokes `dev-stack-adaptive-code-review` skill. Blocker+Major findings route to Stage 6 fix loop.

### Stage 5 — Final `## Acceptance` table verification

**Read** `plugins/dev/commands/references/commit/stage-5-acceptance.md` and execute verbatim. Re-runs every `## Acceptance` table row's test; deferred-to-e2e resolves if this is the last sub-task landing. Regression routes to Stage 6 fix loop.

### Stage 6 — Bounded fix loop

**Read** `plugins/dev/commands/references/commit/stage-6-fix-loop.md`. Not a standalone stage — invoked from Stages 3, 4, or 5 when findings block. After each fix batch, upstream stages re-run in order. Bounds exceeded → escalation + halt.

### Stage 7 — Semantic context merge (v2.3.25 — MANDATORY EXECUTION, not skippable)

**Read** `plugins/dev/commands/references/commit/stage-7-semantic-merge.md` and execute verbatim. Delegates to `tl-semantic-context-merge` skill. Halts cleanly on conflict with `dev/context-merge-conflicts.md` for human resolution.

**Rule (v2.3.25):** this stage MUST invoke `tl-semantic-context-merge` skill via the Skill tool with observable trace. The skill invocation is verified in `status.md` § `## Run history` as:

```yaml
stage-7:
  status: DONE
  tl_semantic_context_merge_invocation:
    invoked_at: <ISO>
    invocation: <subagent id | "inline">          # "inline" when the Skill tool returns no id
    base_ref: <remote>/<base>@<sha>              # must match stage-2.base_remote_sha
    input_units_scanned: <count of context/code-context files touched by this run>
    baseline_units_scanned: <count from base branch>
    merged_units: <count>
    conflicts: <count>
    conflict_file: dev/context-merge-conflicts.md   # or null if no conflicts
  merged_at: <ISO>
```

**"I reasoned it would be a no-op and skipped" is NOT permitted (v2.3.25 — user-reported gap).** Even if the skill reports zero-changes, it MUST run and record its no-op result. The skill's own log is the evidence of execution; internal reasoning is not.

Stage 8's precondition (§8a below in `stage-8-9-push-pr.md`) verifies this block exists in `status.md` § `## Run history`. If missing → Stage 8 HALTS with `blocker: stage-7-not-executed`.

### Stage 7.5 — Gather working-tree changes + structure commit(s) (v2.3.20 — REQUIRED)

**`/dev:build` writes to the working tree without committing** (per its top-of-file invariant). `/dev:commit` owns the commit boundary. This stage runs BEFORE Stage 8 (push).

**Read** `plugins/dev/commands/references/commit/stage-7-5-gather-and-commit.md` and execute verbatim. Summary of what it does:

1. **Scan the working tree** in the target repo (parent-alone → primary product repo; sub-task → sub-task's repo per `subtask_repo` frontmatter). Enumerate every modified / new / deleted file. Categorize each file:
   - `src/*` — source code changes (Stages 5-6 output)
   - `tests/*` — test code changes (Stages 5-6 output)
   - `context/code-context/*` — context-unit updates (Stage 10 output)
   - `units/<repo>/pr-summary.md § ## How to verify` — runbook (Stage 11 output — LOCAL only, NEVER pushed to remote; excluded from commit)
   - Other — surface as a warning, ask which category (source / test / context / dev-only-do-not-commit)

2. **Structure commit(s) — default: ONE well-formed commit for the whole task's diff.** Message follows the convention:

   ```
   feat(<domain>): <what shipped in this task, from parent's feature.md Objective, one line>

   Sub-task: <task-ref, e.g. FEAT-HCAL-01-1 backend>
   §1 Build sequence steps: <N> steps landed
   Tests: <M> tier(s), <`status.md` § `## Acceptance` row count> parent AC/BR/TS covered

   Refs: <parent's business-rules that this sub-task enforced, comma-separated>
   ```

3. **Alternative: `--structured` flag** for multi-commit convention (docs / feat / refactor / test / chore — one per category above). Same author identity, same head-of-branch commit for the PR.

4. **Never commits `units/<repo>/pr-summary.md § ## How to verify`** — LOCAL developer artefact only.

5. **Never commits secrets** — final `grep` for `.env*`, `*credentials*`, `*secret*`, `*token*`, `*.pem`, `*.key` file patterns; if any found in the stage-worthy set, HALT with `blocker: secrets-in-staged-set` — do NOT auto-add to a gitignore, halt for human review.

6. **Commit stays on branch** — do NOT rebase, do NOT push in this stage. Stage 8 pushes.

If the working tree has nothing to commit (someone already committed manually mid-flow) → skip this stage cleanly, log to `units/<repo>/status.md § ## Run history`, continue to Stage 8.

### Stage 8 — Push the branch

**Read** `plugins/dev/commands/references/commit/stage-8-9-push-pr.md` §Stage 8 and execute verbatim.

### Stage 9 — Raise the PR

**Read** `plugins/dev/commands/references/commit/stage-8-9-push-pr.md` §Stage 9 and execute verbatim. PR body = `units/<repo>/pr-summary.md`.

## 6. Stage 10 — Report summary

In-terminal summary:

```
✓ /dev:commit FEAT-SUP-001-1 complete

Task:          Subtask-7 (backend)  ·  Feature-4 Supplier Onboarding
MC parent:     https://mission-control.techjays.com/task/6a94fe0ebc48d4e7d1cab15b
MC sub-task:   https://mission-control.techjays.com/task/6b72a1c48d4e7d1cab2c7
PR:            https://github.com/acme/acme-backend/pull/247

Branch:        feature/FEAT-SUP-001-supplier-onboarding-backend  →  develop
Security:      ✓ 0 Critical, 0 High  (2 Medium warnings surfaced in PR body)
Code review:   ✓ 0 Blocker, 0 Major  (3 Minor follow-ups in PR body)
Acceptance:    ✓ 9/9 verified at commit-time (3 deferred-to-e2e)
Context merge: 3 units merged clean · 4 base units carried forward · 0 conflicts
Push:          ✓ 9 commits pushed to origin
PR:            ✓ opened by /dev:commit

Status:        devReview        (flips to done on PR-merge webhook — future)

Local runbook: features/supplier-onboarding/units/backend/pr-summary.md § ## How to verify
PR summary:    features/supplier-onboarding/dev/backend-pr-summary.md

Next:
  1. Reviewer reviews PR-247   (link above)
  2. Reviewer left comments?  /dev:fix-review FEAT-SUP-001-1 pr=<link>
     folds them back through the commit stages — do not hand-patch the branch
  3. On merge, MC status flips to `done` automatically (webhook — v2.3)
```

**Step 2 is not optional boilerplate.** Of the three lines, it is the only one with work in it, and a
reviewer comment fixed by hand skips the security review, the acceptance re-verify and the context merge
that `/dev:commit` just ran. Name it every time, with the task id already filled in.

**Navigation URL sources (v2.3.17 — task-mcp is the URL source of truth):**

- **MC parent** — call `task-mcp.get_task_by_id_or_number(solution_id, feature.md `jetrix_task_object_id`)`; use `.view_url` from the response. task-mcp constructs the URL server-side using its own `mission_control_ui_url` env var.
- **MC sub-task** — same pattern: `get_task_by_id_or_number(solution_id, units/<repo>/status.md `jetrix_subtask_object_id`)`; use `.view_url`.
- **PR** — from `units/<repo>/status.md § ## Run history` stage-9's `pr_url` (written by Stage 9)

Do NOT construct MC URLs locally from `.jetrix/project.json` `mission_control_ui_url` — task-mcp's own env var is the source of truth and the two may drift. task-mcp's returned `view_url` is guaranteed correct.

All three URLs are must-haves in the terminal summary — the whole point of this stage is to give the developer + reviewer clickable jumps to every relevant surface. If any URL cannot be resolved via task-mcp response, print `(not resolvable from MC)` inline, do NOT invent a URL.

No file writes at Stage 10 — pr-summary + commit-run + delivery-status are already written by earlier stages.

## 7. Failure surfaces

- **Any stage BLOCKED** (Stage 6 bounds exceeded) → local `BLOCKED`, MC `blocked`, `units/<repo>/status.md § ## Run history (a BLOCKED entry)`, halt
- **Stage 7 semantic-merge conflict** → status `devReview` (phase `merge-conflict`), `dev/context-merge-conflicts.md`, halt
- **Stage 8 push rejected** → status stays `devReview` (phase `pr-open`), halt with git error verbatim
- **Stage 9 PR creation failed** → status stays `devReview` (phase `pr-open`), halt with `gh` error verbatim
- **`/dev:commit` on task at `readyForDev` or `agentExecuting`** → refuse (§2 hard gate). Route to `/dev:build`; on `agentExecuting` say a build is already running rather than inviting a second one

## 8. Guardrails

- Never invent behaviour not in `implementation.md` or resulting from a Stage 6 fix
- Never bypass Stage 3 security review without the `SECURITY_REVIEW_OVERRIDE` env
- Never bypass Stage 7 semantic merge without `--force-context-merge=ours`
- Never `git push --force` without `--force-push`
- Never `--no-verify` on push
- Never mark MC status `done` here — reserved for the PR-merge webhook
- Never modify secrets or `.env` files
- Never rebase automatically — halt and instruct if branch is behind base
- Every material design choice → `DEC-###` in `dev/decisions.md`
- Never move MC status to `blocked` for a Stage 7 conflict — that's `devReview` (local only) awaiting human input
