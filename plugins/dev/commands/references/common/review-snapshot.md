# Review snapshot — the one scope every reviewer reads

A **review snapshot** is a real git commit object built from the working tree
through a throwaway index. It gives security review, code review and test
verification a single, stable, diffable scope — without moving the working
tree, the real index, or HEAD.

Read this before any stage that scopes on a diff. `/dev:build` Stage 9 and
`/dev:commit` Stages 0, 2, 3, 4, 7.5 and 8 all depend on it.

**Why it exists.** `/dev:build` leaves everything uncommitted by design, so
`git diff <base>...HEAD` is empty after a build and the reviewers see nothing.
A run that cannot state its scope improvises one, reviews a self-selected
subset, and reports the result as if it were complete — which is exactly how a
commit with five known defects came back reporting three.

---

## 1. Building one

Verified on Windows / Git Bash against a repo with tracked modifications and
untracked files. Run from inside the repo.

```bash
# Let git name the path. Never mktemp, never /tmp - see below.
TMPIDX="$(git -C "$REPO" rev-parse --absolute-git-dir)/delivery-os.review.index"
export GIT_INDEX_FILE="$TMPIDX"
trap 'rm -f "$TMPIDX"' EXIT                    # cleanup is not optional

git -C "$REPO" read-tree HEAD
git -C "$REPO" -c core.safecrlf=false add -A -- $SCOPE   # §3 for $SCOPE
TREE="$(git -C "$REPO" write-tree)"
SNAP="$(git -C "$REPO" commit-tree "$TREE" -p "$BASE_SHA" -m 'review-snapshot')"

unset GIT_INDEX_FILE
git -C "$REPO" diff "$BASE_SHA".."$SNAP"       # what the reviewers read
```

Use `delivery-os.detection.index` for the detection snapshot (§2) so the two
never collide.

| Property | Status |
|---|---|
| Working tree unchanged | verified — `git status --porcelain` byte-identical before and after |
| Portable index path | verified — `--absolute-git-dir`, no `mktemp` or `/tmp` dependency |
| Real index unchanged | verified — `.git/index` md5 identical |
| HEAD unchanged | verified |
| Untracked files included | verified |
| `.gitignore` still applies | verified — ignored paths never enter the tree |
| `$SNAP` is a real commit | verified — every existing `git diff <base>...<head>` call site works on it unmodified |

### 1a. Why the index path comes from git, not from `mktemp`

`mktemp` returns an **MSYS path** (`/tmp/tmp.mb3MaHhjep`). It works from Git
Bash only because `git.exe` ships MSYS path translation. The same command file
executed through PowerShell has no `mktemp` and no `/tmp`, and the snapshot
would fail or write somewhere unintended.

`git rev-parse --absolute-git-dir` returns a path **git itself produced**, so it
is valid in whatever environment git is running in:

```
C:/Users/selva/plugin-test/Inhouse-server/.git
```

Four properties follow, and all four matter:

| | |
|---|---|
| No `mktemp`, no `/tmp` | works from Git Bash, PowerShell or cmd |
| Same filesystem as the repo | no cross-device failures |
| Inside `.git/` | **invisible to `git status`** - a crashed run leaves no mess in the working tree (verified: 0 matches) |
| Deterministic name | a leftover from a crash is simply overwritten by the next `read-tree`, so staleness is self-healing |

**Use `--absolute-git-dir`, never `--git-dir`.** `--git-dir` returns the
relative `.git` **even when `-C <repo>` is passed**, and `GIT_INDEX_FILE`
resolves relative to the *process* working directory, not the repo. On a
multi-repo run that silently writes the index for the wrong repository. The two
forms differ only in a case that is easy to miss and expensive to debug.

**`-c core.safecrlf=false` is required, not cosmetic.** On a repo with LF files
checked out under `core.autocrlf`, a bare `git add -A` emits one
`LF will be replaced by CRLF` warning **per file** — 221 of them on a real run.
The flag suppresses the warning and produces a byte-identical tree
(confirmed: same tree sha with and without). It is passed with `-c` so nothing
in the user's repo config changes.

**`git add -A` here is safe and is not the blanket-staging this plugin forbids
elsewhere.** It writes to a throwaway index at `$GIT_INDEX_FILE` and never to
`.git/index`. The rule against blanket staging governs *delivery* staging in
`/dev:commit` Stage 7.5, which stages named paths only.

**The snapshot is a dangling object.** Nothing references it, so git will
garbage-collect it. It is a scope identifier for the duration of a run and
**must never be written into a file that gets committed** — see
`stage-10-context-update.md` on `mapped_from_commit: pending`.

---

## 2. Two snapshots, not one

| | Built from | Used for |
|---|---|---|
| **Detection** | everything — `git add -A` with no pathspec | classifying the run: is there work here, does it match a task, is it mixed |
| **Review** | `git add -A -- <selected paths>` | **all reviewers, and Stage 7.5's staging set** |

The review snapshot must be **byte-identical to what gets staged**. One
snapshot for both means reviewing one set of changes and delivering another.

Stage 8 gates on it: recompute the review snapshot immediately before staging
and compare. Differs → `blocker: snapshot-stale`.

---

## 3. Choosing the scope

Show every change grouped by directory, with its git state. The user ticks.

```
Changes detected — Inhouse-server
  205 files changed

  Select what belongs to this task:

    [x] context/code-context/      9 files    modified
    [x] CLAUDE.md                  1 file     untracked
    [ ] coverage/                  195 files  untracked, nothing tracked here
        └ generated output? consider adding it to .gitignore

  10 of 205 selected
```

### 3a. Collapse a directory that has nothing tracked

A directory where **no path exists in HEAD** is either new source or generated
output, and the difference is not inferable. Collapse it to one row, show the
count, and leave it **unticked**:

```bash
git cat-file -e "HEAD:<dir>" 2>/dev/null   # non-zero => nothing tracked there
```

On a real repo this turned a 205-row prompt into a 3-row one: 195 of those
files were an untracked `coverage/` directory that nobody intended to deliver.
Listing them flat would make the prompt unreadable and bury the nine files that
mattered.

Say the `.gitignore` line out loud when this fires — an untracked build
directory is usually a missing ignore rule, and naming it is more useful than
silently excluding it every run.

### 3b. A file that is staged AND further modified

`git add -A` takes the **working-tree** version, so a developer who staged a
subset deliberately would get the rest reviewed and delivered too. Never
resolve this silently:

```
  [!] src/auth/session.ts    staged +12/-3  ·  AND unstaged +40/-8
      [a] take the working tree   (both sets)
      [b] take the index only     (what you staged; the rest stays uncommitted)
```

On `[b]`, build that path's entry from the **real index blob**, not the file.

**Want only part of a file?** `git add -p` it first, then answer `[b]`.
Per-hunk selection inside this prompt is deliberately not built — git already
has the right tool, and reimplementing `add -p` in a picker would be a worse
version of something every developer knows.

### 3c. Rules

- **Show every change.** A file absent from the list is a bug; a file present
  and unticked is a decision.
- **Record both sets** — `scope_selected[]` and `scope_excluded[]` — in the
  task's `status.md`, so a later run and a reviewer both see what was left out.
- **Rebuild the review snapshot if the selection changes.**
- **Nothing selected → `blocker: empty-scope`.** Stop cleanly: no commit, no
  push, no PR, no empty commit.
- **Ask once, at the pre-fan-out checkpoint.** Never per worker.

---

## 4. Resolving `$BASE_SHA`

| Route | Order |
|---|---|
| **A** — Delivery OS built it | `units/<repo>/status.md` `base_branch:`, the value confirmed at `/dev:plan`'s checkpoint. **Never re-derived** |
| **B** — adopted work | upstream of the current branch → `apps[].env_branches.dev` from `project.json` → ask at the checkpoint |

- Missing on Route A → halt. Do not fall back to `develop`; that silent default
  is what `/dev:build` Stage 3 already refuses.
- Unresolvable → `blocker: base-unresolvable`, printing the ladder tried.
- Detached HEAD → `blocker: snapshot-detached-head`. There is no branch to
  deliver to.
- Base moved on the remote mid-run → `blocker: base-moved`; re-fetch and resume
  from Stage 2.

---

## 5. Staleness

The snapshot is a point in time; reviewers take minutes.

- Record `snapshot_sha` in `status.md § ## Run history` when it is built, and in
  the header of every findings section produced against it.
- **Recompute and compare immediately before Stage 7.5 stages anything.**
  Differs → the tree moved during review → re-run the affected gates. Never
  stage against findings that cite a tree that no longer exists.
- After every repair round, recompute and record the new sha.

---

## 6. Failure modes

| Failure | Blocker code | Response |
|---|---|---|
| `write-tree` / `commit-tree` fails | `snapshot-build-failed` | halt before any review; print the git error verbatim |
| Detached HEAD | `snapshot-detached-head` | halt |
| Base unresolvable | `base-unresolvable` | halt, print the ladder |
| Base moved mid-run | `base-moved` | halt, re-fetch, resume from Stage 2 |
| Tree moved during review | `snapshot-stale` | re-run affected gates |
| Nothing selected | `empty-scope` | stop cleanly, no empty commit |
| Temp index left behind | — | `trap` removes it on every exit path |

**A stage that cannot build a snapshot does not review.** It halts and says so.
It never falls back to reading files by judgement and reporting the result as a
review — that failure looks like success and ends the search.
