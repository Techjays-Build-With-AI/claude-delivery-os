---
description: Reverse-map an existing codebase into a committed, index-first code-context tree — read the real repository and derive its pages, endpoints (contract, validation, business logic, and every database object they touch) and database objects grouped by kind (tables, collections, views, procedures, functions, triggers) into domain-organised markdown units with semantic layer indexes. The tree is written inside the mapped repo at `<repo>/context/code-context/` and committed on its own branch with a PR against the branch that was mapped, so a few hundred generated files are reviewed rather than landing on dev unseen; a workspace registry ties multiple repos together so later forward planning reuses the as-built units. Read-only on the code; every unit carries a confidence and a source-file citation.
argument-hint: "<repo=<path> | (blank = current workspace)> [env=Development|Prod|...] [layers=frontend,backend,database] [scope=<subpath>] [domains=<a,b>] [refresh=full|changed]"
---

# /tl:code-map

You onboard an **existing codebase** into Delivery OS by deriving a **code-context tree that lives inside that repository** — every page, endpoint and database object, grouped by business domain, with semantic indexes that let an agent find the right file in three cheap reads. Delegate the work to the **`tl-agent`** subagent, which runs `tl-code-map` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain:

- **`repo=`** — path to the product repository to map (default: the current workspace / project repo). Repeatable, or comma-separated, to map several repos in one run (e.g. a separate frontend and backend repo) — each gets its own in-repo tree and a row in the workspace registry.
- **`layers=`** — `frontend`, `backend`, `database`, comma-separated. Default: all three, minus any the repo clearly doesn't contain.
- **`scope=`** — a subpath/module, to map a slice of a large monorepo at a time.
- **`domains=`** — restrict the run to named business domains (`domains=billing,subscription`) once a first pass has established the domain decomposition. Useful for re-mapping one area after a change.
- **`refresh=`** — `full` (re-derive everything; default on a first run) or `changed` (reconcile only units whose source files changed since the `mapped_from_commit` recorded in the existing tree). `changed` is the fast path for a re-run.
- **`env=`** — the Jetrix environment whose per-app branches to align each repo to before mapping (e.g. `env=Development` → each app's `env_branches.Development` branch, typically `dev`; `env=Prod` → typically `main`). Skips the interactive env prompt in §2. Any environment name declared in `.jetrix/project.json` `environments[]` is accepted.

If there's no resolvable repository, say so and ask the user to point you at one — there's nothing to map without code.

A repo with no local path is the commonest cause, and the fix is one command — print it rather than a generic error:

```
<repo> has no local path on this machine.

  /jetrix:init refresh        re-asks for it, and re-fetches anything else
                              the project has gained since the bind
```

**Where output goes** — state this back to the user before starting, because it writes inside their repo: the tree is created at **`<repo>/context/code-context/`** — a `context/` folder at the repo root, with `code-context/` inside it, created if the repo has none — intended to be **committed with the code**. If the repo already has a root-level `context/` used by the application, say so and confirm the location with the user before writing rather than mixing tool output into source. Running from a parent workspace over several repos still writes each repo's context into that repo. The only workspace-level file is the registry, `<workspace>/.jetrix/code-map-registry.md`. Nothing else in the repository is touched, and nothing is committed — the user reviews and commits.

## 2. Choose environment and align branches

Read `.jetrix/project.json`. If it exists (typical case — the workspace was bound via `/jetrix:init`):

- **Pick the environment, once for the whole run.** If `env=` was passed as an argument, use it verbatim. Otherwise present the values in `environments[]` (e.g. `Development`, `Prod`) and ask the user which one to map. Store the choice as `chosen_env`. If `chosen_env` is not in `environments[]`, refuse and list the accepted names.

- **For each repo in scope, align its checked-out branch to that environment's branch.** Look the repo up in `apps[]` by `repoUrl` (or `projectSlug` if the caller passed a slug). Then:

  1. **App has `env_branches[chosen_env]` defined** — call the value `expected_branch`. Read the current branch via `git -C <repo> rev-parse --abbrev-ref HEAD`.
     - **Match** → proceed to §3 for this repo.
     - **Mismatch** → tell the user which repo, the current branch, and the expected branch, and ask to switch. If they decline, skip this repo (record `skipped-by-user` with the branch names in the run summary) and continue with the next. If they confirm:
       - Check `git -C <repo> status --porcelain`. **If dirty**, refuse to switch — print the changed files and ask the user to commit or stash first, then re-run. **Never auto-stash and never proceed with a dirty tree.**
       - If clean: `git -C <repo> fetch --prune` then `git -C <repo> checkout <expected_branch>`. Re-check the branch and confirm HEAD moved before delegating.

  2. **App has empty `env_branches` or `env_branches[chosen_env]` is missing** (e.g. an app that isn't wired to env-branch mappings yet in Jetrix). Ask the user which branch to analyze for this repo, showing the current branch as the default. If they accept the default, proceed. If they name a different branch, apply the same dirty-tree check → `fetch --prune` → `checkout` flow as above.

- **If `.jetrix/project.json` is missing**, or the app has no `env_branches`, or the caller passed an ad-hoc
  `repo=<path>`: **ask which branch, per repo. Never map whatever happens to be checked out.**

  ```
  Which branch should the map read?

    Inhouse-server     on  feature/holiday-calendar     ← currently checked out
                       other branches: main · dev · feature/assets · feature/leave

    Inhouse-client     on  dev                          ← currently checked out
                       other branches: main · dev
  ```

  List the real branches from `git -C <repo> branch -a --format='%(refname:short)'`, mark the current one, and
  **default to nothing** — the user types or picks. Then apply the same dirty-tree check → `fetch --prune` →
  `checkout` flow as above.

**The branch is the single most consequential input and must never be assumed.** A map of the wrong branch is
not slightly wrong — it describes a different system, and everything downstream (`tl-feature-planning` (internal) reuse,
`/dev:build` Stage 0, every unit id) is built on it. A silent default here is the most expensive guess this
command can make.

**Map one branch per run.** If the user needs `main` and `dev` mapped, that is two runs — one tree per branch,
each stamped with its own `mapped_from_commit`. Merging two branches' units into one tree produces ids that
match neither.

Record the outcome per repo (`env-aligned` / `switched-from-<old>-to-<new>` / `skipped-by-user` / `env-alignment-skipped-no-project-json`) so §4 can surface it.

## 3. Delegate

Invoke the **tl-agent** subagent. Pass it this instruction:

> Reverse-map the repository at `<repo>` into a committed, index-first code-context tree using the `tl-code-map` skill — follow `references/extraction-guide.md` for how to read each layer, and write the exact files defined in `references/code-context-templates.md`. **Write the tree inside the mapped repository at `<repo>/context/code-context/`** (create the repo's `context/` folder if absent) — not into the workspace and never inside `.jetrix/`, which is gitignored — so it is committed with the code and travels with the repo; the only workspace-level artifact is `<workspace>/.jetrix/code-map-registry.md`. Run it in **three passes**. **Pass A (discovery):** detect the stack (`shared-context/technology-stack.md` if present, else infer); **derive the business domains** using the extraction guide's ladder (module/folder → route prefix → naming → FK clusters) and assign `<AREA>` tokens, reusing tokens already in the registry so IDs never collide across repos; write a per-layer `_overview.md`; load any existing `code-context/` and the registry so you **reconcile, don't duplicate**; then **enumerate every unit from the declarative sources** — an OpenAPI/route manifest for endpoints, the router config for pages, the schema/migration state for database objects **of every kind** (tables, collections, views, stored procedures, functions, triggers) — into `code-context/map-coverage.md`, every row `pending`. **Pass B (detail):** burn the manifest down. **Database objects first**, one file per object in its kind folder (`tables/`, `collections/`, `views/`, `procedures/`, `functions/`, `triggers/`), each with its real structure **and its Business Purpose** — why the business has it, not just its DDL. **Endpoints next**, one file per `METHOD + path` (plus jobs/events/webhooks with their trigger), each recording the **Request** contract, the **Validation** rules *and where each is enforced* (schema middleware / handler check / database constraint), the **Business Logic** as ordered steps, and a **Data Access** table naming every object touched, its kind, the **access mechanism** (ORM · direct query · stored procedure · function · view · repository · cache) and read/write/execute. **Pages next**, one per routed surface, traced through the API client to the endpoints it consumes. Wire every link **both ways** — including object-to-object (view → source tables, procedure → objects touched, trigger → table it fires on and procedure it calls) — with a per-link **confidence** from the shared five-value vocabulary (`Confirmed · Likely · Assumed · Conflicting · Needs Clarification`): `Confirmed` where the code shows it directly, `Likely` for a strong conventional inference, `Assumed` where it's computed or you couldn't follow it through, `Conflicting`/`Needs Clarification` + an open question where the code contradicts itself or is opaque; **never invent** a relationship the code doesn't support. Mint IDs (`PAGE-/EP-/ENT-<AREA>-NN`) on the **same match keys** forward planning uses (route, normalised `METHOD+path`, object name), and keep every `##` heading forward planning defines **verbatim** (`Reads / Writes Entities`, `Behaviour / Business Rules`, `Called by`, `Used by Endpoints`, `Used by Features` = `(as-built)` until a feature links, `Integrations`, `Permissions`, `Status`) — the enhancements are additive sections, never renames — so a later `tl-feature-planning` (internal) reuses and extends these units instead of duplicating them. **Pass C (synthesis):** write the **semantic indexes** — each layer index gets a `## Domain Map` (a few lines per domain: what it is, what kinds of operations/objects live in it, what it touches, when to look elsewhere) **plus** a `## Units` table whose `Summary` cell is copied verbatim from each unit's own `## Summary`; the database index groups by **business domain** in the Domain Map and by **kind** in the unit tables. Then the root `code-context-index.md`, the `README.md` stating the index-first read protocol, and the workspace registry row. Split a layer index into per-domain sub-indexes if it outgrows one pass (~150 rows / ~500 lines). Mark every unit `origin: reverse-mapped` with a `[code › <file>]` Source Reference and a `mapped_from_commit` stamp. Do **not** modify, refactor or run the repository, and **do not commit** — you map; the command commits in §4 once every repo is done, staging only `context/code-context`, do **not** write secrets or customer data into a tree that will be committed, and do **not** author BA features or infer product scope from the code. Run the link-integrity check **including the coverage check (every row `mapped`, `skipped`-with-a-note, or `removed` — no `pending` left) and the index checks (every unit has a Summary, every index row mirrors it, every index has a Domain Map)**, and report any code you couldn't confidently map. Return where the tree was written, units mapped per layer and per database kind (created vs reconciled), coverage (enumerated vs mapped vs skipped), the confidence spread, the domains derived and their area tokens, index and registry deltas, and integrity findings.
>
> Repository: `<repo or current workspace>` · Layers: `<layers or all>` · Scope: `<scope or whole repo>` · Domains: `<domains or all>` · Refresh: `<full|changed>`

When several repos were requested, delegate **one subagent per repo** (they can run concurrently — each writes only into its own repo). Tell each of them explicitly: **do not write the workspace registry — return your registry row and any pending cross-repo links instead.** You then write the registry yourself from the merged rows, resolve the cross-repo page→endpoint links across the now-complete set, and leave genuinely unresolvable ones in the registry's *Pending cross-repo links* table before reporting.

## 4. Commit the tree on its own branch and open a PR

The tree lives **inside the product repo** and is meant to be committed with the code. Finish the job rather
than handing back a chore — but finish it the way every other command does, on a branch of its own.

**Read the mapped branch; never write to it.** §2 chose that branch because it decides what the map
*describes*. Committing onto it is a different act: this run generates hundreds of files, and on `dev` they
would land unreviewed, while on `main` the push is rejected and the run ends holding work it cannot place.

Per mapped repo:

1. **Branch off the branch that was mapped.** Name it after what it holds, with the mapped branch and the
   date, so two runs never collide and the name says what it is:

   ```bash
   git -C <repo> checkout -b context/code-map-<mapped-branch>-<YYYY-MM-DD>
   ```

   Replace `/` in `<mapped-branch>` with `-` (`feature/assets` → `feature-assets`). If that branch already
   exists — a re-run on the same day — append `-2`, `-3`; never force, never reuse.

2. **Stage only the context tree.** Never `git add -A`, never `git add .`:

   ```bash
   git -C <repo> add context/code-context
   ```

   **This matters more than it looks.** A blanket add sweeps up whatever else is dirty in that working tree —
   and a real run of this command found a committed `.env` holding live database credentials. Widening the add
   would commit more of exactly that.

3. **Show what will be committed**, then commit:

   ```bash
   git -C <repo> status --short -- context/code-context
   git -C <repo> commit -m "docs(context): reverse-map as-built code context

   <N> units across <layers> · areas <TOKENS>
   mapped from <mapped-branch> @ <sha>"
   ```

4. **Push the new branch:**

   ```bash
   git -C <repo> push -u origin context/code-map-<mapped-branch>-<YYYY-MM-DD>
   ```

5. **Raise the PR through the four-step ladder** in
   [`stage-8-9-push-pr.md`](../../dev/commands/references/commit/stage-8-9-push-pr.md) §9c — the same one
   `/dev:commit` and `/qa:setup` use. Read it and follow it; do **not** call `gh pr create` on its own.

   | | |
   |---|---|
   | 1 | `gh` CLI, if installed **and** authenticated |
   | 2 | the PAT `git push` already used, via `git credential fill` → `POST /repos/:owner/:repo/pulls` |
   | 3 | the OAuth token in `gh`'s config file, if `gh` was authed on another machine |
   | 4 | a pre-filled `compare/` URL for the user to click |

   **This exists because `gh` is not installed on most machines**, and a run that stops there has done all the
   work and delivered none of it. Step 2 is the one that usually saves it: anyone who pushed over HTTPS
   already has a usable token cached, and that is the same credential step 4 of this section just used.

   Between steps 3 and 4 the ladder **offers to install `gh`** via a detected package manager (scoop / winget
   / brew) through `AskUserQuestion`. Offer it here too, and honour the same rule: **never install without
   explicit confirmation** — it is a persistent change to their machine, and declining is a normal answer
   that costs them one click in a browser instead.

   `--base` is the **mapped branch**. `--title`: `docs(context): as-built code context for <mapped-branch>`.
   The body is the §5 stats block plus every `⚠ Needs you` finding — **put the findings in it.** A committed
   `.env` or an unauthenticated route is exactly what a reviewer should see before merging, and the PR is
   where they are looking.

   **If the repo has a `PULL_REQUEST_TEMPLATE`, that is the skeleton** — same rule and same resolution order
   as `stage-8-9-push-pr.md` §9b.0, including never ticking a checkbox on the author's behalf. A context PR
   is still a PR in their repo, and it is the one most likely to be waved through without reading, so it
   should at least look like the others.

6. **Stay on the new branch.** Do not switch back. `/dev:plan` reads `context/code-context/` from the working
   tree, so the person who ran this has the tree available immediately; everyone else gets it when the PR
   merges. Say both of those things in §5 — a reader who assumes their teammates can already see it is wrong
   in a way that costs an afternoon.

**When a step fails, say so in one line with the exact command, and stop there.** The commit is already safe
locally. Do not force, do not retry, do not switch branches to work around it.

| Failure | What to print |
|---|---|
| Push rejected (no auth, no remote) | the exact `git push` command; the commit is local and intact |
| Ladder reached step 4 | the compare URL, and say the branch **is** pushed — only the PR is outstanding |
| `403` on PR create | the run needs PR-create access to `<owner>/<repo>`; the branch is pushed and safe |

Everything else about PR failure is the ladder's, not this command's — it already decides what to try next
and what to say. Do not add a second set of rules here that can drift from it.

**Nothing outside `context/code-context/` is ever staged, committed or pushed.** If the working tree was dirty
before this ran, it is still dirty after — those changes are the user's and none of this command's business.
§2 already refused to switch branches on a dirty tree, so reaching here means the only thing to commit is
what this run wrote.

**Secrets never reach the tree.** Pass B writes contracts and business purpose, not values. If a credential,
connection string or customer record would land in a unit file, leave it out and raise it as a finding instead
— this tree is about to be pushed to a shared remote.

## 5. Surface the result

**Short, ranked, one next step.** A reader who skims the first six lines must come away knowing whether
something needs them. Everything else is already in the files — link, do not restate.

```
✓ Mapped 2 repos on dev — PR opened for each

  Inhouse-server   15 endpoints · 4 collections      19/19
  Inhouse-client    6 pages                           6/6
  Areas            AUTH · DASH · PROJ · TEAM · TRACK

⚠ Needs you
  1. .env is committed, with live database credentials
     → rotate them, then: git rm --cached .env && echo .env >> .gitignore
  2. None of the 15 server routes check authentication
     Register issues a JWT; nothing verifies it.
  3. Neither repo has a test runner — coding-standards.md has 17 [NEEDS AUTHOR]
     /dev:build refuses to start until those are filled in.

Review
  Inhouse-server   https://github.com/acme/api/pull/248   → dev
  Inhouse-client   https://github.com/acme/web/pull/91    → dev

  You are on context/code-map-dev-2026-10-21 in each repo, so the tree is
  usable here now. Your teammates get it when these merge.

Next — pick the one that matches what you're doing
  /qa:audit repo=Inhouse-server
      score how testable the code is, then choose which coverage dimensions
      to improve. Prints the report URL and routes you to /qa:plan.

  /ba:scope add "requirements in ./client-docs"
      you have a requirement or a plan folder and want it worked out first.

  /dev:plan tasks/fix-login-timeout.md
      you already know the task. Write it under tasks/, or pull the ticket
      first — /jetrix:pull task PAY-412   (pulls from Jira, the tracker you
      bound at init; a pasted issue URL works too).
```

**Rules for that block, in order of how often they are broken:**

**Lead with what the reader must act on, not with what the run did.** A committed credential outranks a
coverage table every time. If nothing needs them, say `✓ nothing needs you` and stop — do not manufacture
findings to fill the section.

**Six lines of stats, maximum.** Repo, counts, coverage, area tokens. The domain decomposition, confidence
spread, per-kind breakdown and integrity findings all live in the indexes — link them, do not reprint them.

**Print all three next steps, not one.** They are not ranked against each other — they are three different
intents, and only the reader knows which one they arrived with. Fill each line with this repo's real values
(the actual repo name, a real folder, a plausible task slug), never the placeholders above.

| The reader wants to… | Line to print |
|---|---|
| know how testable the code is | `/qa:audit repo=<repo>` — scores every coverage dimension and hands back a report they set Adopt/Skip/Defer in. **Print this even when tests already exist**: the score is what turns an existing suite into Delivery OS quality gates, and without `qa/quality-gates.md` `/dev:build` has nothing to enforce. |
| work out a requirement first | `/ba:scope add "requirements in <path-or-link>"` |
| build a task they already have | `/dev:plan <path>` — `tasks/<slug>.md` if they write it themselves, or `/jetrix:pull task <a real id>` first to fetch it from the tracker bound at `/jetrix:init`. **Fill in a real id in that tracker’s own form and name the tracker** (`/jetrix:pull task PAY-412` — *pulls from Jira*). Never print the literal `<ref>`, and never ask which tracker: `project.json` says. See `/jetrix:pull` § *Never print the word `<ref>` to a user*. |

A branch still unmapped is **not** a fourth next step — it is a `⚠ Needs you` line, because it means the run
covered less than the reader thinks it did.

**A decision the run made goes in one line with its id**, not a paragraph. *"Server ids renumbered to match
main — DEC-013"* is the whole story; the reasoning belongs in `decision-log.md`, which is where someone who
disagrees will go.

**Say what you did not map, and why, in one line each.** *"Branches not mapped: holiday-calendar, assets,
leave — each needs its own run."* A reader who assumes the whole repo was covered is worse off than one told
plainly.

**Always print the PR link and the branch you are on.** §4 commits to `context/code-map-…`, pushes it and
raises a PR — **or, where the ladder reached step 4, prints a compare URL and no PR exists yet**; say
which of the two happened rather than asserting a PR. Two facts follow from that and both have to be said: the tree **is** available to whoever ran
this, right now, because they are standing on that branch; and it is **not** available to anyone else until
the PR merges. A reader who assumes their team can already see it loses an afternoon.

If the push or the PR failed, that is a `⚠ Needs you` line carrying the exact command — not a quiet omission
of the Review block.

Link, last and briefly: the root index, each layer index, `map-coverage.md`, and the registry — with the
one-line read protocol (root index → the layer's Domain Map → the single unit file). That protocol is the
return on the whole run, and it is one sentence.

## Publish it

**`code-map-registry.md` is workspace-level — no repo holds it, so git does not carry it.** Push it as soon as it is written,
the way `/ba:features` pushes a breakdown the moment the folders exist: `/jetrix:push scope code-map-registry.md`.
**Pass the filename** — a bare `/jetrix:push scope` would also send BA documents this run never touched,
some of them mid-edit. Without it the next person to map this workspace mints colliding area tokens, and nothing detects it.

Not on Jetrix, or the push fails → one `⚠ Needs you` line naming the retry command. **Never fail the run over
the upload** — the work is on disk, and a dropped connection must not cost it.

