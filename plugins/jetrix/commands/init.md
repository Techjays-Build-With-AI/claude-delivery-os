---
description: Bind the current workspace to a project in your tracker AND scaffold the delivery-os working tree in one command. Jetrix is the default; pass `--tracker=<name>` to bind against any tool whose MCP you have registered — the command finds that MCP, maps its tools once, and everything downstream is identical. The project reference is required to bind: with none, it prints how to get one (or create one) and stops without writing or calling anything. Writes `.jetrix/project.json` (gitignored) with solution + apps + env config + GitHub install info, `.jetrix/cache/repolocation.json` (gitignored) with per-app local repo paths, and pulls the Solution's `connection-map.md` (if built). Then seeds the minimum working tree — `cache/` and `shared-context/decision-log.md`, the same four files `/delivery-os:init` writes, invoked inline as the final step. Every other folder is created by the command that writes into it. Pass `--skip-scaffold` to bind only. Accepts the Solution ObjectId or slug/name — auto-detects. First MCP call triggers Claude Code's OAuth flow (one-time per teammate per machine). Idempotent — re-run to refresh Jetrix-sourced fields without clobbering hand-edits.
argument-hint: "[project-ref] [--tracker=<name>] [refresh] [--skip-scaffold]"
---

# /jetrix:init

Bind the **current workspace** (cwd) to a Jetrix Solution and scaffold the delivery-os working tree in one shot. Writes the Jetrix wiring (`.jetrix/project.json`, `.jetrix/cache/`, `.jetrix/connection-map.md`) then invokes `/delivery-os:init` inline as its final step, so a teammate goes from empty folder to ready-to-work with one command. Pass `--skip-scaffold` to bind only; `/delivery-os:init` can be run later to fill in the tree.

After a normal run the workspace looks like:

```
<workspace>/
└── .jetrix/                    ← ENTIRELY gitignored (whole folder)
    ├── project.json            (this command writes this)
    ├── connection-map.md       (this command writes this if the portal built one)
    ├── cache/                  (repolocation.json + sync-state.json)
    └── cache/ shared-context/decision-log.md              (seeded by default; skip with --skip-scaffold)
```

**Layout note (v2.0):** Everything sits at `.jetrix/` root — no `<solutionSlug>/` wrapper. Role folders (`ba/`, `tl/`, `qa/`, `doc/`) hold each role's outputs; `features/` holds per-feature bundles that BA, TL, and Dev all write into; `shared-context/` holds cross-role docs (project profile, glossary, decision log). See `delivery-os-conventions` for the full contract.

Use the LOCAL MCP tool `project-mcp` registered in `~/.claude/settings.json` or workspace `.mcp.json`. Never call server URLs directly.

## How this command is laid out

Fourteen steps, in order. **Run them in order** — later ones read what earlier ones wrote, and the four that
live in their own file are the long self-contained ones:

| Step | Lives in |
|---|---|
| 3 · Migrate the layout | `references/init/migrate.md` |
| 4 · Resolve the tracker | `references/init/tracker.md` |
| 9 · Create apps, then confirm | `references/init/apps.md` |
| 13 · Pull the connection map | `references/init/connection-map.md` |
| 14 · Report | `references/init/summary.md` |

**Read a reference file only when you reach its step**, and only if that step applies — three of the five are
Jetrix-only and are skipped outright on another tracker, and §3 is skipped on any fresh workspace.

**If a reference file for a step you are actually going to run cannot be read**, halt and say so; never
reconstruct its flow from memory. Name the file and say that nothing was written.

**A missing file for a step that does not apply is not an error.** Do not open it, do not mention it. A run
that stops before doing anything, over a step with nothing to do, is the worst outcome available — the user
gets a wall of plugin-internals instead of the thing they asked for.

**If several reference files are missing, the plugin install is stale rather than the repo broken.** Say that
once, plainly — *"this command is newer than the installed plugin; update it from the marketplace and
re-run"* — rather than reporting each file as its own failure.

Read the `delivery-os-conventions` skill first if it is not already in context.

## 1. Preflight — verify we are initializing in the right directory

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

3. **Do not ask yet.** Resolve and hold `workspace_root`, and carry on to §2.

   The confirmation happens at **§11**, once the project is chosen and the command knows it is actually going
   to write. A bare `/jetrix:init` on an account with no projects ends at §7 with *"here is how to create
   one"* — asking the user to approve a folder before discovering that costs them a decision for nothing.

   **Ask immediately only for the two red flags above**: a `src`/`dist`/`node_modules`-style basename, or an
   ancestor that already has `.jetrix/`. Those mean the user is probably in the wrong place, and every later
   step would be wasted on the wrong directory.

Treat `workspace_root` as immutable for the rest of the command. Every file path is built as
`<workspace_root>/.jetrix/...`.

**Nothing is written before §12.** §3–§11 read, list and ask; the first byte on disk is `project.json`. A run
that stops anywhere before that leaves the folder exactly as it found it, and says so.

## 2. Parse arguments

`$ARGUMENTS` may carry, in any order:

- **Project reference** (**required to bind** — blank prints the guide and stops, writing nothing):
  - Matches `/^[a-f0-9]{24}$/` → a Jetrix Solution **ObjectId**.
  - Otherwise → a slug, name, or the tracker's own project key.
- **`--tracker=<name>`** (optional, default `jetrix`): the project-management tool holding the tasks.
- **`refresh`** (optional): re-fetch into an existing bind. See §9.
- **`--skip-scaffold`** (optional): skip the §15 tree seed.

## 3. Migrate the layout — only if there is one

**Check first, read second.** Look for `<workspace_root>/.jetrix/`:

- **It does not exist** → this is a fresh workspace. There is nothing to migrate. **Skip this step entirely —
  do not open the reference file** — and continue to §4.
- **It exists, and holds `requirements/`** → already current. Skip.
- **It exists without `requirements/`** → there is a layout to move. Execute
  `plugins/jetrix/commands/references/init/migrate.md` verbatim, before any tracker call.

The gate is here rather than inside the file because a step with nothing to do must not need a file read to
discover that. A first-ever `/jetrix:init` is the most common run there is, and it has nothing to migrate.

## 4. Resolve the tracker

Execute `plugins/jetrix/commands/references/init/tracker.md` verbatim. It decides which tool this workspace
binds to and records how to call it — `provider`, `mcp`, the eleven mapping keys, `status_map`, `capabilities`.

**Everything after this step branches on `capabilities`, never on the provider name.**

## 5. Sign in — the first MCP call does it

The first invocation of any MCP tool triggers Claude Code's OAuth flow. Browser opens → the teammate signs in → consent → token cached locally. The three Jetrix MCPs share one auth server, so a single sign-in covers them; another tracker's MCP has its own.

If OAuth is cancelled → stop with *"Sign-in failed. Rerun `/jetrix:init`."*

## 6. Rerun handling

If `<workspace_root>/.jetrix/project.json` already exists:

- **`refresh` passed** → re-fetch without asking. **The reference is optional** — it is already in `project.json`, so bare `/jetrix:init refresh` is the canonical form and the one to print whenever a gap is reported. It works the same on every tracker, because the provider is recorded too.
- **Same `project_ref`, no `refresh`** → ask *"Workspace already initialized for `<name>` (`<ref>`). Refresh project details? [y/n]"*. On yes, re-fetch. On no, stop.
- **Different `project_ref`** → hard STOP. *"This workspace is already initialized for `<other-name>` (`<other-ref>`). Use a separate workspace folder for each project."*

A refresh re-fetches the project, its apps and their env branches, and re-attempts the connection map. It **preserves** `bound_at`, the repo paths already given, `tracker.mapping` and `tracker.status_map`.

**Preserving a settled answer is right; preserving a blank is not.** After the re-fetch, walk what is
still missing and offer to fill it — once, as one prompt, not per app:

| Still missing after re-fetch | What to do |
|---|---|
| An app whose `repolocation.json` row is `"SKIPPED"` | Offer it again, with `skip` still a valid answer. Someone who skipped the mobile repo in January may have cloned it in March. |
| An app with no `env_branches.dev` | Ask for the branch, defaulting to `develop`. `/dev:build` cuts from it and `/dev:commit` defaults its PR base to it, so a blank here is a decision deferred to the worst moment. |

```
Refreshed 4 apps. Two are still incomplete — fill them in now?

  scheduled-service   repo path?   [skip]
  mobile              dev branch?  [develop]
```

**This is not re-asking.** `container_ref`, `mapping` and `status_map` are preserved exactly as §12
says, and an answer already given is never questioned again. The only thing offered is the value that
is still blank — and a blank is not an answer, it is an absence that nothing else will ever fill.
A declined offer writes `SKIPPED` again and the refresh completes; this never blocks.

**Why it is worth a prompt.** A missing repo path is not felt at init. It is felt at `/dev:plan`,
which logs `<repo> has no local path` and carries on, and then at `/dev:build`, where a feature
spanning that repo halts — far from the cause, and usually in front of someone who was not there when
it was skipped.

## 7. Resolve the project

On `jetrix` the calls are `project-mcp`'s; on any other tracker they are `mapping.resolve_project`. The shape is the same.

**No reference — walk `browse`.** One picker per level, names only, never ids. The user chooses `Acme` → `Delivery`
→ `Supplier Platform`; the id behind it is never typed and never shown unless something fails. A one-element `browse`
is a single picker, which is the Jetrix and Jira case.

**`browse` stops at the project — the thing that already exists.** It does not walk into the list or epic that will
hold the features; §8 does that, because that one may have to be created and this step never creates anything.

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

**Blank — print the guide and stop. Do not list. Do not ask.**

**Make no MCP call.** A bare `/jetrix:init` is not "help me choose from what I have" — someone who knew which
project they wanted would have typed it. It means *"I do not know what to do here."* The answer to that is
instructions, not a list of 97 Solutions and a recommendation guessed from the folder name.

Print this verbatim and **stop. Nothing is written, no project is resolved, no tracker is called.**

```
/jetrix:init binds this folder to one project. It needs the project's id.

── Already have a project ──

  1. Open the portal          https://app.jetrix.ai/
  2. Solution Explorer → open your Solution
  3. Copy the id — the 24-character string in the address bar
  4. Run:                     /jetrix:init <project-id>

     A name or slug works too:  /jetrix:init acme-timesheet

── Starting a new project ──

  1. Solution Explorer → New Solution
     name · one-line description · environments (dev · staging · prod)

  2. Add one app per repository
     web application · backend api · mobile application · fullstack · workflow
     One app = one repo. This is what decides how a feature splits into
     sub-tasks later, so it is worth getting right now.

  3. Connections tab — drag each app onto the canvas, wire them, and label
     every arrow (REST /api/v1, WebSocket events, S3 uploads). Save, then
     Build map.
     Skip this and /tl:code-map reads each repo in isolation: a mobile API
     call has no declared backend counterpart, and re-mapping is the only fix.

  4. Integration tab, per app — paste the GitHub URL, Connect, pick the repo,
     set the env branches (dev → develop, staging → staging, prod → main), Save.

  5. Copy the project id and run:   /jetrix:init <project-id>

── Not using Jetrix ──

  1. Register that tool's MCP, once per machine:

       claude mcp add --transport http <name> <its-mcp-url>

       Jira:  https://mcp.atlassian.com/v2/mcp

  2. Bind. You can name the project, or let it walk you there:

       /jetrix:init --tracker=jira                 pick from a list
       /jetrix:init PAY --tracker=jira             straight to it

     What to type — the PROJECT, not a ticket. Open it in that tool and read
     the URL, the same way you would read a Solution id out of the Jetrix
     portal:

       Jira       .../projects/PAY/...            →  PAY
                  the project key. It is also the prefix on that project's
                  tickets, which is why PAY-14 belongs to PAY.

       ClickUp    .../v/li/901203847              →  901203847
                  the List id. Tasks live in a List, so that is the level
                  that binds.

       Azure      .../MyOrg/Timesheet/_boards/... →  Timesheet
                  the project name.

     Don't know it? Leave it out. It walks the levels that tool actually has
     — for ClickUp that is Workspace → Space → Folder → List — showing names,
     never ids, and never guessing which one you meant.

Nothing has been written. Run the command again with an id when you have one.
```

**Print the portal URL for the environment this machine is registered against** — `https://app.jetrix.ai/` for
production, `https://staging-jetrix.web.app/` for staging. A Solution created in the staging portal does not
exist to production MCPs, and the failure surfaces much later as "project not found" with no hint why.

**No picker, and no recommendation.** Matching a folder name to a Solution name is a guess, and a confident
guess in a bind step is expensive — a workspace bound to the wrong project is not noticed until features start
appearing somewhere nobody is looking.

**On another tracker, blank browses instead.** The guide above exists because creating a Jetrix Solution is a
portal flow we have to explain, and because an account can hold a hundred of them. Neither is true elsewhere:
someone who registered the Jira MCP has already chosen their tool, and what they may genuinely not know is an
internal id — a ClickUp List id is a long number buried in a URL. `browse[]` was built for exactly that.

So `--tracker=jira` with no reference **walks `browse[]`** (§7's picker, names only, one level at a time), and
`--tracker=jira PAY` skips straight past it. What it must never do is guess: no "Recommended" row, and no
matching a folder name against a project name.

**On any other tracker, steps 3–5 do not exist** — there are no apps, no connections tab and no integration tab. Print only: create the project in that tool, note its key, then `/jetrix:init --tracker=<name> <key>`. The repo paths and dev branches are asked at §13 instead.

Capture the project: id, name, slug, description, type, environments.

## 8. Lock the container — where issues will actually be created

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
`references/push/feature.md` §3a exactly as it already is — a section of that file, not of this one. Record it so `project.json` has the same shape on every tracker.

**A refresh never re-asks.** `container_ref` is preserved like `mapping` and `status_map` — re-deriving it would
silently move an existing workspace's features to a different list on the next run.

## 9. Confirm the workspace name

**Jetrix only** — other trackers have no slug to compare against.

Compare `solutionSlug` against workspace folder basename (normalized: lowercase, spaces → dashes). Mismatch → warn and confirm; never hard-fail. This is a nudge, not a rule.

## 10. Fetch the project context — ONE call

**Jetrix only** (`capabilities.apps: true`). Other trackers have no app/env/repo records to fetch — skip §14 and §15 entirely and go to §15 with `apps: []`; §13 fills them.

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

## 11. Create apps, then confirm the bind

Execute `plugins/jetrix/commands/references/init/apps.md` verbatim — **Jetrix only**, and only when `apps[]`
came back empty. On any other tracker there are no apps: skip to §16, and §13 asks for the repo paths.

## 11.5. Confirm the workspace, now that there is something to bind

The project is resolved, the container is locked, the repo paths are known. **This is the first moment a
confirmation is worth asking for**, because everything it approves is now concrete:

```
Bind this workspace?

  Workspace   C:\Users\selva\plugin-test
  Project     Acme / Delivery / Supplier Platform
  Container   Delivery OS          (12 issues)
  Tracker     jetrix

  Writes      .jetrix/project.json · cache/ · shared-context/decision-log.md

  [Y/n]
```

`n` → `Cancelled — nothing written.` and stop. Nothing has touched disk yet, so that is literally true.

## 12. Write `<workspace_root>/.jetrix/project.json`

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

**On any other tracker** the `tracker` block carries that tool's values instead — `provider`, the `mcp` name §6 recorded, its `project_ref`, `capabilities.apps: false`, `tabs: 1`, `documents: "none"`, plus the `mapping` and `status_map` confirmed at §6. The top-level `solution*` fields stay empty and `apps[]` is filled from §13.

**Reports are a Jetrix capability, not a separate binding.** `capabilities.documents` is `scope-mcp` only on Jetrix, and that alone decides whether `scope.html` publishes to Dashboard → Reports. On any other tracker it is `none`: the HTML is written locally and every report step prints the path and the serve line instead. No second project to pick, nothing to ask.

### What this looks like filled in

**Jetrix** — the Solution id goes in `project_ref`; the MC List that holds the features is the container:

```json
"tracker": {
  "provider": "jetrix",
  "mcp": "project-mcp",
  "project_ref":    "6a94fe0ebc48d4e7d1cab15b",
  "project_path":   "Novacore Timesheet",
  "container_ref":  "6a61d4b8c9e2a1d3f4e5b6c7",
  "container_path": "Novacore Timesheet / novacore-timesheet",
  "container_kind": "list",
  "capabilities": { "apps": true, "tabs": 7, "documents": "scope-mcp" },
  "mapping": null,
  "status_map": null
}
```

**Jira** — `project_ref` is the key you read out of the URL. The container is an epic, because that is where
this workspace's features will live:

```json
"tracker": {
  "provider": "jira",
  "mcp": "atlassian",
  "project_ref":    "PAY",
  "project_path":   "Payments",
  "container_ref":  "PAY-12",
  "container_path": "Payments / Delivery OS",
  "container_kind": "epic",
  "capabilities": { "apps": false, "tabs": 1, "documents": "none" },
  "mapping": {
    "browse":            ["jira_get_visible_projects"],
    "resolve_project":   "jira_get_project",
    "resolve_container": "jira_search_epics",
    "create_container":  "jira_create_issue",
    "create_issue":      "jira_create_issue",
    "update_issue":      "jira_update_issue",
    "read_issue":        "jira_get_issue",
    "child_issues":      "jira_search",
    "comments":          "jira_get_comments",
    "attachments":       "jira_get_attachments",
    "set_status":        "jira_transition_issue",
    "put_document":      null
  },
  "status_map": {
    "todo":           "To Do",
    "readyForDev":    "To Do",
    "agentExecuting": "In Progress",
    "inProgress":     "In Progress",
    "devReview":      "In Review",
    "blocked":        "Blocked",
    "done":           "Done"
  }
}
```

**ClickUp** — `browse[]` walked four levels, so `project_path` records all of them. A task cannot exist outside
a List, so the List is both what the walk ended on and the container:

```json
"tracker": {
  "provider": "clickup",
  "mcp": "clickup",
  "project_ref":    "90120318",
  "project_path":   "Acme / Delivery / Payments",
  "container_ref":  "901203847",
  "container_path": "Acme / Delivery / Payments / Delivery OS",
  "container_kind": "list",
  "capabilities": { "apps": false, "tabs": 1, "documents": "none" },
  "mapping": {
    "browse": ["clickup_get_workspaces", "clickup_get_spaces",
               "clickup_get_folders", "clickup_get_lists"],
    "resolve_container": "clickup_get_lists",
    "create_container":  "clickup_create_list",
    "create_issue":      "clickup_create_task",
    "put_document":      null
  },
  "status_map": {
    "todo":           "to do",
    "readyForDev":    "to do",
    "agentExecuting": "in progress",
    "inProgress":     "in progress",
    "devReview":      "in review",
    "blocked":        "blocked",
    "done":           "complete"
  }
}
```

**What is absent on a non-Jetrix tracker, and must not be invented:** `solutionId`, `solutionSlug`,
`solutionName`, `environments` and `apps[]`. Those come from a Jetrix Solution and have no equivalent
elsewhere — which is what `capabilities.apps: false` means. The repo paths and dev branches §13 asks for are
written to `cache/repolocation.json` instead.

**`project_path` and `container_path` exist to be printed.** `901203847` tells a reader nothing; *"Acme /
Delivery / Payments / Delivery OS"* tells them whether the workspace is bound to the right place — and a
workspace bound to the wrong one is expensive to notice.

**`status_map` is `null` on Jetrix** because nothing needs translating: `status` already holds Mission Control’s own seven values, so push sends it unchanged. On every other tracker the map carries **exactly those seven keys** — `todo`, `readyForDev`, `agentExecuting`, `inProgress`, `devReview`, `blocked`, `done` — and nothing else; `phase` is local and never sent. Several keys pointing at one of the tracker’s statuses is normal. A key left out is not: a task reaching that status mid-run has nothing to push, and the board silently stops moving. `mapping` follows the same rule — `null` on Jetrix, filled on every other tracker
by §4's discovery, confirmed by a human once. A refresh preserves both; it never re-derives them.

## 13. Ask for repo paths, then the connection map

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

## 14. Pull the connection map

Execute `plugins/jetrix/commands/references/init/connection-map.md` verbatim — **Jetrix only, and only when
the portal has built one.** On any other tracker §13 already wrote `connection-map.md` from the user's own
answers; running this would overwrite a human's work with a fetch that cannot succeed.

## 15. Gitignore and seed

Ensure `<workspace_root>/.gitignore` includes `.jetrix/` (the entire folder — nothing under it is committed). Create the file if missing; append idempotently. If a prior version added only `.jetrix/cache/`, replace with `.jetrix/`.

If `skip_scaffold=true` → print `· Skipped delivery-os scaffold — run /delivery-os:init later to seed the working tree.` and continue to §16.

Otherwise, invoke the same seeding logic as `/delivery-os:init` inline. `.jetrix/` already exists (created in §16), so `/delivery-os:init`'s precheck passes. The seed is idempotent — files that already exist are never overwritten. It performs:

**Execute `/delivery-os:init` §6 verbatim. Do not restate it here.** It creates three directories and four
files — `cache/repolocation.json`, `cache/sync-state.json`, `shared-context/decision-log.md`, and
`project.json` which §16 already wrote. Nothing else.

Every other folder is created by the command that first writes into it, with content. That is why this step is
four lines rather than a tree: there is no tree to seed. `requirements/` appears when `/ba:scope` runs, `qa/`
when `/qa:audit` runs, `code-map-registry.md` when `/tl:code-map` runs.

**Two copies of a spec drift.** This step used to restate the whole tree and the whole template table, and the
two copies disagreed within one rework — `/delivery-os:init` had been cut to 3 directories while this one still
seeded 23, so the normal path kept producing the old tree and the rewrite was dead letter. One spec, one place.

Set `scaffolded=true` on success (for the §16 summary line).

## 15a. Pull the shared delivery context

**A bind that scaffolds empty folders leaves the second person worse off than a clone.** The repos carry their
own `context/code-context/` and test harness through git; what does not travel is everything workspace-level,
and two of those are hard gates — `/dev:build` Stage 4 on `qa/quality-gates.md`, Stage 0 on
`shared-context/coding-standards.md`. Without them a teammate who just cloned a fully-built repo is refused a
build over files that describe work already finished.

Run the Tier A pull — `references/pull/scope.md` with no requirement slug. It fetches `connection-map.md`,
`code-map-registry.md`, `qa/quality-gates.md`, every `qa/<repo>-setup.md` and `shared-context/coding-standards.md`,
and nothing else. No requirement's scope, registers or ledger: those are opt-in.

`code-map-registry.md` matters as much as the gates. `/tl:code-map` step 9 mints area tokens **reusing the ones
already in the registry so ids never collide across repos**; a teammate mapping without it mints fresh tokens
against a tree that already carries someone else's, and nothing detects the divergence.

Not on Jetrix, or nothing pushed yet → say so in one line and carry on. **Never fail the bind over the pull.**

**Then name the requirements the Solution holds**, read from the manifest paths (`requirements/<slug>/...`), so
the next step is a command the user can run rather than a slug they have to guess:

```
This Solution has 2 requirements:
  asset-management
  billing-portal

Next:
  Joining an existing requirement?  Pull it first —
      /jetrix:pull scope asset-management

  Starting a new one?
      /ba:scope add "<where your client material lives>"
```

With no requirements yet, drop the list and keep only the `/ba:scope` line.

## 16. Report

Execute `plugins/jetrix/commands/references/init/summary.md` verbatim. It chooses **one** next step from what
the bind actually found — never a menu of every role.
