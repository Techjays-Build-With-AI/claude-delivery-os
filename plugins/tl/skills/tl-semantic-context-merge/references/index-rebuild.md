# Index-rebuild — row-union merge for layer indexes

**Purpose.** How to merge the three layer indexes — `context/frontend/frontend-index.md`, `context/backend/backend-index.md`, `context/database/database-index.md` (filenames on disk; frontmatter doc_types are `page-index` / `endpoint-index` / `entity-index` respectively) — when both baseline (`main`) and our feature-branch copy have edits.

Rule of thumb: **indexes are tables keyed by unit_id.** Merge is a row union with per-row field-level LWW.

---

## Index file structure

Every layer index has the same shape:

```markdown
---
doc_type: layer-index
layer: backend                       # or frontend, or database
schema_version: 1.0
updated_at: <ISO>
---

# Backend endpoints

| Unit ID | Path | Method | Owner | Origin | Related Features |
|---|---|---|---|---|---|
| EP-SUP-01 | /supplier | POST | backend-team | implemented | FEAT-SUP-001 |
| EP-ORD-14 | /orders | GET | backend-team | implemented | FEAT-ORD-004 |
| EP-INV-03 | /invoices/:id | GET | backend-team | designed | FEAT-INV-002 |
| ...
```

The columns vary by layer:

- **Frontend page-index**: `Unit ID | Path (route) | Owner | Origin | Related Features`
- **Backend endpoint-index**: `Unit ID | Path | Method | Owner | Origin | Related Features`
- **Database entity-index**: `Unit ID | Table Name | Owner | Origin | Related Features`

All three: **Unit ID is the primary key.**

---

## The row-union merge

For each of the three indexes:

### Step 1 — Parse both sides into records

Read baseline and our copy. Parse the table into two dicts keyed by `unit_id`:

```
baseline_rows = {
  'EP-SUP-01': {path: '/supplier', method: 'POST', owner: 'backend-team', origin: 'designed', related_features: ['FEAT-SUP-001']},
  'EP-ORD-14': {path: '/orders', method: 'GET', owner: 'backend-team', origin: 'implemented', related_features: ['FEAT-ORD-004']},
}

our_rows = {
  'EP-SUP-01': {path: '/supplier', method: 'POST', owner: 'backend-team', origin: 'implemented', related_features: ['FEAT-SUP-001']},
  'EP-SUP-02': {path: '/supplier/duplicate-check', method: 'POST', owner: 'backend-team', origin: 'implemented', related_features: ['FEAT-SUP-001']},
}
```

### Step 2 — Take the row union

Combined key set: `{EP-SUP-01, EP-SUP-02, EP-ORD-14}`.

For each key:

- **In baseline only** → take baseline row unchanged. Track under `baseline_rows_preserved` in the merge log.
- **In our copy only** → take our row unchanged. Track under `our_rows_added` in the merge log.
- **In both** → per-field merge (see Step 3).

### Step 3 — Per-field merge on rows-in-both

For each field in a same-unit-id row:

| Field | Rule |
|---|---|
| `path` | LWW by the associated *unit file's* `updated_at` (not the index's) |
| `method` (endpoint) | LWW by unit file's `updated_at`. If both changed → CONFLICT (method change = contract break) |
| `table_name` (entity) | LWW by unit file's `updated_at`. If both changed → CONFLICT (table rename is a data-layer change) |
| `owner` | LWW by unit file's `updated_at`. Tie → CONFLICT |
| `origin` | **Transition-ordered LWW**: `deprecated > implemented > designed`; never regress |
| `related_features` | **Union of arrays**; dedupe; preserve stable order |

Rationale: index fields are derived from the unit files — the unit file's `updated_at` is the source of truth. Never use the index's `updated_at` for row-level LWW.

### Step 4 — Rebuild the table

- Rows sorted by `unit_id` ascending (stable, deterministic).
- Columns in the canonical order for that layer index.
- Update the index's own `updated_at` frontmatter to `max(baseline.updated_at, ours.updated_at, now())`.

Never leave stale `updated_at` on the merged index.

### Step 5 — Log the union outcome

Append to `dev/context-merge-log.md`:

```yaml
- file: context/backend/backend-index.md
  action: row_union
  our_rows_added: [EP-SUP-02]
  baseline_rows_preserved: [EP-ORD-14]
  merged_rows: [EP-SUP-01]
  field_conflicts: none
  origin_transitions:
    - unit_id: EP-SUP-01
      from: designed
      to: implemented
      by: this_branch
```

---

## Overview files (`_overview.md`)

Each layer has an `_overview.md` — narrative + unit-count summary. Merge rules:

- The prose body: LWW by the file's `updated_at`
- Any tables (e.g. "Recent additions") — row-union like the index

If the overview mentions unit counts (`## 47 endpoints across 6 modules`), regenerate that number from the merged index after the union. Never leave a stale count.

---

## Examples

### Example 1 — Clean row union

**Baseline `backend-index.md`:**

| Unit ID | Path | Method | Owner | Origin |
|---|---|---|---|---|
| EP-ORD-14 | /orders | GET | backend-team | implemented |
| EP-INV-03 | /invoices/:id | GET | backend-team | designed |

**Our `backend-index.md`:**

| Unit ID | Path | Method | Owner | Origin |
|---|---|---|---|---|
| EP-SUP-01 | /supplier | POST | backend-team | implemented |
| EP-SUP-02 | /supplier/duplicate-check | POST | backend-team | implemented |

**Merged:**

| Unit ID | Path | Method | Owner | Origin |
|---|---|---|---|---|
| EP-INV-03 | /invoices/:id | GET | backend-team | designed |
| EP-ORD-14 | /orders | GET | backend-team | implemented |
| EP-SUP-01 | /supplier | POST | backend-team | implemented |
| EP-SUP-02 | /supplier/duplicate-check | POST | backend-team | implemented |

Row union, sorted by `unit_id`. Zero conflicts.

### Example 2 — Row-in-both with origin transition

**Baseline row for `EP-SUP-01`:** `origin: designed, path: null` (someone had planned this endpoint earlier)

**Our row for `EP-SUP-01`:** `origin: implemented, path: /supplier`

**Merged:** `origin: implemented, path: /supplier` — transition forward wins.

### Example 3 — Method change conflict

**Baseline row for `EP-USR-01`:** `method: POST` (baseline branch changed it)

**Our row for `EP-USR-01`:** `method: PUT` (we also changed it)

Different methods, both changed → CONFLICT. Halt. Write to `context-merge-conflicts.md`.

### Example 4 — related_features union

**Baseline row for `EP-USR-01`:** `related_features: [FEAT-USR-001]`

**Our row for `EP-USR-01`:** `related_features: [FEAT-USR-001, FEAT-SUP-001]` (we added the supplier feature dep)

**Merged:** `related_features: [FEAT-USR-001, FEAT-SUP-001]` — union.

---

## Hard rules

**Rule 1 — Row deletion is never automatic.** If a row exists on baseline and is missing on our side, we take the baseline row. Never delete rows during merge.

**Rule 2 — Row addition is always safe.** New rows on either side are always added to the merged index.

**Rule 3 — Field-level LWW uses the unit-file's `updated_at`, not the index's.**

**Rule 4 — Transition-order beats LWW for `origin`.** Never regress `origin`.

**Rule 5 — Method/table_name changes require conflict resolution.** They're contract breaks.

**Rule 6 — Deterministic sort order.** Always sort merged rows by `unit_id` ascending. This makes future diffs stable.

**Rule 7 — Regenerate derived counts.** Overview files that reference counts must be regenerated after the row-union step.

---

## Not this doc's job

- Per-file frontmatter field rules → `field-merge-rules.md`
- Conflict format + halt → `conflict-resolution.md`
