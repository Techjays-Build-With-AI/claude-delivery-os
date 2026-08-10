---
description: Bind the current workspace to a Jetrix Solution. Writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info, and `.jetrix/cache/repolocation.json` (gitignored) with per-app local repo paths. Accepts either the Solution ObjectId or its slug/name — auto-detects. First MCP call triggers Claude Code's OAuth flow (one-time per teammate per machine). Does NOT scaffold delivery-os output folders — that is `/delivery-os:init`. Idempotent — re-run to refresh Jetrix-sourced fields without clobbering hand-edits.
argument-hint: "<projectId | slug/name>"
---

# /jetrix:init

Bind the **current workspace** (cwd) to a Jetrix Solution. Writes the Jetrix wiring (`.jetrix/`) at workspace root. Companion command `/delivery-os:init` scaffolds the delivery-os output folders alongside it — this command handles ONLY the Jetrix binding + OAuth handshake + per-app local repo path collection.

After running both, the workspace looks like:

```
<workspace>/
└── .jetrix/                    ← ENTIRELY gitignored
    ├── project.json            (this command writes this)
    ├── cache/                  (this command writes repolocation.json here)
    └── <solutionSlug>/         (/delivery-os:init creates this)
        └── ...
```

Use the LOCAL MCP tool `project-mcp` registered in `~/.claude/settings.json` or workspace `.mcp.json`. Never call server URLs directly.

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

If `<workspace>/.jetrix/project.json` already exists:

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

Per-app failures inside the bundle are already swallowed by project-mcp — apps whose env-configs or repo-integration fetch failed still appear in the response with `envConfigs: []` / `repositoryIntegration: null`. Not fatal for `/jetrix:init` — write the app with `envConfigs: []` if it came back empty. `repositoryIntegration` is **not** persisted locally either way (see the `project.json` shape below — `repoUrl` is the only repo field kept).

## 8. Write `<workspace>/.jetrix/project.json` (gitignored)

Create `<workspace>/.jetrix/` if missing. Then write `project.json`:

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

Answers → `<workspace>/.jetrix/cache/repolocation.json`:

```json
{
  "<projectId-1>": "/Users/alice/Code/acme-frontend",
  "<projectId-2>": "/Users/alice/Code/acme-backend",
  "<projectId-3>": "SKIPPED"
}
```

Keys = `projectId`. Values = absolute path OR literal `"SKIPPED"`.

## 10. Gitignore `.jetrix/`

Ensure `<workspace>/.gitignore` includes `.jetrix/` (the entire folder — nothing under it is committed). Create the file if missing; append idempotently. If a prior version added only `.jetrix/cache/`, replace with `.jetrix/`.

## 11. Print summary

```
✓ Bound workspace to Jetrix project.

Solution:      <name>  (<solutionId>)
Slug:          <slug>
Type:          <type>
Environments:  dev, staging, prod

Apps (<N>):
  • <projectName>  (<projectType>)  →  <path or SKIPPED>
  • ...

Workspace layout (so far):
  .jetrix/project.json      ← this command wrote this
  .jetrix/cache/            ← repolocation.json + sync-state.json

Next:
  Scaffold delivery-os folder:  /delivery-os:init
                                  (reads .jetrix/project.json — creates .jetrix/<slug>/ working tree)
```

Keep it idempotent — a rerun for the same solutionId refreshes without clobbering hand-edits.
