---
description: Bind the current workspace to a project in your tracker AND scaffold the delivery-os working tree in one command. Jetrix is the default; pass `--tracker=<name>` to bind against any tool whose MCP you have registered — the command finds that MCP, maps its tools once, and everything downstream is identical. The project reference is optional on every tracker: with none, it lists what you have, or prints how to create one. Writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info, `.jetrix/cache/repolocation.json` (gitignored) with per-app local repo paths, and pulls the Solution's `connection-map.md` (if built). Then seeds the delivery-os tree (`shared-context/`, `ba/`, `features/`, `tl/`, `qa/`, `doc/`, `tasks/`) — same work `/delivery-os:init` does, invoked inline as the final step. Pass `--skip-scaffold` to bind only. Accepts the Solution ObjectId or slug/name — auto-detects. First MCP call triggers Claude Code's OAuth flow (one-time per teammate per machine). Idempotent — re-run to refresh Jetrix-sourced fields without clobbering hand-edits.
argument-hint: "[project-ref] [--tracker=<name>] [refresh] [--skip-scaffold]"
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

`$ARGUMENTS` may carry, in any order:

- **Project reference** (optional — blank lists what you have):
  - Matches `/^[a-f0-9]{24}$/` → a Jetrix Solution **ObjectId**.
  - Otherwise → a slug, name, or the tracker's own project key.
- **`--tracker=<name>`** (optional, default `jetrix`): the project-management tool holding the tasks.
- **`refresh`** (optional): re-fetch into an existing bind. See §4.
- **`--skip-scaffold`** (optional): skip the §11.5 tree seed.

## 2. Resolve the tracker

**Default is `jetrix`.** Read it in this order — `project.json`'s `tracker.provider` on a re-run, then `--tracker=`, then the default. Never ask when one of those answers.

Known trackers:

| `--tracker=` | MCP | Add it with |
|---|---|---|
| `jetrix` | `project-mcp` · `scope-mcp` · `task-mcp` | already registered by `/delivery-os:setup` |
| `jira` | `atlassian` | `claude mcp add --transport http atlassian https://mcp.atlassian.com/v2/mcp` |
| `clickup` | `clickup` | `claude mcp add --transport http clickup <url>` |
| `azure` | `azure` | `claude mcp add --transport http azure <url>` |
| anything else | whatever it was registered as | the user adds it; §2b finds it |

### 2a. On `jetrix`, make no check

`/delivery-os:setup` registered those three. If a call fails because the tool isn't there, say `Run /delivery-os:setup first — it registers all three.` and stop. Do not pre-check.

**Never run `claude mcp list`** for any check here — it health-checks every registered server over the network, so on a machine with many connectors the command appears to hang before doing any work.

### 2b. On any other tracker, find its MCP first

The user installed it, so verify it before resolving anything. Resolve with `ToolSearch` — MCP tools may be deferred, so an empty tool list is not an answer:

- `ToolSearch` the tracker name (`jira atlassian issue`, `clickup task`, …). Tools returned → registered; record the server name as `tracker.mcp`, since it is whatever the user typed at `claude mcp add` (`atlassian`, `claude_ai_Atlassian_Rovo`, …) and we never assume it.
- Nothing returned → print the `claude mcp add` line from the table (or, for an unknown tracker, `claude mcp add --transport http <name> <its-mcp-url>`), say `Nothing was written.`, and stop.

### 2c. Map the tracker's tools once

Read the returned schemas and propose the mapping. Ten keys, `null` where the tracker cannot do it:

```
browse[] · resolve_project · resolve_container · create_container
create_issue · update_issue · read_issue · child_issues
comments · attachments · set_status · put_document
```

**`resolve_container` and `create_container` are what §5a needs.** On ClickUp they are `clickup_get_lists` and `clickup_create_list`; on Jira, epic search and epic create; where a tracker files issues straight into the project, both are `null` and §5a records `container_kind: none`. A tracker that can list containers but not create them gets `create_container: null` — §5a then offers only the existing ones and says where to make a new one.

**`browse` is an ordered list, because “project” is not one level in every tool.** Jetrix has Solutions; Jira has Projects; ClickUp has Workspace → Space → Folder → List, and tasks live in the List. Record the tools that walk from the root down to whatever holds tasks — a flat tracker is simply a one-element list:

```
jetrix    browse: [project_list_solutions]
jira      browse: [jira_get_visible_projects]
clickup   browse: [clickup_get_workspaces, clickup_get_spaces,
                   clickup_get_folders, clickup_get_lists]
```

Also propose a `status_map` for `PLANNED · IN_PROGRESS · REVIEW · DONE · BLOCKED` from the statuses the schemas expose. **Always show the status map for confirmation** — it is the one part discovery guesses badly. Store both in `project.json` §8; a re-run never asks again.

### 2d. Capabilities

Set from the tracker, and branch on these — never on the provider name:

| | `jetrix` | every other tracker |
|---|---|---|
| `apps` | `true` — repos come from the Solution | `false` — repo path + dev branch asked in §9 |
| `tabs` | `7` — one file per tab | `1` — the six BA files plus Implementation as `##` sections in one body |
| `documents` | `scope-mcp` — publishes `scope.html` to Dashboard → Reports | `none` — `scope.html` is still rendered, it just stays local |

## 3. First MCP call → OAuth handshake (automatic)

The first invocation of any MCP tool triggers Claude Code's OAuth flow. Browser opens → the teammate signs in → consent → token cached locally. The three Jetrix MCPs share one auth server, so a single sign-in covers them; another tracker's MCP has its own.

If OAuth is cancelled → stop with *"Sign-in failed. Rerun `/jetrix:init`."*

## 4. Rerun handling

If `<workspace_root>/.jetrix/project.json` already exists:

- **`refresh` passed** → re-fetch without asking. **The reference is optional** — it is already in `project.json`, so bare `/jetrix:init refresh` is the canonical form and the one to print whenever a gap is reported. It works the same on every tracker, because the provider is recorded too.
- **Same `project_ref`, no `refresh`** → ask *"Workspace already initialized for `<name>` (`<ref>`). Refresh project details? [y/n]"*. On yes, re-fetch. On no, stop.
- **Different `project_ref`** → hard STOP. *"This workspace is already initialized for `<other-name>` (`<other-ref>`). Use a separate workspace folder for each project."*

A refresh re-fetches the project, its apps and their env branches, and re-attempts the connection map. It **preserves** `bound_at`, the repo paths already given, `tracker.mapping` and `tracker.status_map`.

## 5. Resolve the project

On `jetrix` the calls are `project-mcp`'s; on any other tracker they are `mapping.resolve_project`. The shape is the same.

**No reference — walk `browse`.** One picker per level, names only, never ids. The user chooses `Acme` → `Delivery`
→ `Supplier Platform`; the id behind it is never typed and never shown unless something fails. A one-element `browse`
is a single picker, which is the Jetrix and Jira case.

**`browse` stops at the project — the thing that already exists.** It does not walk into the list or epic that will
hold the features; §5a does that, because that one may have to be created and this step never creates anything.

Record both:

```yaml
project_ref:  "901203847"                          # what the API needs
project_path: "Acme / Delivery / Supplier Platform"  # what a human recognises
```

`project_path` is what every later summary prints. `901203847` means nothing to the person reading it, and a workspace
bound to the wrong list is expensive to notice.

**A reference was given:**
- ObjectId → `get_solution(solution_id=<arg>)`. Anything else → `list_solutions(query=<arg>)`.
- 0 matches → stop, listing what is available.
- >1 → picker: *"Multiple matches: [1] `<name>` (`<slug>`, `<id>`) [2] … Pick a number."*
- 1 → confirm, then fetch it.
- 404 / 403 → stop with *"`<ref>` not found or you're not a Member."*

**Blank — list instead of asking.** `list_solutions()` with no query:

- **Projects returned** → picker, with a final row `None of these — create a new one`.
- **Nothing returned, or that row picked** → print the create instructions for this tracker and stop. Nothing is written.

```
Create it in the portal:

  1. Solution Explorer → New Solution
     name · one-line description · environments (dev · staging · prod)
  2. Copy the project id — the 24-character string in the address bar
  3. Add one app per repository
     web application · backend api · mobile application · fullstack · workflow
     One app = one repo. This decides how a feature splits into sub-tasks later.
  4. Connections tab — drag each app on, wire them, label every arrow,
     Save, then Build map
  5. Integration tab, per app — paste the GitHub URL, Connect, select the repo,
     set the env branches (dev → develop, staging → staging, prod → main), Save

Then:  /jetrix:init <project-id>
```

**The reference is optional on every tracker.** `--tracker=jira` on its own lists that tool's projects exactly as a blank `/jetrix:init` lists Solutions; passing the key is only a shortcut past the picker.

**On any other tracker, steps 3–5 do not exist** — there are no apps, no connections tab and no integration tab. Print only: create the project in that tool, note its key, then `/jetrix:init --tracker=<name> <key>`. The repo paths and dev branches are asked at §9 instead.

Capture the project: id, name, slug, description, type, environments.

### 5a. Lock the container — where features will actually be created

The project is selected. **Issues are not created in it**; they are created in a container under it, and that is the
ref every later push and pull targets. Skipping this is how a ClickUp bind succeeds and then
`/jetrix:push feature` fails with nowhere to put anything — a task cannot exist outside a List.

Call `mapping.resolve_container(project_ref)` and offer what comes back, plus one more row:

```
Where should features go in Supplier Platform?

  [1] Backlog                       48 items
  [2] Delivery OS                   0 items
  [3] Sprint Board                  12 items

  [n] Create a new one — "delivery-os"      ← default, named after this workspace

Pick a number:
```

- **Existing picked** → record it.
- **Create picked** → `mapping.create_container(project_ref, name)`. Default the name to the workspace slug, which is
  what Jetrix already does, so an issue's container says which workspace produced it.
- **`create_container: null`** → offer only the existing rows, and if none fit, print where to create one in that
  tool and stop. Nothing is written — a half-bind is worse than no bind.
- **`resolve_container: null`** → that tracker files issues straight into the project. Record
  `container_kind: none` and set `container_ref` **equal to `project_ref`**, so no consumer has to branch.

Record all three, and print `container_path` in the bind summary — `901203847` tells nobody which list their
features just landed in:

```yaml
container_ref:  "901203847"
container_path: "Acme / Delivery / Supplier Platform / Delivery OS"
container_kind: list
```

**On Jetrix this step asks nothing.** The container is the MC List named after `solutionSlug`, resolved or created by
`/jetrix:push feature` §3a exactly as it already is. Record it so `project.json` has the same shape on every tracker.

**A refresh never re-asks.** `container_ref` is preserved like `mapping` and `status_map` — re-deriving it would
silently move an existing workspace's features to a different list on the next run.

## 6. Soft workspace-name check

**Jetrix only** — other trackers have no slug to compare against.

Compare `solutionSlug` against workspace folder basename (normalized: lowercase, spaces → dashes). Mismatch → warn and confirm; never hard-fail. This is a nudge, not a rule.

## 7. Fetch full project context — ONE call

**Jetrix only** (`capabilities.apps: true`). Other trackers have no app/env/repo records to fetch — skip §7 and §7a entirely and go to §7b with `apps: []`; §9 fills them.

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

**Jetrix only** — other trackers have no app records; §9 collects the repos instead.

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

## 7b. Confirm the project with the user before binding

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
  "tracker": {
    "provider": "jetrix",
    "mcp": "project-mcp",
    "project_ref": "<Solution._id | project key | folder id — the LOCKED project>",
    "project_path": "<the human-readable path the picker walked>",
    "container_ref": "<MC List id | ClickUp List id | epic key — where issues are created>",
    "container_path": "<the same path, plus the container>",
    "container_kind": "list",
    "capabilities": { "apps": true, "tabs": 7, "documents": "scope-mcp" },
    "mapping":    null,
    "status_map": null
  },
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

**Idempotency:** on refresh, merge tracker-sourced fields (name, slug, description, apps[], env_branches). Preserve `bound_at`, `tracker.mapping` and `tracker.status_map` — those were confirmed once and are not re-derived. Never write secrets.

**On any other tracker** the `tracker` block carries that tool's values instead — `provider`, the `mcp` name §2b recorded, its `project_ref`, `capabilities.apps: false`, `tabs: 1`, `documents: "none"`, plus the `mapping` and `status_map` confirmed at §2c. The top-level `solution*` fields stay empty and `apps[]` is filled from §9.

**Reports are a Jetrix capability, not a separate binding.** `capabilities.documents` is `scope-mcp` only on Jetrix, and that alone decides whether `scope.html` publishes to Dashboard → Reports. On any other tracker it is `none`: the HTML is written locally and every report step prints the path and the serve line instead. No second project to pick, nothing to ask.

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

**When `capabilities.apps` is `false`** there is no app list to walk, so ask for the repos directly and take the dev branch in the same breath — that tracker has no Integration tab to hold it, and `/dev:build` branches from `dev` while `/dev:commit` defaults its PR base to it:

```
Which repos does this project cover? One per line, blank to finish.

  D:\work\inhouse-server      dev branch? [develop]
  D:\work\inhouse-client      dev branch? [develop]
```

Each answer becomes an `apps[]` entry — name from the folder, `env_branches.dev` from the answer — plus its `repolocation.json` row keyed by the same generated id.

### 9a. Then draw the connection map — **only when `capabilities.apps` is `false` and there are 2+ repos**

Jetrix gets `connection-map.md` from the portal's Connections tab. No other tracker has one, and the wiring cannot be inferred later — `/tl:code-map` reads each repo in isolation, so a mobile API call with no declared backend counterpart comes out unresolved and re-mapping is the only fix. Ask now, while the repos are already on screen:

```
How do these repos talk to each other?

  inhouse-client  →  inhouse-server    what does it carry? [REST /api/v1]
  inhouse-mobile  →  inhouse-server    what does it carry? [REST /api/v1]

  Any external services? (Stripe, Twilio, a partner API — blank to skip)
```

Offer every ordered pair once, default the label to `REST`, and accept blank for *they do not talk*. Write the answers to `.jetrix/connection-map.md` in the same shape the portal's Build map produces — each app and its role, the wiring edges with what each carries, the auth boundary, and external integrations — so every consumer reads one format whatever the tracker.

**The label is the useful part.** An unlabelled edge says two repos talk but not how, which is the half that `tl-read-code-context` needs to start a cross-repo trace.

A single repo has nothing to wire — skip this entirely. Re-run it any time with `/jetrix:init <project-ref> refresh`, which re-offers the pairs with the current answers as defaults.

From here nothing downstream can tell the difference.

## 10. Pull the connection-map — ONLY if the portal has built one

**Jetrix only.** No other tracker has a Connections tab, so skip §10 entirely — §9a already wrote `connection-map.md` from the user's own answers, and there is nothing to pull.

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
  <ONE action — see below. Never a menu of roles.>
```

**Name one next step, chosen from what the bind actually found.** A list of every role's entry point is not a next step; it is a menu, and it puts the decision back on someone who just asked the command to tell them.

| What the bind found | Print |
|---|---|
| repos on disk, none mapped | `/tl:code-map` — and why: until a repo is mapped, code questions are answered by searching source, and `/dev:build` cannot start because Stage 0 needs `shared-context/coding-standards.md`, which the map authors |
| repos all mapped | `/ba:scope add "<where your client material lives>"` |
| no apps, or no repo linked | the portal step, then `/jetrix:init <project-ref> refresh` |
| no apps and no client material yet | `/ba:scope` — discovery needs no repos |

Where two are genuinely available — repos to map **and** material to scope — lead with the mapping and offer the other on one line beneath it. They are independent tracks, so neither blocks the other.

**One ordering rule overrides the table, on Jetrix.** With **more than one repo and no connection map**, Build map comes before `/tl:code-map` — the map reads each repo in isolation, so without the wiring a mobile API call has no declared backend counterpart and the cross-repo links come out unresolved rather than wired. Say so rather than listing both as equal gaps:

```
Next
  1 · portal → Connections → wire the 3 apps, Save, Build map
  2 · /jetrix:init <project-id> refresh
  3 · /tl:code-map

  Mapping before the wiring exists means every cross-repo link
  comes out unresolved, and re-mapping is the only fix.
```

A single-repo Solution has nothing to wire, so it goes straight to `/tl:code-map`. **On any other tracker this never arises** — §9a already drew the map from the user's own answers, so mapping can start immediately.
```

**Report what is missing, then carry on — never refuse over a gap.** A bind against a project with no apps, no connection map or no linked repo is a normal mid-engagement state, so name each gap and the step that fills it, and close with the exact line to run afterwards:

```
Gaps:
  · no apps on this project            portal → add one per repo
  · Admin panel has no linked repo     portal → that app → Integration tab
  · connection-map not built           portal → Connections → Build map

  Pick them up with:  /jetrix:init refresh
```

**A repo with no local path gets this block, verbatim, wherever it is hit.** It is the most common gap and the one that
stops the most commands — `/tl:code-map` cannot read the repo, `/dev:build` cannot branch in it, `/dev:commit` cannot
push from it — so every one of them prints the same two lines rather than its own wording:

```
Inhouse-server has no local path on this machine.

  /jetrix:init refresh        re-asks for it, and re-fetches anything else
                              the project has gained since the bind
```

On Jetrix the refresh also re-pulls apps, repo links and env branches from the Solution, so a repo linked in the portal
since the bind needs nothing typed. On any other tracker there is nothing upstream to fetch — the refresh simply
re-asks the paths, branches and wiring from §9/§9a with the current answers as defaults.

The one thing that does stop the run is a missing MCP for a non-default tracker (§2b) — there is nothing to bind to, so nothing is written.

Suppress the `[scaffold only]` rows from the printed layout when `scaffolded=false`; instead print one line: `.jetrix/  (delivery-os tree not seeded — run /delivery-os:init to fill it in)`.

Keep it idempotent — a rerun for the same solutionId refreshes without clobbering hand-edits, migrates the connection-map to the new path if needed, re-attempts the connection-map download if the last run failed, and re-runs the scaffold seed (which is itself idempotent) to fill in any missing files.
