# `findings.md` — one file, stable ids, settled decisions

Every review stage writes into **one** file per unit:
`units/<repo>/findings.md`. Four sections, never four files — v2.4 consolidated
sixteen audit files into one on purpose, and a new report per reviewer would
undo it.

```
units/<repo>/findings.md
  ## Code review             /dev:commit Stage 4     Blocker + Major block
  ## Test verification       /dev:commit Stage 5     required gates block
  ## Context merge           /dev:commit Stage 7     conflicts block
  ## Settled                 any stage                decisions that carry forward
```

---

## 1. A finding's id survives runs

The old ids (`SR-C-001`, `CR-B-002`) were sequential per run, so the same defect
got a new id every time and no decision about it could be remembered. An id is
now **derived from what the finding is about**:

```
<ORIGIN>-<CLASS>-<LOCATOR>

  ORIGIN   SEC | REV | TST | CTX
  CLASS    the rule or category     injection.sql · error_handling · tier_mismatch
  LOCATOR  first 8 of sha256( repo + normalised-path + nearest enclosing symbol )
```

```
SEC-authn.missing-4f2a91c8
REV-error_handling-9b7d1e03
```

**Normalised path and enclosing symbol, never a line number.** A line number
changes when anything above it moves, which would mint a new id for an unchanged
defect and lose its decision — the exact failure this replaces. The symbol is
the function, method, class or handler the finding sits inside; where there is
none, use the path alone.

**Same defect, same id, every run, in every reviewer.** That is what makes
§3 possible.

---

## 2. Every finding carries a disposition

No finding reaches the PR body without one. Stage 8 refuses to push while any
is missing (`blocker: findings-undispositioned`).

| Severity | Blocks delivery | Allowed dispositions |
|---|---|---|
| Critical · High · Blocker · Major | **yes** | `fixed` only |
| Medium · Low · Minor | no | `fixed` · `accepted` · `deferred` |
| Nit | no | `fixed` · `accepted` · capped (§4) |

```yaml
- id: REV-naming-3c81f0aa
  severity: Minor
  origin: stage-4
  snapshot_sha: 0f50921291d9
  file: src/supplier/service.ts
  symbol: getSupplierWithDuplicates
  summary: combines fetch and de-dup; the name leaks implementation
  disposition: accepted
  decided_by: selvam
  reason: the split is planned in FEAT-SUP-004; not worth churn now
```

- **`accepted` needs a name and a reason.** An agent may not accept its own
  finding. Acceptance is asked at the pre-fan-out checkpoint, or carried from
  `## Settled`.
- **`deferred` needs a tracker id.** "Later" without a ticket is how a finding
  disappears.

---

## 3. `## Settled` — decisions carry to the next run

When a finding is `accepted` or `deferred`, it moves to `## Settled` and stays
there. Every review dispatch is handed **both** the open set and the settled
set.

| Reviewer finds | Action |
|---|---|
| a finding whose id is in `## Settled` | **do not re-raise it.** It is a decision someone already made |
| the same id, but at a **higher severity** than when it was settled | **reopen it.** The decision was made about a smaller problem |
| an id in `## Settled` that is now fixed | record it fixed; the decision stays, so a recurrence keeps it |

Without this, "disposition every finding" just produces the same dispositions
every run, and the Medium you consciously accepted last week is noise again
this week.

**A settled decision is never silently dropped.** Deleting a row from
`## Settled` is a deliberate act with a reason beside it.

---

## 4. Nit cap

At most **10** Nit findings are listed. Beyond that, report the count and the
top classes. A reviewer that emits forty naming nits has told you one thing, not
forty, and the volume buries the Blocker above it.

---

## 5. Where this is read

| Reader | Uses |
|---|---|
| Stage 6 fix loop | the open blocking set, by id |
| Stage 8 precondition | that nothing is undispositioned |
| Every review dispatch | open + settled, so decisions are respected |
| `pr-summary.md` | the disposition summary |
