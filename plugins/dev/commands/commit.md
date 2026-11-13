---
description: Commit a built task through the full 9-stage commit loop — dynamic code review via dev-stack-adaptive-code-review (Blocker + Major blocking), final `## Acceptance` table re-verification (regression + last-sub-task E2E), bounded fix loop, semantic-context-merge against baseline via tl-semantic-context-merge (unit-level merge, not text-level), push branch, raise PR with units/<repo>/pr-summary.md, print terminal summary. Flips status to devReview (phase pr-open) on start and stays there on success; the PR-merge webhook flips it to done. Sub-task commits work in the sub-task's repo only. Refuses to run without a completed /dev:build.
argument-hint: "<task-number | Task-N | slug | features/<slug> | tasks/<slug>.md | FEAT-<AREA>-NN | list=<name> | requirement=<slug> | --all | (blank = every task /dev:build finished)> [requirement=<slug>] [--concurrency=N] [--resume] [--clear-locks] [--force-context-merge=ours] [--force-push]"
---

# /dev:commit

You are the entry point for the 9-stage commit loop. **Orchestrator only** — parses args, resolves identity, verifies `/dev:build` completed, then routes each stage to its reference file under `plugins/dev/commands/references/commit/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's `units/<repo>/status.md § ## Run history`.

**The single invariant:** `/dev:commit` runs on work that is finished, or refuses. `status` must be `inProgress` and `phase` must be **`built`** (Delivery OS wrote it) or **`adopted`** (someone else did, and Stage 0 took it in). `agentExecuting` means a build is still running.

**Two routes, one gate layer.** Route A arrives at `built` from `/dev:build`. Route B arrives at `adopted` from Stage 0, having never been planned or built here. Both then run the same code review and delivery — see §2's route table for the stages Route B skips.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "every built task"):
- **Task number** — `11` (bare) or `Task-11` / `Feature-11` / `Subtask-11`. A bare integer is accepted wherever a target is, and means `Task-<n>`. This is the normal form — it is what Mission Control shows, and it needs no knowledge of where anything sits on disk.
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/units/backend`
- **Non-feature ticket**: `tasks/<slug>.md` — run state lives at `tasks/<slug>/dev/` (`status.md` § `## Run history`, `status.md`). Every stage is unchanged: same code review, same acceptance re-verify, same PR. Only the path to the run files differs.
- Internal id: `FEAT-<AREA>-NN`
- Blank: **every task that is finished and uncommitted** — `status: inProgress` · `phase: built` **or** `adopted` · `ready_for_dev_commit: true`, across `features/*/units/<repo>/status.md` and `tasks/*/units/<repo>/status.md`. Same default as `/dev:plan` and `/dev:build`: blank means the whole set, a target means that one thing.
- `list=<name>` / `requirement=<slug>` / `--all` — resolved as `/dev:plan` §2a resolves them, then filtered to the gate above.

**Flags:**
- `requirement=<slug>` — scope the target set to one requirement
- `--concurrency=N` — how many tasks commit at once. Default `5`, matching `/dev:plan` and `/dev:build`.
- `--resume` — continue from last completed stage per `units/<repo>/status.md § ## Run history`
- `--clear-locks` — remove every `.jetrix/cache/session.json` row for the resolved repo and print what was removed, then stop. Runs no stages

**Delivering only part of a file?** Stage the hunks you mean first, then answer
`[b] index only` at the scope prompt:

```
git add -p src/auth/session.ts
/dev:commit
```

Per-hunk selection inside the prompt is deliberately not built — git already has
the right tool for it.
- `--force-context-merge=ours` — auto-resolve Stage 7 conflicts to our-side (emergency)
- `--force-push` — allow `git push --force-with-lease` (rare)

## 1a. Batch semantics

A resolved set of more than one task runs the same ten stages per task, independently.

- **One worker per task**, bounded by `--concurrency=N` (default 5). Each task owns its own repo
  checkout, its own branch, and its own `## Run history`, so workers do not contend.
- **One task's failure never halts the batch.** A blocked code-review finding, a failed acceptance
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
2. Read every task's `build.stage-8.final_status` from its `## Run history` **before** starting any of them, and
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

**Verify the work is finished.** Check `status.md`:
- `status: inProgress` · `phase: built` **or** `adopted`
- `ready_for_dev_commit: true`
- `branch:` field non-empty

**No `status.md` at all is not a failure — it is Route B.** Changes exist with no
record, so Stage 0's scope detection takes them in (§2a.2) and writes the record
at `adopted`. Refusing here is what sent a real run down the improvised-scope path
that found three of five planted defects.

Any missing → this task is not built. **Single target:** halt with the "run /dev:build first" message. **Batch:** skip it, keep its reason, and report it with the other skips at the end — one unbuilt task must never stop the tasks that are ready.

**Read the build verdict** from `units/<repo>/status.md § ## Run history` — the field is `build.stage-8.final_status`, **not** `build.stage-8.status`, which only ever holds `DONE` or `BLOCKED` and would match none of the rows below. `IN_PROGRESS` alone does not distinguish a clean build from one that advanced carrying a red Required gate:

| `build.stage-8.final_status` | Action |
|---|---|
| `COMPLETE` · `PARTIAL_DEFERRED` | proceed |
| `PARTIAL_HARNESS` | a Required gate is red for a **harness** reason, not a defect. Proceed only after `AskUserQuestion` confirms, and carry the `harness_config_remedy` and flaky rows into Stage 5 (§5b.i) and the PR body. Never report this run as green |
| `PARTIAL_FAILURES` | **halt** — an unfixed defect. Name the red rows; `/dev:build` should not have advanced |

**Read `tests_only`** from the same file. When `true`, build Stages 9–11 were skipped by design: expect no `context/code-context/**` changes and no `units/<repo>/pr-summary.md § ## How to verify`, and never treat their absence as a missed stage.

**`tests_only: true` scopes the review to what actually changed.** A run that may not edit product code has produced no product-code diff, so reviewing the whole branch at feature grade costs a long run and reports findings this commit did not introduce. Scope each stage to **the files this commit adds or modifies**:

| Stage | Under `tests_only` |
|---|---|
| 4 code review | Review the test files — assertion strength, tier honesty, no disabled or loosened tests. Skip the product-code dimensions that have no diff to read |
| 5 acceptance | Unchanged — re-verify every row. This is the stage that catches code edited between build and commit |
| 7 context merge | Unchanged — it is cheap, and a zero-change result is the expected outcome |

**Check the diff, do not assume it.** `tests_only` says the *build* wrote no product code; it does not promise the change set carries none — earlier harness commits often do. Read `git diff <base>..$SNAP` (the review snapshot, below), and where product files appear, review them normally and say so. Report pre-existing findings as pre-existing, never as introduced by this commit.

**Verify branch is checked out** in the target repo: `git rev-parse --abbrev-ref HEAD` matches the branch recorded in `status.md`. Mismatch → halt with "checkout the feature branch first: `git checkout <branch>`".

### 2a.1. Scope detection — what this run is about to review

**There is no clean-tree check.** There used to be — *"verify no uncommitted
changes, `git status --porcelain` empty"* — and it was the single line that made
the happy path impossible: `/dev:build` leaves its entire output uncommitted by
design, so every properly-built task was refused here. Restoring it in any form
re-breaks the flow.

A dirty tree is the **expected** state at this point. Establish what is in it:

1. **Build the detection snapshot** — `references/common/review-snapshot.md` §1,
   with no pathspec. This is a read: the working tree, the real index and HEAD are
   all untouched.

2. **Nothing in it → stop cleanly.** `git diff --quiet <base>..$DETECT` means there
   is nothing to review and nothing to deliver. Halt with `blocker: empty-scope`,
   one line, exit 0. **No commit, no empty commit, no push, no PR.**

3. **Build the review snapshot** from the paths in scope. Record its sha as
   `snapshot_sha` in `status.md` § `## Run history`, and put it in the header of
   every findings section this run produces. Stages 4 and 5 both read this one
   snapshot, so they review the same bytes as each other and as what Stage 7.5
   will stage.

**Scope selection comes in Phase 2.** Until then the review snapshot covers the
whole working tree, which is correct for a Route A run: `/dev:build` produced
everything in it. The per-file prompt, the staged/unstaged split and the
collapse rule are specified in `review-snapshot.md` §3 and wired later.

**A stage that cannot build a snapshot does not review.** It halts with the
blocker code and says so. It never falls back to reading files by judgement and
reporting that as a review — that failure looks like success and ends the search.

`--resume` after a Stage 7 halt is the one case where pending manual edits are
expected: `dev/context-merge-conflicts.md` and the touched context files carry the
human's resolution. Recompute the snapshot rather than comparing against the old
one — the tree legitimately moved.

### 2a.2. Route and mode — decided once, here

Before any stage runs, Stage 0 answers two questions from the detection
snapshot: **which route**, and **what scope**.

| | Route A | Route B |
|---|---|---|
| Who wrote the code | `/dev:build`, from a plan | a person, an AI, another tool |
| Arrives with | `status.md` at `phase: built` | nothing on disk |
| Record | already exists | **Stage 0 writes one** (§2a.4) |
| Phase | `built` | `adopted` |

Four modes follow from what the snapshot holds:

| Mode | Detection | Action |
|---|---|---|
| **1 — task-aware** | a `status.md` matches the changed paths | Route A, full stage set |
| **2 — local change** | changes exist, no record matches | Route B — adopt (§2a.3), reduced stage set (§2a.6) |
| **3 — mixed** | some paths belong to a record, others do not | **ask once** which set to deliver (§2a.3); never guess a theme |
| **4 — no change** | detection snapshot is empty | halt `empty-scope`, exit 0 |

**Decide once, in the orchestrator, before any fan-out.** A worker never
re-derives its route, and never prompts.

### 2a.3. Adoption — automatic, no command

Mode 2 or 3 means changes exist that no record covers. **Take them in here.**
There is no adopt command and none is planned: this is a step of Stage 0, the
same way `/dev:plan` builds the context graph by running
`tl-feature-planning` with no slash command of its own (`delivery-os-conventions`
§1.f). **A next-step block may never print one.**

Confirm once, then write:

```
No task record matches the changes in Inhouse-server.
  12 files changed (+340 / -28)

  Adopt them as a task and validate?  [Y/n]
    slug: auth-session-expiry        type: bug (inferred from the diff)
```

`n` stops cleanly, writing nothing.

On `Y`, write **two files**, both inside gitignored `.jetrix/`:

```
tasks/<slug>.md                       short description, inferred type
tasks/<slug>/units/<repo>/status.md   status: inProgress · phase: adopted
                                      scope_selected[] · scope_excluded[]
```

| Do | Do not |
|---|---|
| infer the slug and `task_type` from the diff, and **state both** so they can be corrected | write any tracker id — the record is local until `/jetrix:push task <slug>` is run deliberately |
| resolve the touched surfaces from the code-context graph (`plan.md` §2a.1 — already implemented) | compose a `## Build sequence` — the work is done; a plan for finished work is backwards |
| record the selected and excluded path sets | run blocker detection — you cannot block work that already exists |

**The record exists so findings have a file, `--resume` has state, and
`## Settled` has somewhere to carry an accepted finding to the next run.** It
is not a ticket and nothing appears on any board.

`implementation.md` for an adopted task is written **after** review, from the
delivered diff, as a record of what was done.

### 2a.4. Mixed scope — ask once

Mode 3 means the tree holds both the recorded work and something else. Present
the full set grouped by directory, with each path's git state, and let the user
tick — the prompt, the collapse rule for untracked directories, and the
staged-vs-unstaged `[a]`/`[b]` split are all specified in
`references/common/review-snapshot.md` §3.

Two rules carry from there and matter most here:

- **Never silently exclude a file.** Absent from the list is a bug; present and
  unticked is a decision.
- **Record `scope_selected[]` and `scope_excluded[]`** in the record's
  `status.md`, so a later run and a reviewer both see what was left out.

Asked **once, at this checkpoint**. No worker prompts after fan-out.

### 2a.5. Scope certainty — halt rather than improvise

**A run that cannot determine its scope does not review.** If the snapshot
cannot be built, or the user abandons the scope prompt, halt with the blocker
code and stop.

Never fall back to reading files by judgement and reporting the result as a
review. That is what produced a confident three-of-five on a commit carrying
five known defects: no task, no acceptance map, no stated file set, and an
answer that read as complete.

**Every review stage states its scope in its findings header** — the snapshot
sha and the file count it covered. A reviewer with no snapshot has nothing to
state, and must say so.

### 2a.6. Route B runs a reduced stage set

Code review needs only a diff and the repo's own standards.
Everything that exists to validate work *against a ticket* has nothing to read
on Route B and does not run.

| Stage | Route A | Route B |
|---|---|---|
| 1 lock + read BA files + flip tracker status | all three | **lock only** — no BA files exist, no ticket to flip |
| 2 base + snapshot | yes | yes, with the Route B base ladder below |
| **4 code review** | yes | **yes — the point** |
| 5 acceptance | re-verify the ticket's rows | **reduced** — run the tests that exist, check they cover the diff, report gaps |
| 6 fix loop | yes | yes |
| 7 semantic context merge | yes | **skipped** — no build flipped a unit, so there is nothing to merge |
| 7.5 commit · 8 push · 9 PR | yes | yes |

**No tracker write happens on Route B at all** unless the user asks for one.

### 2a.7. Route B base branch

Route A reads `status.md` `base_branch:`, the value confirmed at `/dev:plan`'s
checkpoint, and never re-derives it. Route B has no plan, so:

1. the current branch's upstream (`git rev-parse --abbrev-ref @{u}`)
2. `apps[].env_branches.dev` for this repo from `project.json`
3. **ask**, at this checkpoint

Unresolvable → `blocker: base-unresolvable`, printing the ladder tried.

### 2a.8. How far Route B may infer

**Infer technical context; never invent a business requirement.** The decision
is mechanical, not a judgement — a judgement rule here would depend on the agent
classifying its own situation correctly, which is the thing that already failed.
Evaluate against the review snapshot:

```
ASK — never infer — when ANY of these holds:

  1. the diff touches more than one top-level source directory
  2. any changed path matches:  auth | login | session | token | password
                                payment | billing | invoice | refund
                                crypto | secret | permission | role | acl
  3. the diff touches an endpoint unit whose code-context `## Auth`
     section is non-empty
  4. a changed source file has no test covering it
  5. the diff deletes or weakens an existing check
     (a removed guard, a loosened comparison, a widened scope)

otherwise INFER, and mark every row `source: inferred`
```

Every inferred acceptance row carries four things: `source: inferred`, the diff
hunk it came from, the behaviour inferred, and the test that covers it (or its
absence). A reader must always be able to separate *what the ticket asked for*
from *what the implementation implies*.

All asking happens at this checkpoint — the no-prompt-after-fan-out invariant
holds for Route B exactly as for Route A.

## 3. Stage 1 — Acquire lock + flip status

- **Refuse a colliding run first**, exactly as `/dev:build` Stage 1 does: a live, non-stale row in `.jetrix/cache/session.json` for this repo halts with `blocker: repo-locked`. Per repo path, not per task — a Route A build and a Route B commit share one working tree and must not run together
- **Declare this session.** Append a row per `references/common/session-marker.md`: `kind: commit`, repo, task ref, `started_at`, `gates_passed: false`, `deny: {git_push: true}`. Push stays refused until Stage 7.5 flips `gates_passed`
- Write owner into `status.md` (agent id)
- status `devReview` · phase `pr-open` (broadcast)
- MC: `inProgress → devReview` via `task-mcp.update_task_status`
- Read parent BA files (`feature.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`) — validation contract; passed to Stages 4 + 5
- Read `units/<repo>/status.md § ## Run history` (Stage 10's `context_units_updated:` list)
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

## 5. Route to Stages 4–9

**On Route B, Stage 7 does not run and Stages 1 and 5 are reduced** — §2a.6. Record
the skip explicitly in `status.md` § `## Run history` as
`stage-7: {status: SKIPPED, reason: route-b-no-context-units}`. A stage that was
never applicable must not read as a stage that was forgotten, and Stage 8's
precondition checks for the trace either way.

Read each stage's reference file and execute verbatim. Fix loop is inline routing between Stages 4-5 (see Stage 6 file for the loop mechanics).

### 5a. The reviewers are two fresh-context agents, run in parallel

Stages 4 and 5 are **read-only reviews of one snapshot**, so they run at the
same time, each as its own agent with its own context.

```
commit:<repo>
  ├─ review:code:<repo>        dev-stack-adaptive-code-review    read-only
  └─ review:tests:<repo>       dev-test-verifier                 read-only
```

**Readers parallel, writers serial.** Both reviewers at once is safe. Two
repair agents in one working tree collide, so Stage 6 is always serial (§6).

#### What each reviewer is given — and what it is not

| Given | Withheld |
|---|---|
| the snapshot sha and `git diff <base>..$SNAP` | `analysis.md` |
| the repo path | `implementation.md` |
| `shared-context/coding-standards.md § <repo>` | `status.md § ## Run history` |
| the parent's `business-rules.md` (Route A) | any statement of what the build believed it had done |
| the open findings and `## Settled` | any verdict to write, or to prefer |

> *"Do NOT pass: the builder's diary or any plan/reasoning files, and never a
> verdict to write or to prefer. The reviewer forms independent judgment."*

This is the point of the tier. An agent that inherits the build's reasoning is
primed to accept the code it just watched being written; one handed a diff and
the repo's own standards is not.

#### Review classes

| Reviewer | Class | Blocks? |
|---|---|---|
| `dev-stack-adaptive-code-review` (Stage 4) | adversarial | Blocker + Major |
| built-in `code-review` (Stage 4, second opinion) | **advisory** | never |
| test-verifier (Stage 5) | adversarial on required gates, advisory on inferred rows | required gates only |

**Adversarial** means findings route to the fix loop and the stage re-runs.
**Advisory** means one pass, recorded, never blocking — it informs the human at
the gate. An advisory reviewer that blocks has been miscategorised.

#### Concurrency

Print this before fan-out, every time:

```
Repositories: 3   concurrency 3
Reviewers per commit: 2        peak reviewer agents: 6
Review mode: parallel          Repair mode: serial per repository
```

Bound the **product**, not each factor. A 19-task batch at `--concurrency=5`
with two reviewers each is 10 agents, not 38 — and the number is stated
before any of them start.

**An unavailable reviewer is `BLOCKED`, never `PASS`** — `commit.md` § *When a
required tool cannot run* applies to agents too.

### When a required tool cannot run

A stage's tool may **refuse to start** rather than return findings — a skill may be unavailable in this environment, or may halt when the session's working directory is the folder *above* the repo. This is not a finding, so the fix loop has nothing to act on, and it is not a defect, so halting the run strands finished work over an environment condition.

Do **not** halt, and do **not** silently skip. For each stage whose tool refuses:

1. **Record the refusal verbatim** in `status.md` § `## Run history` under that stage — the exact error text, not a paraphrase:
   ```yaml
   stage-4:
     tool: dev-stack-adaptive-code-review
     tool_status: not-invocable
     tool_error: "<the tool's exact message>"
     method: manual            # the stage's own criteria, applied by hand
   ```
2. **Do the check by hand** against that stage's own criteria and threshold, and record the result in the stage's normal fields. A manual pass is a real pass — it is the *evidence trail* that differs, not the bar.
3. **Say so in the PR body.** A reviewer must be able to see which checks were tool-run and which were manual without opening `status.md` § `## Run history`.
4. **Never record a tool run that did not happen.** `tool_status: not-invocable` with `method: manual` is honest; omitting the field and filling in the findings as though the tool produced them is a spec violation and worse than halting.

Where the refusal is fixable, name the fix in the summary rather than only reporting it — a tool that needs a git repository is fixed by running `/dev:commit` from inside the repository rather than from a parent folder.

**Time every stage.** Each stage's `## Run history` block carries `started_at`, `ended_at` and `duration_s` (integer seconds). Write them on the same edit that records the stage's result — never as a second write. A stage that halts records them too, so a halted run still says where the time went. The final summary prints the per-stage table.

---

### Stage 4 — Dynamic code review

**Read** `plugins/dev/commands/references/commit/stage-4-code-review.md` and execute verbatim. Invokes `dev-stack-adaptive-code-review` skill. Blocker+Major findings route to Stage 6 fix loop.

### Stage 5 — Final `## Acceptance` table verification

**Read** `plugins/dev/commands/references/commit/stage-5-acceptance.md` and execute verbatim. Re-runs every `## Acceptance` table row's test; deferred-to-e2e resolves if this is the last sub-task landing. Regression routes to Stage 6 fix loop.

### Stage 6 — Bounded fix loop

**Read** `plugins/dev/commands/references/commit/stage-6-fix-loop.md`. Not a standalone stage — invoked from Stage 4 or 5 when findings block. After each fix batch, upstream stages re-run in order. Bounds exceeded → escalation + halt.

### Stage 7 — Semantic context merge (v2.3.25 — MANDATORY EXECUTION, not skippable)

**Route A only.** On Route B no build flipped a unit `designed → implemented`, so
there is no graph change to reconcile and nothing for the skill to merge. Record
`SKIPPED` with `reason: route-b-no-context-units` and move to Stage 7.5.

This is the one skip the "mandatory execution" rule allows, and it is allowed
because the stage's *input* is absent, not because a run judged it unnecessary —
which is exactly the reasoning v2.3.25 was written to forbid.

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
Code review:   ✓ 0 Blocker, 0 Major   ·  3 Minor + 1 Nit found, 4 fixed
Findings:      11 found · 11 fixed · 0 accepted · 0 deferred
Tests:         ✓ 5/6 scenarios covered · 5/5 executed passed · 72.4% lines
               1 scenario has no test: AC-4 bulk-import malformed row
               e2e ran (snapshot touched a user-facing surface)
Context merge: 3 units merged clean · 4 base units carried forward · 0 conflicts
Push:          ✓ 9 commits pushed to origin
PR:            ✓ opened by /dev:commit

Status:        devReview        (flips to done on PR-merge webhook — future)
⚠ Hook bypass: 1 this run       (git commit at 14:22 — .jetrix/cache/bypass.log)

Local runbook: features/supplier-onboarding/units/backend/pr-summary.md § ## How to verify
PR summary:    features/supplier-onboarding/dev/backend-pr-summary.md

Next:
  1. Reviewer reviews PR-247   (link above)
  2. Reviewer left comments?  /dev:fix-review FEAT-SUP-001-1 pr=<link>
     folds them back through the commit stages — do not hand-patch the branch
  3. On merge, MC status flips to `done` automatically (webhook — v2.3)
```

**The findings roll-up is a required line.** Report every finding the run
surfaced, at every severity, as **found vs fixed** — not "dispositioned", which
hides whether anything was actually done. `fixed` is the default at every
severity (`stage-6-fix-loop.md` §6e.i), so a clean run reads *N found · N fixed*.

Any finding that ended `accepted` or `deferred` is listed by id, severity and
stated reason underneath — never collapsed into a count. One unfixed Minor that a
human chose to carry is useful information; three hidden inside the word
"dispositioned" is not.

**Step 2 is not optional boilerplate.** Of the three lines, it is the only one with work in it, and a
reviewer comment fixed by hand skips the code review, the acceptance re-verify and the context merge
that `/dev:commit` just ran. Name it every time, with the task id already filled in.

**Navigation URL sources (v2.3.17 — task-mcp is the URL source of truth):**

- **MC parent** — call `task-mcp.get_task_by_id_or_number(solution_id, feature.md `jetrix_task_object_id`)`; use `.view_url` from the response. task-mcp constructs the URL server-side using its own `mission_control_ui_url` env var.
- **MC sub-task** — same pattern: `get_task_by_id_or_number(solution_id, units/<repo>/status.md `jetrix_subtask_object_id`)`; use `.view_url`.
- **PR** — from `units/<repo>/status.md § ## Run history` stage-9's `pr_url` (written by Stage 9)

Do NOT construct MC URLs locally from `.jetrix/project.json` `mission_control_ui_url` — task-mcp's own env var is the source of truth and the two may drift. task-mcp's returned `view_url` is guaranteed correct.

All three URLs are must-haves in the terminal summary — the whole point of this stage is to give the developer + reviewer clickable jumps to every relevant surface. If any URL cannot be resolved via task-mcp response, print `(not resolvable from MC)` inline, do NOT invent a URL.

No file writes at Stage 10 — pr-summary + commit-run + delivery-status are already written by earlier stages.

## 7. Failure surfaces

### A halt is reported in the same shape as a success

A failed run is read more carefully than a successful one, so it gets the same
structure — not a post-mortem, and never an apology.

```
✗ /dev:commit Subtask-7 halted at Stage 5 — acceptance regression

  Blocker:   fix-loop-bounds-exceeded
  Findings:  AC-4 still failing after 3 focused fixes + 2 broad re-runs
  Written:   units/Inhouse-server/findings.md  (3 open, 11 settled)
             units/Inhouse-server/status.md    (## Run history, stage-5)
  Branch:    feature/FEAT-HCAL-01-holiday-calendar-backend  (6 commits, unpushed)
  Snapshot:  0f50921291d9  (18 files)

  Resume:     /dev:commit --resume Subtask-7
  Or inspect: units/Inhouse-server/findings.md § ## Code review
```

Four things, always, in this order: **the named blocker code**, **what
survives and where it is**, **the one command that continues**, and **where to
look**. Never a narrative of what went wrong — the findings file holds that,
and a reader who needs it will open it.

**Every halt removes this run's `session.json` row before returning** (§ Stage 1).
A halt that keeps its row leaves the user's next manual `git commit` refused in
that repo until it goes stale.

**In a batch, one task's halt never stops the others.** Each reports its own
blocker; the run summary lists them together at the end, and a sibling that
succeeded still pushes.


**Every halt below removes this run's `session.json` row before it returns**, and names a blocker code from `docs/dev/build-commit-rework.md` §12c. Stage 6's bounded escalation, a Stage 7 conflict and a Stage 8 push rejection all count — a halt that keeps its row leaves `git push` refused in that repo until it goes stale.

- **Any stage BLOCKED** (Stage 6 bounds exceeded) → local `BLOCKED`, MC `blocked`, `units/<repo>/status.md § ## Run history (a BLOCKED entry)`, halt
- **Stage 7 semantic-merge conflict** → status `devReview` (phase `merge-conflict`), `dev/context-merge-conflicts.md`, halt
- **Stage 8 push rejected** → status stays `devReview` (phase `pr-pending` — nothing reached the remote, so no PR can exist), halt with git error verbatim
- **Stage 9 PR creation failed** → status stays `devReview` (phase `pr-pending`), halt with the failing step's error verbatim. `pr-open` is only ever written beside a real `pr_url` (`references/commit/stage-8-9-push-pr.md` §9f.i); a failed raise is `pr-pending` so the next step is "open it from the compare link, then `--resume`" rather than `/dev:fix-review`, which has no PR to read comments from
- **`/dev:commit` on task at `readyForDev` or `agentExecuting`** → refuse (§2 hard gate). Route to `/dev:build`; on `agentExecuting` say a build is already running rather than inviting a second one

## 8. Guardrails

- Never invent behaviour not in `implementation.md` or resulting from a Stage 6 fix
- Never bypass Stage 7 semantic merge without `--force-context-merge=ours`
- Never `git push --force` without `--force-push`
- Never `--no-verify` on push
- Never mark MC status `done` here — reserved for the PR-merge webhook
- Never modify secrets or `.env` files
- Never rebase automatically — halt and instruct if branch is behind base
- Every material design choice → `DEC-###` in `dev/decisions.md`
- Never move MC status to `blocked` for a Stage 7 conflict — that's `devReview` (local only) awaiting human input
