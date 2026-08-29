---
description: Bind the current workspace to a Jetrix Solution AND scaffold the delivery-os working tree in one command. Writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info, `.jetrix/cache/repolocation.json` (gitignored) with per-app local repo paths, and pulls the Solution's `connection-map.md` (if built). Then seeds the delivery-os tree (`shared-context/`, `ba/`, `features/`, `tl/`, `qa/`, `doc/`, `tasks/`) — same work `/delivery-os:init` does, invoked inline as the final step. Pass `--skip-scaffold` to bind only. Accepts the Solution ObjectId or slug/name — auto-detects. First MCP call triggers Claude Code's OAuth flow (one-time per teammate per machine). Idempotent — re-run to refresh Jetrix-sourced fields without clobbering hand-edits.
argument-hint: "<projectId | slug/name> [--skip-scaffold]"
---

# /jetrix:init

Bind the **current workspace** (cwd) to a Jetrix Solution and scaffold the delivery-os working tree in one shot. Writes the Jetrix wiring (`.jetrix/project.json`, `.jetrix/cache/`, `.jetrix/connection-map.md`) then invokes the same seeding logic as `/delivery-os:init` inline as its final step, so a teammate goes from empty folder to ready-to-work with one command. Pass `--skip-scaffold` to bind only; `/delivery-os:init` can be run later to fill in the tree.

After a normal run the workspace looks like:

```
<workspace>/
└── .jetrix/                    ← ENTIRELY gitignored (whole folder)
    ├── project.json            (this command writes this)
    ├── connection-map.md       (this command writes this if the portal built one)
    ├── cache/                  (repolocation.json + sync-state.json)
    └── shared-context/ ba/ features/ tl/ qa/ doc/ tasks/    (scaffolded by default; skip with --skip-scaffold)
```

**Layout note (v2.0):** Everything sits at `.jetrix/` root — no `<solutionSlug>/` wrapper. Role folders (`ba/`, `tl/`, `qa/`, `doc/`) hold each role's outputs; `features/` holds per-feature bundles that BA, TL, and Dev all write into; `shared-context/` holds cross-role docs (project profile, glossary, decision log). See `delivery-os-conventions` for the full contract.

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

## 0.5. v2 layout migration (soft, idempotent)

**Runs BEFORE any Jetrix calls.** Detects the old v1 layout — where role folders lived under `.jetrix/<slug>/` — and moves them up to the workspace-level `.jetrix/`. Safe to re-run on a v2 workspace (short-circuits when nothing matches).

**Detection:** loop through every subfolder of `.jetrix/` (excluding `cache/`, `shared-context/`, `ba/`, `features/`, `tl/`, `qa/`, `dev/`, `doc/`, `tasks/`). If a subfolder contains any of `ba-output/`, `tl-output/`, `qa-output/`, `dev-output/`, `doc-output/`, `shared-context/`, or `context/features/` — it's a v1 slug folder. Migrate it.

**Migration steps (per detected slug folder — usually exactly one):**

1. **Rename role folders (drop `-output` suffix):**
   ```
   .jetrix/<slug>/ba-output/    → .jetrix/ba/
   .jetrix/<slug>/tl-output/    → .jetrix/tl/
   .jetrix/<slug>/qa-output/    → .jetrix/qa/
   .jetrix/<slug>/dev-output/   → .jetrix/dev-legacy/   (see step 6)
   .jetrix/<slug>/doc-output/   → .jetrix/doc/
   ```

2. **Promote shared-context/ to the top level** (name unchanged, wrapper removed):
   ```
   .jetrix/<slug>/shared-context/ → .jetrix/shared-context/
   ```

3. **Promote features/ to top level:**
   ```
   .jetrix/<slug>/context/features/ → .jetrix/features/
   ```

4. **Move code-map registry under tl/:**
   ```
   .jetrix/<slug>/context/code-map-registry.md → .jetrix/tl/code-map-registry.md
   ```

5. **Move artifacts/ under ba/:**
   ```
   .jetrix/<slug>/artifacts/ → .jetrix/ba/artifacts/
   ```

6. **Move `dev-legacy/feature-tracker.md` to `features/tracker.md`; delete the (now empty) `dev-legacy/`:**
   ```
   .jetrix/dev-legacy/feature-tracker.md → .jetrix/features/tracker.md
   rmdir .jetrix/dev-legacy/
   ```

7. **Group BA flat files into subfolders:**
   ```
   .jetrix/ba/requirement-register.md    → .jetrix/ba/registers/requirements.md
   .jetrix/ba/workflow-register.md       → .jetrix/ba/registers/workflows.md
   .jetrix/ba/use-case-register.md       → .jetrix/ba/registers/use-cases.md
   .jetrix/ba/business-rule-register.md  → .jetrix/ba/registers/business-rules.md
   .jetrix/ba/example-register.md        → .jetrix/ba/registers/examples.md
   .jetrix/ba/data-register.md           → .jetrix/ba/registers/data.md
   .jetrix/ba/integration-register.md    → .jetrix/ba/registers/integrations.md
   .jetrix/ba/assumption-register.md     → .jetrix/ba/registers/assumptions.md
   .jetrix/ba/clarification-log.md       → .jetrix/ba/logs/clarifications.md
   .jetrix/ba/contradiction-log.md       → .jetrix/ba/logs/contradictions.md
   .jetrix/ba/indexing-assistance-needed.md → .jetrix/ba/logs/indexing-assistance-needed.md
   .jetrix/ba/change-log.md              → .jetrix/ba/logs/changes.md
   .jetrix/ba/scope-reviews/             → .jetrix/ba/reviews/
   ```

8. **Group QA + DOC files:**
   ```
   .jetrix/qa/test-audit-*.{html,md,json}  → .jetrix/qa/audits/
   .jetrix/qa/health-*.md                  → .jetrix/qa/health/
   .jetrix/qa/escalation-*.md              → .jetrix/qa/escalations/
   .jetrix/doc/deck-*.pptx                 → .jetrix/doc/decks/
   .jetrix/doc/walkthrough-*.html          → .jetrix/doc/walkthroughs/
   .jetrix/doc/workflow-*.html             → .jetrix/doc/workflows/
   .jetrix/doc/board-*.html                → .jetrix/doc/boards/
   ```

9. **Delete empty v1-only folders:**
   ```
   .jetrix/<slug>/context/frontend/     (empty since Model B — the code graph moved to <repo>/context/code-context/)
   .jetrix/<slug>/context/backend/
   .jetrix/<slug>/context/database/
   .jetrix/<slug>/context/project/
   .jetrix/<slug>/context/               (wrapper, now empty)
   .jetrix/<slug>/                       (last)
   ```
   Only delete these if they are actually empty after the moves above. Non-empty folders stay put and print a warning.

10. **Rewrite sync-state keys** — `.jetrix/cache/sync-state.json` had per-file keys like `ba-output/scope.md`. Rewrite each key using the same rename table above (`ba-output/scope.md` → `ba/scope.md`, `ba-output/requirement-register.md` → `ba/registers/requirements.md`, etc.). Content hashes and Jetrix task IDs stay identical; only the string keys change.

11. **Report** — print a summary: `Migrated <slug>: <N> folders moved, <M> BA register/log files grouped, <K> sync-state keys rewritten.`

**Idempotency:** re-runs are safe. If none of the v1 markers are present, the whole section is a no-op. Each individual move is a `test -e OLD && ! -e NEW` guard.

**Failure handling:** if any step fails partway (e.g., file exists at both old and new location) — print the specific error, halt with `Migration incomplete. Fix the conflict listed above and re-run /jetrix:init.` and do NOT continue to §1. Never leave the workspace in a half-migrated state without telling the teammate.

## 1. Parse arguments

`$ARGUMENTS` may carry up to two tokens in any order — the Solution reference and an optional `--skip-scaffold` flag:

- **Solution reference** (required):
  - Matches `/^[a-f0-9]{24}$/` → treat as a Solution **ObjectId**. Go straight to `project_get_solution`.
  - Otherwise → treat as a **slug or name**. Resolve via `project_list_solutions` first.
- **`--skip-scaffold`** (optional): capture as `skip_scaffold=true`. When set, §11.5 skips the delivery-os tree seed; the teammate can run `/delivery-os:init` later to fill it in.

If no Solution reference is given, ask for either an ObjectId or a name/slug. Do NOT guess.

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

For each app the teammate wants to add, run just the **metadata step** in the CLI — repo linking and env branches happen in the portal (one clear place, no split-brain state).

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

Capture the returned `_id`. **That's it for the CLI** — no repo prompt, no env branches prompt. Ask `Add another app? [y/N]`; on `y` restart Step 1, on `N` exit the loop and print the portal handoff block below.

### Step 2 — portal handoff (repo linking + env branches happen ONCE per app in Jetrix)

Print this block AFTER all apps are created — don't repeat it per app:

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

- `continue` (default) → proceed to §7b with `apps[]` that have empty repos / envs — the fields exist as nulls, the teammate fills them via the portal later, and next `/jetrix:init <slug>` will pick up the changes.
- `wait` → halt with `OK — finish repo linking + env branches in the portal, then re-run /jetrix:init <slug> to bind.` and stop.

Once the loop exits (either path), **re-fetch the bundle** with `project_get_solution_bundle` so §8 writes `project.json` with the freshly-created apps (plus any repos/envs the teammate DID complete during the portal step before typing `continue`). Do NOT try to hand-merge — one clean re-fetch is simpler and self-verifying.

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

### 10b. Migration (already covered by §0.5)

The v2 layout migration in §0.5 handles the old connection-map path (`<slug>/context/connection-map.md` → `.jetrix/connection-map.md`). Nothing extra to do here for workspaces that were bound before v2.0. If you skipped §0.5 (edge case), the fallback `mv` is safe to run inline: `[[ -f "<workspace_root>/.jetrix/<slug>/context/connection-map.md" && ! -f "<workspace_root>/.jetrix/connection-map.md" ]] && mv <old> <new>`.

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

## 11.5. Scaffold the delivery-os working tree (skipped if `--skip-scaffold`)

If `skip_scaffold=true` → print `· Skipped delivery-os scaffold — run /delivery-os:init later to seed the working tree.` and continue to §12.

Otherwise, invoke the same seeding logic as `/delivery-os:init` inline. `.jetrix/` already exists (created in §8), so `/delivery-os:init`'s precheck passes. The seed is idempotent — files that already exist are never overwritten. It performs:

1. **Create the folder tree** under `<workspace_root>/.jetrix/` (each empty leaf gets a `.gitkeep`):
   ```
   shared-context/
   ba/{registers,logs,artifacts,intake-runs,reviews}/
   features/
   tl/{reviews,maturity}/         + tl/code-map-registry.md (placeholder)
   qa/{audits,health,escalations}/ + qa/quality-gates.md (placeholder)
   doc/{decks,walkthroughs,workflows,boards}/
   tasks/
   ```
2. **Seed templates** from `${CLAUDE_PLUGIN_ROOT-of-delivery-os-core}/templates/` — copy each source to its target only if the target does not exist:

   | Target                                       | Template                                        |
   |----------------------------------------------|-------------------------------------------------|
   | `.jetrix/README.md`                          | `templates/workspace-readme.md`                 |
   | `.jetrix/shared-context/project-profile.md`  | `templates/shared-context/project-profile.md`   |
   | `.jetrix/shared-context/glossary.md`         | `templates/shared-context/glossary.md`          |
   | `.jetrix/shared-context/stakeholder-map.md`  | `templates/shared-context/stakeholder-map.md`   |
   | `.jetrix/shared-context/system-landscape.md` | `templates/shared-context/system-landscape.md`  |
   | `.jetrix/shared-context/decision-log.md`     | `templates/shared-context/decision-log.md`      |
   | `.jetrix/shared-context/baseline-profile.md` | `templates/baseline-profile.md`                 |
   | `.jetrix/ba/intake.index.md`                 | `templates/intake.index.md`                     |

3. **Stamp** `generated_at: <today>` and `status: Draft` on each seeded doc where the frontmatter has those fields.

The full spec (rerun handling, exact tree, template stamping rules) lives in `/delivery-os:init` — this step is a straight invocation of the same logic. `/delivery-os:init` remains available as a standalone re-seed utility for existing workspaces or workspaces bound with `--skip-scaffold`.

Set `scaffolded=true` on success (for the §12 summary line).

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

Connection map:   <✓ pulled | · not built yet | ⚠ retry needed>
Delivery-OS tree: <✓ scaffolded | · skipped — run /delivery-os:init to seed>

Workspace layout:
  .jetrix/project.json
  .jetrix/connection-map.md       (if the portal built one)
  .jetrix/cache/                  (repolocation.json + sync-state.json)
  .jetrix/shared-context/         (seeded templates + baseline-profile)         [scaffold only]
  .jetrix/ba/                     (intake.index seeded; registers/ logs/ …)     [scaffold only]
  .jetrix/features/               (empty — per-feature bundles from /ba:features) [scaffold only]
  .jetrix/tl/                     (reviews/ maturity/ code-map-registry.md)     [scaffold only]
  .jetrix/qa/                     (audits/ health/ escalations/ + gates)        [scaffold only]
  .jetrix/doc/                    (decks/ walkthroughs/ workflows/ boards/)     [scaffold only]
  .jetrix/tasks/                                                                [scaffold only]

Next:
  BA:  /ba:scope  →  /ba:features
  TL:  /tl:code-map (brownfield)  or  /tl:scaffold (greenfield)
  QA:  /qa:audit
  Dev: /dev:build FEAT-<n>
  Doc: /doc:proposal · /doc:magic-board · /doc:walkthrough · /doc:workflow
```

Suppress the `[scaffold only]` rows from the printed layout when `scaffolded=false`; instead print one line: `.jetrix/  (delivery-os tree not seeded — run /delivery-os:init to fill it in)`.

Keep it idempotent — a rerun for the same solutionId refreshes without clobbering hand-edits, migrates the connection-map to the new path if needed, re-attempts the connection-map download if the last run failed, and re-runs the scaffold seed (which is itself idempotent) to fill in any missing files.
