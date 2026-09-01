# Field-merge rules — per unit file frontmatter + body

**Purpose.** Concrete rules for how each field on a code-context unit file is merged when both the baseline (`main`) copy and the feature-branch copy have changes.

Applied *after* Phase 1 has both copies in hand for a specific unit id. Never git-line-merged; always field-merged.

---

## Merge context

Every unit file (page / endpoint / entity) has:

- **Frontmatter** — YAML block with typed fields (owner, origin, status, updated_at, etc.)
- **Body sections** — markdown headings + prose (Purpose, Contract, Source References, Related Units, etc.)

Merge treats these separately.

---

## Frontmatter field rules

Read both `updated_at` timestamps first. The one with the later timestamp is the "winner" copy for scalar-field LWW. Ties → conflict (halt).

### 1. `unit_id` (string, immutable)

- Rule: **must match on both sides**. If different → conflict (data corruption; halt).
- Never merged.

### 2. `unit_type` (enum: page | endpoint | entity)

- Rule: **must match on both sides**. Different → conflict.

### 3. `updated_at` (ISO 8601 timestamp)

- Rule: take the **max** of both sides. This becomes the new file's `updated_at`.

### 4. `origin` (enum: designed | implemented | deprecated)

- Rule: **transition-ordered LWW**.
  - `deprecated` > `implemented` > `designed`
  - If both sides agree, take that.
  - If one side is `deprecated` and the other is `implemented`, take `deprecated` (it's a more recent decision).
  - If one side is `implemented` and the other is `designed`, take `implemented` (ours or theirs — whoever moved it forward wins).
- **Never regress** (e.g. never take `designed` over `implemented`) — that would be a rollback and needs human review.

### 5. `owner` (string, e.g. team-name or user)

- Rule: **LWW by `updated_at`**. If both sides changed AND our-copy's `updated_at` == baseline's `updated_at`, → conflict.

### 6. `layer` (enum: frontend | backend | database)

- Rule: **must match on both sides**. Different → conflict (unit moved layers — a rename in disguise; human decides).

### 7. `path` (source file path where the unit lives)

- Rule: **LWW by `updated_at`**. Common case: refactor moved the file. Later timestamp wins.
- Exception: if the path is `null` on one side (unit designed but not implemented), take the non-null side.

### 8. `line` (line number, integer)

- Rule: **LWW by `updated_at`**. Line numbers drift with every commit — always take the newer one.

### 9. `depends_on` (array of unit_ids)

- Rule: **union**. Concatenate arrays, deduplicate exact-match. Preserve stable order (baseline first, then our new entries).

### 10. `related_features` (array of feature_ids)

- Rule: **union**. Same as `depends_on`.

### 11. `deprecated_reason` (string, only present when origin = deprecated)

- Rule: **LWW by `updated_at`**. If both deprecated with different reasons, LWW.

### 12. `status` — reserved field, NOT the delivery status

This field, if present, tracks the unit's contract status (e.g. `draft`, `stable`, `deprecated`). Not delivery status.

- Rule: **transition-ordered LWW**.
  - `deprecated` > `stable` > `draft`
- Same "never regress" caution as `origin`.

### 13. Custom fields (any other key)

- Rule: **LWW by `updated_at`**. If both sides changed AND `updated_at` matches → conflict.

### 14. Absent-on-one-side

If a field is present on baseline and absent on our side, keep the baseline value.
If a field is present on our side and absent on baseline, keep our value (this is us introducing the field).

---

## Body section rules

Body sections are structured by `## Heading` blocks. Merge is section-by-section using the heading as the key.

### 1. `## Purpose`

- Rule: **LWW by `updated_at`**. Whoever wrote it more recently wins.
- Rationale: purpose is definitional; conflicting purposes = design drift; if that happens, catch it via later review.

### 2. `## Contract` (endpoints only — the request/response shape)

- Rule: **LWW by `updated_at`**.
- Special note: if the two contracts differ semantically (different fields, different types), that's a contract change with a downstream impact. LWW wins, but log to `context-merge-log.md` as `contract_changed_via_merge: true` for reviewer attention.

### 3. `## Fields` (entities only — the data model)

- Rule: **union by field name, LWW by `updated_at` per field's type/nullability**.
  - Both sides have `tax_id: string, unique` → keep as-is
  - Baseline has `tax_id: string`; ours has `tax_id: string, unique` → keep the more constrained (ours' `updated_at` later) with LWW
  - Both sides declare `tax_id` with **incompatible** types (e.g. one says `string`, the other `int`) → CONFLICT, halt

### 4. `## Source References`

- Rule: **append-only union**. Merge both lists, dedupe exact-match rows. Order: baseline lines first (preserving history), then our new lines appended.
- Never delete a Source Reference line that exists on baseline.

### 5. `## Related Units`

- Rule: **union by unit_id**. Same as frontmatter `depends_on`.

### 6. `## Change History` (if present)

- Rule: **append-only chronological merge**. Interleave by date; dedupe exact-match entries.

### 7. `## Notes` / `## Rationale` / free-form sections

- Rule: **LWW by `updated_at`**. These are prose fields; can't reasonably auto-merge prose.
- If both sides added distinct notes → LWW. Note in `context-merge-log.md`: `notes_lww: true, other_side_content_available_in_scratch`.

### 8. Sections present on only one side

- Take that side unchanged.

---

## Re-render after merge

After field + section merging, re-emit the file:

1. Frontmatter block first (fields in canonical order: `unit_id`, `unit_type`, `layer`, `owner`, `origin`, `status`, `path`, `line`, `depends_on`, `related_features`, `updated_at`, then any custom keys alphabetized).
2. Blank line.
3. Body sections in canonical order for the unit type:
   - Page: `## Purpose`, `## Contract` (URL/params/behavior), `## Fields` (if it has form fields), `## Source References`, `## Related Units`, `## Change History`, `## Notes`.
   - Endpoint: `## Purpose`, `## Contract`, `## Source References`, `## Related Units`, `## Change History`, `## Notes`.
   - Entity: `## Purpose`, `## Fields`, `## Source References`, `## Related Units`, `## Change History`, `## Notes`.
4. Sections not in the canonical list append at the end preserving heading names.

---

## Examples

### Example 1 — Clean field-level LWW

Baseline `EP-SUP-01.md`:
```yaml
---
unit_id: EP-SUP-01
unit_type: endpoint
owner: backend-team
origin: designed
path: null
line: null
updated_at: 2026-08-25T10:00:00Z
---
```

Our (feature branch):
```yaml
---
unit_id: EP-SUP-01
unit_type: endpoint
owner: backend-team
origin: implemented
path: src/routes/supplier.ts
line: 42
updated_at: 2026-08-30T14:20:00Z
---
```

Merged:
```yaml
---
unit_id: EP-SUP-01
unit_type: endpoint
owner: backend-team
origin: implemented           # transition forward
path: src/routes/supplier.ts  # took our non-null
line: 42
updated_at: 2026-08-30T14:20:00Z  # max
---
```

### Example 2 — Real conflict on owner

Baseline (updated by team-restructure branch):
```yaml
owner: platform-team
updated_at: 2026-08-30T14:20:00Z
```

Our:
```yaml
owner: backend-team
updated_at: 2026-08-30T14:20:00Z
```

Timestamps equal + owner differs → CONFLICT. Halt. Write to `context-merge-conflicts.md`.

### Example 3 — Origin regression attempt

Baseline: `origin: implemented`, `updated_at: 2026-08-30`
Our: `origin: designed`, `updated_at: 2026-08-29`

Never regress → keep `implemented`. Log to `context-merge-log.md`: `origin_regression_prevented: true`.

Actually the correct handling: if OUR file says `designed` and baseline says `implemented`, then baseline is downstream of us and someone else already implemented. Keep `implemented`. This is a rare case (our /dev:build had an outdated view). Continue merging without halting; just log.

### Example 4 — Contract change via merge

Baseline (from another branch merged first) added a required field to Contract.
Our: added a different required field.

Both timestamps present, ours newer → LWW takes ours.

But this is dangerous — the baseline change might have shipped consumers that rely on THEIR field. Log `contract_changed_via_merge: true` for reviewer attention. Don't halt (LWW resolved cleanly by rule), but surface prominently in the merge log.

---

## Not this doc's job

- The row-union rule for indexes lives in `index-rebuild.md`
- The conflict-halt behaviour + `context-merge-conflicts.md` format lives in `conflict-resolution.md`
