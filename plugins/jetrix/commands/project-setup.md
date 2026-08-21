---
description: One-command onboarding — creates a Solution, adds apps, links GitHub repos, saves env branches, binds the workspace, and scaffolds the delivery-os folder tree. All from CLI. The only browser step is a one-time GitHub App install per GitHub org (unavoidable — GitHub auth flows can't be scripted). Use this instead of /jetrix:init when starting from zero.
argument-hint: "[<solution-name>]"
---

# /jetrix:project-setup

The single command a teammate runs to go from **empty workspace folder + no Jetrix Solution** to **ready to work** — Solution + apps + env branches + GitHub links + `.jetrix/project.json` + delivery-os folder tree — without a single portal visit.

Use this instead of `/jetrix:init` **only when starting from zero** (no Solution created yet in Jetrix). If the Solution already exists, `/jetrix:init <slug>` is the right entry point — it handles bind + empty-apps + connection-map pull.

## What this replaces

| Old flow | New flow |
|---|---|
| Portal → New Solution → fill 7-section profile → invite members | (skipped — Solution created via CLI Q&A) |
| Portal → Solution → Apps → New App × N | (one Q&A loop) |
| Portal → App → Integrate Repository × N (with GitHub App install per org) | Same Q&A loop; GitHub App install still browser (unavoidable) |
| Portal → App → Env Configs → set dev / staging / prod × N | Same Q&A loop |
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

Then for each app run the **four-step app loop** (identical to `/jetrix:init` §7a):

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

Capture the returned `_id` as `projectId`.

### 3b. GitHub repo link

```
GitHub repo for "<app name>" (owner/name, e.g. techjays/nutrina-api):
```

Call:
```
mcp__project-mcp__project_list_available_repositories(
  solution_id = <solutionId>,
  project_id  = <projectId>
)
```

**If the repo is in the response** → jump to 3c.

**If the response is empty OR the repo isn't in it** → the Jetrix GitHub App isn't installed on that GitHub org yet (or hasn't been granted access to that repo). Print a **summary block** with all the info the teammate needs:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub App install needed for "<owner>" org
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  App:     Techjays Jetrix Code Reviewer
  Org:     <owner>
  Repo:    <owner>/<name>

  Steps:
    1. Open this URL in your browser:
       https://github.com/apps/techjays-jetrix-code-reviewer/installations/new

    2. Pick the "<owner>" org (or your personal account if the repo
       is under your username).

    3. Under "Repository access", choose either:
         · All repositories             (easy — grants access to every repo
                                        in the org, including future ones)
         · Only select repositories     (safer — pick "<name>" and any other
                                        Jetrix-linked repos in this org)

    4. Click "Install & Authorize". GitHub will redirect you briefly to
       the Jetrix portal to record the install — you can close that tab
       as soon as it loads.

    5. Come back here and type "installed" to continue.

  This install is a ONE-TIME step per GitHub org — subsequent apps in
  the same org don't need it. If another teammate already installed it,
  just make sure this repo is included in the granted repos (step 3).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

installed?
```

Wait for the teammate to answer `installed`. Then **re-run `project_list_available_repositories`**. If the repo is now in the response, proceed. If still not, ask:

```
Repo "<owner>/<name>" is still not visible. Options:
  [1] Retry (I installed the App now / added the repo to granted list)
  [2] Skip repo linking for this app (repoUrl stays null; link later)
  [3] Try a different repo
```

### 3c. Link the repo

```
mcp__project-mcp__project_integrate_repository(
  solution_id     = <solutionId>,
  project_id      = <projectId>,
  repository_id   = "<owner/name>",
  repository_name = "<name>",
  repository_url  = "https://github.com/<owner>/<name>"
)
```

### 3d. Env branches + URLs

```
dev branch?       → develop
dev URL?          → https://dev.nutrina.com  (or type 'skip' → placeholder)

staging branch?   → staging
staging URL?      → https://staging.nutrina.com

prod branch?      → main
prod URL?         → https://nutrina.com
```

If URL is `skip`, substitute `https://tbd.example.com` — the upstream validator requires a valid URL, and this placeholder can be updated later.

Three calls (once per env):
```
mcp__project-mcp__project_save_env_config(
  solution_id      = <solutionId>,
  project_id       = <projectId>,
  environment_name = "dev",     # then "staging", then "prod"
  branch_name      = "<branch>",
  url              = "<url>",
  auto_deploy      = false
)
```

### 3e. Loop or done

After each app: `Add another app? [y/N]`. On `y`, back to 3a with a fresh app. On `N`, exit the loop and continue to §4.

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
    Repo:     github.com/<owner>/<name>
    Local:    <path or SKIPPED>
    Env:      dev=develop / staging=staging / prod=main
  ✓ ...

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
- App create succeeds but repo link fails → app is created but empty of integrations; teammate can re-run `/jetrix:init <slug>` and use the empty-apps flow to link the repo later.
- Env config fails → same; env configs can be added later via `/jetrix:init` (empty-apps flow) or `/jetrix:app add` if we build that as a follow-up.
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
