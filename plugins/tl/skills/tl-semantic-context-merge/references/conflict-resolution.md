# Conflict resolution — how to halt cleanly

**Purpose.** When the field-merge or index-rebuild logic hits a genuine semantic conflict, this skill halts. This doc defines what "halt cleanly" looks like: the file format, the state transitions, and what the human sees.

The invariant: **never silently auto-resolve a conflict.** Better to halt and let a human decide than push a subtly wrong context graph.

---

## What counts as a "real" conflict

Not every field disagreement is a conflict. Most cases resolve via LWW cleanly. A **real** conflict fires when:

1. **Both sides changed the same scalar field to different values, AND the tie-breaker (`updated_at`) is equal.** No LWW winner.
2. **A field that must be immutable differs** (e.g. `unit_id`, `unit_type`, `layer`). Data-model integrity break.
3. **A structural change is semantically incompatible** (e.g. an endpoint `method` changed on both sides to different verbs; an entity `table_name` changed on both sides to different tables). LWW would be dangerous — data-layer contract break.
4. **`origin` would regress with matching timestamps** (extremely rare; usually caught by transition-order rule).
5. **A Contract or Fields section describes incompatible types on both sides** (e.g. baseline says field `amount: decimal(10,2)`, ours says `amount: int64`).

**Not** a conflict:
- Both sides added distinct fields to `depends_on` → union, no conflict
- Both sides bumped `line` to different numbers → LWW by `updated_at`, no conflict
- Baseline has `owner: X`, ours removed the field entirely → keep baseline value, no conflict
- Origin transitions (`designed → implemented`) with a clear winner → no conflict

---

## Halt sequence

When a conflict is detected:

1. Complete the merge for **every other** file that had no conflict. Write those partial results.
2. For any conflicting file, do NOT write the merged copy. Preserve both sides in the scratch dir (`dev/.context-merge-scratch/`):
   - `dev/.context-merge-scratch/main/<path>` — baseline copy
   - `dev/.context-merge-scratch/ours/<path>` — our copy
3. Append a conflict entry to `dev/context-merge-conflicts.md` (see format below).
4. Exit non-zero to `/dev:commit`.
5. `/dev:commit` handles the halt: local state → `MERGE_CONFLICT`; MC status stays `inProgress` (do NOT flip to `blocked` — this is a mergeable state pending human input); prints the escalation summary; halts.

---

## `dev/context-merge-conflicts.md` format

Frontmatter:

```yaml
---
doc_type: context-merge-conflicts
schema_version: 1.0
produced_by: tl-semantic-context-merge
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: 2026-08-31T15:30:00Z
resolution_required_by: human
---
```

Body — one entry per conflict:

```markdown
# Context-merge conflicts — resolution required

The semantic-context-merge could not auto-resolve the following. Please
review each entry and choose either the baseline value or our value (or
manually merge). Then run `/dev:commit --resume` to continue.

Both sides' raw copies are preserved in:
  dev/.context-merge-scratch/main/  (baseline)
  dev/.context-merge-scratch/ours/  (our feature-branch copy)

---

## Conflict 1 — Endpoint contract change on both sides

- File: context/backend/endpoints/user/EP-USR-01.md
- Field: contract (method)
- Baseline: method: PUT   (updated_at 2026-08-30T14:00:00Z, from FEAT-USR-014 branch merged 2 hours ago)
- Ours:     method: POST  (updated_at 2026-08-30T14:00:00Z, from this build)
- Impact: HTTP method is a contract break for consumers. LWW cannot resolve.

Choose:
  [ ] Keep baseline (PUT) — indicates FEAT-USR-014's decision stands; we adapt our code
  [ ] Keep ours (POST) — indicates our decision stands; we file follow-up to reconcile with FEAT-USR-014
  [ ] Manual merge — edit the file directly, then run `/dev:commit --resume`

Related decisions:
- FEAT-USR-014 branch: <find via `git log --all --oneline | grep FEAT-USR-014`>
- Our branch's DEC: <see dev/decisions.md for the POST reasoning>

---

## Conflict 2 — Owner field with tied timestamps

- File: context/backend/endpoints/supplier/EP-SUP-01.md
- Field: owner
- Baseline: owner: platform-team   (updated_at 2026-08-30T14:20:00Z, from team-restructure branch)
- Ours:     owner: backend-team    (updated_at 2026-08-30T14:20:00Z)
- Impact: Ownership determines who reviews future changes to this endpoint.

Choose:
  [ ] Keep baseline (platform-team)
  [ ] Keep ours (backend-team)
```

Each conflict gets:
- Sequential number (`Conflict N`)
- File path
- Field name (or section name for body conflicts)
- Both values + timestamps + provenance hint
- Impact statement (why LWW isn't safe)
- Explicit choices with `[ ]` checkboxes

---

## What `/dev:commit --resume` does after human resolution

Human either:

- **Ticks a `[ ]` box** by writing an `x` in the brackets, then runs `/dev:commit --resume`
- OR **manually edits the file** with their preferred merged content, then runs `/dev:commit --resume`

`/dev:commit --resume` at Stage 7:

1. Re-reads `dev/context-merge-conflicts.md`
2. For each `[x]`-ticked choice → apply the chosen value + rewrite the file
3. For any manual-merge case (no ticks but the target file was modified after the halt) → accept the file as-is
4. Any conflict still with `[ ] [ ] [ ]` untouched → re-halt

5. After all conflicts resolved → clear `dev/context-merge-conflicts.md` (move to `dev/context-merge-conflicts.<timestamp>.md` for audit)
6. Proceed to Stage 8 (push).

---

## Never auto-resolve these

**Rule 1 — Never auto-resolve `unit_id` / `unit_type` / `layer` differences.** Data-model integrity.

**Rule 2 — Never auto-resolve method / table_name changes on both sides.** Contract break.

**Rule 3 — Never regress `origin`.** Transition-order enforcement.

**Rule 4 — Never LWW on tied timestamps.** By definition tied → no LWW winner → conflict.

**Rule 5 — Never take our side just because we're "current".** If baseline's `updated_at` is truly later (rare — someone force-updated), baseline wins per LWW; we never claim ours by fiat.

---

## Guardrails on the halt

- Never touch MC status here (`/dev:commit` handles that per Stage 7's routing)
- Never mutate the branch state (don't reset commits; don't rewrite history)
- Never delete the scratch dir — audit trail
- Never mark the merge as "done" while conflicts remain unfilled

---

## Rare-case: force-continue (developer override)

If the human chooses to force-continue with our values everywhere (rare, dev-emergency), the escape hatch is:

```
/dev:commit --resume --force-context-merge=ours
```

This overrides every conflict to "ours" and proceeds. The merge log records `force_continue: true` for audit. Not for regular use — surface prominently in the PR summary + require a human sign-off in review.

---

## Not this doc's job

- Field-level merge rules → `field-merge-rules.md`
- Index row-union rules → `index-rebuild.md`
- The `/dev:commit` orchestrator's routing after halt → `plugins/dev/commands/references/commit/stage-7-semantic-merge.md`
