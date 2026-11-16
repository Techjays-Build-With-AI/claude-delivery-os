## Stage 7.5 — Gather working-tree changes + structure commit(s)

**Purpose.** `/dev:build` writes to the working tree without committing (v2.3.20 invariant in `build.md`). This stage is where the ONE commit boundary happens: gather all working-tree changes from Stages 5-6 (code + tests) + Stage 10 (context units) + relevant Stage 11 outputs → structure the commit(s) → land them on the current branch. Stage 8 then pushes.

**Runs between Stage 7 (semantic context merge) and Stage 8 (push branch).** After all quality gates (Stages 4–6) pass and the semantic merge is clean.

**On completion:** the branch has one (or, with `--structured`, several) clean commit(s) with structured messages; no untracked files in the source or test scope; secrets scan clean; `units/<repo>/pr-summary.md § ## How to verify` explicitly EXCLUDED from the commit set.

---

### 7.5a. Preconditions

- Stages 4–7 all `status: DONE` in `units/<repo>/status.md § ## Run history`
- `git status` in target repo is well-formed (branch checked out, no rebase in progress, no merge conflict)
- Working tree HAS uncommitted changes (else skip cleanly per §7.5g)

Target repo:
- Parent-alone → primary product repo per `.jetrix/project.json` `apps[0]`
- Sub-task → repo matching `subtask_repo` frontmatter

---

### 7.5b. Stage exactly what was reviewed

**The staged set is the review snapshot's path set. Not the working tree.**

Stage 0 recorded `scope_selected[]` in `status.md` and built `$SNAP` from those
paths; Stages 4 and 5 reviewed that snapshot. Staging anything else delivers
bytes nobody reviewed, which is the failure the whole snapshot mechanism exists to
prevent — review one set of changes, ship another.

```bash
cd <target-repo>
git diff --name-only <base>..$SNAP      # the authoritative list
git status --porcelain                  # cross-check only — see below
```

**Reconcile the two before staging anything:**

| Case | Meaning | Action |
|---|---|---|
| in the snapshot, in the tree | the normal case | stage it |
| in the snapshot, **gone** from the tree | a reviewed file was deleted or reverted after review | **HALT `snapshot-stale`** — the review no longer describes the tree |
| in the tree, **not** in the snapshot | written after the snapshot, or deliberately excluded at Stage 0 | **do not stage.** If `scope_excluded[]` names it, that was a decision; if not, it appeared mid-run → HALT `snapshot-stale` |

**Recompute `$SNAP` first and compare its sha** with the recorded `snapshot_sha`
(§4d of `review-snapshot.md`). Differ → the tree moved during review → re-run the
affected gates before staging. This is the last point at which that is catchable.

Then categorize each path in the set:

| Path pattern | Category | Included in commit? |
|---|---|---|
| `src/**` (and language equivalents: `lib/**`, `app/**`, `pkg/**`, `internal/**`) | `source` | YES |
| `tests/**`, `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**` | `test` | YES |
| `context/code-context/**` | `context-unit` | YES |
| `context/test-map/**` | `test-map` | YES — written by build Stage 5-6; it is what `/dev:commit` Stage 5 executes, so a map left uncommitted makes the next run unable to re-derive what was verified |
| `CLAUDE.md` (repo root) | `repo-doc` | YES — the `delivery-os:*` pointer blocks written by `/tl:scaffold`, `/dev:plan` and build Stage 5-6. It is how the next session finds the context graph, the test map and the repo's UI system at all |
| `units/<repo>/pr-summary.md § ## How to verify`, `units/<repo>/status.md § ## Run history`, `dev/*-status.md § ## Run history`, `units/<repo>/status.md § ## Run history`, `units/<repo>/status.md § ## Acceptance`, `dev/decisions.md`, `dev/escalation-*.md`, `dev/task-update-run.md` | `dev-local` | **NO** — LOCAL only |
| `.jetrix/**` | `workspace-local` | **NO** — workspace state, not repo state |
| `qa/quality-gates.md`, `shared-context/*`, `ba/**`, `features/**` | `workspace-local` | **NO** — those are workspace files, live outside the target repo unless the target repo IS the workspace |
| Other | `unknown` | ASK the user to categorize each (source / test / context / local-only-do-not-commit); halt if not answered within the run |

If any `unknown` file is under a language directory the categorizer failed to detect (e.g. an unusual folder), log `stage-7-5-categorization-warning` to `units/<repo>/status.md § ## Run history` and default it to `source` after asking.

**A file Delivery OS itself wrote must never reach `unknown`.** `CLAUDE.md` and the test map are
produced by `/dev:plan` and `/dev:build`, are repo state the next agent reads, and are always
committed — prompting for them turns a decision nobody needs to make into a halt on every run.
When a future stage starts writing a new repo-level file, add its row here in the same change;
the categorizer is the consumer half of that contract and will otherwise stop the commit.

---

### 7.5b.i. Flip `gates_passed`

Every finding from Stages 4 and 5 is now closed or dispositioned, so set
`gates_passed: true` on this run's `.jetrix/cache/session.json` row. Until
this moment the guard hook refuses `git push` in this repo; after it, Stage 8
may push.

**This is the only place it flips.** Setting it earlier would let a push
through before the findings were settled, which is the one thing the row
exists to prevent.

### 7.5c. Secrets scan (mandatory)

Before staging anything, run a mechanical scan on the working-tree file list for:

- Filename patterns: `.env`, `.env.*`, `*.pem`, `*.key`, `*credentials*`, `*secret*`, `*token*`, `id_rsa*`, `id_ed25519*`
- Path patterns: `**/private/**`, `**/secrets/**`

If ANY file in the `source` / `test` / `context-unit` categories matches:
- HALT with `blocker: secrets-in-staged-set`
- Report the offending file paths
- Do NOT auto-add to `.gitignore`
- Do NOT auto-remove from working tree
- Do NOT commit
- User investigates, decides (was this intentional? if so, add to `.gitignore` and re-run; if accidentally created, delete it and re-run)

---

### 7.5d. Choose commit strategy

Default: **ONE commit** for the whole task's diff. Message convention:

```
feat(<domain>): <one-line summary from parent's feature.md Objective>

Sub-task: <task-ref>
§1 Build sequence: <N> steps landed
Tests: <`status.md` § `## Acceptance` row count> parent AC/BR/TS covered at <tier list>

<optional body — DEC-### references from shared-context/decision-log.md landed this run>

Refs: <parent's BR-N, comma-separated>
```

Alternative: `--structured` flag → multi-commit, one per category:

| Order | Type | Scope | Contents |
|---|---|---|---|
| 1 | `docs(context)` | Context units + repo docs | `context/code-context/**` (Stage 10), `context/test-map/**` (Stage 5-6), `CLAUDE.md` (pointer blocks) |
| 2 | `feat(<domain>)` | Source + tests | `src/**` + `tests/**` for THIS task |
| 3 | `refactor(<scope>)` | Only if genuine refactor | Behavior-neutral changes with DEC-###; SEPARATE from `feat` |
| 4 | `test(<domain>)` | Test harness only | New test infra (fixtures, helpers, CI) if separate from the feature's tests |

Order matters: docs first, feat second, refactor third (behavior-neutral marker), test fourth. Each commit passes its own category-scoped lint / typecheck if the repo has pre-commit hooks.

**Default (single commit) is recommended** for most tasks. `--structured` is for tasks that have genuinely separable behavior changes the user wants reviewable independently.

---

### 7.5e. Stage + commit

**Single-commit path (default):**

```bash
cd <target-repo>
git add \
  src/... tests/... context/code-context/...   # each specific path from §7.5b classification
git commit -m "<message from §7.5d>"
```

Never `git add -A` or `git add .` — always add specific paths from the categorized list. This is what keeps `units/<repo>/pr-summary.md § ## How to verify` and other `dev-local` files out.

**Structured-commit path (`--structured`):**

For each category in order (docs, feat, refactor, test):
```bash
git add <paths for this category>
git commit -m "<category-scoped message>"
```

If any commit fails (pre-commit hook rejects) → HALT. Fix the issue, `/dev:commit --resume`. Never bypass hooks with `--no-verify`.

Never `--amend` a previous commit — always add a new commit.

---

### 7.5e.i. Backfill context-unit provenance — before staging them

`/dev:build` Stage 10 flipped this task's context units to `implemented` and wrote
`implemented_by_commit: pending` and `mapped_from_commit: pending`, because at that
moment no commit contained the code. **This is where they become real.**

Order matters: backfill **before** the commit is created if you can name the sha
afterwards, or commit first and amend-free re-stage. The sequence that works
without amending:

1. Commit the source and test files (§7.5e).
2. For each unit in `status.md` § `## Run history` `stage-10.units_updated`:
   - `implemented_by_commit:` → the sha just created
   - `mapped_from_commit:` → `git log -1 --format=%H -- "${mapped_from%%:*}"`
     **Cut `mapped_from` at the first `:`** — it is commonly `<path>:<symbol>`, and
     passing the whole value matches no path, so every unit comes back looking
     stale.
3. Stage and commit the context tree as a second commit:
   `docs(context): stamp provenance for <task-ref>`.

**Never leave a unit reading `pending` after a successful commit.** A `pending`
that survives delivery is a unit whose drift can never be checked — the readiness
check reports `pending` forever and nobody notices the code moved underneath it.

**Never write the review snapshot's sha.** It is a dangling object git will
garbage-collect, and this tree is committed into the product repo.

A `--structured` run already produces a `docs(context)` commit; fold the backfill
into it rather than adding a third.

### 7.5f. Verify + log

After commits land:

```bash
git log --oneline <base-branch>..HEAD    # show new commits on this branch
git status                               # verify working tree clean (except dev-local files)
```

Expected state after this stage:
- N commits on the branch (1 for default, up to 4 for `--structured`)
- Working tree has ONLY `dev-local` and `workspace-local` files remaining as uncommitted (they were intentionally excluded)
- `src/**`, `tests/**`, `context/code-context/**` all clean

Log to `units/<repo>/status.md § ## Run history`:

```yaml
stage-7-5:
  status: DONE
  strategy: single | structured
  commits_made:
    - sha: <full sha>
      subject: <first line>
      files: <N>
      lines: +<M> -<K>
    - ...
  files_excluded:
    - units/<repo>/pr-summary.md § ## How to verify
    - units/<repo>/status.md § ## Run history
    - .jetrix/...
  provenance_backfilled:
    units: [EP-SUP-01, EP-SUP-02, ENT-SUP-01]
    implemented_by_commit: <sha>      # no unit may still read `pending`
  secrets_scan: clean
  working_tree_after: clean (dev-local + workspace-local uncommitted, as expected)
  finished_at: <ISO>
```

---

### 7.5g. Skip cleanly if nothing to commit

If §7.5b's scan finds NO files in the `source` / `test` / `context-unit` categories that are uncommitted, someone already committed manually mid-flow. Skip this stage:

```yaml
stage-7-5:
  status: SKIPPED
  reason: working tree has no source/test/context uncommitted changes
  finished_at: <ISO>
```

Continue to Stage 8 (push). Stage 8 will push the existing commits on the branch, whatever they are.

---

### 7.5h. On failure

- **Secrets scan hit** → HALT per §7.5c
- **Uncategorized file the user won't classify** → HALT with the file listed
- **`git commit` fails (pre-commit hook)** → HALT with hook output; user fixes and `/dev:commit --resume`
- **Any git error** → HALT with the git error output; do NOT retry

State transitions on halt:
- Local: unchanged (stays at whatever Stage 6 landed on)
- MC: unchanged
- Working tree: unchanged (may have partial staging from a partially-applied `--structured` run; user can `git reset` if needed, but the tool does NOT auto-reset)

---

### 7.5i. On `--resume`

If Stage 7.5 was interrupted:
- Check `units/<repo>/status.md § ## Run history` for `stage-7-5.commits_made` — if any listed, those commits landed; do not duplicate
- Re-scan working tree for anything STILL uncommitted; if empty → skip cleanly
- If additional changes remain → continue from the appropriate strategy step

---

### Skills / agents invoked

- No subagents — pure shell + file categorization + git operations
- Direct `git status`, `git add <specific paths>`, `git commit -m <message>`, `git log` calls
- Never `git push` (Stage 8's job)
- Never `git rebase`, never `git reset --hard`, never `--no-verify`, never `-c commit.gpgsign=false`

Read-only calls to task-mcp are permitted if the commit message needs the MC task URL — pass through `get_task_by_id_or_number(...)` `view_url` from the response.
