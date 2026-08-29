---
description: Publish local delivery-os work up to Jetrix via the stage-specific MCP. Argument selects which stage to sync — `scope` (BA outputs → scope-mcp), `feature` (BA feature folders → task-mcp), `task` (any .md file or folder of .md files → task-mcp, with optional --list / --sprint targeting), `implementation` (TL plan → Task's implementation tab), `deliverable` (client HTMLs → deliverable-mcp). Uploads use the direct-to-GCS pattern (server brokers signed URLs, local bash + curl streams bytes from disk straight to GCS), so pushes never route file bytes through Claude's context — a 100-file push is as fast as a 1-file push.
argument-hint: "<stage> [<path>] [--list=<name|id>] [--sprint=<id>]"
---

# /jetrix:push

Publish local delivery-os work to Jetrix. The first argument names the **stage** — this decides which local paths get scanned and which MCP handles the sync:

| Stage | MCP | What it pushes |
|---|---|---|
| `scope` | `scope-mcp` | BA outputs — `ba/*.md`, `shared-context/*.md`, `features/feature-index.md` |
| `feature` | `task-mcp` | Per-feature MC Tasks — creates ONE Task per `features/<slug>/` folder |
| `task` | `task-mcp` | Ad-hoc tasks — ONE MC Task per `.md` file. Accepts a file, a folder, or omit for `tasks/**/*.md`. Optional `--list=<name\|id>` or `--sprint=<id>` chooses the target. |
| `implementation` | `task-mcp` | TL plan → each Task's Implementation tab (`implementationDetails`), status → `READY_FOR_DEV` |
| `deliverable` | `deliverable-mcp` | Client HTMLs — `doc/*.html` |
| `all` | (all above) | Runs every implemented stage in order. |

Every stage uses a **three-phase direct-to-GCS pattern** on its MCP (`*_prepare_push` → local `curl` PUTs → `*_finalize_push`) so the plugin does at most 2 MCP calls + 1 Bash call per push, regardless of file count. **File bytes never enter Claude's context**; they go straight from local disk to GCS via signed URLs (same pattern the UI's KnowledgeHubService uses).

The per-stage flow (walk / hash / MCP call sequence / skip-unchanged rules / prereq checks / error messages) lives in a dedicated file under `commands/references/push/`. Each stage file is 100–300 lines and is meant to be read verbatim when its stage runs. **Follow the stage file's instructions exactly — do NOT paraphrase, do NOT skip steps.** This top-level command handles preflight + arg parsing + routing only.

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution — NOT on your current directory.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing everywhere → stop and tell the user to run `/jetrix:init <projectId | slug>` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — the entire `.jetrix/` is gitignored; it's the local working copy.
3. Note `<workspace_root>/.jetrix/` as **`project_root`** — every content file walk below is relative to it. (Legacy v1 workspaces nested content under `.jetrix/<solutionSlug>/`; `/jetrix:init` §0.5 migrates those to v2 on the next run, so you never build a v1 path yourself.)
4. Verify the role folders exist (`ba/`, `shared-context/`, `features/`, …). If missing → tell the user to run `/delivery-os:init` (or re-run `/jetrix:init` without `--skip-scaffold`).

> **Directory contract (referenced throughout every stage file):**
> ```
> <workspace_root>/
> └── .jetrix/                         ← project_root, ENTIRELY gitignored
>     ├── project.json
>     ├── connection-map.md            (if the portal built one)
>     ├── cache/sync-state.json        ← sync-state ALWAYS lives here
>     ├── shared-context/
>     ├── ba/                          (scope.md, registers/, logs/, artifacts/, reviews/, …)
>     ├── features/                    (feature-index.md + per-feature <slug>/{feature.md, dev/, …})
>     ├── tl/                          (reviews/, maturity/, code-map-registry.md)
>     ├── qa/                          (quality-gates.md, audits/, health/, escalations/)
>     ├── doc/                         (decks/, walkthroughs/, workflows/, boards/)
>     └── tasks/
> ```
> Every `sync-state.json` reference in any stage file resolves to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:push <stage> [<filename>]
```

- `<stage>` (required): `scope` | `feature` | `task` | `implementation` | `deliverable` | `all`. If missing or unknown, print the table above and stop.
- `<filename>` (optional, scope only): push a single file at that relative path instead of the whole stage.
- `<path>` (optional, task only): `.md` file or folder; see the `task` stage below.
- `--list=<name|id>` / `--sprint=<id>` (task only): target selector — see the `task` stage below.

## 2. Route to the stage-specific flow

Once the stage is resolved, `Read` the corresponding file and execute its instructions verbatim. The stage file assumes the preflight above has run and `project_root` / `workspace_root` / `solutionId` / `solutionSlug` are known.

| Stage | Full flow lives at |
|---|---|
| `scope` | `plugins/jetrix/commands/references/push/scope.md` |
| `feature` | `plugins/jetrix/commands/references/push/feature.md` |
| `task` | `plugins/jetrix/commands/references/push/task.md` |
| `implementation` | `plugins/jetrix/commands/references/push/implementation.md` |
| `deliverable` | `plugins/jetrix/commands/references/push/deliverable.md` (pending) |

If the stage file cannot be read → halt and report; do NOT reconstruct the flow from memory.

## Stage: `all`

Runs every implemented stage in order:

1. Read + execute `references/push/scope.md`.
2. Read + execute `references/push/feature.md`.
3. Read + execute `references/push/implementation.md`.

Skip any stage whose prereqs (per its file's own prereq check) don't hold — surface the skip with the same "run X first" message the stage file itself defines.

`task` and `deliverable` are NOT part of `all` — those are opt-in stages.

## Universal prereq (applies to every stage)

Every stage file assumes:
- `.jetrix/project.json` exists (verified by preflight §0 above).
- `.jetrix/cache/sync-state.json` exists (create empty `{}` if absent — done once at first push).

Any stage-specific prereq (e.g. `features/` for `feature` stage) is checked inside that stage's file. Failures produce a clear "run this command first" message; never a silent crash.
