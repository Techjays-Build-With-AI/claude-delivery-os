## Batch shape — ask once, before any agent starts

**Purpose.** When the target resolves to more than one task, decide how the
batch is laid out across branches and whether it runs as one sweep or one task
at a time. Asked **once**, against printed measurements.

**Runs in** `/dev:build` for blank, `--all`, `list=`, `requirement=`, or a split
parent with several sub-tasks. A single task-ref skips this file entirely.

**This file changes nothing about the command boundary.** `/dev:build` writes
code and stops: no commits, no pushes, no PRs. `/dev:commit` owns that, per task,
exactly as before.

---

### B1. Measure before asking

Read every target's `features/<slug>/dependencies.md` frontmatter and its
`implementation.md § 1 Build sequence`:

| Signal | Source | Why it matters |
|---|---|---|
| **Repo spread** | `units/<repo>/` per task | tasks in different repos can never share a branch |
| **Module spread** | the `AREA` in `FEAT-<AREA>-NN` | one area usually reviews as one change |
| **Dependency density** | `depends_on_features` edges ÷ task count | a dense chain is one story, not N stories |
| **Size** | `§1` step count per task | a large task earns its own branch |

Print the measurements with the question. A recommendation the user cannot check
is a guess wearing a number.

---

### B2. Question 1 — one branch, or one per group

A **group** is tasks that can share a branch: same repo, same area, connected in
the dependency graph.

```
one repo AND one area AND density ≥ 0.6 AND every task ≤ 15 steps
    → recommend SINGLE BRANCH

otherwise
    → recommend GROUP  (one branch per repo × area cluster)
```

```
10 tasks · 1 repo · 1 module (PLAT) · 9 of 10 dependent · avg 6 steps

  Recommended: ONE branch
    all small, all in platform, all chained — splitting this into three
    branches would make three reviews of the same change

  1  One branch     all 10 tasks        ← recommended
  2  Per group      3 branches
  3  Per task      10 branches
```

**A task over 15 steps, or touching auth / payments / migrations, gets its own
branch regardless** — that escalation is per task, not per batch.

---

### B3. Question 2 — all at once, or one at a time

Only when the batch holds more than one task.

| Mode | What happens |
|---|---|
| **`sweep`** | build every task the graph allows, in waves, then report. Default |
| **`one-at-a-time`** | build the first task, then stop. `--resume` takes the next |

```
  How should this run?

  1  sweep           build all 10, then report        ← recommended
  2  one-at-a-time   build one, stop, resume when ready
```

**`one-at-a-time` is for when you want to commit and review between tasks.**
`/dev:build` still does not commit — it stops so you can run `/dev:commit`
yourself before the next task starts.

---

### B4. Branch creation

- **Single branch** — created once; Stage 3 verifies it and continues rather than
  branching per task.
- **Per group** — one branch per group, created once; same rule inside the group.
- **Per task** — Stage 3 branches as it always has.

Name a shared branch from its area and intent, not from its first task. A branch
called `feat/FEAT-PLAT-01-…` carrying four features misleads every reviewer who
opens it.

**A group never spans repos** — §B2 clusters on `repo × area` precisely so this
holds.

---

### B5. Waves and ordering

Order is still the command's job and is never asked. Compute waves over the
dependency graph — over groups when grouping, over tasks otherwise — and report
the plan before the first agent starts:

```
Plan: 3 groups · 2 waves · mode sweep · concurrency 5

  wave 1   group A  feat/plat-baseline     4 tasks
  wave 2   group B  feat/role-management   3 tasks
           group C  feat/dashboard         3 tasks   (B and C in parallel)
```

**Never say "held" without saying until what.** A held group names what it waits
on, in one line.

---

### B6. Failure containment

| What failed | Effect |
|---|---|
| One task | the fix loop runs; if it exhausts, that task halts and its group stops there. The branch keeps the commits-worth of work in the tree |
| A whole group | dependants are `SKIPPED_DEPENDENCY_FAILED`, named with the group that failed |
| Independent groups | unaffected |

Report skips with the batch, never silently, and name the action that unblocks
them rather than only the status.

---

### B7. What this file does not decide

Ordering within the graph — derived, never asked.
Whether a task is ready — Stage 2 pre-flight, per task.
Anything about commits, pushes or PRs — `/dev:commit` owns that boundary.
