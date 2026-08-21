---
description: Bind the current workspace to a Jetrix Solution. Writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info, and `.jetrix/cache/repolocation.json` (gitignored) with per-app local repo paths. Also pulls the Solution's `connection-map.md` (if built) to `.jetrix/connection-map.md` so downstream commands have it immediately. Accepts either the Solution ObjectId or its slug/name — auto-detects. First MCP call triggers Claude Code's OAuth flow (one-time per teammate per machine). Does NOT scaffold delivery-os output folders — that is `/delivery-os:init`. Idempotent — re-run to refresh Jetrix-sourced fields without clobbering hand-edits.
argument-hint: "<projectId | slug/name>"
---

# /jetrix:init

Bind the **current workspace** (cwd) to a Jetrix Solution. Writes the Jetrix wiring (`.jetrix/`) at workspace root. Companion command `/delivery-os:init` scaffolds the delivery-os output folders alongside it — this command handles ONLY the Jetrix binding + OAuth handshake + per-app local repo path collection + connection-map fetch.

After running both, the workspace looks like:

```
<workspace>/
└── .jetrix/                    ← ENTIRELY gitignored
    ├── project.json            (this command writes this)
    ├── connection-map.md       (this command writes this if the portal built one)
    ├── cache/                  (this command writes repolocation.json here)
    └── <solutionSlug>/         (/delivery-os:init creates this)
        └── ...
```

Use the LOCAL MCP tool `project-mcp` registered in `~/.claude/settings.json` or workspace `.mcp.json`. Never call server URLs directly.

## 0. Preflight — verify we're initializing in the right directory

**This is the FIRST step. Do not skip. Do not create any files or folders before it passes.** Bash's cwd persists across tool calls; a previous `cd` may have moved us away from the workspace root. Confirm the resolved absolute path before touching disk.

1. Resolve `$PWD` to an absolute path via one Bash call:
   ```bash
   pwd
   ```
   Capture the output as `workspace_root`. Every downstream write MUST use this absolute path — never `$PWD` or relative paths.

2. Sanity-check that `workspace_root` looks like a project root, not a random subfolder:
   - Does it contain any of: `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `README.md`? → looks like a repo root. Good.
   - Does the basename match any of these red-flag names: `src`, `dist`, `build`, `node_modules`, `.venv`, `venv`, `target`, `__pycache__`? → warn and force explicit re-confirmation before continuing.
   - Does an ancestor directory (walk up to 3 levels) already contain `.jetrix/`? → the user might be trying to re-init inside an already-bound workspace by mistake. Print that ancestor path and ask which workspace they meant.

3. Show the resolved path and ask:
   ```
   Initialize Jetrix workspace at "<workspace_root>"? [Y/n]
   ```
   - `Y` (default on empty) → proceed to §1.
   - `n` → exit cleanly with `Cancelled — nothing written.`

Once confirmed, treat `workspace_root` as immutable for the rest of this command. Every file path is built as `<workspace_root>/.jetrix/...`.

## 1. Parse arguments

`$ARGUMENTS` should be exactly one token:

- If it matches `/^[a-f0-9]{24}$/` → treat as a Solution **ObjectId**. Go straight to `project_get_solution`.
- Otherwise → treat as a **slug or name**. Resolve via `project_list_solutions` first.

If empty, ask for either an ObjectId or a name/slug. Do NOT guess.

## 2. Precheck

Confirm `project-mcp` is registered as an MCP server. If not → stop and tell the teammate to register it. Do not attempt other MCP calls until this is fixed.

## 3. First MCP call → OAuth handshake (automatic)

The first invocation of any `mcp__project-mcp__*` tool triggers Claude Code's OAuth flow. Browser opens → teammate signs in to Jetrix → consent → token cached locally by Claude Code. All Jetrix MCPs share the auth server, so this one sign-in covers everything. Nothing to do beyond completing the browser flow.

If OAuth is cancelled → stop with *"Sign-in failed. Rerun `/jetrix:init`."*

## 4. Rerun handling

If `<workspace_root>/.jetrix/project.json` already exists:

- **Same `solutionId` as the argument** → ask *"Workspace already initialized for `<solutionName>` (`<solutionId>`). Refresh project details from Jetrix? [y/n]"*. On yes, continue and re-fetch. On no, stop.
- **Different `solutionId`** → hard STOP. Tell teammate *"This workspace is already initialized for `<other-name>` (`<other-id>`). Use a separate workspace folder for each Jetrix project."*

## 5. Resolve the Solution

**ObjectId path:**
- `mcp__project-mcp__get_solution(solution_id=<arg>)`
- On 404 / 403 → stop with *"Solution `<id>` not found or you're not a Member."*

**Slug/name path:**
- `mcp__project-mcp__list_solutions(query=<arg>)`
- 0 matches → stop; list available names.
- >1 matches → interactive picker: *"Multiple matches: [1] `<name>` (`<slug>`, `<id>`) [2] ... Pick a number."*
- 1 match → confirm; then `get_solution(solution_id=<picked>)`.

Capture full solution: `_id`, `name`, `slug`, `description`, `type`, `environments`.

## 6. Soft workspace-name check

Compare `solutionSlug` against workspace folder basename (normalized: lowercase, spaces → dashes). Mismatch → warn and confirm; never hard-fail. This is a nudge, not a rule.

## 7. Fetch full project context — ONE call

Call `mcp__project-mcp__get_solution_bundle(solution_id)`. This returns everything in a single MCP tool invocation:

```json
{
  "solution": { "_id": "...", "name": "...", "slug": "...", "type": "...", ... },
  "apps": [
    {
      "project": { "_id": "...", "name": "...", "slug": "...", "project_type": "...", "repoUrl": "..." },
      "envConfigs": [ { "environmentName": "dev", "branchName": "dev", "url": "...", "autoDeploy": true }, ... ],
      "repositoryIntegration": { "repository_owner": "...", "repository_name": "...", "installation_id": "..." }
    },
    ...
  ]
}
```

**Do NOT fall back to `project_list_projects` / `project_get_project` / `project_get_env_configs` / `project_get_repository_integration` cascades unless the bundle tool errors out.** Those are still available for finer-grained fetches (e.g., single-app refresh) but drive per-app UX prompt storms; the bundle is the sanctioned single-call entry point for init.

**Defensive client-side filter (server bug guard):** `project_get_solution_bundle` has historically leaked apps from OTHER solutions into `apps[]` (see 2026-08-20 report). After receiving the bundle, filter `apps[]` where `project.solution === <requested solution_id>` (or `project.solutionId === <id>` depending on shape) — drop anything else silently. Log a warning to stderr if any leaks were filtered out so the server-side bug stays visible.

Per-app failures inside the bundle are already swallowed by project-mcp — apps whose env-configs or repo-integration fetch failed still appear in the response with `envConfigs: []` / `repositoryIntegration: null`. Not fatal for `/jetrix:init` — write the app with `envConfigs: []` if it came back empty. `repositoryIntegration` is **not** persisted locally either way (see the `project.json` shape below — `repoUrl` is the only repo field kept).

## 7a. If `apps[]` is empty — interactive app creation (no portal visit needed)

**Trigger:** the Solution exists but has zero apps yet. Rather than sending the teammate to the portal, walk them through creating each app right here.

```
Solution "<name>" has no apps yet. Add one now? [Y/n]
```

- `n` → skip this section; `project.json` gets written with `apps: []`. The teammate can re-run `/jetrix:init` any time to fill this in.
- `Y` (default) → proceed with the loop below.

For each app the teammate wants to add, run through **four steps**:

### Step 1 — collect app metadata

```
App name?          → e.g. "Nutrina API"
Description?       → one line, e.g. "REST API for Nutrina supplier onboarding"
Project type?      → number picker:
                      [1] backend api
                      [2] web application
                      [3] mobile application
                      [4] fullstack
                      [5] workflow
                      [6] database
                      [7] desktop application
```

Then call:

```
mcp__project-mcp__project_create_project(
  solution_id  = <solutionId>,
  name         = "<name>",
  description  = "<description>",
  project_type = "<picked value>"
)
```

Capture the returned `_id` — you'll need it for steps 2-4.

### Step 2 — link a GitHub repo

Ask which repo, then discover what's available:

```
GitHub repo for "<app name>" (owner/name, e.g. techjays/nutrina):
```

Call:

```
mcp__project-mcp__project_list_available_repositories(
  solution_id = <solutionId>,
  project_id  = <new app _id>
)
```

**Two branches:**

- Response contains repos → find the row where `repository_id` matches the teammate's `owner/name` input (case-insensitive). If a match exists, extract `repository_name` + `repository_url` from that row and jump to §Step 2c below.

- Response is empty (or the teammate's repo isn't in it) → the Jetrix GitHub App either isn't installed on the target org yet, or hasn't been granted access to that repo. Print:

  ```
  ⚠ The Jetrix GitHub App isn't installed on the "<org>" GitHub org yet
    (or hasn't been granted access to "<repo>").

    Open this URL in your browser to install / grant access:
      https://github.com/apps/techjays-jetrix-code-reviewer/installations/new

    (After you finish on github.com, GitHub redirects you briefly to the
    Jetrix portal to record the install, then you can close that tab.)

    Once done, come back here and answer "installed" to continue.
  ```

  Wait for the teammate to answer `installed`. Then **re-run `project_list_available_repositories`** and try the match again. If it still doesn't come back, ask if they want to skip repo linking for this app (`project.json` will save `repoUrl: null`) or retry.

### Step 2c — link it

```
mcp__project-mcp__project_integrate_repository(
  solution_id     = <solutionId>,
  project_id      = <new app _id>,
  repository_id   = "<owner/name>",
  repository_name = "<name>",
  repository_url  = "https://github.com/<owner>/<name>"
)
```

### Step 3 — set env branches (dev / staging / prod)

For each of the three canonical environments, ask for the branch name. Use `main` or `master` as sensible defaults for prod; `develop` / `staging` for the others.

```
dev branch?       → develop
staging branch?   → staging
prod branch?      → main
```

Also ask for the deployed URLs — required by upstream validator. Use `https://tbd.example.com` as a placeholder if the env isn't deployed yet; the teammate can update it later.

```
dev URL?          → https://dev.nutrina.com   (or 'skip' → https://tbd.example.com)
staging URL?      → https://staging.nutrina.com
prod URL?         → https://nutrina.com
```

Then three calls (once per env):

```
mcp__project-mcp__project_save_env_config(
  solution_id      = <solutionId>,
  project_id       = <new app _id>,
  environment_name = "dev",
  branch_name      = "<dev branch>",
  url              = "<dev url>",
  auto_deploy      = false
)
```

Repeat for `staging` and `prod`.

### Step 4 — loop

```
Add another app? [y/N]
```

- `y` → back to Step 1 with a fresh app
- `N` (default) → exit the loop, continue to §7b

Once the loop exits, **re-fetch the bundle** with `project_get_solution_bundle` so §8 writes `project.json` with the freshly-created apps + env configs + repo integrations. Do NOT try to hand-merge the individual create responses into the bundle shape — one clean re-fetch is simpler and self-verifying.

## 7b. Confirm the Solution with the user before binding

**Before writing ANY file to disk**, print the resolved Solution and ask for an explicit `Y`. Users typo Solution ids/slugs and the wrong binding is expensive to undo (every subsequent `/jetrix:push` writes against the wrong Solution).

```
Found Solution: "<solutionName>"  (id: <solutionId>, slug: <solutionSlug>)
  Type:  <type>
  Envs:  <comma-separated environments>
  Apps:  <N> (<projectName-1>, <projectName-2>, ...)
  Repos: <repo-owner-1>/<repo-name-1>, <repo-owner-2>/<repo-name-2>

Bind this workspace ("<workspace_root>") to this Solution? [Y/n]
```

- `Y` (default on empty) → continue to §8.
- `n` → exit cleanly with `Cancelled — nothing written.`
- Anything else → re-prompt once, then bail.

Show the resolved `workspace_root` explicitly so the teammate sees exactly where the binding will land. This catches both wrong-Solution and wrong-directory typos at the same gate.

## 8. Write `<workspace_root>/.jetrix/project.json` (gitignored)

Create `<workspace_root>/.jetrix/` if missing. Then write `project.json`:

```json
{
  "solutionId": "<Solution._id>",
  "solutionSlug": "<slug>",
  "solutionName": "<name>",
  "solutionType": "<type>",
  "solutionDescription": "<description>",
  "environments": ["dev", "staging", "prod"],
  "apps": [
    {
      "projectId": "<Project._id>",
      "projectSlug": "<slug>",
      "projectName": "<name>",
      "projectType": "<web application | backend api | mobile application | service>",
      "repoUrl": "<https://github.com/...>",
      "env_branches": {
        "dev": "dev",
        "staging": "staging",
        "prod": "master"
      }
    }
  ],
  "bound_at": "<ISO-8601 timestamp of first bind>",
  "last_pulled": null
}
```

**Idempotency:** on refresh, merge Jetrix-sourced fields (name, slug, description, apps[], env_branches). Preserve `bound_at`. Never write secrets — env-config response already excludes them.

## 9. Ask for per-app local repo paths

For each app in `apps[]`, prompt teammate:

> *"Where's the `<projectName>` (`<projectType>`) repo on your laptop? Absolute path, or 'skip' if you don't work on this app."*

Answers → `<workspace_root>/.jetrix/cache/repolocation.json`:

```json
{
  "<projectId-1>": "/Users/alice/Code/acme-frontend",
  "<projectId-2>": "/Users/alice/Code/acme-backend",
  "<projectId-3>": "SKIPPED"
}
```

Keys = `projectId`. Values = absolute path OR literal `"SKIPPED"`.

## 10. Pull the connection-map — ONLY if the portal has built one

The connection-map is the LLM-synthesised architecture doc for the Solution, authored via the portal's Connections tab. Its canonical local path is **`<workspace_root>/.jetrix/connection-map.md`** — at the `.jetrix/` root, NOT under `<slug>/context/`. Rationale: `.jetrix/` root is stable across future plugin folder-reorgs; the connection-map is one file per Solution, not per feature/page/entity, so it belongs alongside `project.json`.

### 10a. Gate on the metadata we already have

**Do NOT call `scope_pull_connection_map` blindly.** The Solution bundle fetched in §7 already carries `solution.connection_map_ref` — a `null` value means the portal has never built a map, so there is nothing to fetch. Skipping the MCP call in that case saves a full round-trip on the common "not built yet" path.

Check:

```
if bundle.solution.connection_map_ref is null (or missing):
    print "· No connection-map yet — open the portal → Connections tab → Build map."
    skip §10b + §10c + §10d entirely
    continue to §11
```

Only if `connection_map_ref` is set (has `gcs_path` + `updated_at`) do you proceed with §10b onwards. Apply the same pattern to any future doc: if the metadata says it doesn't exist, don't call the fetch. Never make an "empty" pull call just to discover it's empty.

### 10b. Migration (soft) — if the file is still at the old location, move it

Only runs when a build exists, right before the download so we don't leave a stale file behind:

```bash
OLD="<workspace_root>/.jetrix/<solutionSlug>/context/connection-map.md"
NEW="<workspace_root>/.jetrix/connection-map.md"
if [[ -f "$OLD" && ! -f "$NEW" ]]; then
  mv "$OLD" "$NEW"
  echo "Migrated connection-map to new canonical path: $NEW"
fi
```

### 10c. Fetch a fresh signed URL

Now that we know a build exists, ONE MCP call gets us a signed URL:

```
mcp__scope-mcp__scope_pull_connection_map(solution_id=<solutionId>)
```

Response contract:
```json
{
  "document_id": "68f2...",
  "gcs_path": "gs://<bucket>/project-context/<solutionId>/connection-map.md",
  "original_name": "connection-map.md",
  "size_kb": 3,
  "updated_at": "2026-08-19T10:14:22.000Z",
  "signed_download_url": "https://storage.googleapis.com/...",
  "tags": ["connection-map", "solution-context"]
}
```

If this tool errors with "No connection-map found" (race between §7 and §10c — someone deleted the ref, or a permissions issue) → soft-fail with the same message from §10a. Do NOT retry.

### 10d. Download + update sync-state

```bash
mkdir -p "<workspace_root>/.jetrix"
curl --fail --silent --show-error \
     --output "<workspace_root>/.jetrix/connection-map.md" \
     "<signed_download_url>"
```

Update `<workspace_root>/.jetrix/cache/sync-state.json` under the top-level `connection_map` key (merge, don't clobber other stages' keys):

```json
{
  "connection_map": {
    "document_id": "68f2...",
    "gcs_path": "gs://.../connection-map.md",
    "size_kb": 3,
    "updated_at": "2026-08-19T10:14:22.000Z",
    "pulled_at": "<ISO-8601 now>",
    "local_path": ".jetrix/connection-map.md"
  }
}
```

**Failure handling** — never block init on connection-map problems:

- curl exits non-zero (network, 4xx, 5xx from GCS) → print `· connection-map download failed (HTTP <code>) — will retry on next /jetrix:pull scope.` Continue to §11. Do NOT update sync-state on a failed download so the next pull naturally retries.
- Any other error → same soft-fail behavior. Init is done either way.

## 11. Gitignore `.jetrix/`

Ensure `<workspace_root>/.gitignore` includes `.jetrix/` (the entire folder — nothing under it is committed). Create the file if missing; append idempotently. If a prior version added only `.jetrix/cache/`, replace with `.jetrix/`.

## 12. Print summary

```
✓ Bound workspace to Jetrix project.

Workspace:     <workspace_root>
Solution:      <name>  (<solutionId>)
Slug:          <slug>
Type:          <type>
Environments:  dev, staging, prod

Apps (<N>):
  • <projectName>  (<projectType>)  →  <path or SKIPPED>
  • ...

Connection map: <✓ pulled | · not built yet | ⚠ retry needed>

Workspace layout (so far):
  .jetrix/project.json       ← this command wrote this
  .jetrix/connection-map.md  ← this command wrote this (if the portal built one)
  .jetrix/cache/             ← repolocation.json + sync-state.json

Next:
  Scaffold delivery-os folder:  /delivery-os:init
                                  (reads .jetrix/project.json — creates .jetrix/<slug>/ working tree)
```

Keep it idempotent — a rerun for the same solutionId refreshes without clobbering hand-edits, migrates the connection-map to the new path if needed, and re-attempts the connection-map download if the last run failed.
