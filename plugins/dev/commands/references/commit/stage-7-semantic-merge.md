## Stage 7 — Semantic context merge

**Purpose.** Merge this branch's code-context (units marked `origin: implemented` by `/dev:build` Stage 10 + index rows added) against the base branch's baseline context. Delegate to the new `tl-semantic-context-merge` skill. Prevents git's text-level merge from clobbering the graph structure when the PR merges.

**Runs after Stages 3–5 pass.** State: `REVIEW` (unchanged); MC: `devReview` (unchanged). On any semantic conflict, halts cleanly with `dev/context-merge-conflicts.md` for human resolution.

**On completion:** merged context files written locally (still on the feature branch working tree), ready for Stage 8's push.

---

### 7a. Preconditions (v2.3.25 — base branch on disk is now REQUIRED)

- Stages 3–5 clean
- `dev/build-run.md` Stage 10 has `context_units_updated: [<paths>]` list
- Access to the context-mcp `context_pull_manifest` tool for `env='main'`
- **`commit-run.md` `stage-2.base_pulled_at` is set** (v2.3.25 — base branch was pulled locally in Stage 2). Without the base on disk, this stage cannot merge against a real baseline — it would either hallucinate a diff OR (as seen in real runs) rationalize itself into a no-op. Missing → HALT with `blocker: base-branch-not-pulled-for-merge`.
- **`commit-run.md` `stage-2.base_remote_sha` matches `git rev-parse <remote>/<base>` right now** — if the remote has moved since Stage 2 ran, someone else pushed to base while this commit ran; re-fetch and re-run Stage 2 before proceeding.

### 7a.i. Non-skippable execution (v2.3.25 — closes the "reasoned it would be a no-op" gap)

**This stage MUST invoke `tl-semantic-context-merge` via the Skill tool. Internal reasoning that "it would be a no-op" is NOT sufficient evidence of execution — the skill's own invocation log is the evidence. Skip = spec violation.**

Every `/dev:commit` run — even trivial ones with zero context-unit changes — invokes the skill and records the invocation in `commit-run.md`. Zero-change results are LEGITIMATE outcomes; skipping the invocation IS NOT.

Recording format (Stage 8's precondition §8a checks this):

```yaml
stage-7:
  status: DONE
  tl_semantic_context_merge_invocation:
    invoked_at: <ISO>                              # required — presence proves invocation
    subagent_id: <id from Skill tool response>     # required — proves a real skill call happened, not a mental reasoning
    base_ref: <remote>/<base>@<sha>                # required — must match stage-2.base_remote_sha
    input_units_scanned: <count>                    # this branch's units the merge considered
    baseline_units_scanned: <count>                 # base branch's units the merge considered
    merged_units: <count>                           # units the merge wrote (may be zero for no-op)
    conflicts: <count>                              # units flagged for human resolution
    conflict_file: dev/context-merge-conflicts.md   # or null if no conflicts
  merged_at: <ISO>
```

If Stage 7 completes without this block being written → Stage 8 refuses to push (see stage-8-9-push-pr.md §8a). No workaround. No "I checked internally, it's fine" bypass.

---

### 7b. Skill invocation

Invoke `tl-semantic-context-merge` inline (no subagent per Skill Rule 9). The skill:

1. Reads `dev/build-run.md` Stage 10's touched-unit list
2. Calls `mcp__context-mcp__context_pull_manifest(solution_id=<from .jetrix/project.json>, env='main')`
3. Filters manifest to only touched units + the 3 layer indexes + 3 overviews
4. Downloads baseline copies to `dev/.context-merge-scratch/main/`
5. Reads local (feature-branch) copies of the same paths
6. Applies field-merge-rules (per-unit-file) + index-rebuild rules (per layer index)
7. On any conflict, writes `dev/context-merge-conflicts.md` and exits non-zero
8. On clean merge, writes merged files locally + writes `dev/context-merge-log.md`

See:
- `plugins/tl/skills/tl-semantic-context-merge/SKILL.md`
- `plugins/tl/skills/tl-semantic-context-merge/references/field-merge-rules.md`
- `plugins/tl/skills/tl-semantic-context-merge/references/index-rebuild.md`
- `plugins/tl/skills/tl-semantic-context-merge/references/conflict-resolution.md`

---

### 7c. Post-merge commit

After the skill emits merged files successfully:

1. `git add` the touched context files + updated indexes + updated overviews
2. Create ONE commit with message:

```
context: semantic merge from main baseline for FEAT-SUP-001

Merged N units, M base rows preserved, K our rows added.
Details: dev/context-merge-log.md
```

3. `git push` is NOT this stage's job — Stage 8 handles push.

If merge produced ZERO changes (branch's context is identical to baseline for all touched paths — rare; means no other branch has landed in between), skip the commit but still log Stage 7 done.

---

### 7d. Route on conflict

If `dev/context-merge-conflicts.md` exists after the skill returns:

1. Local state: `REVIEW → MERGE_CONFLICT` (new state; per v2.2 conventions)
2. MC status: STAYS `devReview` (do NOT flip to `blocked` — this is a resolvable state)
3. Print in-terminal:

```
✗ /dev:commit FEAT-SUP-001-1 halted at Stage 7 — semantic context merge conflicts

N conflicts require human resolution. See:
  dev/context-merge-conflicts.md

Both copies preserved in:
  dev/.context-merge-scratch/main/  (baseline)
  dev/.context-merge-scratch/ours/  (our feature-branch copy)

Fix the conflicts by ticking [x] in the file, or edit files manually,
then run:  /dev:commit FEAT-SUP-001-1 --resume
```

4. Halt — do NOT proceed to Stage 8.

The developer resolves, then `/dev:commit --resume` re-enters Stage 7, applies the human's choices, then completes cleanly.

---

### 7e. Force-continue escape hatch

Rare / emergency only. If the developer passes `--force-context-merge=ours`:

1. Every conflict auto-resolves to "ours"
2. `dev/context-merge-log.md` records `force_continue: true`
3. PR body includes a ⚠ prominent warning: "Semantic context merge force-continued; N conflicts overridden with our-side values. Human review required."
4. Stage 7 proceeds to commit + Stage 8

This is for genuine emergencies (e.g. baseline was polluted by a botched branch merge and the human confirms the "ours" tree is correct). Not for daily use.

---

### 7f. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-7:
  status: DONE | HALTED | FORCE_CONTINUED
  started_at: <ISO>
  finished_at: <ISO>
  units_touched: [EP-SUP-01, EP-SUP-02, ENT-SUP-01]
  indexes_touched: [context/backend/backend-index.md, context/database/database-index.md]
  our_rows_added: [EP-SUP-01, EP-SUP-02, ENT-SUP-01]
  baseline_rows_preserved: [EP-ORD-14, EP-INV-03, ENT-ORD-01, ENT-INV-01]
  merged_rows: []
  conflicts: 0
  merge_commit_sha: <sha>
  log_file: dev/context-merge-log.md
  conflicts_file: null | dev/context-merge-conflicts.md
```

---

### 7g. Skills / agents invoked

- `tl-semantic-context-merge` (inline; no subagent)
- `mcp__context-mcp__context_pull_manifest` (baseline read only)

Never write to `env='main'` from this stage — that's a separate flow (out of scope for `/dev:commit`).

---

### 7h. On `--resume`

If `--resume` finds `stage-7.status: DONE` AND no new commits since `finished_at`, skip.

If `stage-7.status: HALTED` (conflicts pending), re-read `dev/context-merge-conflicts.md`:
- Every conflict has `[x]` on one choice → apply choices, complete merge
- Some conflicts still `[ ] [ ] [ ]` untouched → re-halt with the same conflicts message

If `stage-7.status: FORCE_CONTINUED`, treat as DONE.

---

### 7i. Never

- Never invoke `git merge` (git line-merges the graph badly)
- Never write to baseline context (`env='main'`) from here
- Never proceed past a conflict without explicit human resolution or `--force-context-merge=ours`
- Never leave the scratch dir uncleaned after a successful merge — clean it as part of the commit
- Never bump `origin` back to `designed` — the semantic-merge preserves `implemented` (per field-merge-rules Rule "never regress")
