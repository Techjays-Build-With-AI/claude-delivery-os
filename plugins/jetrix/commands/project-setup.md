---
description: One-command onboarding — creates a Solution + apps via CLI Q&A, binds the workspace, and scaffolds the delivery-os folder tree. Prints a portal handoff block so the teammate links each app's GitHub repo + sets env branches in one sitting in Jetrix Solution Explorer → Integration tab. Use this instead of /jetrix:init when starting from zero.
argument-hint: "[<solution-name>]"
---

# /jetrix:project-setup

The single command a teammate runs to go from **empty workspace folder + no Jetrix Solution** to **ready to work** — Solution + apps + `.jetrix/project.json` + delivery-os folder tree — with one portal visit at the end for repo linking and env branches (Integration tab, one sitting).

Use this instead of `/jetrix:init` **only when starting from zero** (no Solution created yet in Jetrix). If the Solution already exists, `/jetrix:init <slug>` is the right entry point — it handles bind + empty-apps + connection-map pull.

## What this replaces

| Old flow | New flow |
|---|---|
| Portal → New Solution → fill 7-section profile → invite members | (skipped — Solution created via CLI Q&A) |
| Portal → Solution → Apps → New App × N | (one Q&A loop — CLI creates the apps) |
| Portal → App → Integrate Repository × N (with GitHub App install per org) | Portal handoff block prints the exact clicks — CLI does NOT try to link repos |
| Portal → App → Env Configs → set dev / staging / prod × N | Same portal handoff — set on the Integration tab in one sitting |
| CLI: `/jetrix:init <slug>` | Rolled into this command |
| CLI: `/delivery-os:init` | Rolled into this command |

One command, one Q&A session, ready to work.

## Prerequisites

- `/delivery-os:setup` has been run once on this machine (registers the three MCPs). If not, this command halts with `Run /delivery-os:setup first` and stops.
- The teammate is signed in to Jetrix on the browser (Claude Code's OAuth flow may prompt on first tool call — that's normal).
- The teammate has `project.create` permission in their org (org-admin, or an equivalent role).

## 0. Preflight — verify workspace path

**Same as `/jetrix:init` §0.** Do NOT skip. Bash's cwd persists across tool calls; make sure `.jetrix/` will land in the right folder.

1. `pwd` → capture as `workspace_root` (absolute).
2. Sanity-check basename against red-flag names (`src`, `dist`, `build`, `node_modules`, …). Warn if it looks like a subfolder.
3. Ask: `Initialize Jetrix workspace at "<workspace_root>"? [Y/n]` — halt if `n`.

Every downstream write uses the absolute path — never `$PWD` or relative paths.

## 1. Guard: MCP registration + arg parsing

- Run `claude mcp list` via Bash. If any of `project-mcp`, `scope-mcp`, `task-mcp` is missing → halt with:
  ```
  Missing MCP registration. Run /delivery-os:setup first, then re-run this command.
  ```
- Parse `$ARGUMENTS`. If present → use it as the default Solution name suggestion. If empty → prompt in §2 without a default.

## 2. Solution creation Q&A

```
Solution name?      → e.g. "Nutrina Supplier Portal"
Description?        → "supplier onboarding + document review platform"
Solution type?      → number picker:
                       [1] Development   (default)
                       [2] POC
                       [3] D&D
                       [4] Maintenance
```

Show a **confirmation** before creating:

```
About to create Jetrix Solution:
  Name:        Nutrina Supplier Portal
  Description: supplier onboarding + document review platform
  Type:        Development

Continue? [Y/n]
```

On `Y`:

```
mcp__project-mcp__project_create_solution(
  name          = "<name>",
  description   = "<description>",
  solution_type = "<type>"
)
```

Capture the returned `_id` as `solutionId` and `slug` as `solutionSlug`. If the tool errors with `already exists` → tell the teammate to use `/jetrix:init <slug>` instead (bind to the existing Solution), then stop.

## 3. Apps loop — one Q&A round per app

Ask the teammate how many apps to add:

```
How many apps in this Solution?
(Common shapes:
  1 → single fullstack repo
  2 → frontend + backend
  3 → frontend + backend + mobile
  4+ → microservices)

How many? [default 2]
```

Then for each app run just the **metadata step** (matches `/jetrix:init` §7a). Repo linking + env branches happen in the Jetrix portal after — one clear place, no split-brain.

### 3a. App metadata

```
App name?      → "Nutrina API"
Description?   → "REST API for supplier onboarding"
Project type?  → [1] backend api
                 [2] web application
                 [3] mobile application
                 [4] fullstack
                 [5] workflow
                 [6] database
                 [7] desktop application
```

Call:
```
mcp__project-mcp__project_create_project(
  solution_id  = <solutionId>,
  name         = "<name>",
  description  = "<description>",
  project_type = "<picked>"
)
```

Capture the returned `_id` as `projectId`. **That's it for the CLI on this app** — no repo prompt, no env-branch prompt.

### 3b. Loop or done

After each app: `Add another app? [y/N]`. On `y`, back to 3a with a fresh app. On `N`, exit the loop and print the portal handoff block below.

### 3c. Portal handoff — link repos + set env branches

Print this ONCE after all apps are created (never per-app — the teammate does the whole batch in the portal in a single sitting):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Next: link a GitHub repo + set env branches for each app
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Open your Jetrix portal in the browser and go to
     "Solution Explorer" (same portal you sign in to normally —
     use whichever environment your MCPs are pointing at).

  2. Find Solution "<solutionName>" (Project ID: <solutionId>).

  3. For EACH app below, click it → open the "Integration" tab →
     paste the repo URL → click "Connect" → in the GitHub popup,
     grant access to that repo (one repo per app — GitHub asks
     each time, that's expected):

<one line per created app, e.g.>
       · Nutrina API      (backend api)     → paste https://github.com/<owner>/<repo>
       · Nutrina Web      (web application) → paste https://github.com/<owner>/<repo>

  4. In the same Integration tab, set the env branches (dev /
     staging / prod → develop / staging / main are the common
     defaults) and hit Save.

  This is a one-time click per app. Everything below (bind +
  scaffold) works fine without it; you can come back later.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Continue to bind the workspace now, or come back to Jetrix
first? [continue/wait]
```

- `continue` (default) → proceed to §4 with the apps as-is; `.jetrix/project.json` will save `repoUrl: null` and empty `env_branches` for each app. Next `/jetrix:init <slug>` picks up whatever the teammate filled in via the portal.
- `wait` → halt with `OK — finish repo linking + env branches in the portal, then re-run /jetrix:init <slug> to bind the workspace.` and stop.

## 4. Bind the workspace — same as `/jetrix:init` §7 through §10

Now that the Solution + apps exist in Jetrix, re-run the standard init sequence:

1. **Re-fetch bundle** — `mcp__project-mcp__project_get_solution_bundle(solutionId)`. This returns the freshly-created state (all your apps + env configs + repo integrations) in one shot.
2. **Confirm** — print the resolved Solution + apps + repos and ask `Bind this workspace to this Solution? [Y/n]`. Halt on `n` with `Cancelled — Solution stays created; workspace not bound. Re-run /jetrix:init <slug> anytime to bind.`
3. **Write `.jetrix/project.json`** — per `/jetrix:init` §8.
4. **Ask for per-app local repo paths** — per `/jetrix:init` §9.
5. **Pull connection-map** — per `/jetrix:init` §10 (§10a gate skips it if the Solution has no `connection_map_ref` — which is guaranteed for a fresh Solution, so this is a no-op the first time; teammate can build the map in the portal Connections tab later and re-run `/jetrix:pull scope`).
6. **Update `.gitignore`** — per `/jetrix:init` §11.

## 5. Scaffold the delivery-os folder tree — inline `/delivery-os:init`

Rather than telling the teammate to run a second command, invoke `/delivery-os:init` inline. That creates `.jetrix/<solutionSlug>/` with `ba-output/`, `context/`, `tl-output/`, `qa-output/`, `dev-output/`, `doc-output/`, `shared-context/` (with seeded templates), and `artifacts/`.

## 6. Final summary

Print a green-tick summary that mirrors §7's confirmation block plus one section for what was actually done:

```
✓ Jetrix + delivery-os workspace ready.

Workspace:       <workspace_root>
Solution:        <name>  (<solutionId>)
Slug:            <slug>
Type:            Development
Environments:    dev, staging, prod

Apps (<N>):
  ✓ <projectName>  (<projectType>)
    Repo:     <repoUrl or "· not linked yet — Integration tab in portal">
    Local:    <path or SKIPPED>
    Env:      <"dev=… / staging=… / prod=…" if the teammate set them in the portal
              before typing 'continue', else "· not set yet — Integration tab in portal">
  ✓ ...

Pending in portal (open Solution Explorer → each app → Integration tab):
  · Link GitHub repos + set env branches for each app
    (Not blocking — /ba:scope and everything else works without it.
     Do it whenever; next /jetrix:init <slug> picks up the changes.)

Connection map:  · Not built yet — open portal → Connections tab → Build map.
                   (Or, if you know the wiring already, we can add a
                   /jetrix:build-map command later.)

Workspace layout:
  .jetrix/project.json
  .jetrix/cache/                  (repolocation.json + sync-state.json)
  .jetrix/<slug>/                 (delivery-os working tree)
    ├── ba-output/
    ├── context/
    ├── tl-output/
    ├── qa-output/
    ├── dev-output/
    ├── doc-output/
    ├── shared-context/           (seeded templates)
    └── artifacts/

Next:
  /ba:scope                       — start the BA scope conversation
  /jetrix:pull scope              — refresh from Jetrix any time
  /jetrix:push scope              — publish your BA work back
```

## Failure handling

If ANY step in §2-5 errors halfway through:

- Solution create fails → nothing to clean up; teammate re-runs.
- App create fails → previously-created apps stay; teammate can re-run `/jetrix:init <slug>` and the empty-apps flow will add the remaining ones.
- Bundle re-fetch fails → the created Solution + apps still exist in Jetrix; teammate just runs `/jetrix:init <slug>` to complete the workspace binding.

Never rollback creates on failure — leaves the teammate in a recoverable state instead of forcing them to start over. Always print the exact error message and the specific command to re-run.

## Idempotency

Not fully idempotent — the Solution name uniqueness check at `project_create_solution` prevents accidentally creating two Solutions with the same name. If a teammate re-runs this command with the same Solution name they get:

```
Solution "Nutrina Supplier Portal" already exists. Options:
  [1] Bind to the existing Solution instead → /jetrix:init nutrina-supplier-portal
  [2] Create with a different name          → re-prompt
  [3] Cancel
```

Preferred UX: point them at `/jetrix:init` when the Solution already exists. That's what init was designed for.
