## Stage 7.5 — Gather working-tree changes + structure commit(s)

**Purpose.** `/dev:build` writes to the working tree without committing (v2.3.20 invariant in `build.md`). This stage is where the ONE commit boundary happens: gather all working-tree changes from Stages 5-6 (code + tests) + Stage 10 (context units) + relevant Stage 11 outputs → structure the commit(s) → land them on the current branch. Stage 8 then pushes.

**Runs between Stage 7 (semantic context merge) and Stage 8 (push branch).** After all quality gates (Stages 3–6) pass and the semantic merge is clean.

**On completion:** the branch has one (or, with `--structured`, several) clean commit(s) with structured messages; no untracked files in the source or test scope; secrets scan clean; `dev/local-runbook.md` explicitly EXCLUDED from the commit set.

---

### 7.5a. Preconditions

- Stages 3–7 all `status: DONE` in `dev/<repo>-commit-run.md`
- `git status` in target repo is well-formed (branch checked out, no rebase in progress, no merge conflict)
- Working tree HAS uncommitted changes (else skip cleanly per §7.5g)

Target repo:
- Parent-alone → primary product repo per `.jetrix/project.json` `apps[0]`
- Sub-task → repo matching `subtask_repo` frontmatter

---

### 7.5b. Scan working tree + categorize each file

Run in the target repo:

```bash
cd <target-repo>
git status --porcelain
```

Categorize every line:

| Path pattern | Category | Included in commit? |
|---|---|---|
| `src/**` (and language equivalents: `lib/**`, `app/**`, `pkg/**`, `internal/**`) | `source` | YES |
| `tests/**`, `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**` | `test` | YES |
| `context/code-context/**` | `context-unit` | YES |
| `dev/local-runbook.md`, `dev/build-run.md`, `dev/*-commit-run.md`, `dev/implementation-log.md`, `dev/acceptance-map.md`, `dev/security-findings-*.md`, `dev/decisions.md`, `dev/escalation-*.md`, `dev/task-update-run.md` | `dev-local` | **NO** — LOCAL only |
| `.jetrix/**` | `workspace-local` | **NO** — workspace state, not repo state |
| `qa/quality-gates.md`, `shared-context/*`, `ba/**`, `features/**` | `workspace-local` | **NO** — those are workspace files, live outside the target repo unless the target repo IS the workspace |
| Other | `unknown` | ASK the user to categorize each (source / test / context / local-only-do-not-commit); halt if not answered within the run |

If any `unknown` file is under a language directory the categorizer failed to detect (e.g. an unusual folder), log `stage-7-5-categorization-warning` to `dev/<repo>-commit-run.md` and default it to `source` after asking.

---

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
Tests: <acceptance-map row count> parent AC/BR/TS covered at <tier list>

<optional body — DEC-### references from shared-context/decision-log.md landed this run>

Refs: <parent's BR-N, comma-separated>
```

Alternative: `--structured` flag → multi-commit, one per category:

| Order | Type | Scope | Contents |
|---|---|---|---|
| 1 | `docs(context)` | Context units | `context/code-context/**` files (Stage 10 output) |
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

Never `git add -A` or `git add .` — always add specific paths from the categorized list. This is what keeps `dev/local-runbook.md` and other `dev-local` files out.

**Structured-commit path (`--structured`):**

For each category in order (docs, feat, refactor, test):
```bash
git add <paths for this category>
git commit -m "<category-scoped message>"
```

If any commit fails (pre-commit hook rejects) → HALT. Fix the issue, `/dev:commit --resume`. Never bypass hooks with `--no-verify`.

Never `--amend` a previous commit — always add a new commit.

---

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

Log to `dev/<repo>-commit-run.md`:

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
    - dev/local-runbook.md
    - dev/build-run.md
    - .jetrix/...
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
- Check `dev/<repo>-commit-run.md` for `stage-7-5.commits_made` — if any listed, those commits landed; do not duplicate
- Re-scan working tree for anything STILL uncommitted; if empty → skip cleanly
- If additional changes remain → continue from the appropriate strategy step

---

### Skills / agents invoked

- No subagents — pure shell + file categorization + git operations
- Direct `git status`, `git add <specific paths>`, `git commit -m <message>`, `git log` calls
- Never `git push` (Stage 8's job)
- Never `git rebase`, never `git reset --hard`, never `--no-verify`, never `-c commit.gpgsign=false`

Read-only calls to task-mcp are permitted if the commit message needs the MC task URL — pass through `get_task_by_id_or_number(...)` `view_url` from the response.
