## Stage 10 — Update code-context units (`designed → implemented`)

**Purpose.** For every TL unit this task built (endpoint, entity, page), update the unit file in the target repo's `<repo>/context/code-context/` to reflect that it's now real code, not just design. Adds source-file citation + commit stamp + confidence promotion.

**Runs after Stage 9 security review passes.** State: `agentExecuting` (unchanged). MC: `inProgress`.

**On completion:** every owned unit is marked `origin: implemented` with the concrete evidence pointing at the code. Layer indexes reflect the new status. Ready for `/dev:commit` Stage 7's semantic merge.

---

### 10a. Preconditions (v2.3.27 — HARD gates)

- `units/<repo>/status.md § ## Run history` `stage-9.status: DONE` (or SKIPPED)
- Branch commits present — `git log <base>..HEAD` returns ≥ 1 commit
- Target repo has `<repo>/context/code-context/` — created by `tl-feature-planning` (internal) OR `/tl:code-map`
- **Stage 9 repair loop invoked if it had Critical findings (v2.3.27)** — read `status.md` § `## Run history` `stage-9.findings`. If pre-repair `findings.critical > 0` but no `stage-9.repair_loop_invocation.invoked_at` block exists → HALT with `blocker: stage-9-repair-loop-not-invoked`. Same enforcement pattern as `/dev:commit` Stage 8 §8a for its fix loops. Flipping context units to `origin: implemented` on code with an unaddressed Critical security finding would misrepresent the graph as "verified" when the review actively said "block".
- **Stage 9 final findings ARE clean** — after any repair loop, `stage-9.findings.critical` must be zero. Non-zero → HALT with `blocker: stage-9-repair-loop-did-not-clear-critical` (fix loop ran but ended ESCALATED; check `units/<repo>/status.md § ## Run history (a BLOCKED entry)`).

If context tree is missing → escalate. `/dev:plan` should have run `tl-feature-planning` (internal) to create the graph; if we got here without it, that's a plan-side gap.

---

### 10b. Identify owned units

The units to update are the ones this task owns (from `implementation.md` §1 Build sequence Units column + §3 Operations exposed and consumed + §4 Stored data changes + §5 User-facing surfaces for parent-alone, OR `units/<repo>/implementation.md` for sub-task).

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
# Was (from forward planning)
origin: designed
design_confidence: Likely                   # or Assumed

# After Stage 10 update
origin: implemented
status: Active                              # from Proposed - the unit is real now
implementation_state: Implemented           # from Planned - THIS is what readers filter on
design_confidence: Confirmed                # promote from Likely (design was verified by working code)
implemented_at: 2026-08-31T15:21:44Z        # ADD (from git commit timestamp of last touching commit)
implemented_by_commit: <HEAD SHA>           # ADD
implemented_by_task: FEAT-SUP-001-1         # ADD (feature id + sub-task suffix if applicable)
mapped_from: src/routes/supplier.ts         # ADD (canonical source file)
mapped_from_line: 42                        # ADD (line of the export / entry point, if resolvable)
mapped_from_commit: <sha>                   # ADD — `git log -1 --format=%H -- <that file>`
```

**`mapped_from_commit` is the SOURCE FILE's commit, not the branch HEAD.** `implemented_by_commit` already records where the work landed; this records which version of the file the unit actually describes, and they are different questions. Take it from `git log -1 --format=%H -- <that file>`. Without it the unit cannot be checked for drift later — and a unit nobody can check is one that quietly goes wrong.

**All four lifecycle fields move together, or none of them do.** `origin`, `status`,
`implementation_state` and `design_confidence` describe one fact - this unit is built - and a reader
filters on whichever one they happen to use. A real run flipped `origin` alone and left 17 units
reading `origin: implemented` beside `implementation_state: Planned`; the code was there, the build
reported COMPLETE, and anyone asking the context what was built was told the licence domain had never
been started. Writing one field and not the rest is worse than writing none, because the
contradiction looks like data rather than a bug.

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

- Update the row's `Status` column to match the unit's new `status:` — **`Proposed` → `Active`**. Take the value from the unit file rather than assuming a vocabulary: an index row left at `Proposed` beside an implemented unit is the same contradiction as the frontmatter one, and it is what a reader sees first.
- Update the row's `Confidence` column (if present) per §10c rules
- If the row's `Summary` cell drifted from the unit's `## Summary` (rare — should stay in sync), take the unit's current summary as truth

---

### 10e.i. Completion check - no unit this task built may still read `Planned`

Before Stage 10 reports DONE, re-read every unit you touched **and** every unit cited in this task's
`implementation.md`, and confirm none still carries `implementation_state: Planned` or
`status: Proposed`.

Any that does is one of two things, and both need saying out loud rather than passing silently:

| What it means | What to do |
|---|---|
| You built it but missed the flip | Flip it now, then re-check |
| Another task's sub-task built it - a **shared unit** attributed to a different feature in the index | Flip it and record `implemented_by_task` as the task that actually wrote the code |

The second case is the one that bites. §10b claims units by grepping the index's `Used by Features`
column for THIS task's id, so a unit shared across features - a licence table used by DASH, LICN and
EXIT - is claimed only by the feature the index names. When a different feature's sub-task writes the
code, nobody claims it, and it stays `Planned` forever while the code sits in the repo. **Ownership
for this check is whoever wrote the code, not whoever the index attributes it to.**

Report the count in `status.md` § `## Run history` as `stage-10.units_flipped` and
`stage-10.units_still_planned`. A non-zero `units_still_planned` is a finding, not a footnote: name
each one in the build summary. The build must not report `COMPLETE` while the context says work it
just did was never started.

---

### 10f. Don't touch base branch's context

**Critical.** The updates happen on the FEATURE BRANCH ONLY. Base branch (`develop`) keeps whatever it has. `/dev:commit`'s Stage 7 semantic merge (via `tl-semantic-context-merge` skill) is what reconciles the two later.

Do NOT try to preview the merge here — just write to HEAD; commit later.

---

### 10g. Leave the updates in the working tree — NO staging, NO commit (v2.3.20)

**Per the top-of-file invariant in `build.md`, /dev:build never runs `git add`, `git commit`, or `git push`. Stage 10's context-unit updates land in the working tree and stay there until `/dev:commit` gathers them.**

The updates ARE part of what `/dev:commit` will gather:
- Source + test code from Stages 5-6 (working tree, uncommitted)
- Context-unit updates from Stage 10 (working tree, uncommitted)
- Any pr-summary.md § ## How to verify written by Stage 11 (working tree, uncommitted)

`/dev:commit`'s Stage N gather-working-tree step collects ALL of this and structures the commit(s) per the user's preference (default: one well-formed commit; `--structured`: multiple by convention). The developer sees ONE clean commit history from `/dev:commit`, not a scatter of per-stage commits from `/dev:build`.

Under NO circumstances does Stage 10 shell out to git. If the codebase you're mapping REQUIRES a specific staging pattern (e.g. some monorepo tools that scan git index), escalate as `units/<repo>/status.md § ## Run history (a BLOCKED entry)` — don't unilaterally add git operations to Stage 10.

---

### 10h. Progress log format

Append to `units/<repo>/status.md § ## Run history`:

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
- No shell to git (v2.3.20). Stage 10 does NOT stage, does NOT commit. See §10g and the top-of-file invariant in `build.md`.

Never invoke `tl-semantic-context-merge` from Stage 10 — that's `/dev:commit` Stage 7. Never invoke `tl-code-map` — that's user-driven brownfield reverse-map.
