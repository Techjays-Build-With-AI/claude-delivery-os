---
description: Refresh local delivery-os work from Jetrix via the stage-specific MCP. Argument selects which stage to pull — `scope` (BA outputs ← scope-mcp + feature folders ← task-mcp, combined), `context` (TL graph ← context-mcp), `task <ref>` / `sprint <ref>` / `list <ref>` (single feature or a set ← task-mcp), `all` (every implemented stage). Downloads use the direct-from-GCS pattern (server issues signed URLs, local bash + curl streams bytes straight to disk), so pull is fast regardless of file count. Idempotent — files whose remote contentHash matches the local hash are left untouched.
argument-hint: "<stage> [<ref>]"
---

# /jetrix:pull

Refresh the local delivery-os container from Jetrix. The first argument names the **stage** — this decides which MCP fetches and which local paths get written:

| Stage | MCP | What it pulls |
|---|---|---|
| `scope` | `scope-mcp` + `task-mcp` | BA outputs + every feature folder (combined pull) |
| `context` | `context-mcp` | TL knowledge graph (env-scoped; default `main`). Optional `--unit=<ids>` or `--path=<glob>` for patch pulls. |
| `task <ref>` | `task-mcp` | ONE feature folder — `<ref>` is `TASK-<number>`, `FEAT-<id>`, or a MongoDB `_id` |
| `sprint <ref>` | `task-mcp` | Every feature currently in a sprint — `<ref>` is a sprint number or MongoDB `_id` |
| `list <ref>` | `task-mcp` | Every feature in an MC List — `<ref>` is a list name or MongoDB `_id` |
| `all` | (all above) | Full workspace: `scope` + `context`. |

Every stage uses a **two-phase direct-from-GCS pattern** — 1 MCP call for the manifest + 1 Bash call for the downloads. **File bytes never enter Claude's context**; they go from GCS straight to disk via signed download URLs.

The per-stage flow (manifest call, filter, curl loop, sync-state update) lives in a dedicated file under `commands/references/pull/`. Each stage file is 30–250 lines and is meant to be read verbatim when its stage runs. **Follow the stage file's instructions exactly — do NOT paraphrase, do NOT skip steps.** This top-level command handles preflight + arg parsing + routing only.

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing → tell the user to run `/jetrix:init` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — the entire `.jetrix/` is gitignored; it's the local working copy.
3. The delivery-os container is nested at `<workspace_root>/.jetrix/<solutionSlug>/`. Note this as **`project_root`**.
4. If `project_root` is missing, create the empty tree (`ba-output/`, `shared-context/`, `context/features/`) — Pull is the natural onboarding flow for a fresh teammate who just cloned the repo and ran `/jetrix:init`.

> **Directory contract:**
> ```
> <workspace_root>/
> └── .jetrix/                         ← ENTIRELY gitignored
>     ├── project.json
>     ├── cache/sync-state.json        ← sync-state ALWAYS lives here
>     └── <solutionSlug>/              ← project_root
>         ├── ba-output/
>         ├── shared-context/
>         └── context/
> ```
> Sync-state reads/writes in any stage file resolve to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:pull <stage> [<ref>]
```

- `<stage>` (required): `scope` | `context` | `task <ref>` | `sprint <ref>` | `list <ref>` | `all`. If missing or unknown, print the table above and stop.
- `<ref>` (required for `task`/`sprint`/`list` stages): identifier — accepts human forms (`TASK-42`, `FEAT-CLSF-01`, sprint number, list name) or a MongoDB `_id`. Plugin routes the ref to the right filter param on `feature_pull_bundle`.
- `--unit=<ids>` / `--path=<glob>` (context stage only): narrow the pull to specific unit files. Default is every context doc in the env.

## 2. Route to the stage-specific flow

Once the stage is resolved, `Read` the corresponding file and execute its instructions verbatim. The stage file assumes the preflight above has run and `project_root` / `workspace_root` / `solutionId` / `solutionSlug` are known.

| Stage | Full flow lives at |
|---|---|
| `scope` | `plugins/jetrix/commands/references/pull/scope.md` |
| `context` | `plugins/jetrix/commands/references/pull/context.md` |
| `task <ref>` | `plugins/jetrix/commands/references/pull/task.md` |
| `sprint <ref>` | `plugins/jetrix/commands/references/pull/sprint.md` |
| `list <ref>` | `plugins/jetrix/commands/references/pull/list.md` |

If the stage file cannot be read → halt and report; do NOT reconstruct the flow from memory.

## Stage: `all`

Runs every implemented stage in order:

1. Read + execute `references/pull/scope.md`.
2. Read + execute `references/pull/context.md`.

`task` / `sprint` / `list` are NOT part of `all` — those are targeted single-ref pulls, opt-in only.

## Universal prereq (applies to every stage)

Every stage file assumes:
- `.jetrix/project.json` exists (verified by preflight §0 above).
- `.jetrix/cache/sync-state.json` exists (create empty `{}` if absent — done once at first pull).

Any stage-specific prereq is checked inside that stage's file. Pulls are the natural onboarding flow for a fresh workspace, so most stages will happily populate an empty tree.
