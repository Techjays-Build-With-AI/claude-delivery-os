# `/dev:build` + `/dev:commit` — architecture rework

Implementation reference · v1.0 · 2026-11-03

**Status:** decisions settled, Phase 1 ready to implement. Phases 2–5 carry two
open mechanisms named in §14.

This document separates **what exists today** from **what changes**. Every
"exists" row cites the file that implements it, so an implementer can read the
current behaviour before changing it. Nothing here is implemented yet.

---

## 1. The problem, in one paragraph

v2.3.20 moved the git-write boundary out of `/dev:build` and into `/dev:commit`
Stage 7.5 — build writes to the working tree and never commits. The stages
*upstream* of 7.5 were never updated, and they all scope on
`git diff <base>...HEAD`. On the happy path that diff is empty: build produced no
commits, so commit-time security review and code review inspect nothing, and
`/dev:commit` Stage 0's clean-tree precondition refuses the dirty tree that
`/dev:build` is contractually required to leave behind.

The gates are well specified and currently inspect zero bytes.

---

## 2. Settled decisions

| # | Decision | Chosen |
|---|---|---|
| D1 | Route B state | **Reuse `tasks/<slug>/units/<repo>/`** and the existing `/dev:plan` adoption path. No new state system, no new status vocabulary. |
| D2 | Build Stage 9 security | **Demote to report-only.** It records findings; it runs no repair loop. Commit owns security remediation. |
| D3 | Test evidence | **One source of truth — `units/<repo>/status.md § ## Acceptance`.** Build writes build-time evidence, Commit appends commit-time evidence. No `test-coverage.md`. |
| D4 | Artifacts | **Keep the v2.4 consolidation.** `findings.md` gains a `## Test verification` section; no new report files. |
| D5 | Code review | **Adaptive reviewer blocks; built-in reviewer is a second opinion.** |
| D6 | Medium/Low severity | **Existing policy — surface in findings + PR body.** No mid-run prompts; the no-prompt-after-fan-out invariant holds. |
| **D7** | Adopted-work state | **New `phase: adopted`.** See §6 — without it `/dev:commit` refuses every Route B run. |
| **D8** | Adoption | **Automatic, with no command and no flag.** `/dev:commit` Stage 0 creates the record itself when one is missing. There is no `/dev:plan --adopt` for a user to type. See §5. |
| **D9** | Review design | **Findings persist with settled decisions · review classes · withhold rules.** Markdown only. Enforcement code is out of scope — see §10d. |
| **D10** | Severity | **Detect all · block some · disposition everything.** No finding reaches the PR undispositioned; nit cap + batched cheap-fix pass. Supersedes D6. See §11. |
| **D11** | Recall | **Measure it.** Planted-defect eval, scored per defect class, gating the plugin's own merges. See §12a. |
| **D12** | Push / PR policy | **No flag.** Push and PR are the terminal step of the gate sequence; passing the gates *is* the authorization. A run that cannot close its findings does not reach them. |
| **D14** | Enforcement | **Three `PreToolUse` hooks, fail-open.** Marker present → restrict; absent, unreadable or stale → allow. Audited bypass. See §12b. |
| **D15** | Failure contract | **Every failure has a named blocker code, durable state, and one `--resume` command.** See §12c. |
| **D13** | Scope certainty | **A review that cannot determine its scope halts.** It never reviews a self-selected subset and reports it as a review. See §12.0a. |

D7–D11 are the decisions that unblock Phases 2 and 3. **D10 supersedes D6** —
the no-mid-run-prompt invariant survives, because disposition is asked at the
pre-fan-out checkpoint or carried from a settled decision, never mid-loop.

---

## 3. The two routes

Route B means *the code was written outside the Build workflow* — by hand, by
Claude directly, by another tool. It does **not** mean "without a task record".
Both routes carry a task record; they differ in who wrote the code.

```
Route A — Delivery OS authored the code
  /dev:plan  →  /dev:build  →  /dev:commit

Route B — someone else authored the code
  existing changes  →  adoption  →  /dev:commit
```

Both converge on the same Commit gate layer: snapshot → security · code · test
review → consolidation → targeted repair → delivery.

| | Route A | Route B |
|---|---|---|
| Requirement source | task / feature AC | the diff + repo context |
| Implementation | `/dev:build` Stages 5–6 | already on disk |
| Scenario source | `acceptance-criteria.md`, `test-scenarios.md` | inferred from the diff, **labelled inferred** |
| Acceptance rows | build Stage 8 writes them | the verifier writes them, marked `inferred` |
| Entry state | `inProgress` / `built` | `inProgress` / **`adopted`** |
| Repair | targeted, back to a build agent | targeted, optional |

**Route B must never present an inferred expectation as a stated requirement.**
Every row it mints carries `source: inferred` so a reader can tell what the code
implies from what a human asked for.

### 3a. How far Route B may infer

**Infer technical context; never invent a business requirement.** The line is
whether the code itself settles the question.

**The decision is mechanical, not a judgement.** A judgement rule here would
depend on the agent classifying its own situation correctly — the same thing
that failed in §12.0. So it is a lookup on observable facts, evaluated against
the review snapshot:

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

Each trigger is checkable from the snapshot plus the code-context graph — no
interpretation required. Trigger 3 is where the graph pays for itself: it is
the only cheap way to know an endpoint is authenticated without reading the
middleware chain.

| Situation | Resolves to | Why |
|---|---|---|
| Narrow bug fix, existing regression test | infer | no trigger fires |
| New operation, behaviour visible in code and tests | ask (trigger 3 or 4) | the contract is visible; the *expectation* is not |
| Several unrelated modules changed | ask (trigger 1) | there is no single theme to infer |
| Large refactor, no stated outcome | ask (trigger 4, usually 1) | |
| Security-sensitive, undocumented | ask (trigger 2 or 3) | an inference must never stand as acceptance criteria |

Every inferred row carries four things: `source: inferred`, the diff hunk or
file it was derived from, the expected behaviour inferred, and the test that
covers it (or its absence). A reader must always be able to separate *what the
ticket asked for* from *what the implementation implies*.

All asking happens at the pre-fan-out checkpoint — the no-prompt-after-fan-out
invariant holds for Route B exactly as it does for Route A.

---

## 4. The snapshot contract — the core fix

Reviewers need a real git object to diff against, without moving the working
tree or the index.

### 4a. Mechanism

```bash
TMPIDX="$(git -C "$REPO" rev-parse --absolute-git-dir)/delivery-os.review.index"
export GIT_INDEX_FILE="$TMPIDX"
trap 'rm -f "$TMPIDX"' EXIT                              # cleanup is mandatory
git -C "$REPO" read-tree HEAD
git -C "$REPO" -c core.safecrlf=false add -A -- $SCOPE   # §4b — scope, not blanket
TREE="$(git -C "$REPO" write-tree)"
SNAP="$(git -C "$REPO" commit-tree "$TREE" -p "$BASE_SHA" -m 'review-snapshot')"
unset GIT_INDEX_FILE
git -C "$REPO" diff "$BASE_SHA".."$SNAP"
```

**Verified on Windows / Git Bash** against a repo with tracked modifications and
untracked files: working tree byte-identical, `.git/index` md5 identical, HEAD
unchanged, untracked files included, `.gitignore` honoured, `$SNAP` a real commit
object. The full contract is
`plugins/dev/commands/references/common/review-snapshot.md`.

Properties: the working tree never moves, the real index never moves,
`.gitignore` still applies, `$SNAP` is a genuine commit object so every existing
`git diff <base>...<head>` call site works unchanged, and the sha **is** the
shared review identifier every finding cites.

`git add -A` here writes to a throwaway index and never the real one. It does not
violate the "never blanket-stage" rule, which governs delivery staging in
Stage 7.5.

**The index path must come from git, never from `mktemp`.** `mktemp` returns an
MSYS path (`/tmp/tmp.mb3MaHhjep`) that works from Git Bash only because `git.exe`
ships MSYS translation; the same command file run through PowerShell has neither
`mktemp` nor `/tmp`. `git rev-parse --absolute-git-dir` returns a path git itself
produced, on the repo's own filesystem, inside `.git/` where `git status` cannot
see it — so a crashed run leaves no mess, and the deterministic name means the
next `read-tree` simply overwrites a stale one.

**Never `--git-dir`.** It returns the relative `.git` **even when `-C <repo>` is
passed**, and `GIT_INDEX_FILE` resolves against the *process* working directory —
silently writing the wrong repository's index on a multi-repo run.

**`-c core.safecrlf=false` is required, not cosmetic.** Without it a repo with LF
files under `core.autocrlf` emits one `LF will be replaced by CRLF` warning **per
file** — 221 on the test repo. The flag suppresses them and produces a
byte-identical tree (same tree sha confirmed with and without); `-c` means nothing
in the user's config changes.

### 4b. Two snapshots, not one

| Snapshot | Built from | Used for |
|---|---|---|
| **Detection** | everything (`git add -A` unscoped) | classifying the run — task-related vs unrelated vs none |
| **Review** | `git add -A -- <selected paths>` | all reviewers, **and** Stage 7.5's staging set |

The review snapshot must be **byte-identical to what gets staged**. One snapshot
for both means reviewing one set of changes and shipping another, which is the
failure the whole mechanism exists to prevent.

Where detection finds changes outside the intended scope, the scope question is
asked **once, at the pre-fan-out checkpoint**, never per worker.

### 4b.i. The scope-selection prompt

Group by repository, then by the directory the change sits in, and pre-tick
nothing the run cannot justify:

```
Changes detected — Inhouse-server
  12 files changed · +340 / -28

  Select what belongs to this task:

    [x] src/auth/session.ts            modified    authentication
    [x] src/auth/token.ts              modified    authentication
    [x] tests/auth/session.test.ts     untracked   authentication tests
    [ ] src/billing/invoice.ts         staged      billing
    [ ] tests/billing/invoice.test.ts  staged      billing tests
    [ ] README.md                      modified    documentation

  3 of 6 selected
```

Rules:

- **Show every change, with its git state** — `modified` · `staged` ·
  `unstaged` · `untracked`. A staged file the developer forgot about is exactly
  what this prompt exists to surface.
- **Collapse a directory with nothing tracked in HEAD into one unticked row.**
  `git cat-file -e "HEAD:<dir>"` returning non-zero is the mechanical test. On
  the real test repo this turned a 205-row prompt into three: 195 of those files
  were an untracked `coverage/` directory nobody meant to deliver, and listing
  them flat would have buried the nine that mattered. Name the `.gitignore` line
  when it fires — an untracked build directory is usually a missing ignore rule.
- **A file that is staged AND further modified needs a third answer.** `git add -A`
  into the temp index takes the **working-tree** version, so a developer who
  staged a subset deliberately would get the rest reviewed and delivered with it.
  Never resolve this silently. Flag the file and offer both:

  ```
    [!] src/auth/session.ts    staged +12/-3  ·  AND unstaged +40/-8
        [a] take the working tree   (both sets — the default for a normal build)
        [b] take the index only     (what you staged; the rest stays uncommitted)
  ```

  On `[b]`, build that path's tree entry from the **real index blob**, not the
  working file.

- **Want only part of a file reviewed and shipped?** Stage it first and answer
  `[b]`:

  ```
  git add -p src/auth/session.ts     # pick the hunks you mean
  /dev:commit                        # answer [b] index only on that file
  ```

  Per-hunk selection inside the prompt is deliberately not built — git already
  has the right tool for it, and rebuilding `add -p` in a picker would be a
  worse version of something every developer already knows. This is a stated
  precondition, not a gap.
- **Never silently exclude a file.** A file absent from the list is a bug; a file
  present and unticked is a decision.
- **Record both sets** — `scope_selected[]` and `scope_excluded[]` — in the task
  context, so a later run and a reviewer can both see what was deliberately left
  out.
- **Build the review snapshot from the selected paths only**, and rebuild it if
  the selection changes.
- **The final staged set is the selected set.** Stage 7.5 stages exactly these
  paths; Stage 8 gates on the sha matching.

### 4c. Base sha resolution

| Route | Order |
|---|---|
| A | `units/<repo>/status.md` `base_branch:` → the value confirmed at `/dev:plan`'s checkpoint. Never re-derived. |
| B | upstream of the current branch → `apps[].env_branches.dev` from `project.json` → ask at the checkpoint |

A missing base on Route A is a halt, not a fallback — the silent `develop`
default is what `/dev:build` Stage 3 already refuses.

### 4d. Staleness

A snapshot is a point in time and reviewers take minutes.

- Recompute the review snapshot sha immediately before Stage 7.5 staging.
- Differs from the reviewed sha → the tree moved during review. Re-run the
  affected gates; do not stage against findings that cite a tree that no longer
  exists.
- After every repair round, recompute and record the new sha. Findings carry the
  sha they were produced against.

**The detection primitive ships in Phase 1, the orchestration in Phase 4.**
Phase 1 computes and records the sha and compares it at staging time; what to
*re-run* on a mismatch is the repair loop's concern. Splitting it the other way
round would mean Phases 2 and 3 run on snapshots nothing checks.

### 4e. Provenance — snapshot shas are dangling

A snapshot commit is unreferenced and will be garbage-collected. It must never be
written into a file that gets committed.

- Build Stage 10 writes `mapped_from_commit: pending`.
- `/dev:commit` Stage 7.5 **backfills the real sha** after the commit lands.
- A context unit citing a snapshot sha is a unit nobody can ever resolve.

---

## 5. Adoption — D8

`/dev:plan` already adopts a free-text description or a loose `.md` file into
`tasks/<slug>.md` and runs the non-feature track
(`references/plan/non-feature-track.md`). Route B reuses that. But it needs one
mode flag and one doorway.

### 5a. Why a flag is needed

The non-feature track composes a **build sequence** — ordered steps, files to
touch, `Satisfies` links — and pushes it to the tracker. For code that is
already written, that is a plan for work already done, and blocker detection has
nothing to block: you cannot hold work that has shipped to the working tree.

Adoption is therefore **a step inside `/dev:commit` Stage 0**, not a command:

| Does | Skips |
|---|---|
| create `tasks/<slug>.md` with the type inferred and stated | §1 build-sequence compose |
| resolve surfaces from the graph (plan.md §2a.1 — already implemented) | blocker detection (Stage 3) |
| create `tasks/<slug>/units/<repo>/status.md` at `inProgress` / `adopted` | the split checkpoint (non-features never split) |
| record the intended scope — the file set the developer means to deliver | the MC push of a build plan |
| push the ticket itself, so the work is visible on the board | |

`implementation.md` for an adopted task is written **after** review, from the
delivered diff, as a record of what was done — not before, as a plan.

### 5b. The doorway

Option A (plan then commit) and Option B (commit does it internally) are a false
choice. Take A's mechanism and B's entry point:

`/dev:commit` on a dirty tree with no matching task record **offers the adoption
inline**, at the pre-fan-out checkpoint, exactly as `/dev:plan` §2c offers to pull
missing BA files:

```
No task record matches the changes in Inhouse-server.
  12 files changed (+340 / -28)

  Adopt them as a task and validate?  [Y/n]
    slug: auth-session-expiry        type: bug (inferred from the diff)
```

One command for the developer; one mechanism underneath; the adoption is still
a step of Stage 0, not a second command. `n` stops cleanly without writing anything.

---

## 6. State model change — D7

**This is a blocking prerequisite for Route B that neither earlier revision
caught.**

`/dev:commit` Stage 0 gates on `status: inProgress` **and** `phase: built` **and**
`ready_for_dev_commit: true` (`plugins/dev/commands/commit.md` §2). An adopted
task has never been built, so it would land at `readyForDev` / `planned` and
`/dev:commit` would refuse it and route to `/dev:build` — which would then try to
implement code that already exists.

Add one phase:

| `status` | `phase` | Set by | Means |
|---|---|---|---|
| `inProgress` | `built` | `/dev:build` Stage 11 | Delivery OS wrote the code |
| `inProgress` | **`adopted`** | `/dev:commit` Stage 0 | the code exists; Delivery OS did not write it |

Two files change with it:

- `delivery-os-conventions` SKILL.md §5 — add the row to the phase table and to
  the five-gates table.
- `commit.md` §2 — the gate becomes `phase: built | adopted`.

`phase` is local-only and never pushed to any tracker, so no `status_map` key is
needed and no tracker sees a value it does not understand.

---

## 7. Stage-by-stage changes

### 7a. `/dev:build`

| Stage | Exists today | Change |
|---|---|---|
| 0 | plan + blockers + coding-standards + QA gates | Route B: skip plan/blocker checks for `phase: adopted`; coding-standards gate still applies |
| 3 | branch cut from `status.md` `base_branch:` | unchanged |
| 4 | QA harness gate, auto-bootstrap | unchanged |
| 5–6 | `dev-stack-adaptive-implementation` | unchanged |
| 7 | real-service startup, two runs, failure classifier | unchanged |
| 8 | `## Acceptance` build-time column | unchanged |
| **9** | `security-review` on `<base>...HEAD`; **3-attempt repair loop**; `repair_loop_invocation` trace | **report-only (D2).** Scope → review snapshot. Remove the repair loop. Findings → `findings.md § ## Security — build`, carried to Commit Stage 3 |
| **10** | flips units `designed → implemented`; **hard-gates on Stage 9's repair trace**; `mapped_from_commit` from `git log` | gate becomes "Stage 9 ran and recorded findings", not "repair loop cleared Critical" — Commit is now the authority. `mapped_from_commit: pending` (§4e) |
| **11** | summary prints `Commits: N`; `commit_sha` in the log | report **files changed** and **commits: 0 (uncommitted)**. Never print a commit count build did not produce |

Removing Stage 9's repair loop deletes an entire bounded-retry path from the
build and ends the double security remediation.

### 7b. `/dev:commit`

| Stage | Exists today | Change |
|---|---|---|
| **0** | verify built; **"verify no uncommitted changes"** | **replace with scope detection.** Build the detection snapshot, classify the run, resolve the route, check `phase: built \| adopted` |
| 1 | lock, flip `devReview`/`pr-open` | unchanged |
| 2 | base branch via `AskUserQuestion`, fetch base | add Route B's base ladder (§4c). Build the **review** snapshot here |
| **3** | security on `<base>...HEAD` | scope → `$SNAP`. Runs as a **fresh-context reviewer agent** |
| **4** | `dev-stack-adaptive-code-review` on `<base>...HEAD` | scope → `$SNAP`. Fresh-context agent. Built-in reviewer runs alongside as non-blocking second opinion (D5) |
| **5** | re-verify `## Acceptance`, close deferred E2E | add the **test-verifier** as a third parallel agent (§9). Keep the two-column design — never overwrite build evidence |
| 6 | bounded fix loop, invocation traces | fresh repair agent per round; serial per repo; selective re-review (§8c) |
| 7 | `tl-semantic-context-merge` | unchanged |
| **7.5** | gather, categorize, secrets scan, commit | stage **exactly the review snapshot's path set**. Recompute sha first (§4d). Backfill `mapped_from_commit` (§4e) |
| 8 | push, hard-gated on every invocation trace | add a gate on the snapshot sha matching what was reviewed |
| 9 | PR via the 4-step ladder | unchanged |

### 7b.i. Greenfield — the graph exists, but it is `designed`

**No `/tl:code-map` on a fresh repo.** There is nothing to reverse-map. The
graph is authored forward instead: `/dev:plan` Stage 1 detects `NOT_PLANNED`
and auto-runs `tl-feature-planning`, which mints `PAGE-/EP-/ENT-` units as
`origin: designed` · `status: Proposed` · `implementation_state: Planned`.
`/dev:build` Stage 10 then flips them to `implemented`. `/tl:code-map` is for
brownfield only, and `tl-feature-planning` is a skill with no slash command —
never print one.

`/tl:scaffold` runs before the first `/dev:plan` and settles the stack: it asks
for every decision the architecture leaves open (with a recommendation, never a
silent guess), creates the skeleton and tooling, proves a green base build, logs
a `DEC-###` per decision, and writes
`shared-context/{technology-stack, architecture, coding-standards}.md`.

**That last file is load-bearing.** `/dev:build` Stage 0 hard-gates on
`coding-standards.md § <repo>` and halts with `coding-standards-missing`
without it. Greenfield gets it from `/tl:scaffold`; brownfield gets it from
`/tl:code-map` Pass C. A fresh repo that skipped the scaffold cannot build.

**What this costs the review stages, and what to do about it.** Two things in
this plan read the graph, and on a fresh repo it is thin:

| Reads the graph | On greenfield | Rule |
|---|---|---|
| §12 cause 2 — widen scope to callers/callees of a changed file | few links exist at feature 1; there is little to expand to | **degrade and say so.** Review the changed files whole; record `scope_expansion: unavailable — graph has N links`. Never silently review less than on a mapped repo |
| §3a trigger 3 — endpoint's `## Auth` is non-empty | the unit is *designed*, so this reads intent rather than built code | **still the right signal.** Auth that was designed is auth that must be asked about |

The graph's value scales with what is in it, and that is fine: at feature 1 the
diff is most of the repo, so scope expansion has little left to find. What is
not fine is reporting the same coverage on a thin graph as on a complete one.

### 7b.ii. Route B runs a reduced stage set — not the whole flow

**The point of Route B is security review and code review on local changes.**
Those two stages need only a diff and the repo's own standards — no ticket, no
acceptance criteria, no plan. Everything in `/dev:commit` that exists to
validate work *against a ticket* has nothing to read on Route B and must not
run.

| Stage | Route A | Route B | Why |
|---|---|---|---|
| 0 identity + scope | resolve the task | **diff-driven**, adopt inline | there is no task to resolve |
| 1 lock + read BA files + flip tracker status | all three | **lock only** | no `acceptance-criteria.md` to read; no ticket to flip |
| 2 base + snapshot | yes | **yes** | |
| **3 security review** | yes | **yes — this is the point** | needs only the diff |
| **4 code review** | yes | **yes — this is the point** | needs the diff + `coding-standards.md § <repo>` |
| 5 acceptance | re-verify the ticket's rows | **reduced** — run the tests that exist, check they cover the diff, report gaps | no ticket rows exist; rows are inferred and labelled |
| 6 fix loop | yes | **yes** | findings are findings |
| 7 semantic context merge | yes | **skip** | no build flipped any unit `designed → implemented`, so there is nothing to merge |
| 7.5 gather + commit | yes | **yes** | |
| 8 push · 9 PR | yes | **yes** | |

Nine of eleven stages, one skipped outright and two reduced. **No tracker
write happens on Route B at all** unless the user asks for one.

#### Adoption is automatic — there is no command for it

**No user ever types an adopt command, and none exists.** `/dev:commit` Stage 0
detects that changes exist with no matching record and creates one itself,
after a single confirmation.

This follows the rule `delivery-os-conventions` §1.f already states — *"some
commands exist for an agent to invoke, not for a person to type"* — and the
precedent it already sets: `tl-feature-planning` builds the context graph with
no slash command, because `/dev:plan` runs it. Adoption is the same shape.

**A next-step block may never print an adopt command.** There is one entry
point for local changes and it is `/dev:commit`.

#### What adopt actually creates — a record, not a ticket

The confusion worth removing: adopt exists so **findings have somewhere to
live and `--resume` has something to read**, not so a ticket appears on the
board.

```
.jetrix/tasks/<slug>.md                       # short description + inferred type
.jetrix/tasks/<slug>/units/<repo>/status.md   # state, selected scope, run history
.jetrix/tasks/<slug>/units/<repo>/findings.md # written during the run
```

Two files up front. All three are inside gitignored `.jetrix/`.

**No tracker id is minted.** This follows the rule the existing adopt path
already states (`plan.md` §2a step 2a): *"Write no `jetrix_task_object_id`…
the adopted task is local until `/jetrix:push task <slug>` is run
deliberately."* So a local fix never creates board noise, and a user who later
decides it should be tracked has a path that does not duplicate anything.

Without the record there are three concrete problems, and they are the whole
justification: findings have no file, `--resume` has no state to re-enter from,
and `## Settled` has nowhere to carry an accepted finding to the next run —
so the same Medium is re-raised forever.

### 7c. Modes that must not regress

`--tests-only` and `--vulnerable` keep their own Stage 8.5 terminal handling and
their own state (`tests_only: true` / `vulnerable: true`). They are **not**
absorbed into Route B. Both are in the Phase 6 regression set.

---

## 8. Agent topology

### 8a. Three levels

| Level | Agent | Owns |
|---|---|---|
| L1 | main orchestrator | route detection, **all questions**, wave scheduling, final report. Does no work |
| L2 | repository worker | one per `units/<repo>/` — `build:<repo>` or `commit:<repo>` |
| L3 | review agents | `review:security:<repo>` · `review:code:<repo>` · `review:tests:<repo>` — fresh context, read-only, parallel |

Fresh context is the mechanism, not a nicety. An agent that inherits the build
transcript is primed to accept the code it watched being written; one handed only
a snapshot sha and a diff is not.

### 8b. Concurrency

```
Repository concurrency   5   (--concurrency, existing default)
Reviewers per worker     3   (fixed)
Peak reviewer agents    15
Review mode              parallel
Repair mode              serial, per repository
```

**Print this block before fanning out.** A 19-task batch must never silently
launch 57 agents.

### 8c. Routing rules

- **Readers parallel, writers serial.** Three reviewers at once is safe. Two
  repair agents in one working tree collide.
- **Fresh repair agent per round**, scoped to `allowed_files` and the finding.
  Reusing the agent carries round N's rationalisation into round N+1.
- **Selective re-review:** security re-runs on any source change; the test
  verifier always re-runs; code review re-runs only when the repair touched a
  file in its finding set or its cited evidence.
- **An unavailable reviewer is `BLOCKED`, never `PASS`** — the existing rule in
  `commit.md` → *When a required tool cannot run*, extended to agents.
- **Named streams.** Every agent carries its name so the user can watch, message
  or cancel one without killing the batch.

---

## 9. Test verification — the division of labour

Build and Commit must not answer the same question with different authority.

| | Build | Commit |
|---|---|---|
| Create and execute tests | yes | re-execute the relevant ones independently |
| Tier/mock check | **mechanical** — Stage 8c already detects `vi.mock` at `tier: integration` and refuses ✅ (`mock-contradicts-tier`) | — |
| Test quality | — | **semantic** — does the assertion actually exercise the stated behaviour, or does the fixture mock it away |
| Scenario coverage | record the mapping in `## Acceptance` | identify missing scenarios and weak tests |
| Security | early report-only signal | authoritative gate |

Build asks *"did we write tests?"*. Commit asks *"do those tests prove it?"*.
Stating the split this way is what stops the verifier re-implementing Stage 8c.

### 9a. Verification statuses

`PASS` · `FAIL` · `BLOCKED` · `SKIPPED` · `NOT AUTOMATED` · `INCONCLUSIVE`.
**Only `PASS` counts as verified.**

Route B with no usable harness (`quality-gates.md § <repo>` absent or no gate
commands) reports `BLOCKED` or `NOT AUTOMATED` per row. It never silently passes,
and it never bootstraps a harness — that is `/qa:setup`'s job.

### 9b. Row shape

Keep the existing columns. The commit-time column is **appended**, never
substituted:

| Kind | ID | Statement | Verified by | Build-time | Commit-time |
|---|---|---|---|---|---|
| AC | AC-2 | Expired session is rejected | `session.test.ts::expired` | ✅ pass | ✅ pass |
| AC | AC-4 | Missing token requires auth | `auth.test.ts::no-token` | ✅ pass | ❌ fail |

`Kind` and `ID` are the traceability keys back to `AC-`/`BR-`/`TS-`/`NFR-`.
Dropping them turns an auditable map into a list of sentences.

Route B rows carry `source: inferred` and cite the diff hunk they were derived
from.

---

## 10. Review design

Three changes to how reviews run. All three are markdown edits to stage files
and reviewer briefs — no executable code, nothing outside build and commit.

The ideas for §10a and §10b come from
[`awslabs/aidlc-workflows`](https://github.com/awslabs/aidlc-workflows) (MIT-0).
Two further mechanisms from that project — engine-issued review receipts and a
reviewed-output freeze hook — require executable enforcement code and are
**out of scope for this document**. They are tracked separately as the
enforcement layer; see §10d.

### 10a. Findings persist, with settled decisions

**What we have.** `findings.md` is rebuilt per run. A Medium accepted last week
returns next week as a fresh finding, and the person who accepted it is not
recorded.

**What AWS does.** Every re-dispatch receives open findings *and prior
decisions*:

> *"A decided finding later reported fixed stays among the settled decisions, so a recurrence keeps its decision."*

Prior findings keep their engine-assigned ids; the reviewer reports each as
`Fixed` or `Still applies` and may not re-grade a settled row — except to raise
its severity, which reopens it.

**What we change.** Findings get **stable ids that survive runs**, keyed on
`(repo, rule-class, file, normalised symbol)` rather than line number, plus a
`## Settled` section in `findings.md` holding every accepted or deferred
finding with its reason and who decided. Every review dispatch is handed the
open set and the settled set. **This is the mechanism §11 needs** — without it,
"disposition every finding" just produces the same dispositions every run.

Markdown only: a new section in an existing file, plus an id-derivation rule in
the reviewer brief.

### 10b. Review classes

AWS resolves each review to `adversarial` (refute-and-repair, bounded by
`reviewer_max_iterations`, default 2), `advisory` (one pass, feeds a human
gate), or `none`. We treat every review as blocking.

| Review | Class |
|---|---|
| commit Stage 3 security | `adversarial` |
| commit Stage 4 — `dev-stack-adaptive-code-review` | `adversarial` (blocking gate) |
| commit Stage 4 — built-in `code-review` | **`advisory`** — second opinion, never blocks |
| commit Stage 5 test verification | `adversarial` on required gates, `advisory` on inferred rows |
| build Stage 9 security | **`advisory`** — matches the D2 demotion |

### 10c. What a reviewer must not be given

Copy this rule as written. It is sharper than our "fresh context" phrasing
because it names what to **withhold**:

> *"Do NOT pass: `memory.md` (builder's diary) or any plan/reasoning files, and never a verdict to write or to prefer. The reviewer forms independent judgment."*

Our equivalent: a reviewer agent receives the snapshot sha, the diff, the repo
path, `coding-standards.md § <repo>`, the parent's `business-rules.md`, and the
open + settled findings. It is **not** given `analysis.md`, `implementation.md`,
the build's `## Run history`, or any statement of what the build believed it had
done.

### 10d. Deliberately out of scope — the enforcement layer

Two mechanisms were considered and **cut from this document**, because they
require executable code that can block a tool call and that is a different
project from a build/commit rework:

| Cut | What it would replace | Why it is not here |
|---|---|---|
| Engine-issued review receipts (`review-ledger.js`) | the forgeable `fix_loop_invocation:` yaml an agent writes about itself | needs a CLI the agent does not author; is an enforcement concern, not a stage concern |
| Reviewed-output freeze (`PreToolUse` hook) | §4d's after-the-fact sha comparison | needs a hook that blocks writes; same |

**What this costs us, stated plainly:** the invocation traces in
`stage-6-fix-loop.md` §6a.i, `stage-7-semantic-merge.md` §7a.i and
`stage-8-9-push-pr.md` §8a remain an honour system. They are the strongest
thing available without enforcement code, and they are what v2.3.25/27 already
ship, so this document leaves that exactly as it found it — no better, no worse.

§4d's sha comparison stays as the staleness mechanism. It detects rather than
prevents, which is weaker, and that is the accepted trade for keeping this
scope to markdown.

The enforcement layer is worth doing and should be tracked on its own — both
source files are MIT-0 and can be ported rather than designed.

---

## 11. Severity — detect all, block some, disposition everything

Current behaviour, verified: **we already detect every severity.** Build Stage 9
§9e records Critical/High/Medium/Low; commit Stage 3 records those plus Info;
Stage 4 records Blocker/Major/Minor/Nit. Nothing is missed at detection.

What is missing is **closure**. Medium/Low/Minor/Nit are written into the PR
body and die there — undispositioned, untracked, re-raised as noise next run.

**The fix is to separate blocking from closing**, not to put every severity into
the fix loop. Routing 40 nits through a loop bounded at 3 focused attempts each,
every one re-triggering the 3→4→5 cascade, trades a real risk of regression for
cosmetic gain. AWS bounds at 2 iterations then escalates; Anthropic's playbook
recommends explicit nit caps.

| Severity | Blocks delivery | Must carry a disposition before the PR opens |
|---|---|---|
| Critical · High · Blocker · Major | **yes** — fix loop, bounds unchanged | yes |
| Medium · Low · Minor | no | **yes** — `fixed` \| `accepted` (reason + who) \| `deferred` (tracker id) |
| Nit | no | capped at 10; beyond the cap, counted not listed |

**No finding reaches the PR body without a disposition.** That is the gate —
`/dev:commit` Stage 8 refuses to push while any finding is undispositioned. It
costs nothing on a clean run and makes "we'll get to it" impossible to leave
implicit.

**The batched cheap-fix pass.** After the blocking loop closes, fix the
mechanically-safe Low/Minor findings — unused import, missing null guard, magic
number to constant, missing error branch — in **one** batch with **one** gate
re-run. Not one loop per finding. This captures most of the value inside a
bound.

**Accepting needs a name.** `accepted` records who accepted and why, and lands
in `## Settled` (§10c) so it is never re-raised. An agent may not accept its own
finding; acceptance is asked at the pre-fan-out checkpoint or carried from a
prior settled decision.

---

## 12. Review recall — why 3 of 5, and what fixes it

A team member wrote changes with AI directly — **no `/dev:plan`, no
`/dev:build`** — then ran `/dev:commit` to review and push, with **5 known
issues planted**. It reported 3, missed 2. Their own review skill found all 5.

### 12.0 What actually happened — confirmed

This was **Route B**, run through a command that has no Route B. Trace Stage 0
with no task record and an uncommitted tree:

| Gate | Should have | Did |
|---|---|---|
| Target resolution — scan `features/*/units/<repo>/status.md` + `tasks/*/…` for `inProgress` + `built` | resolve an empty set | continued |
| Verify `/dev:build` completed (`commit.md:78`) | halt — *"run /dev:build first"* | continued |
| Verify clean tree (`commit.md:108`) | halt — tree is dirty | continued |
| Stage 3/4 scope — `git diff <base>...HEAD` | empty, nothing committed | **improvised a scope** |

**Four hard gates walked past, and then a review of a self-selected file set.**
Three planted issues were in files the agent chose to open; two were not. Their
skill found five because it reviewed the actual changed files.

So the root cause is **cause 1 — no defined review scope**, not reviewer
quality. Causes 2–4 below remain real and worth fixing, but they are not what
produced this result.

**Two consequences, and the second is the bigger one:**

1. **Route B is the primary path, not an edge case.** The team already works
   this way. Phases 1 and 2 are the fix for the observed failure; Phase 3 is a
   quality improvement on top of it.
2. **Our hard gates are advisory in practice.** Not theoretically — observed,
   four times in one run. This does not reopen §10d's scope decision, but it
   removes any doubt about whether the enforcement layer is needed.

### 12.0a The rule this produces

**A review that cannot determine its scope halts. It never reviews a
self-selected subset and reports the result as a review.**

The failure here was not that two issues were missed. It was that three were
reported as though they were all of them — a confident answer from a run with
no task, no acceptance map, no test evidence and no stated file set. Partial
coverage reported as complete is worse than a refusal, because it ends the
search.

Every review stage states its scope in its findings header — the snapshot sha
and the file count it covered. A reviewer with no snapshot has nothing to state
and must say so.

---

### 12.1 The six causes

Reading the actual rules, there are **six independent causes**, any one of which
produces this result. Cause 1 is confirmed as what fired here; the rest are
latent and will surface once scope is fixed.

| # | Cause | Where | Fix |
|---|---|---|---|
| 1 | **The diff is empty → the reviewer improvises a scope.** Stage 3/4 scope on `git diff <base>...HEAD`; with nothing committed it is empty, so the agent reads a self-selected file set and covers a subset | `stage-3-security.md:23`, `stage-4-code-review.md:23` | **CONFIRMED — this is what fired (§12.0).** Fixed by Phase 1 (snapshot) + Phase 2 (Route B scope selection) |
| 2 | **Changed lines + 5 lines of context only.** An *absence* bug — missing null guard, missing auth check, missing error branch — has no changed line to attach to. A cross-file contract bug is correct locally and wrong in combination | `dev-stack-adaptive-code-review` SKILL.md Rule 1 | review the **changed files whole**, plus immediate callers/callees resolved from the code-context graph — the one place a graph beats grep |
| 3 | **"One finding per issue."** Rule 5 merges related findings. Two planted issues of the same class collapse into one report — found, but counted once | SKILL.md Rule 5 | keep the merge for *instances of one defect*; forbid merging across distinct planted causes. Report an instance count |
| 4 | **Consistency with the repo suppresses findings.** Rules 2 and 6 instruct the reviewer not to flag something the repo does consistently. **A planted issue that mirrors existing bad practice is invisible by design** | SKILL.md Rules 2, 6 | keep for *style*; exempt the correctness, security and BR-enforcement dimensions. A repo-wide missing null guard is still a bug |
| 5 | **Severity filtering looks like missing.** A found Minor is not surfaced as blocking, so the team reads it as missed | `stage-4-code-review.md` §4d | §11 — disposition every finding, and report *found-but-downgraded* separately from *not found* |
| 6 | **One reviewer, inherited context.** Stage 4 runs inline in the commit worker with the build's reasoning in scope, and the built-in `code-review` is not wired at all (grep: zero references) | `commit.md:205` | **D5 + §10d + §10e** — two reviewers, union of findings, fresh context, builder's diary withheld |

Cause 4 is the one I would bet on for the two that were missed, and it is the
most uncomfortable: **our reviewer is explicitly instructed not to report them.**

### 12a. Make recall measurable — the planted-defect eval

The team's test is an eval. Make it the standing one.

- A fixture repo carrying **N planted defects** with known severity and known
  class (absence · cross-file · security · BR violation · style).
- CI runs `/dev:commit`'s review stages against it and scores **recall per
  class**, not just overall.
- **Gate the plugin's own merges on recall.** Anthropic's playbook: 20–50 real
  tasks, run whenever skills or hooks change, merges gated on pass rate.
- **Every miss becomes a permanent case.** The two issues missed here are the
  first two entries.

We have no recall number today, for any reviewer, at any severity. Everything
above is reasoning from rules; the eval is what turns it into evidence.

---

## 12b. Enforcement — the three hooks, specified

Three `PreToolUse` hooks convert the three most-violated invariants from prose
into refusals. One script, three matchers, no CLI, no new runtime.
`plugins/dev/hooks/hooks.json` already wires `PreToolUse`, so this is a second
matcher on existing plumbing.

### 12b.1 What they block

| Hook | Blocks | Enforces |
|---|---|---|
| `Bash(git commit*)` | while a **build** session is live on that repo | *"`/dev:build` never commits"* — stated 3× in prose today |
| `Bash(git push*)` | while a **commit** session is live on that repo and `gates_passed` is false | no push before findings close |
| `Edit` · `Write` | on paths listed in a live **fix-loop** session | the agent cannot fix a failing test by editing the test |

### 12b.2 Polarity — fail open, always

**Marker present → restrict. Marker absent, unreadable, or stale → allow.**

This is the decision that determines whether anyone keeps the hooks installed.
A developer committing by hand with no Delivery OS session running must never
be blocked. The hooks are invisible except inside a live session.

| Condition | Hook does |
|---|---|
| `session.json` missing or unparseable | **allow**, exit 0, say nothing |
| no live session covers this repo | **allow**, exit 0 |
| session is stale (§12b.4) | **allow**, and print one line naming the stale session |
| live session restricts this operation | **block**, exit 2, with §12b.5's message |
| `DELIVERY_OS_HOOK_BYPASS=1` | **allow**, and log it (§12b.6) |

### 12b.3 The marker

One file, `.jetrix/cache/session.json`, written by the command, read by the hook.

```json
{
  "sessions": [
    {
      "id": "build-2026-11-04-1032-a1b2",
      "kind": "build",
      "repo": "D:/work/Inhouse-server",
      "task": "Subtask-7",
      "started_at": "2026-11-04T10:32:11Z",
      "gates_passed": false,
      "deny": {
        "git_commit": true,
        "git_push": true,
        "write_paths": []
      }
    }
  ]
}
```

| Written | By |
|---|---|
| created | `/dev:build` Stage 1 · `/dev:commit` Stage 1 |
| `write_paths` filled | Stage 6 fix loop on entry, emptied on exit |
| `gates_passed: true` | `/dev:commit` Stage 7.5, once every finding is closed or dispositioned |
| removed | Stage 11 (build) · Stage 9 (commit) · **and on every halt path** |

**Removal on halt is not optional.** Every `BLOCKED` exit removes its own
session before it returns. A halt that leaves a marker behind is the failure
mode that gets hooks uninstalled.

### 12b.4 Staleness — a crashed session must not brick the repo

A session is **stale** when `started_at` is more than **4 hours** old. No PID
checks, no heartbeats — both are fiddly cross-platform and both fail in ways
that are worse than the problem.

Three ways a stale marker clears, and all three are cheap:

| | |
|---|---|
| The hook ignores it | allow + one line: `stale build session from 10:32 ignored — /dev:build --clear-locks to remove` |
| A new run of the same kind on the same repo **reclaims** it | says so in its first output line; never silently inherits |
| `--clear-locks` on either command | removes every session for that repo and prints what it removed |

### 12b.5 What a block says

A refusal that does not say how to proceed is a bug report waiting to happen:

```
Blocked: git commit

  A /dev:build session is live on Inhouse-server (Subtask-7, started 10:32).
  /dev:build never commits — /dev:commit gathers the working tree after its
  gates pass. That boundary is what keeps unreviewed code out of the branch.

  If the build is finished:   /dev:commit Subtask-7
  If it crashed:              /dev:build --clear-locks
  If you need this anyway:    DELIVERY_OS_HOOK_BYPASS=1 git commit ...
                              (logged, and shown in the run summary)
```

Three facts, always: **what blocked it · why · the command that proceeds.**

### 12b.6 Bypass — available and auditable

`DELIVERY_OS_HOOK_BYPASS=1` allows the operation and appends to
`.jetrix/cache/bypass.log`: timestamp, operation, session id, repo. Every run
summary and PR body that follows a bypass prints `⚠ 1 hook bypass this run`
with the line.

**A silent bypass is worse than no hook.** An audited one is a pressure valve
that keeps the hooks installed.

---

## 12c. Failure handling — every mode, its response, its recovery

Three properties make a failed run usable rather than abandoned. Every entry
below has all three:

1. **A named blocker code** — never a generic error
2. **Durable state** — what was done survives the halt
3. **One command that resumes** — never "start again"

### 12c.1 Hooks

| Failure | Response | Recovery |
|---|---|---|
| Hook blocks a legitimate operation | exit 2 with §12b.5's three facts | the named command, or an audited bypass |
| Hook cannot run (node absent) | Claude Code skips it; **no enforcement, no breakage** | `/dev:build` Stage 0 warns once if node is missing |
| Marker left behind by a crash | stale after 4h, ignored with a line | `--clear-locks`, or the next run reclaims |
| Marker deleted mid-run | enforcement silently off for that run | Stage 11 / Stage 9 notices its own session is gone and records `session_marker_lost: true` in the run history |

### 12c.2 Snapshot

| Failure | Blocker code | Response | Recovery |
|---|---|---|---|
| Temp index left behind | — | `trap 'rm -f "$GIT_INDEX_FILE"' EXIT` on every path | automatic |
| `write-tree` / `commit-tree` fails | `snapshot-build-failed` | halt before any review; print the git error verbatim | fix the git condition, `--resume` |
| Detached HEAD | `snapshot-detached-head` | halt — there is no branch to deliver to | checkout a branch, `--resume` |
| Base sha unresolvable | `base-unresolvable` | halt, print the ladder tried (§4c) | name the base, `--resume` |
| Base moved on the remote mid-run | `base-moved` | halt at Stage 7's existing check | re-fetch, `--resume` from Stage 2 |
| Tree moved during review | `snapshot-stale` | re-run affected gates (§4d) | automatic, bounded by the fix-loop budget |
| Nothing in scope after selection | `empty-scope` | **stop cleanly** — no commit, no push, no PR | nothing to recover |

### 12c.3 Agents

| Failure | Blocker code | Response | Recovery |
|---|---|---|---|
| Reviewer dies / returns no verdict | — | **re-dispatch exactly once**, recorded as `retry: 1`. Second failure → `reviewer-no-verdict` | `--resume` re-dispatches with a fresh budget |
| Reviewer returns malformed findings | `reviewer-malformed-findings` | keep the raw output in `findings.md § ## Raw`, halt that unit only | fix or re-run that reviewer |
| Reviewer tool cannot run at all | — | existing rule: record `tool_status: not-invocable`, do the check by hand, say so in the PR | none needed |
| Repair exceeds bounds | `fix-loop-bounds-exceeded` | escalation written, `blocked` / `escalated`, **siblings continue** | human fixes, `--resume` with a fresh budget |
| Two runs collide on one repo | `repo-locked` | refuse the second, naming the first session and its start time | wait, or `--clear-locks` if the first is dead |
| Agent spawn fails / concurrency exhausted | — | queue behind the bound; never drop a unit silently | automatic |

**The repo lock is per repo path, not per task.** `owner_lock` in `status.md`
is per task, and a Route B adopted task is a different file — so a build on
branch X and a Route B commit on the same working tree would not see each
other. `session.json` (§12b.3) is the lock, because it is already keyed by repo.

### 12c.4 Stages

| Failure | Blocker code | Response | Recovery |
|---|---|---|---|
| External service won't start | `required-env-vars-missing` / `service-start-failed` | halt **before** running tests — never test against a partial env | set the var in `dev/build-env.local`, `--resume` |
| Pre-commit hook rejects | `precommit-rejected` | surface the hook output verbatim, halt. **Never `--no-verify`** | fix, `--resume` |
| Push rejected (non-fast-forward) | `push-rejected` | halt with the rebase command | rebase, `--resume` |
| Push rejected (permissions / protection) | `push-forbidden` | halt naming the rule or the missing access | resolve, `--resume` |
| PR ladder reaches step 4 | — | branch **is** pushed; print the compare URL; `phase: pr-pending` | open it in the browser, `--resume` records `pr_url` |
| Secrets found in the staged set | `secrets-in-staged-set` | halt. Never auto-gitignore, never auto-delete | human decides, `--resume` |
| Undispositioned findings at Stage 8 | `findings-undispositioned` | halt, listing each one | disposition them, `--resume` |

### 12c.5 The resume contract

**Every blocker code above is resumable with one command**, and that command is
the same one that failed, plus `--resume`:

```
/dev:build  --resume <target>
/dev:commit --resume <target>
```

Resume reads `units/<repo>/status.md § ## Run history`, finds the last stage
that did not reach `DONE`, and re-enters there. Three rules make that safe:

- **Completed stages are not re-run** unless their inputs changed — a changed
  snapshot sha invalidates Stages 3–5; new commits invalidate Stage 7 onward.
- **Nothing is half-written.** A stage either records `DONE` or leaves the state
  it found. That is what makes "re-enter at the last incomplete stage" correct
  rather than hopeful.
- **A halt always removes its session marker** (§12b.3) so a resumed run is
  never blocked by its own predecessor.

### 12c.6 What is reported when a run fails

A failed run prints the same shape as a successful one, which is what makes it
readable:

```
✗ /dev:commit Subtask-7 halted at Stage 5 — acceptance regression

  Blocker:   fix-loop-bounds-exceeded
  Findings:  AC-4 still failing after 3 focused fixes + 2 broad re-runs
  Written:   units/Inhouse-server/findings.md  (3 open, 11 settled)
             units/Inhouse-server/status.md    (## Run history, stage-5)
  Branch:    feature/FEAT-HCAL-01-holiday-calendar-backend  (6 commits, unpushed)

  Resume:    /dev:commit --resume Subtask-7
  Or inspect: units/Inhouse-server/findings.md § ## Code review
```

**Never report a halt as a summary of what went wrong.** Report what survives,
where it is, and the one command that continues.

---

## 13. Artifacts — current vs after

**No new file inside `.jetrix/`, and none removed.** Every change there is a new
*section* or *field* in a file that already exists — v2.4 consolidated sixteen
audit files into six, and re-splitting them to carry new content would undo the
thing that made the tree readable.

**One new file in the product repo**: the scenario→test map (§13c). It is
committed with the code for the same reason the code-context graph is — a
gitignored workspace copy is invisible to everyone who did not run the build.

### 13a. The unit folder

```
.jetrix/requirements/<slug>/features/<slug>/units/<repo>/     ← unchanged path
.jetrix/tasks/<slug>/units/<repo>/                            ← unchanged path (Route B)
```

| File | Today | After |
|---|---|---|
| `implementation.md` | Implementation tab, §1–§8 | **unchanged** on Route A. On Route B written *after* review, from the delivered diff |
| `description.md` | Description tab, N>1 only | unchanged |
| `status.md` | `## Run history` · `## Acceptance` | **+ fields**: `snapshot_sha`, `scope_selected[]`, `scope_excluded[]`, `base_sha`, `review_class` per stage · `phase: adopted` now legal · `## Acceptance` rows may carry `source: inferred` |
| `findings.md` | `## Security — build` · `## Security — commit` · `## Code review` · `## Context merge` | **+ `## Test verification`** (D4) · **+ `## Settled`** (§10a) · every finding gains a stable cross-run id, a `disposition`, and the snapshot sha it was found against |
| `analysis.md` | plan scratchpad | unchanged. **Never passed to a reviewer** (§10c) |
| `pr-summary.md` | PR body · `## How to verify` | **+ disposition summary** — no finding reaches it undispositioned (§11) |
| `discussion.md` · `attachments/` | pull-only | unchanged |
| `plan-blockers.md` | conditional | unchanged; not written on an adopted task |
| `merge-conflicts.md` | conditional | unchanged |

### 13b. What is deliberately NOT created

| Not created | Why | Where that content lives |
|---|---|---|
| `test-coverage.md` | duplicates the scenario→test mapping | `status.md § ## Acceptance`, `Verified by` column |
| `security-review.md` · `code-review.md` | v2.4 consolidation | `findings.md` sections |
| `test-verification-report.md` | same | `findings.md § ## Test verification` |
| `acceptance-report.md` | would split the two-column design | `status.md § ## Acceptance` |
| a snapshot file | the snapshot is a dangling git object, not a file | `snapshot_sha` in `status.md` |
| a Route B state store | D1 — reuse `tasks/<slug>/units/<repo>/` | the existing unit shape |

### 13c. The scenario→test map travels with the code (Model B)

**`.jetrix/` is entirely gitignored.** `status.md § ## Acceptance` is a local
working copy — a teammate who clones the repo sees none of it, and the PR body
is a snapshot frozen at PR time. So the thing a person wants to open and check
by hand does not exist for anyone but the developer who ran the build.

Split the artefact by **how often it changes**:

| | Lives | Changes | Committed |
|---|---|---|---|
| **The map** — scenario → test file → test name → tier → fixtures | `<repo>/context/test-map/<feature-slug>.md` | only when tests change | **yes** — reviewed in the PR diff |
| **The results** — pass/fail/flaky, per run, build + commit columns | `.jetrix/…/units/<repo>/status.md § ## Acceptance` | every run | no — gitignored |

This is the same Model B split the code-context graph already uses: durable
structure in the repo, per-run state in `.jetrix/`. Committing results would
churn the repo on every build and make the diff unreadable.

```markdown
<!-- <repo>/context/test-map/holiday-calendar-management.md -->
---
doc_type: test-map
feature_id: FEAT-HCAL-01
produced_by: dev
generated_at: 2026-11-03
---

# Test map — Holiday calendar management

| Kind | ID | Scenario | Tier | Test | Run it | Needs | Fixtures |
|---|---|---|---|---|---|---|---|
| AC | AC-1 | Adding a holiday on a free date succeeds | integration | `create.spec.ts::adds` | `npm test -- tests/holidays/create.spec.ts -t "adds"` | `real-db` | `holidayFactory` |
| AC | AC-2 | A date already held refuses distinctly | integration | `create.spec.ts::duplicate` | `npm test -- tests/holidays/create.spec.ts -t "duplicate"` | `real-db` | `holidayFactory` |
| BR | BR-1 | One holiday per date, active rows only | unit | `rules.spec.ts::uniqueness` | `npm test -- tests/holidays/rules.spec.ts -t "uniqueness"` | — | — |
| TS | TS-4 | Full add → list → remove journey | e2e | `tests/e2e/holiday.spec.ts` | `npm run test:e2e -- --grep "holiday"` | `backend-running`, `frontend-running` | `seedCalendar` |

## Not automated
| ID | Scenario | Why | How to check by hand |
|---|---|---|---|
| NFR-2 | Calendar renders under 200ms on a 3-year dataset | needs production-scale data | runbook in the PR summary |
```

**`Run it` and `Needs` are the point of the document**, and they are what make
the architecture work:

- **`Run it`** is a copy-and-run command per scenario, so a person or an agent
  runs one row without reconstructing the invocation (runner, path syntax,
  name-filter flag — all stack-specific).
- **`Needs`** is what `/dev:commit` reads to decide what to start. **Build
  declares; commit executes.** Build knows the tier and the dependency because
  build wrote the test; commit re-deriving either from file paths is how the two
  halves drift.

**`CLAUDE.md` points at the map.** Build Stage 5-6 adds a `## Tests` section to
the repo's `CLAUDE.md` once, idempotently, saying coverage lives in
`context/test-map/<slug>.md`. `CLAUDE.md` is what an agent reads on entering a
repo; a map nobody is pointed at is a map nobody opens, and the next agent
writes a second `holidayFactory`.

**Written by** `/dev:build` Stage 5-6, as the tests are written — not after.
**Verified by** `/dev:commit` Stage 5's `dev-test-verifier` against the tests
that actually exist. **Reviewed** like any other file, because it is in the diff.

The `## Not automated` block is where `NOT AUTOMATED` and `INCONCLUSIVE` rows
(§9a) get a home instead of vanishing into a status value nobody reads.

### 13d. Fixtures and mocks — ownership

Fixtures were named in every earlier revision of this plan and had no owner.
They have two, at different scopes:

| Scope | Owner | Lives | Example |
|---|---|---|---|
| **Harness-level** — factories, builders, test DB/container setup, shared mocks | `/qa:setup`, recorded in `quality-gates.md § <repo> → ## Conventions` | the repo's own test tree | `tests/support/factories/`, `tests/support/mongo.ts` |
| **Feature-level** — the fixtures one feature's tests need | `/dev:build` Stage 6 | beside those tests | `tests/holidays/fixtures/seedCalendar.ts` |

Three rules:

- **Reuse before creating.** Stage 6 reads `## Conventions` first; a second
  parallel factory for an entity that already has one is a code-review Major
  (Dimension 7, reuse).
- **Every fixture a scenario depends on is named in the test map** — that is
  the `Fixtures` column. A fixture nobody can trace to a scenario is dead weight;
  a scenario whose fixture is missing is why the test passes against nothing.
- **A fixture that mocks the behaviour under test is a finding, not a fixture.**
  This is the semantic half of §9 — build's Stage 8c catches the mechanical case
  (`vi.mock` at `tier: integration`); the commit test-verifier catches the case
  where the mock is legal at that tier but returns a canned answer that makes the
  assertion vacuous.

### 13e. New files this rework adds

Exactly one in the plugin, one fixture at Phase 6, and this document.

| Path | Kind | Phase | Purpose |
|---|---|---|---|
| `plugins/dev/commands/references/common/review-snapshot.md` | plugin reference | 1 | the one snapshot contract every consumer reads — §16a |
| `<repo>/context/test-map/<feature-slug>.md` | **product repo**, committed | 3 | scenario → test → fixtures, checkable by hand — §13c |
| `plugins/dev/commands/references/common/findings-contract.md` | plugin reference | 3 | stable finding ids, dispositions, `## Settled` — §10a |
| `plugins/dev/commands/references/common/session-marker.md` | plugin reference | 0 | the hook/command contract — §12b.3 |
| `plugins/dev/hooks/guard.js` | **executable** | 0 | the three `PreToolUse` hooks — §12b |
| `plugins/dev/skills/dev-test-verifier/SKILL.md` | plugin skill | 3 | the semantic test reviewer — §9. Stage 5 invokes it by name, so it had to exist |
| `examples/review-recall-fixture/` | test fixture | 6 | planted defects with known class, for the recall eval — §12a |
| `docs/dev/build-commit-rework.md` | doc | — | this file |

Every finding cites the snapshot sha it was produced against.

---

## 14. Phases

Frozen.

| Phase | Work | Blocked by |
|---|---|---|
| **0** | **enforcement + failure handling** — the three hooks (§12b) · session marker + per-repo lock · `--clear-locks` · the blocker-code and resume contract (§12c) | nothing |
| **1** | snapshot helper · the nine diff call-sites · Stage 0 scope detection · provenance (§4e) · Stage 11 commit-count correction · Stage 9 demotion · **Stage 10 gate correction** · staleness detection primitive (§4d) | nothing — **ready**, worksheet in §16 |
| **2** | route detection · `phase: adopted` (D7) · automatic adoption in Stage 0 (D8) · mixed-change scope selection (§4b.i) · **halt-on-undeterminable-scope (§12.0a)** | Phase 1 |
| **3** | fresh-context reviewers · built-in `code-review` as advisory second opinion · test-verifier · withhold rules (§10c) · review classes (§10b) · persistent findings + `## Settled` (§10a) · named agent streams · concurrency block · **scope widening for causes 2–4 (§12)** | Phase 1 |
| **4** | controlled repair · selective re-review · staleness orchestration · **disposition gate + batched cheap-fix pass (§11)** | Phase 3 |
| **5** | scoped staging · snapshot-match gate · commit/push/PR verification | Phase 1, 4 |
| **6** | regression: §15 + `--tests-only` + `--vulnerable` · **planted-defect recall eval (§12a)** | all |

**Phase 0 ships one hook script; everything after it is markdown.** Hooks go
first so every later phase lands on enforced ground rather than being added to
a system that cannot hold its own invariants — which is the condition that
produced the 3-of-5 run.

Phase 0 is small: one node script, three matchers, one marker file, and the
blocker-code/resume contract that the other phases then conform to.

Two ordering notes, both deliberate:

- **Visibility ships inside Phase 3, not after it.** Reviewers without named
  streams and a wave table are a black box that spawns fifteen agents — worse
  for the user than today.
- **Staleness splits across 1 and 4.** The primitive (compute, record, compare
  at staging) is Phase 1 because Phases 2–3 otherwise run on snapshots nothing
  checks. What to re-run on a mismatch is Phase 4's.

---

## 15. Regression scenarios

| Scenario | Expected |
|---|---|
| Route A feature, multi-repo split | full plan → build → commit, per-repo PRs |
| Route A bug via `tasks/<slug>.md` | non-feature track unchanged |
| Route B manual edit, no task | adoption offered, validated, delivered |
| Staged + unstaged in one file | both detected, neither discarded |
| New untracked file | included only when in the selected scope |
| Unrelated local edit | excluded from the review snapshot and from staging |
| Tree edited mid-review | stale snapshot detected, affected gates re-run |
| No change | stop; no empty commit, no push, no PR |
| Critical security finding | delivery blocked, repair routed |
| No harness on Route B | `BLOCKED` / `NOT AUTOMATED`, never silent pass |
| `--tests-only` | Stage 8.5 terminal handling intact |
| `--vulnerable` | majors still reported, not taken |
| Push fails | local commit preserved, actual status reported |

---

## 16. Implementation worksheet

Compiled by inspection on 2026-11-03 against `feature/delivery-os-rework`.
Line numbers are from that commit; **re-confirm each before editing.**

**How to use this.** Steps are numbered `<phase>.<step>` and ordered so that no
step depends on one below it. Each carries the files it touches and how to
verify it. A phase is not done until its gate (§16.8) passes.

**The plan originally said "four diff call-sites". There are nine**, across five
files, plus two that must be left alone, plus two `--resume` paths that key off
commit history and need the snapshot sha instead.

---

### 16.1 Phase 0 - enforcement + the failure contract

Ships first so every later phase lands on ground that holds its own invariants.
One node script; everything else is markdown.

| # | Step | Files | Verify |
|---|---|---|---|
| 0.1 | DONE - Session-marker schema | §12b.3 into `references/common/session-marker.md` (new) | - |
| 0.2 | DONE - Hook script - read marker, drop stale (4h), match operation, exit 0/2 | `plugins/dev/hooks/guard.js` (new) | run by hand with a crafted marker; confirm exit 0 with **no** marker |
| 0.3 | DONE - Wire three matchers | `plugins/dev/hooks/hooks.json` | `git commit` blocked with a live build marker; **allowed with none** |
| 0.4 | DONE - Write the marker at session start | `build.md` Stage 1 - `commit.md` Stage 1 | marker appears with `repo` + `started_at` |
| 0.5 | DONE - Update + remove it | `stage-7-5` sets `gates_passed: true` - build Stage 11 - commit Stage 9 - **every halt path in both commands** | kill a run mid-way -> marker gone or stale-ignored |
| 0.6 | DONE - `--clear-locks` on both commands | `build.md` §1 - `commit.md` §1 | prints what it removed |
| 0.7 | DONE - Bypass + log + surfacing | `guard.js` - build Stage 11 - commit Stage 10 summary | `DELIVERY_OS_HOOK_BYPASS=1` allows and logs |
| 0.8 | DONE - Per-repo collision refusal | `commit.md` Stage 0 - `build.md` Stage 0 | second run on the same repo refuses with `repo-locked` |
| 0.9 | DONE - Adopt the blocker-code + resume vocabulary (§12c) | `build.md` §5 - `commit.md` §7 | every halt names a code from §12c |

**Why 0.3 before 0.4:** prove the hook is harmless (fail-open, no marker) before
anything starts writing markers. Reversed, a bug blocks every commit on the box.

---

### 16.2 Phase 1 - snapshot, diff scope, provenance

| # | Step | Files | Verify |
|---|---|---|---|
| 1.1 | DONE - The snapshot contract - §4a mechanism - §4b two snapshots - §4b.i prompt - §4c base ladder - §4d staleness - `trap` cleanup | `references/common/review-snapshot.md` (new) | - |
| 1.2 | DONE - **Prove it on Windows** - index path from `git rev-parse --absolute-git-dir`, never `mktemp`/`/tmp`; `-c core.safecrlf=false` | - | DONE - tree/index/HEAD byte-identical, untracked included, 0 warnings |
| 1.3 | DONE - Build Stage 9 -> report-only **and** Stage 10 gate correction, **together** | `stage-9-security.md` (14, 43, 209, §9e, delete §9g + §9g.i, §9h) - `stage-10-context-update.md` (§10a) | a build with a Critical finding still reaches Stage 10 |
| 1.4 | DONE - Provenance - one change, three places | `stage-10-context-update.md` (14, 54, 58, 61, 194) - `code-context-readiness.md:41` (+`pending` row) - `stage-7-5` new §7.5e.i backfill | a built unit reads `pending`; a real sha after commit |
| 1.5 | DONE - Commit Stage 0 - clean-tree check -> scope detection | `commit.md:108` - `commit.md:104` | `/dev:commit` no longer refuses a post-build tree |
| 1.6 | DONE - Stage 3 scope substitution | `stage-3-security.md` 15, 23, 57-58, 120, **143** | findings header names the snapshot sha + file count |
| 1.7 | DONE - Stage 4 scope substitution | `stage-4-code-review.md` 23, 45-46, 101, **§4h** | same |
| 1.8 | DONE - Reviewer skill input contract | `dev-stack-adaptive-code-review/SKILL.md` 16, 61 | accepts a snapshot ref |
| 1.9 | DONE - Stage 7.5 stages the selected set - Stage 8 snapshot-match gate | `stage-7-5-gather-and-commit.md` §7.5b - `stage-8-9-push-pr.md` §8a | edit a file mid-run -> `snapshot-stale` |
| 1.10 | DONE - Build Stage 11 commit-count honesty | `stage-11-summary.md:31` | prints `Commits: 0 - uncommitted` |
| 1.11 | DONE - `empty-scope` - nothing in scope after selection stops cleanly: no commit, no push, no PR, no empty commit (§12c.2) | `commit.md` Stage 0 | a clean tree exits 0 with one line |

#### The nine call-sites — /dev:build

| File | Line | Today | Change |
|---|---|---|---|
| `references/build/stage-9-security.md` | 14 | `Branch has commits — git log <base>..HEAD returns at least one` | **delete.** Build produces no commits |
| | 43 | `"diff_range": "<base>...<HEAD>"` | `"diff_range": "<base>..$SNAP"` |
| | 209 | log `scope: diff (develop...HEAD, 8 files)` | `scope: snapshot <sha12> vs develop (N files)` |
| | §9e, §9g, §9g.i | Critical blocks → 3-attempt repair loop → `repair_loop_invocation` trace | **demote to report-only (D2).** Delete §9g and §9g.i. Critical findings are recorded and carried to commit Stage 3, not repaired here |
| | §9h | `repair_attempts: 1` | replace with `findings_recorded:` + `carried_to_commit: true` |
| `references/build/stage-10-context-update.md` | 14 | `Branch commits present — git log <base>..HEAD ≥ 1` | **delete** |
| | §10a | HALT on `stage-9-repair-loop-not-invoked` / `-did-not-clear-critical` | **replace** with "Stage 9 ran and recorded findings". Commit is now the security authority — keeping this gate would block every build once §9g is gone |
| | 54 | `implemented_by_commit: <HEAD SHA>` | `implemented_by_commit: pending` |
| | 58, 61 | `mapped_from_commit` from `git log -1 --format=%H -- <file>` | `mapped_from_commit: pending` + the §4e rationale (a dangling sha must never reach a committed file) |
| | 194 | `commit_sha: a1b2c3d` | delete from the log block |
| `references/build/stage-11-summary.md` | 31 | `Commits:  8  (7 code + 1 context-update)` | `Files changed:  18 (+624/-12) · uncommitted` and `Commits: 0 — /dev:commit owns the git-write boundary` |
| `references/plan/code-context-readiness.md` | 41 | `\| no mapped_from_commit \| never stamped \| report unknown, never stale \|` | add a row: `\| mapped_from_commit: pending \| built, not yet committed \| report pending, never stale \|` |

#### The nine call-sites — /dev:commit

| File | Line | Today | Change |
|---|---|---|---|
| `commands/commit.md` | 104 | `tests_only` → `Read git diff <base>...HEAD` | `git diff <base>..$SNAP` |
| | **108** | **`Verify no uncommitted changes (git status --porcelain empty)`** | **replace with scope detection** — build the detection snapshot, classify, select scope (§4b.i), build the review snapshot. This single line is what refuses every v2.3.20-conformant build |
| `references/commit/stage-3-security.md` | 14 | `git log HEAD..<remote>/<base>` empty | **keep** — ancestry check, unrelated to diff scope |
| | 15 | precondition: `git diff <base>...HEAD` returns the expected file list | rewrite against `$SNAP` |
| | 23 | **Scope:** `git diff <base>...HEAD` | **Scope:** `git diff <base>..$SNAP` |
| | 57–58 | `diff_base` / `diff_head` frontmatter | add `snapshot_sha:` — every finding cites it |
| | 120 | log `scope: "git diff develop...HEAD (18 files…)"` | snapshot form |
| | 143 | `--resume`: re-run if new commits via `git log --since=` | re-run if the **snapshot sha differs** from the recorded one |
| `references/commit/stage-4-code-review.md` | 23 | The feature diff — `git diff <base>...HEAD` | `$SNAP` |
| | 45–46 | `diff_base` / `diff_head` | add `snapshot_sha:` |
| | 101 | log scope string | snapshot form |
| | §4h | `--resume` on new commits | snapshot-sha comparison |
| `skills/dev-stack-adaptive-code-review/SKILL.md` | 16 | input contract: `git diff <base>...<HEAD>` | accept a snapshot ref; the skill is stack-adaptive, not commit-aware |
| | 61 | Rule 1 — diff-scoped only | same wording, snapshot ref |
| `references/commit/stage-7-5-gather-and-commit.md` | §7.5b | categorize `git status --porcelain` | stage **exactly `scope_selected[]`** from §4b.i |
| | §7.5e | `git add <specific paths>` | unchanged in spirit; paths come from the selection |
| | new §7.5e.i | — | **backfill** `implemented_by_commit` + `mapped_from_commit` in touched context units with the real sha, then amend-free re-stage those files |
| | 128 | `git log --oneline <base>..HEAD` | **keep** — runs after the commit exists |
| `references/commit/stage-8-9-push-pr.md` | §8a | trace gates | add: reviewed snapshot sha == staged sha, else `blocker: snapshot-stale` |

### 16d. Left alone, deliberately

| File | Why |
|---|---|
| `references/plan/blocker-detection.md:121` | `git diff --name-only <base>...<branch>` runs at **plan** time against a real branch. Different question |
| `references/commit/stage-8-9-push-pr.md:330,333` | `compare/<base>...<head>` is a GitHub **URL**, not a git command |
| `references/commit/stage-7-semantic-merge.md` | operates on context-unit files, not a diff |
| `commands/fix-review.md` | gates on `pr_url`; post-PR, so real commits exist by then |


#### Left alone, deliberately

| File | Why |
|---|---|
| `references/plan/blocker-detection.md:121` | `git diff --name-only <base>...<branch>` runs at **plan** time against a real branch. Different question |
| `references/commit/stage-8-9-push-pr.md:330,333` | `compare/<base>...<head>` is a GitHub **URL**, not a git command |
| `references/commit/stage-7-semantic-merge.md` | operates on context-unit files, not a diff |
| `commands/fix-review.md` | gates on `pr_url`; post-PR, so real commits exist |
| `stage-3-security.md:14` | `git log HEAD..<remote>/<base>` is the ancestry check, unrelated to diff scope |

---

### 16.3 Phase 2 - routing and Route B

| # | Step | Files | Verify |
|---|---|---|---|
| 2.1 | DONE - Add `phase: adopted` to the vocabulary | `delivery-os-conventions/SKILL.md` 782, 796, 827 | - |
| 2.2 | DONE - Open the commit gate to it | `commit.md` 12, 27, 79 | - |
| 2.3 | DONE - Propagate the state | `loop-control.md` 25, 44, 56 - `feature-delivery-loop/SKILL.md:74` - `dev-context-templates.md:28` - `dev_readme.md:65` | grep for `phase: built` finds no stale gate |
| 2.4 | DONE - **Automatic adoption inside Stage 0** - write the record, resolve surfaces, set `inProgress`/`adopted`; **skip** build-sequence compose and blocker detection. No flag, no command | `commit.md` Stage 0 - reuses `references/plan/non-feature-track.md` read order | record appears with no `## Build sequence`; `/dev:plan` gains no new flag |
| 2.5 | DONE - Mode detection at Stage 0 (1/2/3/4) + route resolution | `commit.md` Stage 0 | a dirty tree with no task resolves to Route B |
| 2.6 | DONE - The inline adoption doorway (D8) | `commit.md` Stage 0 | one `[Y/n]`, then it runs |
| 2.7 | DONE - Scope-selection prompt §4b.i - states shown, staged/unstaged `[a]`/`[b]`, `scope_selected[]` / `scope_excluded[]` recorded | `commit.md` Stage 0 | index-only path builds from the index blob |
| 2.8 | DONE - Route B base ladder §4c | `commit.md` Stage 2 | upstream -> `env_branches.dev` -> ask |
| 2.9 | DONE - Halt-on-undeterminable-scope (D13) + scope stated in every findings header | `commit.md` Stage 0 - stages 3/4/5 | no snapshot -> halt, never an improvised review |
| 2.10 | DONE - Route B QA check -> `BLOCKED` / `NOT AUTOMATED`, never silent pass | `stage-5-acceptance.md` | repo with no harness reports per-row |
| 2.13 | DONE - Document the per-hunk precondition in the command's own help - `git add -p`, then answer `[b]` (§4b.i) | `commit.md` §1 + `argument-hint` | a user reading `/help` finds it without opening this doc |
| 2.12 | DONE - **Route B reduced stage set (§7b.ii)** - Stage 1 lock-only, Stage 5 reduced, Stage 7 skipped, no tracker write | `commit.md` §3, §5 - `stage-5-acceptance.md` - `stage-7-semantic-merge.md` | Route B run touches no tracker and skips semantic merge |
| 2.11 | DONE - §3a five-trigger ask-vs-infer | `commit.md` Stage 0 | an `auth/` path forces ask |

---

### 16.4 Phase 3 - reviewers

| # | Step | Files | Verify |
|---|---|---|---|
| 3.1 | DONE - Stable cross-run finding ids + `## Settled` | `stage-3/4/5` - `findings.md` schema §13a | a finding accepted last run is not re-raised |
| 3.2 | DONE - Review classes (§10b) | `stage-3`, `stage-4`, `stage-5`, build `stage-9` | advisory never blocks |
| 3.3 | DONE - Withhold rules (§10c) | `stage-3/4/5` dispatch blocks | brief contains no builder reasoning |
| 3.4 | DONE - Three fresh-context reviewer agents, parallel, read-only | `commit.md` §5 routing | three named streams appear |
| 3.5 | DONE - Built-in `code-review` as advisory second opinion | `stage-4-code-review.md` | union of findings, source labelled |
| 3.6 | DONE - The test-verifier (§9) | `stage-5-acceptance.md` | semantic check, not a re-run of Stage 8c |
| 3.7 | DONE - Recall fixes - scope widening (cause 2) - merge rule (cause 3) - consistency exemption for correctness/security/BR (cause 4) - found-but-downgraded reported separately (cause 5) | `dev-stack-adaptive-code-review/SKILL.md` Rules 1, 2, 5, 6 - `stage-4` §4d | a repo-wide missing guard is now reported |
| 3.8 | DONE - Greenfield degradation §7b.i | `stage-4` - `stage-5` | thin graph records `scope_expansion: unavailable` |
| 3.9 | DONE - Test map written at build Stage 6, verified at commit Stage 5 | `stage-5-6-implement.md` - `stage-5-acceptance.md` - §13c template | `<repo>/context/test-map/<slug>.md` appears in the diff |
| 3.10 | DONE - Fixture ownership + reuse rule (§13d) | `stage-5-6-implement.md` - `qa-test-setup` conventions | duplicate factory flagged Major |
| 3.11 | DONE - Named streams - wave table - concurrency block before fan-out | `build.md` §3 - `commit.md` §1a | `5 x 3 = 15` printed |
| 3.12 | DONE - **Update the shared contract** - `findings.md` gains `## Test verification` + `## Settled` in the §1 tree - `<repo>/context/test-map/` added to §1.b - new `doc_type: test-map` in §2 - stable cross-run finding ids described | `delivery-os-conventions/SKILL.md` §1, §1.b, §2 | an agent reading only the contract produces the right files |

---

### 16.5 Phase 4 - repair and disposition

| # | Step | Files | Verify |
|---|---|---|---|
| 4.1 | DONE - Fresh repair agent per round, serial per repo | `stage-6-fix-loop.md` | two repairs never run concurrently in one tree |
| 4.2 | DONE - Reviewer re-dispatch exactly once on no-verdict | `stage-3/4/5` | second failure -> `reviewer-no-verdict` |
| 4.3 | DONE - Selective re-review rules | `stage-6-fix-loop.md` §6e | code review skipped when its files are untouched |
| 4.4 | DONE - Disposition gate (§11) | `stage-6` - `stage-8-9` §8a | `findings-undispositioned` halt fires |
| 4.5 | DONE - Nit cap (10) + batched cheap-fix pass | `stage-6-fix-loop.md` | 40 nits do not produce 40 loops |
| 4.6 | DONE - Staleness orchestration - what re-runs on a changed sha | `stage-6` - §4d | |

---

### 16.6 Phase 5 - delivery

**D12 needs no step.** Push and PR are already the terminal stages gated on
everything before them; there is nothing to add and no flag to introduce. The
work here is making sure the gate set is complete, not making delivery optional.

| # | Step | Files | Verify |
|---|---|---|---|
| 5.1 | DONE - Stage exactly `scope_selected[]` | `stage-7-5-gather-and-commit.md` §7.5e | excluded file stays uncommitted |
| 5.2 | DONE - Backfill provenance before staging context units | `stage-7-5` §7.5e.i | real sha lands in the unit |
| 5.3 | DONE - Push + PR gated on §8a's full precondition set | `stage-8-9-push-pr.md` | |
| 5.4 | DONE - Failure reporting shape (§12c.6) | both commands' summary sections | a halt prints what survives + one resume command |

---

### 16.7 Phase 6 - regression and recall

| # | Step | Files | Verify |
|---|---|---|---|
| 6.1 | DONE - Build the fixture - N planted defects, known severity + class | `examples/review-recall-fixture/` (new) | seeded from the team's original 5 |
| 6.2 | DONE - Recall eval runner, scored **per class** | `scripts/` + CI | produces a recall number |
| 6.3 | DONE - Gate plugin merges on recall | `.github/workflows/lint.yml` | |
| 6.4 | DONE - Regression: every §15 scenario | - | all pass |
| 6.5 | DONE - Regression: `--tests-only` and `--vulnerable` keep Stage 8.5 handling | - | both still terminate correctly |
| 6.6 | DONE - **User-facing docs** - Route B, `--clear-locks`, the hooks, the test map | `USAGE.md` §5 - `README.md` - `plugins/dev/dev_readme.md` | a reader can find Route B without this document |
| 6.7 | DONE - **Pre-existing drift, fixed while we are in these files** - `USAGE.md` §3c/§3d and `README.md` still advertise `/tl:plan`, `/tl:review`, `/tl:resolve` (all retired per conventions §1.f) - `USAGE.md` §3e/§7 list `/jetrix:push context`, a stage that does not exist | `USAGE.md` - `README.md` | every command named in the docs exists |

---

### 16.8 Phase gates

A phase is done when **all** of these hold. Do not start the next one early.

| Phase | Gate |
|---|---|
| 0 | `git commit` works normally with no marker - blocked with one - a killed run does not brick the repo - `--clear-locks` works |
| 1 | `/dev:build` -> `/dev:commit` completes on a scratch repo - Stage 3 and 4 findings headers name a non-empty file count - a built unit reads `pending`, then a real sha after commit |
| 2 | AI-written changes with no task -> `/dev:commit` adopts, selects scope, reviews, delivers - an undeterminable scope halts |
| 3 | three named reviewer streams - a settled finding is not re-raised - the test map lands in the repo diff |
| 4 | a blocking finding routes, repairs, re-reviews, closes - an undispositioned Medium halts the push |
| 5 | an excluded file is still uncommitted after a successful PR |
| 6 | a recall number exists |

**Run `node scripts/lint-plugins.js` after every step**, and a full
`/dev:build` -> `/dev:commit` at every phase gate.

### 16.9 Two checks added during implementation, not in the original plan

Six instances of one bug class surfaced while building this: a stage gating on a
field an earlier stage never records. Four were found by hand, which does not
scale. Both checks now live in `scripts/lint-plugins.js` and run in CI.

| Check | Catches | Level |
|---|---|---|
| `contracts` | a file reads `stage-N.field` that stage-N's own yaml block never records | ERROR |
| `frontmatter` | the `unit-status` template and the conventions' field list disagree | ERROR |

**`contracts` keys on the loop, not the number.** `/dev:build` and `/dev:commit`
both have a stage-9 (security vs PR) and they are different stages; unioning
them makes the check silently lenient. A cross-loop read is written
`build.stage-8.final_status` — the only unambiguous form.

Between them these found two bugs nobody had noticed: `stage-9.attempts` (from
v2.3.22) and `base_branch` — written by `/dev:plan`, read by `/dev:build`
Stage 3 and `/dev:commit` Stage 2, and declared in no contract at all.

---

## 17. Readiness

| Phase | Ready to implement | Blocked on |
|---|---|---|
| **1** | **Yes** — nine call-sites inspected, worksheet to file and line (§16a–f) | nothing |
| **2** | **Yes** — D7/D8 settled, state edits listed (§16e) | Phase 1 landing |
| **3** | **Yes** — D5, §10a–c, §12 causes 2–4 all specified | Phase 1 landing |
| **4** | **Yes** — §11 disposition model, bounds unchanged | Phase 3 |
| **5** | **Yes** | Phases 1, 4 |
| **6** | Needs a fixture repo built (§12a) | Phases 1–5 |

**Every phase is implementable from this document as written.** Nothing is
blocked on a decision.

### 17a. What would make the work safer, and what is missing

Specification completeness is not the same as readiness to verify. These are the
gaps between "the change is written down" and "the change is known to work":

| # | Need | Blocks? | Why |
|---|---|---|---|
| 1 | **A scratch repo + bound workspace to run `/dev:build` → `/dev:commit` against** | **Yes, for verification** | §16f requires a real run between steps. Without one, every change is reasoned-correct and untested |
| 2 | **One real `/dev:commit` transcript, or confirmation the current flow runs at all** | **Yes, for Phase 1's premise** | see §17b |
| 3 | Which 2 of the team's 5 planted issues were missed, and their class | No | decides which of §12's six causes is real |
| 4 | What the team's own review skill does — scope, passes, severity model | No | it is a working reference for the recall we lack |
| 5 | A real `units/<repo>/status.md` and `findings.md` from a completed run | No | the stage files are written against a schema; real files drift |
| 6 | Whether the built-in `security-review` already handles uncommitted work | No | if yes, several of the nine substitutions shrink to nothing |

### 17b. One contradiction to resolve first

My analysis says `/dev:commit` Stage 0 (`commit.md:108`) refuses a dirty working
tree, and `/dev:build` leaves one by design — so the happy path cannot complete.

**But the team ran `/dev:commit` and got 3 findings.** Both cannot be true. One
of these is the case, and they lead to different work:

| Possibility | Consequence |
|---|---|
| They ran an older plugin version | Phase 1 is correct as written |
| The agent improvised past Stage 0 | the gates are softer in practice than the spec — worth knowing **before** adding more of them |
| They committed by hand first, then ran `/dev:commit` | Stage 0 passed legitimately; the empty-diff cause (§12 cause 1) is **not** what caused the miss, and causes 2–4 carry more weight |
| I have misread something | Phase 1's premise needs re-checking |

One transcript, or one real run, settles it. It is the cheapest high-value thing
available and it should happen before the first edit.

---

## 18. Invariants that do not change

- `/dev:build` never commits, stages or pushes.
- `/dev:commit` owns the git-write boundary.
- No worker prompts after fan-out; every question is asked at the checkpoint.
- Never discard, reset or clean unrelated local changes.
- Never `git add -A` into the **real** index at delivery time.
- Never `--no-verify`, never `--force` without an explicit flag.
- Never mark MC `done` from a command — that is the PR-merge webhook.
- An unavailable gate is blocked, never passed.
