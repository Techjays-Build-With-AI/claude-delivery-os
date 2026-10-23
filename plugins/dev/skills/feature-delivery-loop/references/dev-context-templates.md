# Unit file templates

Every file under `units/<repo>/`. These are written by one stage and read back by another, so the shape is a
contract, not a style preference — `--resume` reads `status.md` to answer *where am I*, and the fix loop reads
`findings.md` to answer *what is still open*.

**Three rules hold across all of them:**

1. **Machine state lives in frontmatter; narrative lives in sections.** A stage that needs to know whether it may
   run reads one YAML key, never a paragraph.
2. **History is append-only.** Never rewrite an earlier entry — a run that failed and was retried is the record
   that matters most when someone asks why the branch looks like that.
3. **Never delete a row to make a table look clean.** A dropped acceptance row and a passing one are
   indistinguishable afterwards, which is the failure these files exist to prevent.

---

## 1. `status.md` — state, history, proof

The single state file. Three parts, and consumers read only the part they need.

```md
---
doc_type: unit-status
unit: backend                     # the repo slug; matches cache/repolocation.json
feature_id: FEAT-SUP-001
status: inProgress                # the shared value — identical here, on Jetrix, on any tracker
phase: built                      # local only, never pushed (conventions §5)
branch: feature/FEAT-SUP-001-supplier-onboarding-backend
base_branch: develop
base_sha: 4f2c9a1
owner_lock: dev-agent-2026-10-21T09:14:02Z
ready_for_dev_build: true
ready_for_dev_commit: false
blocker_ids: []                   # PB-### still open
status_pushed: true
tests_only: false
updated_at: 2026-10-21T11:02:17Z
---

## Run history

One entry per stage, appended. Newest last, so the file reads in the order things happened.

### 2026-10-21T09:14:02Z · /dev:plan · Stage 2 analysis
- skill: tl-feature-planning
- in:   feature.md · acceptance-criteria.md · EP-SUP-02 · ENT-SUP-01
- out:  analysis.md (build_sequence 12 steps · impact_matrix 12/12 · risks 3)
- 41s

### 2026-10-21T09:19:40Z · /dev:build · Stage 7 execute tests
- cmd:  poetry run pytest -q
- out:  273 passed · 28 skipped · exit 0
- 2m04s

### 2026-10-21T10:48:11Z · /dev:build · Stage 8 verdict
- final_status: COMPLETE     # COMPLETE · PARTIAL_DEFERRED · PARTIAL_HARNESS · PARTIAL_FAILURES
- 12/12 §1 steps · 9/9 acceptance rows settled

### 2026-10-21T11:02:17Z · BLOCKED
- why:  PB-004 — the ERP sandbox rejects the test credential
- what is unblocked: nothing in this unit; frontend is unaffected
- next: /dev:resolve --plan Feature-4
```

**Every entry carries a timestamp, the command, the stage, and what it produced.** An entry with no output is
a stage that ran and did nothing, which is worth recording for exactly that reason.

**A `BLOCKED` entry replaces the old `escalation-<n>.md`.** It names *why*, *what is still unblocked* (so the
other units are not stopped by association), and the command that resolves it.

```md
## Acceptance

One row per parent assertion. **Every parent AC, BR, NFR and test scenario gets a row** — including the ones
that cannot be settled here.

| Kind | ID | Assertion | Evidence | Result | Notes |
|---|---|---|---|---|---|
| AC | AC-03 | Rejects a duplicate supplier tag | `test_supplier.py::test_dup_tag` | ✅ pass | |
| BR | BR-07 | One open record per normalised tag | `test_supplier.py::test_unique` | ✅ pass | |
| AC | AC-08 | Coordinator sees the rejection reason | — | ⏸ deferred-to-e2e | needs the frontend unit |
| NFR | NFR-02 | p95 under 400ms at 50 rps | load run, 310ms | ✅ pass | |
| TS | TS-11 | ERP sync retries twice then alerts | — | verified: not-verified | ERP sandbox unavailable |
```

Results are controlled: `✅ pass` · `❌ fail` · `⏸ deferred-to-e2e` · `verified: manually` ·
`verified: not-verified`.

**`deferred-to-e2e` is a cross-unit row** — it closes only when every sibling unit is done, which is why the
parent's `status.md` carries a per-unit table and the last unit to land resolves them.

**`verified: not-verified` is not a failure and not a pass.** It says a check could not run. Scoring it either
way is the lie these columns exist to prevent.

---

## 2. `findings.md` — fix-loop state, read and rewritten

**Not an archive.** Build Stage 9 and commit Stages 3–5 write it; **Stage 6 reads it**, fixes each finding,
re-runs the originating stage and rewrites this file. Stage 8 refuses to push without the resulting trace.

```md
---
doc_type: unit-findings
unit: backend
fix_loop_invocation: 2026-10-21T10:31:00Z
open: 1
fixed: 4
escalated: 0
---

## Security — build
*Critical-blocking only. Build does not stop for Medium.*

### SEC-B-01 · Critical · open · attempts_used: 1/3
Raw SQL interpolation in `suppliers/repo.py:142`.
- found by: Stage 9 · 2026-10-21T10:22:00Z
- fix: parameterise; re-run Stage 9
- attempt 1 (10:31): parameterised, re-run clean — pending re-verify

## Security — commit
*Critical + High.*
None.

## Code review
*7 dimensions × Blocker / Major / Minor / Nit.*

### CR-04 · Minor · fixed · attempts_used: 1/3
`list_suppliers` returns an unbounded page.
- dimension: performance
- fix: default `limit=50`, cap 500 · fixed 10:44

## Context merge
None — 3 units merged cleanly.
```

**Every finding carries `id · severity · origin stage · status · attempts_used`**, bounded at **3 focused fixes
and 2 broad stage re-runs**. Status moves `open → fixed → escalated` and never skips.

**Bounds exceeded → the run halts** and the reason goes in `status.md`'s `## Run history` as a `BLOCKED` entry.
Each unit runs its own loop with its own bounds, which is why this file is per-unit.

**A section with nothing in it says `None.`** An empty heading reads as "not run yet", and those are different.

---

## 3. `analysis.md` — the plan scratchpad

Written by `/dev:plan` Stage 2. **Stage 4 compose refuses to run without it.**

```md
---
doc_type: analysis-scratchpad
unit: backend
feature_id: FEAT-SUP-001
---

## build_sequence
1. ENT-SUP-01 — add `normalised_tag`, unique partial index · satisfies BR-07
2. EP-SUP-02 — POST /suppliers validates and rejects duplicates · satisfies AC-03, BR-07
…

## impact_matrix
All twelve dimensions. **`N/A` is written explicitly, never omitted** — an absent row is indistinguishable from
one nobody considered, and Source 5 of blocker detection reads this block for `unknown` entries.

| Dimension | Impact |
|---|---|
| Data model | ENT-SUP-01 gains a column + index |
| Auth | N/A — no permission surface changes |
| External integrations | unknown — does the ERP push accept the new field? |

## risks_and_rollback
- The unique index fails to build if production already holds duplicates.
  - cheapest: build `CONCURRENTLY`, backfill, then add the constraint
  - full: drop the constraint, revert the migration
```

**Blocker resolutions fold back into this file**, not into the plan — the plan is composed from it, so changing
the plan directly leaves the two disagreeing.

---

## 4. `pr-summary.md` — the PR body

Passed to the PR as its body. **The residue, not the working notes**: the findings stay in `findings.md`;
what reaches the reviewer is what survived.

**This shape applies when the repo has no template of its own.** If it carries a
`PULL_REQUEST_TEMPLATE`, that is the skeleton and this content fills it — see
[`stage-8-9-push-pr.md`](../../../commands/references/commit/stage-8-9-push-pr.md) §9b.0, which also covers
the rules that matter there: never tick a checkbox for the author, never delete an empty section, never drop
content that their template has no home for.

```md
## What shipped
Duplicate supplier tags are now rejected at write time rather than by a prior read.

## Not blocking, worth knowing
- 2 Medium security warnings — rate limiting on the public lookup (follow-up)
- 3 Minor review notes — naming in `repo.py`

## How to verify
```bash
cp .env.example .env          # ERP_BASE_URL may stay blank
docker compose up -d postgres
poetry run alembic upgrade head
poetry run pytest -q
```
Then POST the same tag twice to `/suppliers` — the second returns 409 with the existing record's id.

## Checked by hand
NFR-02 (p95 under 400ms) — measured with a local load run, not by a gate.
```

**`## How to verify` is the old `local-runbook.md`.** It was excluded from every commit as a local artefact
while containing exactly what a reviewer needs; folding it here sends it to the person who uses it.

**Say what was checked manually.** A reviewer who assumes a tool verified something it did not is worse off
than one told plainly.

---

## 5. `discussion.md` — pull-only

Per task **and** per unit: a sub-task is a task, with its own thread. A clarification left on the backend
sub-task is missed when only the parent is fetched.

```md
---
doc_type: unit-discussion
readonly: true                    # /jetrix:push refuses any file carrying this
unresolved_count: 1
---

## Comments

### 2026-10-20T14:02Z · Priya (Acme) · unresolved
Does the duplicate check apply across archived suppliers too?
  ↳ 2026-10-20T15:30Z · dev-agent
    Currently active-only. Raised as PB-003.

## Attachments
| File | Size | Added | Local |
|---|---|---|---|
| erp-field-map.xlsx | 41 KB | 2026-10-18 | `attachments/1-erp-field-map.xlsx` |
```

Threads nest by `parentCommentId`, soft-deleted entries are filtered, and `unresolved_count` is the number that
matters — **unresolved threads become `PB-###` via blocker detection Source 6.**

---

## 6. `plan-blockers.md` and `merge-conflicts.md` — conditional, you fill them

The only two files a **human** writes into. They exist only while something is genuinely undecided.

```md
---
doc_type: plan-blockers
status: OPEN                      # OPEN · RESOLVING · RESOLVED
---

## PB-003 · Does the duplicate check span archived suppliers?
**Blocks:** EP-SUP-02 validation · BR-07 wording · AC-03's test

| Option | Consequence |
|---|---|
| Active only | A re-registered supplier reuses a retired tag. Matches today's behaviour. |
| All records | Retired tags are never reusable. Needs a migration over archived rows. |

**Recommendation:** active only — it matches the stated rule and needs no migration.

**Resolution:**
```

**A blocker answered in the conversation never produces a file.** This exists for the ones deferred, and the
blank `Resolution:` field is the only thing `/dev:resolve` reads.

---

## What these replaced

| Was | Now |
|---|---|
| `plan-run.md` · `build-run.md` · `commit-run.md` · `implementation-log.md` · `.compare-url.txt` | `status.md` § `## Run history` |
| `acceptance-map.md` | `status.md` § `## Acceptance` |
| `escalation-<n>.md` | a `BLOCKED` entry in `## Run history` |
| `security-findings-build.md` · `security-findings-commit.md` · `code-review-findings.md` · `context-merge-log.md` | `findings.md`, four sections |
| `local-runbook.md` | `pr-summary.md` § `## How to verify` |
| `comments.md` · `attachments.md` | `discussion.md`, two sections |
| `traceability.md` | removed — a full schema with no writer and no reader |

The state file already declared it held *run history* and an *acceptance status table*. Those two were never a
merge opportunity; they were an existing overlap being written twice.
