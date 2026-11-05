---
doc_type: recall-fixture-key
produced_by: qa
---

# Answer key — do not show this to a reviewer under test

Each defect below is planted in `src/`. A run scores **recall per class**, not
just overall, because the classes fail for different reasons and a single
percentage hides which fix is working.

| # | Id | Class | File | What is wrong | Severity | Which cause would hide it |
|---|---|---|---|---|---|---|
| 1 | `RF-01` | absence | `src/session.js` | `isExpired` is never called before granting access — an expired session is accepted | Critical | cause 2 — no changed line to attach to |
| 2 | `RF-02` | cross-file | `src/handler.js` → `src/store.js` | caller passes a possibly-undefined `userId`; the callee indexes it without a guard | Major | cause 2 — each side is correct alone |
| 3 | `RF-03` | matches-existing-pattern | `src/handler.js` | no null guard on input, exactly like the three handlers around it | Major | **cause 4 — the reviewer is told not to flag what the repo does consistently** |
| 4 | `RF-04` | security | `src/store.js` | query built by string concatenation from user input | Critical | cause 1 — invisible if the diff is empty |
| 5 | `RF-05` | business-rule | `src/session.js` | BR-1 says one active session per user; nothing enforces it | Major | cause 3 — merges into "validation" with RF-03 |
| 6 | `RF-06` | crypto | `src/session.js` | session token from `Math.random()` — predictable | High | none; this is a positive control that most reviewers should catch |

## Scoring

```
recall(class) = found(class) / planted(class)
```

- **Found** means reported at any severity. A finding reported as Minor still
  counts as found — that is why the review must report *found-but-downgraded*
  separately from *not found*.
- A merged finding covering two distinct defects counts as **one**.
- Record the snapshot sha and the file count the reviewer stated. A run that
  could not state its scope scores zero regardless of what it found.

## Baselines

| Reviewer | Score | Missed | Notes |
|---|---|---|---|
| `/dev:commit`, improvised scope (the run that motivated this) | 3 / 5 | 2 | no snapshot; reviewed a self-selected file set |
| Automated security scanner (`security-guidance` plugin), 2026-11-04 | 3 / 6 clean + 1 merged | `RF-05` | found `RF-01`, `RF-04`, `RF-06`; merged `RF-02`+`RF-03` into one IDOR finding |

**What the scanner baseline teaches, and why it is kept:**

- **`RF-05` is the hard one.** A business rule lives in a document, not in a
  code signature — no generic scanner can match it. Only a reviewer handed the
  parent's `business-rules.md` can. That is Dimension 5, and it is the argument
  for keeping `dev-stack-adaptive-code-review` as the blocking gate rather than
  swapping in a generic reviewer.
- **`RF-02` + `RF-03` merged into one finding.** Two independently-fixable
  defects reported as one — exactly the failure Rule 5 now forbids. Scoring
  counts that as **one found, one missed**.
- **A scanner is a good second opinion and a poor gate.** It caught the two
  pattern-matchable defects cleanly and missed the one that required knowing
  what the software was supposed to do.
