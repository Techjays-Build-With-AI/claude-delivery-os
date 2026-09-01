## Stage 10 — Update code-context units (`designed → implemented`)

**Purpose.** For every TL unit this task built (endpoint, entity, page), update the unit file in the target repo's `<repo>/context/code-context/` to reflect that it's now real code, not just design. Adds source-file citation + commit stamp + confidence promotion.

**Runs after Stage 9 security review passes.** State: `TESTING` (unchanged). MC: `inProgress`.

**On completion:** every owned unit is marked `origin: implemented` with the concrete evidence pointing at the code. Layer indexes reflect the new status. Ready for `/dev:commit` Stage 7's semantic merge.

---

### 10a. Preconditions

- `dev/build-run.md` `stage-9.status: DONE` (or SKIPPED)
- Branch commits present — `git log <base>..HEAD` returns ≥ 1 commit
- Target repo has `<repo>/context/code-context/` — created by `/tl:plan` OR `/tl:code-map`

If context tree is missing → escalate. `/dev:plan` should have run `/tl:plan` to create the graph; if we got here without it, that's a plan-side gap.

---

### 10b. Identify owned units

The units to update are the ones this task owns (from `implementation.md` §1 Build sequence Units column + §3 Operations exposed and consumed + §4 Stored data changes + §5 User-facing surfaces for parent-alone, OR `subtask/<repo>/implementation.md` for sub-task).

Read the 3 layer indexes for the target repo:

- `<repo>/context/code-context/frontend/frontend-index.md`
- `<repo>/context/code-context/backend/backend-index.md`
- `<repo>/context/code-context/database/database-index.md`

Grep the `Used by Features` column for THIS task's `FEAT-<AREA>-NN` (parent) OR `FEAT-<AREA>-NN-<N>` (sub-task). Every row matching → an owned unit.

---

### 10c. Update each unit file's frontmatter

For each owned unit file:

Read the file. In frontmatter, apply these updates:

```yaml
# Was (from /tl:plan)
origin: designed
design_confidence: Likely                   # or Assumed

# After Stage 10 update
origin: implemented
design_confidence: Confirmed                # promote from Likely (design was verified by working code)
implemented_at: 2026-08-31T15:21:44Z        # ADD (from git commit timestamp of last touching commit)
implemented_by_commit: <HEAD SHA>           # ADD
implemented_by_task: FEAT-SUP-001-1         # ADD (feature id + sub-task suffix if applicable)
mapped_from: src/routes/supplier.ts         # ADD (canonical source file)
mapped_from_line: 42                        # ADD (line of the export / entry point, if resolvable)
```

Confidence promotion rules:

| Before | After (if implementation matches design) |
|---|---|
| Assumed | Likely |
| Likely | Confirmed |
| Confirmed | Confirmed (already highest) |
| Conflicting | Confirmed (implementation resolved the conflict) |
| Needs Clarification | Confirmed |

If implementation DOESN'T match design (e.g. plan-blocker resolution changed the endpoint contract mid-build):

- Update the design's confidence field per the actual implementation
- Add a `## Design deviation` block to the unit body noting the difference and the `DEC-###` that caused it

---

### 10d. Update each unit file's body

Append (do not overwrite) to `## Source References`:

```markdown
## Source References

- [feature › FEAT-SUP-001-1]                             ← already there from designed
- [code › src/routes/supplier.ts:42]                     ← ADD (from mapped_from)
- [test › tests/endpoints/supplier.spec.ts]              ← ADD (references first test file that asserts on this unit)
```

Update `## Status` from `draft` (designed) → `active` (implemented, tested locally, waiting for merge).

For endpoints — verify `## Business Logic` section matches actual code (if implementation revealed steps the design didn't have, add them; if design steps weren't actually needed, remove them and log a `DEC-###`).

For entities — verify `## Fields written by this feature` (from `implementation.md §4 Stored data changes`) matches actual migrations.

For pages — verify `## Consumes endpoints` matches actual API calls in code.

---

### 10e. Update layer indexes

For each involved layer index:

- Update the row's `Status` column — `draft` → `active`
- Update the row's `Confidence` column (if present) per §10c rules
- If the row's `Summary` cell drifted from the unit's `## Summary` (rare — should stay in sync), take the unit's current summary as truth

---

### 10f. Don't touch base branch's context

**Critical.** The updates happen on the FEATURE BRANCH ONLY. Base branch (`develop`) keeps whatever it has. `/dev:commit`'s Stage 7 semantic merge (via `tl-semantic-context-merge` skill) is what reconciles the two later.

Do NOT try to preview the merge here — just write to HEAD; commit later.

---

### 10g. Stage the updates (git add, no commit yet)

Run in the target repo:

```bash
cd <target-repo>
git add "context/code-context/"
```

The updates become part of the branch's next commit. `/dev:build` doesn't commit — that's `/dev:commit`'s Stage 8. If Stage 11's summary generation needs the git state clean, this staging keeps the working tree tidy while leaving the commit itself for the developer to make (or for `/dev:commit` to make en-masse).

Alternatively, wait for Stage 11 to commit code + context together as one commit `chore: update code-context units to implemented`. Ship a single well-formed commit rather than a partial staging.

Recommendation: **commit here, one commit per Stage-10 run**, with a fixed message:

```
chore(context): mark 3 units implemented for FEAT-SUP-001-1

- backend/domains/supplier/endpoints/create.md — implemented @ src/routes/supplier.ts:42
- backend/domains/supplier/endpoints/duplicate-check.md — implemented @ src/routes/supplier.ts:78
- database/tables/supplier.md — implemented @ src/db/migrations/20260831142400_add_supplier_table.ts
```

One clean commit; easy to see in the branch.

---

### 10h. Progress log format

Append to `dev/build-run.md`:

```yaml
stage-10:
  status: DONE
  started_at: 2026-08-31T15:21:45Z
  units_updated:
    - id: EP-SUP-01
      layer: backend
      path: context/code-context/backend/domains/supplier/endpoints/create.md
      frontmatter_changes: [origin, design_confidence, implemented_at, implemented_by_commit, implemented_by_task, mapped_from]
      source_refs_added: [code, test]
    - id: EP-SUP-02
      layer: backend
      path: ...
    - id: ENT-SUP-01
      layer: database
      path: ...
  indexes_updated:
    - backend/backend-index.md
    - database/database-index.md
  commit_sha: a1b2c3d
  finished_at: 2026-08-31T15:23:11Z
```

---

### 10i. On `--resume`

If `--resume` finds `stage-10.status: DONE`, skip.

If new commits were added to the branch between the last Stage 10 run and the resume (developer hand-edited), re-run Stage 10 fully — the units file `implemented_at` timestamp + commit stamp should reflect the latest commit that touched them.

---

### Skills / agents invoked

- Direct file writes to `<repo>/context/code-context/` — no subagent
- Shell for `git add` + `git commit` if using single-commit-per-stage strategy (§10g)

Never invoke `tl-semantic-context-merge` from Stage 10 — that's `/dev:commit` Stage 7. Never invoke `tl-code-map` — that's user-driven brownfield reverse-map.
