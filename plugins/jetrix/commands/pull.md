---
description: Refresh local delivery-os work from Jetrix via the stage-specific MCP. Argument selects which stage to pull — `scope` (BA outputs + feature folders + connection-map, one combined pull), `connection-map` (only the Solution architecture doc, targeted), `task <ref>` / `sprint <ref>` / `list <ref>` (single feature or a set ← task-mcp), `all` (equivalent to `scope`). Downloads use the direct-from-GCS pattern with `curl --parallel` (HTTP/2 multiplexed to GCS — same mechanism the browser uses), so pull is fast regardless of file count. Idempotent — files whose remote contentHash matches sync-state's are skipped without downloading.
argument-hint: "<stage> [<ref>]"
---

# /jetrix:pull

Refresh the local delivery-os container from Jetrix. The first argument names the **stage** — this decides which MCP fetches and which local paths get written:

| Stage | MCP | What it pulls |
|---|---|---|
| `scope` | `scope-mcp` + `task-mcp` | Everything Solution-scoped: BA outputs, shared-context/, **connection-map**, and every feature folder — one combined pull |
| `connection-map` | `scope-mcp` | Targeted pull of just the Solution's `connection-map.md`. Rarely needed — `scope` already includes it. Use when you want to skip BA/feature pulls. |
| `task <ref>` | `task-mcp` | ONE feature folder — `<ref>` is `TASK-<number>`, `FEAT-<id>`, or a MongoDB `_id` |
| `sprint <ref>` | `task-mcp` | Every feature currently in a sprint — `<ref>` is a sprint number or MongoDB `_id` |
| `list <ref>` | `task-mcp` | Every feature in an MC List — `<ref>` is a list name or MongoDB `_id` |
| `all` | (same as `scope`) | Alias for `scope` — the scope manifest already covers connection-map + BA outputs + features |

Every stage uses **one MCP call for the manifest + one Bash call for parallel downloads**. `curl --parallel` opens 8 concurrent HTTP/2 transfers over a single TCP connection to `storage.googleapis.com` — same mechanism the browser uses when the Documents-tab UI loads many files. **File bytes never enter Claude's context**; they go from GCS straight to disk via signed download URLs.

The per-stage flow (manifest call, filter, curl loop, sync-state update) lives in a dedicated file under `commands/references/pull/`. Each stage file is 30–250 lines and is meant to be read verbatim when its stage runs. **Follow the stage file's instructions exactly — do NOT paraphrase, do NOT skip steps.** This top-level command handles preflight + arg parsing + routing only.

---

## 0. Preflight — resolve the delivery-os workspace

**This command operates on the delivery-os container folder that `/jetrix:init` bound to a Jetrix Solution.** Resolve the workspace FIRST:

1. Walk up from `$PWD` looking for **`.jetrix/project.json`** (up to 3 parent levels). If missing → tell the user to run `/jetrix:init` first.
2. Read `solutionId` + `solutionSlug` from it. Note the folder that CONTAINS `.jetrix/` as **`workspace_root`** — the entire `.jetrix/` is gitignored; it's the local working copy.
3. The delivery-os container is nested at `<workspace_root>/.jetrix/`. Note this as **`project_root`**.
4. If `project_root` is missing, create the empty tree (`ba/`, `shared-context/`, `features/`) — Pull is the natural onboarding flow for a fresh teammate who just cloned the repo and ran `/jetrix:init`.

> **Directory contract:**
> ``
> <workspace_root>/
> └── .jetrix/                         ← project_root, ENTIRELY gitignored
>     ├── project.json
>     ├── connection-map.md            (if the portal built one)
>     ├── cache/sync-state.json        ← sync-state ALWAYS lives here
>     ├── shared-context/
>     ├── ba/                          (scope.md, registers/, logs/, artifacts/, reviews/, …)
>     ├── requirements/<slug>/features/ (per-feature <slug>/{feature.md, dev/, …})
>     ├── tl/                          (reviews/, maturity/, code-map-registry.md)
>     ├── qa/                          (quality-gates.md, audits/, health/, escalations/)
>     ├── doc/                         (decks/, walkthroughs/, workflows/, boards/)
>     └── tasks/
> ``
> (Legacy v1 workspaces nested content under `.jetrix/<solutionSlug>/`; `/jetrix:init` §3 migrates those to v2 on the next run.)
>
> Sync-state reads/writes in any stage file resolve to `<workspace_root>/.jetrix/cache/sync-state.json` — NEVER inside `<project_root>/`.

## 1. Parse the stage argument

```
/jetrix:pull <stage> [<ref>]
```

- `<stage>` (required): `scope` | `connection-map` | `task <ref>` | `sprint <ref>` | `list <ref>` | `all`. If missing or unknown, print the table above and stop.
- `<ref>` (required for `task`/`sprint`/`list` stages): identifier — accepts human forms (`TASK-42`, `FEAT-CLSF-01`, sprint number, list name) or a MongoDB `_id`. Plugin routes the ref to the right filter param on `feature_pull_bundle`. **On any other tracker it is whatever that tool calls an issue** — a key, an id, or a URL pasted straight from the browser.

### Never print the word `<ref>` to a user

`<ref>` names an argument; it does not tell anyone what to type. Whenever this command appears in a next-step
line, a report or an error, **substitute a real example in the bound tracker’s own form** — `provider` in
`project.json` already says which, so there is nothing to ask:

| `provider` | Print |
|---|---|
| `jetrix` | `/jetrix:pull task Task-230` |
| `jira` | `/jetrix:pull task PAY-412` |
| `clickup` | `/jetrix:pull task 86a1kx2p` |
| `azure` | `/jetrix:pull task 4471` |
| anything else | the id form that tracker’s own UI shows |

Best of all, use **a ref that actually exists** — one from the run that is printing the line. A real number
the reader recognises beats any placeholder.

**And say it works on their tracker.** The command is called `/jetrix:pull` because the plugin is, not
because it only pulls from Jetrix — it branches on `capabilities` like everything else and pulls from
whichever tracker `/jetrix:init` bound. A Jira user reading a line that says "jetrix" reasonably assumes it
is not for them, so add the half-line: *pulls from the tracker you bound — Jira here*.

**Pasting a URL is always valid**, on every tracker, and is the form most people reach for. Offer it when
the id form is unobvious: `/jetrix:pull task https://acme.atlassian.net/browse/PAY-412`.

## 1.5. Resolve the tracker

Read `tracker` from `project.json`. The stage files branch on `capabilities`, never on `provider`.

| | `jetrix` | any other tracker |
|---|---|---|
| which server | `scope-mcp` + `task-mcp` | `tracker.mcp`, via `tracker.mapping` |
| what is read | the Solution's List | `tracker.container_ref`, so an unrelated ticket in the same project is never swept in |
| task fields | 7 tabs → 7 files | **one body** → split on `##` into the same 7 files |
| `scope` stage | pulls BA docs + connection-map + features | documents are local-only, so it pulls **features only** |
| `connection-map` stage | pulls it | **skipped** — `/jetrix:init` §13 wrote it from the user's own answers |
| status | MC’s enum **is** ours — copied straight into `status` | **the inverse of `tracker.status_map`** — `delivery-os-conventions` §5. Never write the tracker’s own wording into `status`: nothing matches it and the task stops being buildable. |

**Splitting a body back into files is governed by `delivery-os-conventions` §1.c, and it is strict.** No
`<!-- delivery-os:v1 … -->` marker → do not split: the body was written by hand in the tracker, so it becomes
`feature.md` verbatim and the run says so. An unrecognised `##` heading → **halt**, never drop it — a heading someone
added in the tracker is content.

**Which local folder an issue belongs to comes from the marker's `<FEAT-ID>`**, not from the issue's position or title.
An issue with no marker is a hand-filed ticket and materialises under `tasks/<slug>.md`, which is what
`/dev:plan` §2f already expects.

## 2. Route to the stage-specific flow

Once the stage is resolved, `Read` the corresponding file and execute its instructions verbatim. The stage file assumes the preflight above has run and `project_root` / `workspace_root` / `solutionId` / `solutionSlug` are known.

| Stage | Full flow lives at |
|---|---|
| `scope` | `plugins/jetrix/commands/references/pull/scope.md` |
| `connection-map` | `plugins/jetrix/commands/references/pull/connection-map.md` |
| `task <ref>` | `plugins/jetrix/commands/references/pull/task.md` |
| `sprint <ref>` | `plugins/jetrix/commands/references/pull/sprint.md` |
| `list <ref>` | `plugins/jetrix/commands/references/pull/list.md` |

If the stage file cannot be read → halt and report; do NOT reconstruct the flow from memory.

## Stage: `all`

Alias for `scope`. Since `scope_pull_manifest` now returns every Solution-scoped doc (BA outputs, shared-context/, connection-map) in one call, running `scope` refreshes everything the workspace needs. Just execute `references/pull/scope.md`.

`task` / `sprint` / `list` are NOT part of `all` — those are targeted single-ref pulls, opt-in only.

## Universal prereq (applies to every stage)

Every stage file assumes:
- `.jetrix/project.json` exists (verified by preflight §0 above).
- `.jetrix/cache/sync-state.json` exists (create empty `{}` if absent — done once at first pull).

Any stage-specific prereq is checked inside that stage's file. Pulls are the natural onboarding flow for a fresh workspace, so most stages will happily populate an empty tree.

## What a pull is allowed to overwrite

Applies to **every** stage. A pull brings down someone else's work; the local tree may hold work of its own.

| Local vs last pull | Remote vs last pull | What happens |
|---|---|---|
| unchanged | unchanged | nothing — not even a write. Only `lastPulled` is bumped |
| unchanged | changed | download and overwrite. This is the normal case |
| changed | unchanged | **keep the local file.** Someone edited it here and nobody edited it there |
| changed | changed | **stop and ask.** Both sides moved |

**The last row is the one that matters.** Overwriting there loses work that exists in exactly one place.
Name the file, say what changed on each side, and let the human choose — keep local, take remote, or open
both. Never pick for them, and never pick remote by default because it is "the source of truth": the
tracker is the source of truth for *status and assignment*, not for a paragraph someone just wrote locally.

**Files pull never writes at all** are listed per stage — `status.md` on a feature, `feature.md` §
`## Workflow`, `dependencies.md` § `## Open questions`. These are local authoring surfaces with no tracker
counterpart, so there is nothing to compare them against and nothing to overwrite them with.

**A file carrying no `<!-- delivery-os:v1 … -->` marker was written by hand in the tracker.** It is content,
not a round-trip, and it lands verbatim under `tasks/<slug>.md` rather than being split into a layout it was
never in. `delivery-os-conventions` §1.c.
