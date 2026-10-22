# /jetrix:init — creating apps and confirming the bind

**Jetrix only.** Other trackers have no apps; their repo paths are asked at §14 instead.

## 7a. If `apps[]` is empty — interactive app creation (no portal visit needed)

**Jetrix only** — other trackers have no app records; §13 collects the repos instead.

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

- `continue` (default) → proceed to §15 with `apps[]` that have empty repos / envs — the fields exist as nulls, the teammate fills them via the portal later, and next `/jetrix:init <slug>` will pick up the changes.
- `wait` → halt with `OK — finish repo linking + env branches in the portal, then re-run /jetrix:init <slug> to bind.` and stop.

Once the loop exits (either path), **re-fetch the bundle** with `project_get_solution_bundle` so §16 writes `project.json` with the freshly-created apps (plus any repos/envs the teammate DID complete during the portal step before typing `continue`). Do NOT try to hand-merge — one clean re-fetch is simpler and self-verifying.

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

- `Y` (default on empty) → continue to §16.
- `n` → exit cleanly with `Cancelled — nothing written.`
- Anything else → re-prompt once, then bail.

Show the resolved `workspace_root` explicitly so the teammate sees exactly where the binding will land. This catches both wrong-Solution and wrong-directory typos at the same gate.
