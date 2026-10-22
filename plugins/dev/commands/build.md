---
description: Build a planned task through the full 11-stage loop — branch, QA harness gate (auto-bootstraps greenfield via qa-greenfield-harness), implement per implementation.md using dev-stack-adaptive-implementation (dynamic per stack, reads repo conventions, matches idiomatic patterns), write stack-adaptive tests, execute them locally, validate against parent's Acceptance Criteria + Business Rules + Test Scenarios + NFRs, run a scoped security review (feature-diff only, Critical-blocking at build-time; /dev:commit is stricter), update code-context units to origin:implemented, and produce a summary + pr-summary.md § ## How to verify. Bounded fix loop until 100% or escalation. Refuses to run without a plan from /dev:plan, OR with unresolved plan-blockers.md. Accepts any task identifier (MC task number, feature slug or folder, sub-task folder, FEAT-<AREA>-NN). Sub-task builds work in the sub-task's repo only, on a branch named feature/FEAT-<AREA>-NN-<slug>-<repo>. Never merges, never pushes, never raises a PR — /dev:commit does that.
argument-hint: "<task-number | Task-N | slug | features/<slug> | tasks/<slug>.md | FEAT-<AREA>-NN | list=<name> | requirement=<slug> | --all | (blank = every task at readyForDev)> [repo=<slug|slug,slug>] [requirement=<slug>] [--concurrency=N] [--resume] [--no-security-review] [--skip-qa] [--tests-only] [--vulnerable]"
---

# /dev:build

You are the entry point for the 11-stage build loop. **Orchestrator only** — this file parses args, resolves identity, verifies the plan + no unresolved blockers, then routes each stage to its reference file under `plugins/dev/commands/references/build/`. Do NOT paraphrase the stage files' instructions — `Read` them and execute verbatim.

Read the **`delivery-os-conventions`** skill first if it's not in context — the v2.2 loop-control state model + MC status mapping. Then read the task's plan (produced by `/dev:plan`).

**The single invariant:** `/dev:build` runs on a decidable plan or refuses. Never prompts the user mid-run.

## 0. Delegate to `dev-agent`

**Every mode of this command runs as a `dev-agent` subagent**, never in the main conversation. The invariant
above is the reason it can: a build run has no decision in it to put to anyone. Blockers are resolved at
`/dev:plan` time, and Stage 0 refuses a task whose `plan-blockers.md` is still OPEN — so there is nothing
the main thread is needed for, and an eleven-stage loop costs it nothing.

The mandated progress broadcasts (`loop-control.md`) still happen; they appear in the agent's own stream,
which the user can open and watch.

| | |
|---|---|
| `/dev:build <task>` | one `dev-agent` for the task; a split parent fans out one per sub-task |
| `--tests-only` / `--vulnerable` | one `dev-agent` **per repo**, in parallel, bounded by `--concurrency` |

**`/dev:commit` is deliberately not like this.** It stops and asks — Stage 2 confirms the base branch with
`AskUserQuestion` — so it stays in the conversation. That is the test: a command that can ask the user
something mid-run belongs inline; one that cannot, does not.

**Never commits, never stages, never pushes (v2.3.20 clarified — the git-write boundary belongs to `/dev:commit`).** All source files, test files, and context-unit updates that `/dev:build` produces LAND IN THE WORKING TREE. Never `git add`, never `git commit`, never `git push`, never open a PR — that's the separation of concerns the plugin has always documented, and this is the invariant that enforces it. `/dev:commit` gathers everything from the working tree, structures the commit(s), pushes, and opens the PR after its stricter security + review gates pass. Stage 10 (context-graph update) writes updated units to the working tree without committing them; Stage 11 writes `units/<repo>/pr-summary.md § ## How to verify` without committing it; all Stages 5-6 code + test writes land in the working tree without commits per §1 build step.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (required, unless blank for "every task at `readyForDev`"):
- **Task number** — `11` (bare) or `Task-11` / `Feature-11` / `Subtask-11`. A bare integer is accepted wherever a target is, and means `Task-<n>`. This is the normal form — it is what Mission Control shows, and it needs no knowledge of where anything sits on disk.
- Local feature slug: `supplier-onboarding`
- Local feature folder: `features/supplier-onboarding`
- Sub-task folder: `features/supplier-onboarding/units/backend`
- Internal id: `FEAT-<AREA>-NN`
- **Non-feature ticket**: `tasks/<slug>.md` (bug / story / task / epic planned via `/dev:plan` §2f). A markdown path **outside** `tasks/`, or a free-text description, has not been planned yet — say so and point at `/dev:plan <that path or description>`, which adopts it; never adopt either here, because build needs a plan. Its plan lives at `tasks/<slug>/dev/` — read `implementation.md`, `status.md`, and `plan-blockers.md` from there, not from `features/`. Never split: a non-feature builds in one repo, on `fix/<slug>` for a bug, `feature/<slug>` otherwise.
- Blank: **every task at `readyForDev`** — scan each feature’s own `status.md` **and** `tasks/*/units/<repo>/status.md`, and build the lot, bounded by `--concurrency`. Features and non-feature tickets go into one set; do not ask the user to choose between the two groups. The default matches `/dev:plan` and `/ba:features`: a blank command means the whole batch, and a target means that one thing.
- `list=<name>` / `requirement=<slug>` / `--all` — the multi-target forms, resolved exactly as `/dev:plan` §2a resolves them, then filtered to `readyForDev`. `--all` with `requirement=<slug>` scopes to that initiative.

**Flags:**
- `requirement=<slug>` — scope the target set to one requirement
- `--resume` — continue from last completed stage per `units/<repo>/status.md § ## Run history`
- `--no-security-review` — skip Stage 9's diff security review (dev-time convenience; `/dev:commit` always runs security)
- `--skip-qa` — **skip Stage 4's harness bootstrap and write no tests.** For a change whose risk does not justify standing up a test framework: a CSS value, a copy fix, a config default. Stage 4 logs `qa_gate_state: skipped-by-user` and Stages 5–6 write code without tests; Stage 8 builds the `## Acceptance` table from inspection instead of test evidence and marks every row `verified: manually`. `/dev:commit` still runs its full security and code review — this flag buys you out of *testing*, never out of *review*.

- `--tests-only` — **write tests against code already on disk; write no production code.** Runs Stage 4 → the test half of Stages 5–6 → 7 → 8, and ends at Stage 8.5. See §1a.
- `--vulnerable` — **upgrade vulnerable dependencies; write no feature code.** Same shape as `--tests-only`, pointed at the dependency manifest instead of the source. See §1b.

**When `--skip-qa` is the right call, and when it is not.** A repo with no test framework forces a real choice: install one, or accept that this change is verified by eye. For a one-line presentational fix the harness costs more than the change and protects nothing — take the flag. For anything touching behaviour, data, auth, or money, the absence of tests is the reason to build the harness, not to skip it. `/dev:build` never decides this for you: without the flag it bootstraps, with it it does not.

**`--skip-qa` and `--tests-only` are opposites.** One writes code without tests; the other writes tests without code. Passing both is a contradiction — reject it with *"--tests-only writes tests; --skip-qa writes none. Pick one."*

## 1a. `--tests-only` — test code that already exists

For a repo whose implementation is already written — a brownfield module, a hand-fixed bug, anything built outside the loop. The rest of `/dev:build` assumes it writes the code; this runs the **test half against code on disk** instead.

```
/dev:build --tests-only repo=backend               # whole repo, risk-ranked
/dev:build --tests-only repo=backend src/suppliers # scope it
/dev:build --tests-only <task-ref>                 # scope to a ticket's AC / Expected Result
```

`repo=` follows the same rule as §1b — the repo slug, several allowed, **one `dev-agent` per repo in
parallel** bounded by `--concurrency`. A task-ref carries its own repo and needs no flag.

| | |
|---|---|
| **Reads** | source on disk · `qa/quality-gates.md` tier pool · the ticket's Acceptance Criteria or Expected Result when a ref is given |
| **Runs** | Stage 4 (harness gate) → Stage 5–6 **test half only** → Stage 7 execute → Stage 8 `## Acceptance` table → the bounded fix loop |
| **Skips** | the implementation half of Stage 5–6 entirely. It writes no production code |
| **Never** | edits product logic to make a test pass · deletes, disables or loosens an existing test · marks `✅ pass` without a test behind it |
| **Ranks** | uncovered business logic and branches first; getters and generated code last |
| **Reports** | branch-coverage delta, what remains uncovered, and every exclusion with its reason |

**No `/dev:plan` plan is required** — that gate exists because the normal path builds from `implementation.md`, and here there is nothing to build. Where a task ref *is* given, its assertions become the `## Acceptance` table rows; without one, the map is built from the code's own observable behaviour and every row that cannot be settled reads `not-verified`.

A concern whose tier is missing from the gate table is reported as `tier-unavailable`, not silently skipped — see `dev-stack-adaptive-implementation`.

**Where it ends — Stage 8.5.** Stages 9–11 do not run: there is no product diff to security-review, no context unit to flip `designed → implemented`, and no runbook to write for code that already shipped. Stage 8.5 is the terminal stage instead — it writes the run summary, records `tests_only: true`, and sets the local state `/dev:commit` requires. Execute `references/build/stage-8-validate.md` §8.5 verbatim.

`/dev:commit` then reads `tests_only` and the build verdict at its Stage 0, and runs its normal stages from there.
## 1b. `--vulnerable` — upgrade what the scanners flagged

**This is a catch-up tool, not the standing mechanism.** Dependabot — which `/qa:setup` wires into every repo
it touches — owns the steady state: one PR per advisory, as each lands, small enough to review. Use this mode
once on a repo carrying a backlog, to get the count down to where Dependabot is useful again. A repo that
needs it twice has a Dependabot that nobody is merging, and that is the thing to fix.

**It will not clear every finding, and should not.** It takes patch and minor, refuses majors, and hands back
the ones left as decisions — a major changes behaviour and is not a call an unattended run gets to make. A
run that closes every production finding has done its job even with dev-only majors outstanding.

For the findings `/qa:setup` baselined at `BL-08` and the ones `/tl:maturity` scores at `D1.4`. Both report
them; **neither fixes them** — QA never edits product logic, maturity is read-only, and the build and commit
security reviews only ever see the feature diff, so a pre-existing advisory in a framework is in nobody's
path. This mode is that path.

```
/dev:build --vulnerable repo=backend                      # everything the scan reports
/dev:build --vulnerable repo=backend express              # one package and its tree
/dev:build --vulnerable repo=backend --severity=critical  # narrow the set
/dev:build --vulnerable repo=backend --majors             # take the majors, after you have approved them
```

**`repo=` is the argument, and it is the repo slug** — the same key as `qa/quality-gates.md § <repo>`,
`cache/repolocation.json` and `units/<repo>/`. That is deliberate: the slug is what maps to the `BL-08`
audit command this mode has to run, so naming the repo and finding the command are one lookup. A path works
too, and `repo=backend,frontend` or blank takes several.

### One `dev-agent` per repo, in parallel

Vulnerabilities are per-manifest, not per-feature, so there is no task to infer the repo from — unlike every
other `/dev:build` run, where the sub-task's `units/<repo>/` settles it.

| Repos in scope | What happens |
|---|---|
| One | one `dev-agent`, that repo |
| Several (named, or blank) | **fan out one `dev-agent` per repo, in parallel**, bounded by `--concurrency` (default 5) |

**One agent per repo, never one agent over several.** Each repo has its own manifest, its own audit command,
its own harness and its own blast radius — and each ends with its own branch and its own PR. A client and a
server upgraded in one run produce a PR no one reviewer can judge.

**A failure in one repo never halts the others**, as in `/dev:plan`: each agent reports its own outcome and
the summary lists them together, per repo.

### Majors: finish the safe work, then ask in the summary

A major changes behaviour, so it needs a human yes. But this mode runs as a background agent (§0) and
`/dev:build` never prompts mid-run — an agent that stops to ask simply sits there unread. So it does not ask.
It **finishes everything safe, ends, and puts the majors in the summary as a decision**, with the command
that takes them:

```
✓ Inhouse-server — patch + minor applied, tests green
  Production   2 critical, 16 high  →  0, 0
  Development  0 critical, 23 high  →  unchanged

Your call — 3 majors left, none taken:

  jest        29 → 30   closes 27 dev findings
                        test runner; config and matchers may need edits
  lint-staged 15 → 16   closes 2 dev findings
                        requires Node 20+
  nodemon     —          advisory has no fix. It is in dependencies but only
                        used by npm start; moving it to devDependencies removes
                        the exposure without an upgrade

  Proceed?   /dev:build --vulnerable repo=backend --majors
             takes them one at a time, verifying after each
```

**Three lines per major, no more**: the versions, what it closes, and **what might break** — that last one is
the whole reason a human is being asked. "jest 29 → 30" alone is not a decision anyone can make.

**`--majors` takes them one at a time**, each verified on its own, stopping at the first that breaks the
suite and naming it. Never batch them: the point of asking was to know which one costs you an afternoon.

**A major with no safe path is still reported, not retried** — like `nodemon` above, where the real fix is a
manifest move rather than a version. Say what the actual remedy is; do not list it as an upgrade that failed.

**Stack-agnostic by construction.** The manifest, the audit command and the upgrade command are the repo's
own, read from `qa/quality-gates.md` (`BL-08`) and the project's tooling — never guessed, never branched on
language here. If no audit command is configured for that repo, that is the blocker: say so and point at
`/qa:setup repo=<slug>`.

| | |
|---|---|
| **Reads** | the dependency manifest and lockfile · the `BL-08` audit command and its baseline · `qa/quality-gates.md` tier pool |
| **Writes** | **both the manifest and the lockfile** · nothing else |
| **Runs** | Stage 4 (harness gate) → upgrade → Stage 7 execute → Stage 8 `## Acceptance` → the bounded fix loop |
| **Skips** | Stages 5–6 entirely. **It writes no feature code** |
| **Never** | changes product behaviour to accommodate an upgrade · silences a finding instead of fixing it · bumps a major without saying so |
| **Orders** | **production dependencies first**, then dev. Within each: patch and minor together, verified once; each **major** separately, verified on its own — that is where behaviour changes, and a batch tells you nothing about which bump broke what |
| **Reports** | per package: old → new, the advisories it closes, and the test result that proves nothing regressed |

**Split production from development findings, and run the check — never estimate it.** The audit's headline
count includes dev dependencies, which never reach production: a `jest` advisory is not exposure, it is
hygiene. Run the production-only form of the audit command (`npm audit --omit=dev` and its equivalents) and
report two numbers:

```
Production   2 critical, 16 high   → 0 critical, 0 high
Development  0 critical, 23 high   → 0 critical, 23 high   (jest 30, lint-staged 16 — majors)
```

**One combined number hides the one that matters and inflates the one that does not.** "36 findings
remaining" reads as a failure when all 36 are dev-only majors; "2 critical in production" reads as routine
when it is the only line anyone should act on. Lead with production. A run that fixed every production
finding has succeeded even with dev findings left, and must say so plainly.

**Never assert the split without running it.** Saying findings "are all in development dependencies"
without the production-only audit behind it is a guess presented as a fact, and it is the one claim here
that would stop someone looking further.

**Raise the manifest, not just the lockfile — but only where this run earned it.** A lockfile-only upgrade
protects `npm ci` and nothing else: the manifest still permits the vulnerable range, so a fresh resolve, a
new clone or a dependency bot can pull the old version straight back. **A run that changed only the lockfile
has half-applied the fix** and must say so rather than reporting the advisories closed.

Raising a range is not free, though — it changes what every future install resolves, for everyone. So:

| | |
|---|---|
| Raise | a **direct** dependency **this run upgraded**, to the version actually installed, in the repo's own range style (`^`, `~`, exact — match what is already there) |
| Leave | every transitive dependency. The 27 packages that moved underneath are the lockfile's business and must not appear in the manifest |
| Leave | anything this run did not upgrade. A manifest edit without a verified install behind it is a guess |
| Stop and say so | a raise that breaks a **peer dependency** constraint, or a range that looks deliberately pinned (an exact version, or a comment next to it). Report it; do not force it |

**Then prove the new ranges resolve.** Re-resolve from the manifest (`npm install --package-lock-only` or
the stack's equivalent) and confirm it produces the same versions the tests just passed against. Without
that, the manifest carries a range nobody has ever installed — which is the same class of mistake as a
coverage floor nobody measured.

**Branch first, from the base — never reuse one.** Stage 3 creates `fix/vuln-<repo>-<YYYY-MM-DD>` cut from
the repo's base branch, exactly as any other build branches. Reusing a branch that already exists, or
building on an unmerged one, produces a diff that cannot merge until the other lands — and buries the
upgrade inside somebody else's review.

**The harness gate is the point — with one exception.** A dependency upgrade is only safe to the extent
tests cover what it touches, so Stage 4 runs first and a repo with smoke tests only should be told that
plainly: the upgrade may still be right, but "tests passed" means much less than it sounds.

**The exception: never halt on the `BL-08` audit gate itself.** A harness marked `Blocked` *because* the
dependency audit fails is blocked by the exact thing this mode exists to fix — halting there is circular and
makes the findings unfixable. Proceed, and say in the summary that this was the reason. Any **other** red
Required gate still halts: a broken test runner means the upgrade cannot be verified at all.

**A finding with no safe upgrade is an escalation, not a silence.** No fixed version, or the only fix is a
major that breaks the API: record it, leave the baseline entry, and say what the exposure is. Never add an
ignore rule to go green — that is weakening a check, and `§3a` of the QA setup guide draws the same line.

**Where it ends — Stage 8.5**, as `--tests-only` does: no product diff to context-map, no runbook to write.
It records `vulnerable: true` alongside `tests_only`, and `/dev:commit` runs its normal stages from there —
including its own security review, which *will* see this diff.

**No `/dev:plan` plan is required**, for the same reason as `--tests-only`: there is no `implementation.md`
to build from. The acceptance rows are the advisories closed and the suites that still pass.

## 2. Stage 0 — Identity resolution + plan verification (hard gate)

Same 4-way resolution as `/dev:plan` Stage 0 — see `plugins/dev/commands/plan.md` §2a. Determine `task_kind` (parent-alone or sub-task) and canonical `(feature_id, task_object_id, task_number, task_folder)`.

**Verify the plan exists.** Check for `implementation.md` (with sections §1–§9 per v2.3.11 frame — Build sequence through Shared contract) and `status.md` under the task folder. Missing OR `status.md` `status` is not `readyForDev` → this task has no plan. **Single target:** halt with the "run /dev:plan first" message. **Batch:** skip it, keep its reason, and report it with the other skips at the end — one unplanned task must never stop the tasks that are ready.

**Verify no unresolved plan blockers (v2.2 hard gate).** Check for `units/<repo>/plan-blockers.md`:

- Missing → continue
- Exists, `status: RESOLVED` → log the resolved `DEC-###` refs into `status.md` § `## Run history`; continue
- Exists, `status: OPEN` or `RESOLVING` → halt with "run /dev:plan --resume first" message. Never make build-time decisions.

**Verify engineering standards contract (v2.3.11 hard gate).** Check for `shared-context/coding-standards.md` § `<repo>`:

- Missing → halt with `blocker: coding-standards-missing`. Message points at `plugins/tl/skills/tl-project-scaffold/references/scaffold-guide.md` §4 for the required-sections template (greenfield: re-run `tl-project-scaffold` if the scaffold skipped it; brownfield: author the file directly using the template).
- Present, but §6 (function complexity budget), §7 (duplication policy), §8 (recursion policy), §9 (constants & magic values), §10 (state & side effects), or §12 (anti-patterns forbidden) is blank / absent → halt with `blocker: coding-standards-incomplete`, listing which section(s).
- Present + all required sections filled → continue. Log `coding_standards_checked: true` + the file's `updated_at` timestamp to `status.md` § `## Run history`.

Rationale: `dev-stack-adaptive-implementation` Rule 13/14 and code-review Dimension 8 are hard consumers of this file. Without it, Rule 13's write-time checks have no thresholds to compare against and Dimension 8's review checks have no policy to enforce — the "100% engineering standard" guarantee collapses to hope. Catching the gap at Stage 0 means the fix lands before any code is written, not after review flags it.

**Verify QA gate contract (v2.3.16 gate — soft-when-Stack-Inferred).** Check for `qa/quality-gates.md`:

**This is a read, not a gate — Stage 4 owns bootstrapping.** Stage 0 halts on exactly one state. Anything Stage 4 can fix automatically it must be allowed to reach; halting here made Stage 4's auto-bootstrap unreachable and forced users to stand up a harness by hand before a one-line fix.

- Present, `harness_status: Active` (or the legacy spelling `Ready`) → strict mode. Read Required tiers per capability class. Rule 7 in `dev-stack-adaptive-implementation` writes tests at every declared tier for every §1 step. Log `qa_gate_state: Active`.
- Present, `harness_status: Stack-Inferred` → soft mode. Tier pools were inferred from stack detection at plan time; NEW feature coverage is still 100% at every applicable tier from the inferred pool. Rule 7 writes tests at every inferred tier. Log `qa_gate_state: Stack-Inferred` + `stack_inferred_from: <source>`.
- **Missing, `harness_status: Draft`, or no `harness_status` key at all → continue.** Log `qa_gate_state: needs-bootstrap` and carry on; **Stage 4 auto-bootstraps it** after the branch exists. Never halt for these. A file with no `harness_status` key is the scaffold placeholder — the same thing as missing, and it must not read as "not Active".
- Present, `harness_status: Broken` → **halt** with `blocker: quality-gates-broken`. This is the one state Stage 4 refuses to bootstrap over, because a broken harness means a previously-working setup regressed and silently replacing it would hide that. Route to `/qa:health`.

Keep `harness_status` vocabulary aligned with Stage 4: `Active` · `Stack-Inferred` · `Draft` · `Broken`. `Ready` is the legacy spelling of `Active` and is accepted on read, never written.

The Stack-Inferred path is the intentional escape hatch for teams that want to plan+build a new feature WITHOUT first backfilling test coverage on an existing codebase. The NEW feature still gets 100% coverage at every applicable tier — the inference just skips the audit-of-existing-code step. Backfill of existing coverage is deferred to a later `/qa:audit → /qa:plan → /qa:setup` run.

## 3. Route to stages 1–11 (per-task workers; parallel fan-out for split-parent targets; resume-aware)

**Target-based routing (v2.3.20 — parallel fan-out for split features):**

| Resolved target | Workers | Concurrency |
|---|---|---|
| Sub-task ID (`Subtask-N`, `units/<repo>` folder, or feature ID + `--subtask=<repo>`) | 1 worker for THIS sub-task | Single |
| Feature ID / slug / folder of a PARENT-ALONE feature | 1 worker for the parent | Single |
| Feature ID / slug / folder of a SPLIT feature (has `units/<repo>/` children) | ONE worker PER sub-task, FAN OUT in PARALLEL | Bounded by `--concurrency=N` (default: 5) |
| Blank, `list=`, `requirement=` or `--all` → every task at `readyForDev` | One worker per parent-alone task, and per sub-task for each split parent — the whole set fans out together | Bounded by `--concurrency=N` (default: 5) across the entire set, not per feature |

**Order the batch yourself — never ask the user to sequence it.**

A batch is not a flat list. `features/<slug>/dependencies.md` carries the graph in frontmatter:

```yaml
depends_on_features: [FEAT-PLAT-01]
enables_features: [FEAT-ROLE-02, FEAT-REGR-01, FEAT-DASH-01]
```

Build it in **waves**: every target whose `depends_on_features` are all either already `done` or not
in this batch forms wave 1 and runs in parallel up to `--concurrency`; when a wave finishes, recompute
and run the next. Report the wave plan before starting — how many waves, what is in each, and why
anything is held back — so the ordering is visible rather than implied.

- **A dependency that failed holds its dependants.** They are not built against a base that is missing
  what they need: mark each `SKIPPED_DEPENDENCY_FAILED`, naming the feature that failed, and report
  them with the other skips. Building anyway produces a red suite whose cause is in another feature.
- **A cycle is a BA defect, not a build decision.** Report the cycle with its members and build them
  in declared order; do not try to break it, and do not halt the rest of the batch over it.
- **Without this, the batch is arbitrary order**, which is what forced the run summary to tell the
  user "build Feature-37 first, almost every other feature depends on it". That instruction is this
  command's job, not the user's — if a target must come first, put it in wave 1 and say so.

**Fan-out semantics for split-parent targets:**

- Each sub-task worker is fully independent: its own repo, its own branch (created in Stage 3), its own Stages 1–11, its own `## Run history` under `features/<slug>/units/<repo>/status.md`.
- Workers run in parallel up to `--concurrency=N`. A default of 5 matches the `/dev:plan` batch behavior.
- Per-worker isolation: one sub-task's Stage 8 failure halts THAT worker only — sibling workers keep running.
- `--resume` on a split-parent target resumes each sub-task worker independently based on its own `status.md` § `## Run history`.
- Sub-task builds are safe to parallelize because the wire contract is locked in §8 Shared contract of every sub-task's plan (Rule 11.3 verbatim inheritance); the frontend tests against a mocked backend that matches §8, not against the running backend.

**Consolidated report after all workers complete (or halt):**

```
✓ /dev:build <feature-ref> complete — <N> sub-tasks built (or halted)

Per sub-task results:
  ✓ Subtask-2 (backend)   — 12/12 §1 steps, 273+28 tests green, 0 Critical security
    ↳ Branch: feature/FEAT-HCAL-01-holiday-calendar-management-backend
    ↳ MC:     https://mission-control.techjays.com/task/6a95e0a0...   ↳ Local state: inProgress
  ✓ Subtask-3 (frontend)  — 9/9 §1 steps, 148 tests green, 0 Critical security
    ↳ Branch: feature/FEAT-HCAL-01-holiday-calendar-management-frontend
    ↳ MC:     https://mission-control.techjays.com/task/6a95e0a1...   ↳ Local state: inProgress

Working tree (per repo):
  · Inhouse-server:   <M> files changed (+624/-12), uncommitted   ← /dev:commit Subtask-2 gathers these
  · Inhouse-client:   <K> files changed (+412/-8),  uncommitted   ← /dev:commit Subtask-3 gathers these

Next:
  · /dev:commit Subtask-2   ← runs stricter security + review + gathers Inhouse-server working tree → commits + pushes + PR
  · /dev:commit Subtask-3   ← same for Inhouse-client
```

**Per-worker execution:** Read each stage's reference file and execute verbatim. Stages 1–3 (mount + preflight + branch) are inline in this command file below; Stages 4–11 delegate. No stage in any worker calls `git add` / `git commit` / `git push` — the "Never commits, never stages, never pushes" invariant at the top of this file applies uniformly.

### Stage 1 — Acquire lock + mount context

- Write owner into `status.md`
- status `agentExecuting` · phase `planning` (broadcast)
- MC: `readyForDev → inProgress` via `task-mcp.update_task_status`
- Read parent BA files (`feature.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `dependencies.md` § `## Open questions`) — validation contract
- Read task's Implementation content (`implementation.md` at feature root for parent-alone; `units/<repo>/{description,implementation}.md` for sub-task; plus parent's `tl-plan.md` rollup for split cross-sub-task dep context only)
- Read `discussion.md` § `## Comments` and list `attachments/` in **this task's own folder** — `features/<slug>/` parent-alone, `features/<slug>/units/<repo>/` sub-task, `tasks/<slug>/` filed ticket (pulled from MC — team clarifications, and mockups/spreadsheets the implementation must match). Open an attachment only when a step actually needs it. Absent = the task has no discussion; not an error
- Read `shared-context/decision-log.md`, `shared-context/coding-standards.md` § `<repo>` (Rule 13/Dimension 8 contract)
- Record sources consulted in `units/<repo>/status.md § ## Run history`

### Stage 2 — Pre-flight

Three cheap re-checks:
- **MC status:** if MC now says `blocked` → halt with the block reason
- **Local drift:** invoke shared drift helper; prompt Y/S if drift found
- **Cross-sub-task deps** (sub-task only): read parent's rollup Sub-tasks table; if any `Depends on` sub-task is not `done` AND this task's dev-plan marks the dep as hard → halt

### Stage 3 — Branch creation (FIRST)

- Resolve target repo (parent-alone → primary product repo; sub-task → repo matching `subtask_repo` frontmatter). If `SKIPPED` or absent in `repolocation.json` → halt with the missing-path block below, not a generic escalation — there is a one-command fix and the user should see it:

  ```
  <repo> has no local path on this machine.

    /jetrix:init refresh      re-asks for it, and re-fetches anything else
                              the project has gained since the bind
  ```
- **Read the base branch from `status.md` `base_branch:`** — `/dev:plan` asked the user for it at its
  checkpoint. Do **not** re-derive it from `project.json`, and do **not** prompt: this stage runs under the
  no-prompt invariant, which is the whole reason the question lives at plan time.
  - **`base_branch:` missing** (a plan written before this was recorded) → halt with "re-run `/dev:plan` to
    confirm the base branch". Do not fall back to `develop`; that silent default is what this replaced.
  - **`base_branch:` names a branch that no longer exists on the remote** → halt and say so. Never cut from
    whatever happens to be checked out.
- Create branch:
  - Parent-alone → `feature/FEAT-<AREA>-NN-<slug>`
  - Sub-task → `feature/FEAT-<AREA>-NN-<slug>-<repo>`
  - **Filed ticket** → `fix/task-<n>-<slug>` when `task_type` is `bug`, else `feature/task-<n>-<slug>`. There is no `FEAT-<AREA>-NN` for these, so the task number carries the identity.
  - **`--tests-only`** → `test/<scope-slug>`.
- Never `main` / `master` / `staging` / `production` / `develop`. Confirm base build is green in target repo. Write branch name into `status.md`.

**This stage is not optional, and it runs before any file is touched.** Every change `/dev:build` makes lands on its own branch — a one-line CSS fix on a filed bug as much as a multi-repo feature. If a later gate halts the run, the branch still exists and the working tree is still clean, so nothing is stranded on `main`.

### Stage 4 — QA harness gate

**Read** `plugins/dev/commands/references/build/stage-4-qa-gate.md` and execute verbatim. Auto-bootstraps via `qa-greenfield-harness` skill if `qa/quality-gates.md` is missing / Draft.

### Stages 5 + 6 — Implementation + test writing

**Read** `plugins/dev/commands/references/build/stage-5-6-implement.md` and execute verbatim. Delegates to `dev-stack-adaptive-implementation` skill.

status `agentExecuting` · phase `planning` → `implementing` (broadcast)

### Stage 7 — Execute tests locally

**Read** `plugins/dev/commands/references/build/stage-7-test-execute.md` and execute verbatim. Runs every Required gate from `qa/quality-gates.md`.

status `agentExecuting` · phase `implementing` → `testing` (broadcast)

### Stage 8 — Validate against parent AC + BR + TS + NFRs

**Read** `plugins/dev/commands/references/build/stage-8-validate.md` and execute verbatim. Builds `units/<repo>/status.md § ## Acceptance`. Any `❌ fail` row → bounded repair loop (3 focused / 2 broad).

### Stage 9 — Security review (build-time, Critical-blocking)

**Read** `plugins/dev/commands/references/build/stage-9-security.md` and execute verbatim. Invokes Claude Code's `security-review` skill on the feature diff. Skipped if `--no-security-review`.

### Stage 10 — Update code-context units (`designed → implemented`)

**Read** `plugins/dev/commands/references/build/stage-10-context-update.md` and execute verbatim. Updates every owned TL unit file's frontmatter + Source References. Commits the changes.

### Stage 11 — Report summary + `pr-summary.md` § `## How to verify`

**Read** `plugins/dev/commands/references/build/stage-11-summary.md` and execute verbatim. Prints in-terminal summary + writes `units/<repo>/pr-summary.md § ## How to verify`.

status `inProgress` · phase `built` (build phase done; awaits `/dev:commit`)

## 4. Summary output

The Stage 11 summary IS the final output. See its reference file for the exact terminal format.

## 5. Failure surfaces

- **Any stage BLOCKED** → local state `BLOCKED`, MC `blocked`, `units/<repo>/status.md § ## Run history (a BLOCKED entry)` written, halt. Never partial-ship.
- **Any repair loop bound exceeded** → same as above, cleanly.
- **`/dev:build` on task at `blocked`** → refuse (§2 hard gate). **Read `phase` to route:** `plan-blockers` → `/dev:resolve --plan <task>` (or `/dev:plan --resume` if every `Resolution:` is already filled); `escalated` → do **not** offer either — name the escalation from `status.md` § `## Run history` and stop. Routing an execution-time escalation to `--resume` re-runs planning over a problem planning did not cause.

## 6. Guardrails

- Never invent behaviour not in `implementation.md`
- Never make build-time decisions (blockers must be resolved at `/dev:plan` time)
- Never push, merge, or raise PR (that's `/dev:commit`)
- Never modify secrets or `.env` files
- Never scaffold code with a guessed stack (route to `/dev:bootstrap` for project-zero)
- Retry limits per `feature-delivery-loop/references/loop-control.md`
- Every material design choice → `DEC-###` in `shared-context/decision-log.md`
