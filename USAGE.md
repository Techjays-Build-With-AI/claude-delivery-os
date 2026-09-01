# Delivery OS — Usage Guide

End-to-end guide for the Techjays Delivery OS Claude Code plugins. Covers first-time setup, workspace binding (greenfield + brownfield), BA discovery, TL context graph, QA harness, and the per-feature plan → build → commit loop.

Read once end-to-end; refer back by section.

---

## 0. Install and register (once per machine)

### 0a. Install the plugin from the marketplace

**Add the marketplace.** Registers `techjays-delivery-os` with Claude Code and unlocks all seven bundled plugins.

```
/plugin marketplace add Techjays-Build-With-AI/claude-delivery-os
```

**Install the plugins.** `delivery-os` (the shared core) must go first — every other plugin reads its templates and vocabulary at load time.

```
/plugin install delivery-os@techjays-delivery-os     # shared core — install FIRST
/plugin install jetrix@techjays-delivery-os          # /jetrix:init, /jetrix:pull, /jetrix:push, /jetrix:task-update
/plugin install ba@techjays-delivery-os              # /ba:scope, /ba:review, /ba:resolve, /ba:features
/plugin install tl@techjays-delivery-os              # /tl:plan, /tl:review, /tl:resolve, /tl:scaffold, /tl:code-map
/plugin install dev@techjays-delivery-os             # /dev:plan, /dev:build, /dev:commit, /dev:fix-review, /dev:resolve, /dev:bootstrap
/plugin install qa@techjays-delivery-os              # /qa:audit, /qa:plan, /qa:setup, /qa:health
/plugin install doc@techjays-delivery-os             # /doc:proposal, /doc:deck, /doc:magic-board, /doc:workflow, /doc:walkthrough
```

**Keep them fresh.** Refresh the marketplace metadata if a new plugin was published, then update installed plugins.

```
/plugin marketplace update techjays-delivery-os                # refresh marketplace metadata
/plugin update delivery-os@techjays-delivery-os                # update one plugin
/plugin update --all                                            # update every installed plugin
```

**Update `delivery-os` first**, then the domain plugins — a stale core against a fresh `ba`/`tl`/`dev` can throw contract errors.

### 0b. Wire the MCP servers

**Register the delivery-os MCP servers.** Runs OAuth once; every subsequent `/jetrix:*` call reuses the token.

```
/delivery-os:setup                    # prod URLs  — default
/delivery-os:setup --staging          # staging URLs
/delivery-os:setup --local            # localhost URLs (dev of the MCPs themselves)
```

**One environment per machine.** To switch, `claude mcp remove <name>` then re-run. Idempotent — safe to re-run.

---

## 1. Bind the workspace to Jetrix (once per workspace)

Every Delivery OS workspace binds to **one** Jetrix Solution. The bind writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info.

### 1a. Bind an EXISTING Jetrix Solution (most common)

```
/jetrix:init                                     # interactive picker of your Solutions
/jetrix:init <solution-slug>                     # bind by slug
/jetrix:init <solution-object-id>                # bind by ObjectId
/jetrix:init --skip-scaffold                     # bind only; don't seed the .jetrix/ tree
```

Runs the bind → pulls solution metadata → seeds the `.jetrix/` tree (`shared-context/`, `ba/`, `features/`, `tl/`, `qa/`, `doc/`).

### 1b. Create a NEW Jetrix Solution from zero (greenfield)

```
/jetrix:project-setup                            # interactive Q&A → creates Solution + apps
```

Prints a portal handoff block — link each app's GitHub repo + set env branches in the Jetrix portal's Solution Explorer → Integration tab.

### 1c. Re-seed an existing bind

```
/delivery-os:init                                # re-seeds .jetrix/ tree; idempotent
```

Use if the tree got corrupted or you passed `--skip-scaffold` earlier.

### 1d. Greenfield vs Brownfield paths after bind

| Scenario | Next step |
|---|---|
| **Greenfield** (no source repo yet) | `/tl:scaffold` — create the initial app repository skeleton with green base build |
| **Brownfield** (existing repos to onboard) | `/tl:code-map` — reverse-map each existing repo into a committed code-context tree |

Both paths converge on the BA discovery phase in §2.

---

## 2. BA — Discovery + scope

The BA agent processes client artifacts and produces a **living scope document** + supporting registers + a **feature breakdown**.

### 2a. Add discovery sources

```
/ba:scope add "path/to/folder/or/gdrive/URL"
/ba:scope add "meeting-transcript.md"
/ba:scope add "client-figma-export/"
```

References the originals (never copies/moves). Six usage modes auto-detected per source.

### 2b. Build or refresh scope

```
/ba:scope                                        # incremental — re-processes registered sources
/ba:scope --refresh                              # full re-processing
```

Produces `ba/scope.md` + registers (`business-rules.md`, `integrations.md`, `data.md`, `workflows.md`, `use-cases.md`).

### 2c. Review the scope (paranoid BA pass)

```
/ba:review                                       # scores each feature 1–10 + open questions
/ba:review ba/scope.md                           # explicit path (default)
```

Renders `ba/reviews/scope-review-<timestamp>.html` — interactive dashboard.

### 2d. Fold client answers back

```
/ba:resolve <path-to-responses.md>               # judges each answer + updates scope
```

### 2e. Break scope into features

```
/ba:features                                     # produces features/<slug>/ folders
/ba:features features/<slug>                     # re-run for one feature
```

Each feature folder contains: `feature.md`, `implementation-plan.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `dependencies.md`, `nfrs.md`, `open-questions.md`, `test-scenarios.md`, `status.md`.

### 2f. Sync BA outputs to Jetrix

```
/jetrix:push scope                               # ba/*.md, shared-context/*.md, feature-index.md
/jetrix:push feature                             # creates Feature Tasks + Subtasks in MC
```

---

## 3. TL — Context graph + planning

### 3a. Brownfield: reverse-map existing repos into code-context

```
/tl:code-map                                     # maps every repo declared in .jetrix/project.json
/tl:code-map <repo-path>                         # map one specific repo
```

Writes `<repo>/context/code-context/` — units per page/endpoint/entity — grouped by domain, with semantic layer indexes. Auto-authors `shared-context/coding-standards.md` from detected stack.

### 3b. Greenfield: scaffold the initial application repository

```
/tl:scaffold                                     # picks defaults from technology-stack.md
/tl:scaffold --stack=<name>                      # override stack choice
```

Produces the app skeleton + tooling + green base build + `shared-context/{technology-stack,architecture,coding-standards}.md`.

### 3c. Plan a feature into technical units

```
/tl:plan <feature-slug>                          # one feature
/tl:plan features/<slug>                         # by folder path
/tl:plan FEAT-<AREA>-NN                          # by internal id
/tl:plan --all                                   # every feature in feature-index.md
/tl:plan initiative=<name>                       # only features tagged with this initiative
```

Wires each feature to owned pages/endpoints/entities; keeps 3 layer indexes; logs decisions; runs link-integrity check.

### 3d. Review a technical plan

```
/tl:review <feature-slug>                        # scored dashboard, opens interactively
```

Applies BA answers back to the TL plan:

```
/tl:resolve <path-to-responses.md>
```

### 3e. Sync TL context to Jetrix

```
/jetrix:push context                             # per-repo code-context tree
```

---

## 4. QA — Test harness setup

### 4a. Audit the current test setup

```
/qa:audit                                        # read-only — scores 12 dimensions
/qa:audit <repo-path>                            # single repo
```

Renders `qa/audits/test-audit-<timestamp>.html`. Human approves recommendations.

### 4b. Plan the harness from approved audit

```
/qa:plan <path-to-approvals.md>                  # from the audit HTML export
```

Drafts `qa/quality-gates.md` (harness contract).

### 4c. Build the harness

```
/qa:setup                                        # implements the plan; proves green
```

Publishes `qa/quality-gates.md` with `harness_status: Ready`. Downstream `/dev:build` gates on this file.

### 4d. Health-check drift later

```
/qa:health                                       # re-scan; flag if standards drifted
```

**Alternative for teams that don't want to backfill existing coverage:** answer **Skip** at `/dev:plan` §1e QA-check prompt. Writes `qa/quality-gates.md` with `harness_status: Stack-Inferred` and stack-detected tier pools; new features still get 100% coverage at inferred tiers; existing repo coverage stays un-audited.

---

## 5. Feature delivery loop (per feature)

Repeat this loop per feature you're shipping.

### 5a. Plan the feature (writes implementation.md; pushes MC tasks)

```
/dev:plan <feature-slug>                         # by local slug
/dev:plan <feature-folder>                       # e.g. features/holiday-calendar-management
/dev:plan FEAT-<AREA>-NN                         # by internal id
/dev:plan Task-N                                 # by MC task number
/dev:plan Feature-N
/dev:plan Subtask-N
/dev:plan list=<name>                            # every feature under this MC list
/dev:plan initiative=<name>                      # every feature tagged with this initiative
/dev:plan --all                                  # all features
/dev:plan                                        # blank = next PLANNED task
```

Flags:

```
/dev:plan <target> --split                       # force multi-repo sub-task decomposition
/dev:plan <target> --no-split                    # force parent-alone (single repo)
/dev:plan <target> --resume                      # fold blocker resolutions + re-compose
/dev:plan <target> --dry-run                     # compose locally, don't push to MC
/dev:plan <target> --concurrency=N               # parallelism cap (default 5)
```

Runs 4 stages: identity → code-context readiness (auto-prompts QA-check + coding-standards) → per-task analysis → compose + push (with read-back verify).

**On blockers** → task lands in `BLOCKED_ON_PLAN`, `dev/plan-blockers.md` OPEN. Resolve interactively:

```
/dev:resolve --plan                              # interactive walk; picks default target
/dev:resolve --plan <target>                     # explicit target
```

After every `Resolution:` filled → invokes `/dev:plan --resume` inline.

### 5b. Build the feature (implements code; runs tests; no commits)

```
/dev:build <feature-slug>                        # parent slug → fans out to all sub-tasks in PARALLEL
/dev:build Subtask-N                             # build just one sub-task
/dev:build FEAT-<AREA>-NN                        # by internal id
/dev:build --resume                              # continue from last stage per build-run.md
/dev:build --no-security-review                  # dev convenience; /dev:commit still runs security
/dev:build --concurrency=N                       # parallel fan-out cap (default 5)
```

Runs 11 stages: mount → preflight → branch → QA harness gate → implementation + tests (per §1 step) → execute tests → validate → security review (Critical-blocking only) → context update → summary + `dev/local-runbook.md`.

**Never commits, never pushes** — `/dev:commit` owns the git-write boundary.

### 5c. Commit + push + open PR

```
/dev:commit <task-ref>                           # by any identifier resolvable to a task
/dev:commit Subtask-N
/dev:commit --resume                             # continue from last stage per commit-run.md
/dev:commit --structured                         # multi-commit convention (docs / feat / refactor / test)
/dev:commit --allow-protected-base               # allow main/master as PR base (rare)
```

Runs 10 stages: identity → base-branch prompt + pull → security review (Critical + High) → code review (7 dimensions) → acceptance-map re-verify → bounded fix loop → semantic context merge → gather working tree + commit → push branch → open PR.

PR creation fallback ladder:
1. `gh` CLI if installed + authed
2. Extracts PAT from your existing Git Credential Manager (`git credential fill`)
3. Reads token from `gh` config file if present
4. Prints pre-filled compare URL if none of the above work

---

## 6. Update a task after discussion (surgical patch)

If you talked through changes with Claude and want to update an existing MC task's content:

```
/jetrix:task-update <task-ref>                   # interactive; walks each change
```

Collects change intent across the conversation → batches into one review → applies specific patches (never rewrites) → pushes to MC with read-back verify → prints URLs.

Respects frame rules — refuses to add retired sections (Coverage, Assumptions, Deferred to E2E).

---

## 7. Sync operations (pull / push)

### Pull from Jetrix

```
/jetrix:pull scope                               # BA outputs + feature folders + connection-map
/jetrix:pull connection-map                      # only the solution architecture doc
/jetrix:pull task <ref>                          # single feature or a set (via task-mcp)
/jetrix:pull sprint <ref>
/jetrix:pull list <ref>
/jetrix:pull all                                 # equivalent to `scope`
```

Idempotent — files whose remote contentHash matches sync-state's are skipped.

### Push to Jetrix

```
/jetrix:push scope                               # BA outputs → scope-mcp
/jetrix:push feature                             # BA feature folders → task-mcp (parent + subtasks)
/jetrix:push task <ref>                          # any .md file / folder → task-mcp
/jetrix:push task --list=<name>                  # target a specific MC list
/jetrix:push task --sprint=<name>                # target a specific sprint
/jetrix:push implementation                      # TL plan → Task's Implementation tab
/jetrix:push context                             # per-repo code-context tree → context-mcp
/jetrix:push deliverable                         # client HTMLs → deliverable-mcp
```

Direct-to-GCS pattern — 100-file push as fast as 1-file push. Never routes file bytes through Claude's context.

---

## 8. The complete happy-path sequence

### 8a. Greenfield project

```
/delivery-os:setup                               # once per machine
/jetrix:project-setup                            # create Solution + bind workspace
# ... link GitHub repos in Jetrix portal Solution Explorer → Integration ...
/ba:scope add "path/to/client-docs/"
/ba:scope
/ba:review
/ba:features
/jetrix:push scope
/tl:scaffold                                     # create app skeleton
/qa:audit && /qa:plan approvals.md && /qa:setup  # if not skipping
/tl:plan --all                                   # plan every feature into TL graph
# Per feature:
/dev:plan <feature-slug>
/dev:build <feature-slug>                        # parallel over sub-tasks
/dev:commit Subtask-N                            # per sub-task
```

### 8b. Brownfield project (existing repos)

```
/delivery-os:setup                               # once per machine
/jetrix:init                                     # bind existing Solution OR /jetrix:project-setup
/tl:code-map                                     # reverse-map existing repos; auto-authors coding-standards.md
/ba:scope add "path/to/client-docs/"
/ba:scope
/ba:review
/ba:features
/jetrix:push scope
/qa:audit                                        # optional — Skip path at /dev:plan §1e also works
/tl:plan --all
# Per feature:
/dev:plan <feature-slug>
/dev:build <feature-slug>
/dev:commit Subtask-N
```

---

## 9. Quick reference — commands by category

### Setup
| Command | Purpose |
|---|---|
| `/delivery-os:setup [--staging | --local]` | Register MCP servers (once per machine) |
| `/delivery-os:init` | Re-seed `.jetrix/` tree |
| `/jetrix:init [<solution>] [--skip-scaffold]` | Bind workspace to existing Solution |
| `/jetrix:project-setup` | Create new Solution from zero |

### Sync
| Command | Purpose |
|---|---|
| `/jetrix:pull <stage>` | Pull from Jetrix (scope/task/sprint/list/all/connection-map) |
| `/jetrix:push <stage>` | Push to Jetrix (scope/feature/task/implementation/context/deliverable) |
| `/jetrix:task-update <task-ref>` | Surgical patch of an existing task after discussion |

### BA (Business Analysis)
| Command | Purpose |
|---|---|
| `/ba:scope add "<source>"` | Register a discovery source |
| `/ba:scope [--refresh]` | Build/update living scope |
| `/ba:review [<scope-path>]` | Paranoid BA review, scored dashboard |
| `/ba:resolve <responses.md>` | Fold client answers into scope |
| `/ba:features [<feature-folder>]` | Break scope into implementation-ready features |

### TL (Tech Lead)
| Command | Purpose |
|---|---|
| `/tl:code-map [<repo-path>]` | Reverse-map brownfield repos into code-context |
| `/tl:scaffold [--stack=<name>]` | Scaffold initial application (greenfield) |
| `/tl:plan <target> [--all] [initiative=<name>]` | Plan features into technical context graph |
| `/tl:review <feature>` | Score technical plan |
| `/tl:resolve <responses.md>` | Fold answers into TL plan |
| `/tl:maturity` | Assess codebase maturity |

### QA
| Command | Purpose |
|---|---|
| `/qa:audit [<repo-path>]` | Score test setup (read-only) |
| `/qa:plan <approvals.md>` | Plan the harness from approved audit |
| `/qa:setup` | Build the harness; publish quality-gates.md |
| `/qa:health` | Drift check |

### Dev (per feature)
| Command | Purpose |
|---|---|
| `/dev:plan <target> [--split | --no-split] [--resume] [--dry-run] [--concurrency=N]` | Plan feature; write implementation.md; push MC tasks |
| `/dev:resolve --plan [<target>]` | Interactive blocker resolution |
| `/dev:build <target> [--resume] [--no-security-review] [--concurrency=N]` | Build code + tests; no commits |
| `/dev:commit <target> [--resume] [--structured] [--allow-protected-base]` | Semantic-merge + commit + push + PR |

---

## 10. Key concepts (30-second read)

- **`.jetrix/` folder** — the entire folder is gitignored. It's your local working copy of Jetrix state. Regenerated via `/jetrix:init`.
- **Source of truth** — Jetrix. Your local files are a working copy. Push what you edited; pull to refresh.
- **Split features** — a feature that spans multiple repos becomes one parent Task + one Sub-task per repo in MC. `/dev:plan` decides; you can force with `--split` / `--no-split`.
- **Parent-alone features** — single-repo, or bug/story. No sub-tasks. `/dev:build` runs against the parent directly.
- **Read-back verify** — every push to MC verifies with SHA-256 that the server stored what was sent. Mismatch surfaces immediately.
- **`/dev:build` never commits or pushes.** `/dev:commit` owns the git-write boundary.
- **Env promotion (dev → main)** happens in MC's merge agent on PR merge — the plugin has no merge concern.

---

## 11. When things go wrong

- **Plan halts on missing `coding-standards.md`** → run `/tl:code-map` to auto-author it
- **Plan halts on `BLOCKED_ON_PLAN`** → run `/dev:resolve --plan` to walk each blocker
- **Build halts on missing env var (e.g. `FIREBASE_SERVICE_ACCOUNT`)** → set it in `dev/build-env.local` (gitignored) and re-run with `--resume`
- **Build halts on `mock-contradicts-tier`** → your test declares `tier: integration` but uses mocks; either remove the mock or demote the tier
- **Commit halts on `stage-7-not-executed`** → semantic merge was skipped; `/dev:commit --resume` re-runs
- **Commit halts on `secrets-in-staged-set`** → a credential file made it into the working tree; move it to `dev/build-env.local` or add to `.gitignore`
- **PR creation fell through to compare URL** → click the URL, form is pre-filled, click Create pull request

---

## 12. Getting help

- Read this file end-to-end once
- Each command has `--help` (via `/help <command>` from Claude Code)
- File issues at https://github.com/Techjays-Build-With-AI/claude-delivery-os/issues

Every command in this guide is idempotent — re-running is safe.
