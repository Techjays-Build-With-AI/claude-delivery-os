# Plan-Time Blocker Resolution — Design & Implementation Plan (v2.2)

> **Status:** Draft · **Owner:** dev plugin · **Depends on:** `/dev:plan` v2.1 in place · **Related:** [dev-plan-command.md](dev-plan-command.md), [dev-build-command.md](dev-build-command.md), [dev-commit-command.md](dev-commit-command.md)
>
> This adds an explicit **blocker-resolution phase to `/dev:plan`** so `/dev:build` never has to make build-time decisions. Every §-number is a checkable spec.

---

## 1. Purpose

`/dev:build` is designed to run without prompts — deterministic, bounded, no user pauses. That only works if the plan is 100% complete: every field is known, every contract is defined, every business rule is decidable from the plan alone.

Today's flow surfaces some of those unknowns as `[HELD]` markers in `tl-plan.md` or as items in BA's `open-questions.md`. That's not enough — `/dev:build` still has to decide what to do when it hits one. This plan adds a **first-class blocker resolution loop inside `/dev:plan`** so `/dev:build` inherits a clean, actionable plan or refuses to run.

**The invariant:** `/dev:build` never asks the user a question. If a question exists, it belongs in `/dev:plan`.

---

## 2. Blockers vs escalations (the distinction)

Two different halt conditions, two different files, two different resolution flows:

| Signal | When it fires | File | Resolution |
|---|---|---|---|
| **Blocker** (NEW) | Detected upfront during `/dev:plan` Stage 3 | `dev/plan-blockers.md` | User fills in a Resolution field per blocker → re-run `/dev:plan --resume` |
| **Escalation** (existing) | Something WENT WRONG during `/dev:build` execution (test flaky, retry exhausted, unexpected failure) | `dev/escalation-<n>.md` | User makes a decision after seeing the failure → re-run the halted command |

Blockers say *"I can't proceed until you decide X."* Escalations say *"Something broke that I couldn't fix; here's what happened."*

Blockers are **upfront**; escalations are **runtime**. This spec covers only the upfront path.

---

## 3. What counts as a plan-time blocker

Categories, with concrete examples from the supplier-onboarding use case:

| # | Category | Example |
|---|---|---|
| 1 | **Missing integration contract** | *"Compliance service duplicate-check endpoint contract not in `ba/registers/integrations.md` — need URL, auth, request/response shape."* |
| 2 | **Undecided auth model** | *"Supplier onboarding requires role check but `shared-context/system-landscape.md` doesn't declare which role can onboard."* |
| 3 | **Ambiguous schema field** | *"`supplier.tax_id` — is this globally unique or unique per country? BA says both in different places."* |
| 4 | **Missing external endpoint / credentials** | *"Feature depends on webhook to Stripe but no Stripe account/API key path documented."* |
| 5 | **Unclear business rule edge case** | *"BR-3: 'reject duplicate submissions' — is a re-submission after 24h still a duplicate?"* |
| 6 | **Environment / config unknown** | *"Feature uses SMTP but SMTP_HOST/USER/PASS not in `shared-context/technology-stack.md` and no `.env.example` exists."* |
| 7 | **Missing dependency choice** | *"BA declares 'send PDF invoice' but no PDF library chosen for this stack; three plausible options."* |
| 8 | **Data flow ambiguity** | *"Feature reads from `supplier` and `contact` tables but the schema shows both have `email` — which is source of truth?"* |
| 9 | **Cross-feature ordering unknown** | *"Feature depends on FEAT-USER-01 (User Management) which isn't in the current batch — is it built already, or must this feature mock it?"* |
| 10 | **UI copy / branding unknown** | *"Error message text — BA says 'user-friendly error' but the actual wording isn't in the scope."* |

**The detection rule is behavioural, not enumerated.** A blocker exists whenever `/dev:build` would have to *choose* between two or more plausible actions and the choice materially affects the deliverable. If the choice is style (e.g. tab vs space), it's not a blocker — the code review skill handles that. If the choice is *"reject with 409 or return existing record"*, it's a blocker.

---

## 4. Detection during `/dev:plan` Stage 3

**Adds a new sub-step §3f — Blocker detection** between the existing §3e (Implementation planning writes implementation.md) and §3f (Finalise). Runs on every task (parent-alone or per-sub-task).

### 4a. Detection sources (union)

Scan these five inputs for build-time decision requirements:

1. **`tl-plan.md` (or per-sub-task `implementation.md`)** — grep for `[HELD ·]`, `TBD`, `<?>`, `<UNKNOWN>`, `NEEDS:` markers
2. **BA `open-questions.md`** — rows with Impact starting with `Blocks build` or `Blocks estimate`
3. **BA `ba/registers/integrations.md`** — declared integrations with `status: unresolved` or missing contract fields
4. **`shared-context/system-landscape.md`** — feature declares an actor role but role isn't defined
5. **`implementation.md §3 Impacted components`** — any dimension marked `unknown` (not `N/A` — `N/A` is a legitimate decision; `unknown` is a blocker)

### 4b. Detection heuristics (behavioural, per §3)

For each ordered step in `implementation.md`, apply these questions:

- Does this step reference an external system whose contract isn't documented?
- Does this step apply a business rule with an unclarified edge case?
- Does this step need a config value (env var, credential, URL) not declared in `technology-stack.md` or `.env.example`?
- Does this step have two or more implementations that would be functionally different (not stylistically)?

Any YES → mint a blocker.

### 4c. Blocker ID minting

Format: `PB-###` (Plan Blocker, sequential within a task). Append-only per `plan-blockers.md`; a rerun of `/dev:plan --resume` never reuses a retired ID.

For sub-tasks, the ID prefix carries the sub-task number: `PB-1-###` (task 1) / `PB-2-###` (task 2). This lets the parent's rollup Sub-tasks table cross-reference.

---

## 5. `dev/plan-blockers.md` file format

Per task, under the task's `dev/` folder (parent-alone or sub-task):

```markdown
---
doc_type: plan-blockers
schema_version: 1.0
produced_by: dev
feature_id: FEAT-SUP-001
subtask_number: 1                   # OMIT for parent-alone
subtask_repo: backend               # OMIT for parent-alone
generated_at: 2026-08-31T14:22:00Z
status: OPEN                        # OPEN | RESOLVING | RESOLVED
---

# Plan blockers — <feature title>

**How to resolve:** for each blocker below, edit the `Resolution:` field with your decision, then re-run `/dev:plan --resume` on this task. The plan will fold your resolutions into `implementation.md` and `implementation.md §3 Impacted components` automatically. This file's `status` will move to `RESOLVED` and `/dev:build` will unblock.

**Do not delete this file after resolution** — it's the audit trail of decisions this feature required. `/dev:plan --resume` marks each blocker `resolved: true` in-place.

---

## PB-001 — Compliance service duplicate-check contract missing

**Detected in:** `implementation.md` step 3 (backend)
**Blocks:** implementing the duplicate detection logic; `AC-B2` (duplicate → 409) cannot be validated without knowing what "duplicate" means to the compliance service.

**Description**
`ba/registers/integrations.md` lists `INT-001 Compliance service` but the record has no endpoint URL, no auth mechanism, no request/response schema. The backend sub-task's `implementation.md` §2 API endpoints assumes a `POST /compliance/dedupe` returning `{ exists: bool, existingId?: str }` — this is a guess, not a decision.

**Options** (with recommendation)
| # | Option | Trade-off |
|---|---|---|
| 1 (recommended) | Use existing internal compliance service at `https://compliance.acme.internal/v1/duplicate-check`. Bearer auth via `COMPLIANCE_TOKEN` env var. Response: `{ isDuplicate: bool, existingTaxId?: str }`. | Confirmed working in staging; owned by Platform team. |
| 2 | Integrate a third-party service (e.g. LexisNexis). | Higher accuracy but adds vendor + cost + procurement time. |
| 3 | Skip external check; do local DB uniqueness on `(tax_id, country)`. | Simpler but misses fraud detection. |

**Resolution:**
_(fill in — reference an option # OR describe your choice; if picking option 1 verbatim, just write `1`)_

**Applied at plan-fold:**
_(auto-filled by /dev:plan --resume — do not edit)_

---

## PB-002 — `tax_id` uniqueness scope (global vs per-country)

**Detected in:** BA `open-questions.md` OQ-SUP-004 (marked "Blocks build")
**Blocks:** schema design for `ENT-SUP-01 supplier` — column type + constraint depends on this.

**Description**
Business rule BR-1 says "`tax_id` is unique per country." BA scope §3.2 says "supplier is identified by `tax_id`." These may conflict for cross-border suppliers with the same `tax_id`.

**Options**
| # | Option | Trade-off |
|---|---|---|
| 1 (recommended) | (tax_id, country) composite uniqueness — matches BR-1 verbatim. | Slightly more DB work; correct per stated rule. |
| 2 | Global `tax_id` uniqueness — matches BA scope §3.2. | Simpler but rejects legitimate cross-border suppliers. |

**Resolution:**
_(fill in)_

**Applied at plan-fold:**
_(auto-filled)_

---
```

**Frontmatter states:**
- `OPEN` — one or more blockers awaiting resolution (initial state)
- `RESOLVING` — set by `/dev:plan --resume` while it's folding answers (transient; user rarely sees)
- `RESOLVED` — all blockers have Resolution + Applied fields filled; `/dev:build` unblocks

---

## 6. Resolution flow

### 6a. On first `/dev:plan` run (blockers detected)

1. Stage 3 detects blockers (per §4)
2. Writes `dev/plan-blockers.md` with `status: OPEN` and every blocker's `Resolution` field blank
3. Sets local state → `BLOCKED_ON_PLAN` (new state)
4. Sets MC status → `blocked` (existing enum value; MC's UI shows the block)
5. Halts with:

```
✗ /dev:plan halted — 2 blockers require decisions before build can start:

   PB-001  Compliance service duplicate-check contract missing        [Blocks AC-B2]
   PB-002  tax_id uniqueness scope (global vs per-country)             [Blocks schema]

Resolve them:
   1. Open: features/<slug>/subtask/backend/dev/plan-blockers.md
   2. Fill in the "Resolution:" field under each PB-###
   3. Re-run: /dev:plan --resume FEAT-SUP-001-1

Or if you can't resolve now:
   · Escalate to BA/TL for input on the specific PB-### you're stuck on
   · Leave the file open; MC status stays `blocked` so the tracker reflects reality
```

### 6b. On resolution and `--resume`

1. User edits `plan-blockers.md`, fills every `Resolution:` field
2. User runs `/dev:plan --resume <task>`
3. Stage 3 detects `plan-blockers.md` exists, iterates blockers:
   - **All have non-empty Resolution** → set `status: RESOLVING`, proceed to fold
   - **Any Resolution still empty** → halt again, name the empty ones
4. **Fold resolutions:**
   - For each blocker, apply its resolution to the target file:
     - `PB-001` (integration contract) → update `implementation.md §3 Impacted components` §Third-party integrations + `implementation.md` step 3 API-call body
     - `PB-002` (schema) → update `implementation.md §3 Impacted components` §Database + `implementation.md` step 1 migration content
     - Every fold is deterministic per the resolution — no re-planning, no reasoning about "how the answer applies", just the specific edit named in the blocker's Options table
   - Write `Applied at plan-fold:` field on each PB with an ISO timestamp + a citation to the file/line edited
   - Log each fold as a `DEC-###` in `shared-context/decision-log.md`
5. Set `plan-blockers.md` `status: RESOLVED`
6. Re-run the rest of Stage 3 (impact + dev-plan refresh with the folded content)
7. Set local state → `PLANNED`
8. Set MC status → `readyForDev`
9. Report success:

```
✓ /dev:plan --resume complete — 2 blockers folded into the plan

   PB-001  → resolved (option 1: internal compliance service)
             applied to: implementation.md §3 Impacted components §3rd-party, implementation.md step 3
             logged as DEC-042
   PB-002  → resolved (option 1: composite uniqueness)
             applied to: implementation.md §3 Impacted components §Database, implementation.md step 1
             logged as DEC-043

Local state:  PLANNED
MC status:    readyForDev

Next: /dev:build FEAT-SUP-001-1
```

### 6c. Partial resolution

If some blockers are resolved and others aren't, `--resume` should still fold the resolved ones (they're not the ambiguous parts) and halt on the unresolved. Rationale: the user might resolve incrementally with input from different stakeholders. Progress is real, not all-or-nothing.

Each fold is independent — folding PB-001 shouldn't invalidate PB-002's edits.

### 6d. Resolution changes mind

If a user re-opens `plan-blockers.md` after resolution, edits an already-applied `Resolution:`, and re-runs `--resume`:
- The old fold's `DEC-###` is preserved (audit trail)
- A new `DEC-###` records the change
- The plan re-folds the new resolution
- `status:` stays `RESOLVED`

---

## 7. `/dev:build` refusal semantics

`/dev:build` Stage 0 plan verification adds one more check:

- Before Stage 1, look for `dev/plan-blockers.md` under the task folder
- If exists AND `status:` is `OPEN` or `RESOLVING` → halt cleanly:

```
✗ /dev:build refused — task <target> has unresolved plan blockers.

Run:
   /dev:plan --resume <target>

Or open: <task-folder>/dev/plan-blockers.md — resolve each PB-### first.
```

- If exists AND `status: RESOLVED` → continue normally. The file stays for audit; `/dev:build` reads it once to log the resolved DEC-### references in `build-run.md`.

---

## 8. Local + MC status

**Local state additions** — new state `BLOCKED_ON_PLAN` distinct from execution-time `BLOCKED`:

| Trigger | Local state | MC status |
|---|---|---|
| `/dev:plan` writes `plan-blockers.md` OPEN | `BLOCKED_ON_PLAN` | `blocked` |
| `/dev:plan --resume` finds file OPEN/RESOLVING with unresolved rows | `BLOCKED_ON_PLAN` | `blocked` (unchanged) |
| `/dev:plan --resume` folds all resolutions, sets file RESOLVED | `PLANNED` | `readyForDev` |
| `/dev:build` refuses on OPEN file | `BLOCKED_ON_PLAN` (unchanged) | `blocked` (unchanged) |

**Parent status derivation** — if any sub-task is `BLOCKED_ON_PLAN`, parent's derived status is `BLOCKED` (existing rule; execution-time or plan-time both count as blocked).

---

## 9. Distinction from BA `open-questions.md`

BA's `open-questions.md` (per `/ba:features`) captures business questions during BA scope decomposition — the "blocks estimate" questions. Some of those pre-existing questions ARE blockers for build (`/dev:plan` picks them up in §4a source #2). Others resolved during BA/TL flow — those don't reappear as blockers.

**In short:** `open-questions.md` is BA's log; `plan-blockers.md` is dev's action list. `/dev:plan` promotes an OQ into a PB when (and only when) it would materially affect the build.

Same for TL `[HELD]` markers in `tl-plan.md` — those get promoted to PBs.

---

## 10. Files to create / modify

### Create

| Path | Purpose |
|---|---|
| [plugins/dev/commands/references/plan/blocker-detection.md](../../plugins/dev/commands/references/plan/) | The 5-source detection ladder + heuristics + template for `plan-blockers.md` |
| [plugins/dev/commands/references/plan/blocker-fold.md](../../plugins/dev/commands/references/plan/) | The deterministic per-category fold rules (how to apply a resolution to `implementation.md` / `implementation.md §3 Impacted components`) |

### Modify

| Path | Change |
|---|---|
| [plugins/dev/commands/plan.md](../../plugins/dev/commands/plan.md) | Add §3.5 blocker-detection sub-step between existing Stage 3 and completion; `--resume` semantics extended for blocker folding |
| [plugins/dev/commands/references/plan/development-planning.md](../../plugins/dev/commands/references/plan/) | End of Stage 3 hands off to `blocker-detection.md`; on `--resume`, hands off to `blocker-fold.md` first |
| [plugins/dev/commands/build.md](../../plugins/dev/commands/build.md) | Stage 0 adds "no unresolved blockers" gate |
| [plugins/delivery-os-core/skills/delivery-os-conventions/SKILL.md](../../plugins/delivery-os-core/skills/delivery-os-conventions/) | v2.2 — add `plan-blockers` doc_type + `BLOCKED_ON_PLAN` local state + `PB-###` id convention |

### No delete

Nothing retires. This is additive.

---

## 11. Order of implementation

1. **`delivery-os-conventions` v2.2 bump** — add `plan-blockers` doc_type, `BLOCKED_ON_PLAN` state, `PB-###` id
2. **Create `blocker-detection.md`** reference file — the 5 sources + heuristics + `plan-blockers.md` template
3. **Create `blocker-fold.md`** reference file — per-category deterministic fold rules
4. **Modify `plan.md` command** — add §3.5 (blocker phase) + `--resume` fold path
5. **Modify `development-planning.md`** reference — hand-offs to the two new files
6. **Modify `build.md` command** — Stage 0 blocker refusal
7. **Smoke test:** run `/dev:plan` on a feature with a known undecided integration contract → verify blocker written → resolve in the file → re-run `--resume` → verify fold + status transition

---

## 12. Success criteria

- Running `/dev:plan` on a feature with any of the 10 blocker categories present → detects, writes `plan-blockers.md`, halts, sets MC `blocked`
- User fills Resolution fields → `/dev:plan --resume` folds them deterministically, logs `DEC-###`, sets `status: RESOLVED`, MC `readyForDev`
- Partial resolution → folds the resolved ones, halts on the rest
- `/dev:build` before resolution → halts cleanly with "run /dev:plan --resume"
- `/dev:build` after resolution → reads `plan-blockers.md`, logs the DEC-### references into `build-run.md`, continues normally
- Zero mid-run prompts in `/dev:build` — invariant holds
- Every fold is auditable via `DEC-###` in `shared-context/decision-log.md`

---

## 13. Explicitly out of scope

- Auto-suggesting resolutions with an LLM — the whole point is that the user (or BA/TL) decides. Options with recommendation are as far as we go.
- Escalating blockers to different resolution owners (BA vs TL vs dev) — human triages that from the blocker's Description. v2.3 could add `owner:` field per PB.
- Automated re-detection after fold (in case the fold reveals new blockers) — for v2.2, one resolution round is sufficient; re-run `/dev:plan --resume` yourself if you want another pass.
- Cross-task blocker deduplication — if two sub-tasks both hit "compliance contract missing," each writes its own PB. Rationale: they might resolve differently per repo. v2.3 could add shared-blocker links.

---

## 14. Blockers / open questions (for this feature itself)

**PBR-01** — Should the `Resolution:` field accept free text (user writes their answer prose-style) OR strictly one of the numbered options? Recommendation: accept both — a plain number (`1`) OR free text. Fold rules handle both cases: number → apply option verbatim; free text → interpret the closest option and log a `DEC-###` with the exact user words. **Non-blocking.**

**PBR-02** — Should `/dev:plan --resume` re-run detection after folding, to catch any new blockers the fold might reveal? Recommendation: **no for v2.2** — one pass; user re-runs if desired. Simpler semantics. **Non-blocking.**

**PBR-03** — Should the plan-fold write the `DEC-###` inline in the target file (e.g. in implementation.md) OR only to `shared-context/decision-log.md`? Recommendation: both — one line in `shared-context/decision-log.md` (canonical) plus a `(DEC-042)` inline citation in implementation.md so a reader tracing the plan can see WHY a step reads the way it does. **Non-blocking.**

---

**End of plan-blocker-resolution plan.** After this ships, `/dev:build` runs on a decidable plan or refuses. `/dev:build`'s "no prompts" contract becomes enforceable.
