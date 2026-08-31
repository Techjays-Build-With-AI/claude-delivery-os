---
description: Interactive plan-blocker resolution — walk every OPEN PB-### in dev/*plan-blockers.md, present the options table + recommendation, ask the user to pick per blocker, write Resolution: fields to disk, then invoke `/dev:plan --resume` to fold resolutions + compose + push. Batch-friendly single sitting flow that replaces the manual "open file, edit each PB, save, run resume" cycle. Refuses to run if no OPEN blockers exist.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | FEAT-<AREA>-NN | (blank = pick task with OPEN blockers)> --plan"
---

# /dev:resolve

You are the interactive blocker-resolution entry point. Walk every OPEN `PB-###` in the target task's plan-blockers files, present the options + recommendation, collect the user's choice per blocker, write Resolution fields back to disk, then hand off to `/dev:plan --resume` to fold the resolutions into the analysis scratchpad + compose + push.

Read the **`delivery-os-conventions`** skill first if not in context — the v2.3 file layout, plan-blockers doc_type, and `BLOCKED_ON_PLAN` state model.

**The single invariant:** you never invent a resolution. Every Resolution field is either (a) an option number the user picked, (b) free text the user typed, or (c) marked `_skipped_ — task stays BLOCKED_ON_PLAN` when the user chose to defer.

---

## 1. Parse arguments

`$ARGUMENTS` may contain:

**Task target** (optional — blank picks the task with OPEN blockers):
- MC task number: `Task-N`, `Feature-N`, `Subtask-N`
- Local feature slug: `holiday-calendar-management`
- Local feature folder: `features/holiday-calendar-management`
- Internal id: `FEAT-<AREA>-NN`
- Blank: find the ONE feature whose `dev/*plan-blockers.md` has `status: OPEN`. If more than one → list them and ask which.

**Flags:**
- `--plan` (default and currently only supported mode) — resolve plan-time PB-### blockers
- (future: `--build`, `--commit` could handle escalation-*.md or merge-conflicts.md; not implemented yet)

If `--plan` is absent, default to `--plan` and note in the report.

## 2. Stage 0 — Identify target + locate blocker files

Same 4-way task resolution as `/dev:plan` Stage 0.

Once resolved to `(feature_id, feature_folder)`, scan for OPEN blocker files:

```
features/<slug>/dev/plan-blockers.md              # parent-alone
features/<slug>/dev/<repo>-plan-blockers.md       # per sub-task on split
```

For each file found, read its frontmatter:
- If `status: OPEN` → include in the resolution session
- If `status: RESOLVING` → include (partial run from a previous attempt)
- If `status: RESOLVED` → skip (nothing to do)
- If frontmatter missing / malformed → halt with the file path + reason

**No OPEN files** → halt with:

```
✓ No OPEN plan blockers for <task-ref>. Nothing to resolve.

Run: /dev:build <task-ref>  (if state is PLANNED)
     /dev:plan <task-ref>   (if plan hasn't run)
```

**One or more files** → set state `RESOLVING` in each file's frontmatter (idempotent — a `--resume` semantics if this command is re-invoked mid-session).

## 3. Stage 1 — Parse each PB-### block

For each blocker file, extract per PB-###:

- **id** (e.g. `PB-1-001`)
- **title** (the `## PB-###` heading text after the id)
- **Detected in** metadata line
- **Category** metadata line
- **Blocks** metadata line — what depends on this decision
- **Suggested owner** metadata line
- **Description** — the free-form paragraph explaining the question
- **Options table** — parse the markdown table into structured `[{n, is_recommended, name, tradeoff}]`
- **Current Resolution** field content (should be `_(fill in — write the option number OR describe your choice)_` for a fresh OPEN file)

Preserve every line's whitespace + surrounding markdown so the file's other content isn't touched on write-back.

Sort resolution order by:
1. Backend blockers first, then frontend (deterministic — matches build sequence dependency)
2. Within a file, in the order the PB-### blocks appear

## 4. Stage 2 — Present each blocker + collect user choice

For each PB-###, invoke `AskUserQuestion`. The prompt must be self-contained — the user must be able to make the decision from the prompt alone, without opening the file. The `question` field is the primary display area (shown prominently at the top of the prompt); it MUST carry the full question + a concise explanation + a concrete real-world example so the reader has the WHOLE context in view before scanning options.

### 4a. Structuring the `question` field

Format (target 300-800 chars — enough to explain, short enough to scan):

```
<PB-### title as a question — ending with "?">

**Why this matters:** <2-3 sentences from the Description explaining what depends on this decision and why it can't be defaulted or left to the build>

**Concrete example:** <one real-world scenario — 2-3 sentences — that shows the observable difference between the options; use the actual entities from this task (holiday-calendar, EP-HCAL-01, etc.), not placeholders>

**Detected in:** dev/<repo>-analysis.md § <block> · **Blocks:** <BR-N, AC-N> · **Recommended: Option 1 (<name>)**
```

Rules for the `question` text:
- **Ends with a question mark** — one canonical question the user answers
- **Sentence-case Markdown** allowed — bold, backticks for identifiers, no headings
- **Real-world example is mandatory** — use the actual feature's entities (dates, endpoints, entity names, user actors). Not "user A/B" placeholders. Show what a real user SEES if this decision goes one way vs another.
- **No file paths or code snippets** — this is a decision prompt for a stakeholder, not source
- **Cite the recommendation** — one line at the end, so a user in a hurry can just pick the recommended option

### 4b. Structuring each `option`

For each option from the file's Options table, build:

- **`label`** (1-5 words shown in the option list): `Option 1 — Active-only (Recommended)` OR `Option 2 — All rows` OR `Option 3 — No constraint`
- **`description`** (1-2 sentences shown under the label — the trade-off in plain terms): what happens if this is picked, phrased around observable behaviour, NOT the mechanism
- **`preview`** (rendered as monospace side-by-side content when the user focuses this option): a concrete real-world scenario showing the OUTCOME of picking THIS option — different from the question's example, showing how THIS option specifically plays out. 4-8 lines of prose.

### 4c. Free-text input — always available

The `AskUserQuestion` tool auto-provides an **"Other"** option that lets the user type free text. This IS the "type option" — you do NOT add a separate "Type your own answer" entry; the tool has it built in. Mention this in the `question` text ONCE (last line) if the options might not cover the user's case:

```
... **Or pick "Other" to type your own resolution.**
```

### 4d. Skip option (deferred resolution)

Add ONE extra explicit option per blocker:

- **`label`**: `Skip this blocker for now`
- **`description`**: `Task stays BLOCKED_ON_PLAN; the Resolution field is left as-is with a comment noting this run's skip. You can re-run /dev:resolve later or edit the file manually.`
- **`preview`**: Explanation of what happens next if skipped — build stays blocked, siblings continue, /dev:build refuses on this task until resolved.

Place Skip LAST in the options array.

### 4e. Example — the actual prompt for PB-1-001

For your holiday-calendar backend blocker, the `AskUserQuestion` invocation should look like:

```
question: "Does one-holiday-per-date apply to *removed* holidays, or only to *active* ones?

**Why this matters:** BR-1 says 'a date can hold only one holiday' but doesn't say whether a soft-deleted holiday still occupies its date. This decides the shape of the unique index on the `holidays` collection — a decision that's fixed at declaration time and expensive to reverse after data exists.

**Concrete example:** Priya adds Diwali on 2026-11-08. Arjun later notices it was mis-dated and removes it. The next day Priya (or anyone) tries to add Diwali on 2026-11-08 again. Should this second add succeed (Option 1 — active-only) or be refused because the date has 'ever' held a holiday (Option 2 — all rows)? For a soft-delete design where removal is meant to preserve audit but free the calendar, Option 1 matches the mental model.

**Detected in:** dev/backend-analysis.md § build_sequence step 1 · **Blocks:** BR-1, AC-9, AC-7, test scenario 11 · **Recommended: Option 1 (Active-only).** Or pick 'Other' to type your own resolution."

header: "PB-1-001"

options:
  - label: "Option 1 — Active-only (Recommended)"
    description: "A date freed by a removal can be re-used. The 409 refuses only against a live holiday. Matches the calendar mental model and the TL design (DEC-013)."
    preview: |
      Concrete outcome — Option 1:
      · Priya adds Diwali 2026-11-08     → 201 (added)
      · Arjun removes it (soft delete)   → 200 (removed, is_removed=true)
      · Priya re-adds Diwali 2026-11-08  → 201 (added — new active row)
      Collection ends with 2 rows for the same date:
        one with is_removed=true, one with is_removed=false.
      Partial unique index scoped to is_removed:false enforces BR-1.

  - label: "Option 2 — All rows (permanent burn)"
    description: "Exactly one row per date, ever. Simple to audit. But a mis-dated holiday removed by mistake permanently burns that date."
    preview: |
      Concrete outcome — Option 2:
      · Priya adds Diwali 2026-11-08     → 201 (added)
      · Arjun removes it (soft delete)   → 200 (removed, is_removed=true)
      · Priya re-adds Diwali 2026-11-08  → 409 (already exists)
      That date can NEVER hold a holiday again through the UI.
      Recovery requires manual DB edit (AC-7 forbids a restore control).
      A single misclick permanently loses a calendar slot.

  - label: "Option 3 — No DB constraint"
    description: "Application-level read-then-write. Most flexible but opens a race window under the concurrency NFR — two concurrent adds can both pass the check and both insert."
    preview: |
      Concrete outcome — Option 3:
      · Two users both add Diwali 2026-11-08 concurrently
      · Both read: 'no holiday on this date'
      · Both insert                        → 201, 201
      Collection ends with 2 ACTIVE rows for the same date.
      BR-1 defeated under load. Rejected by TL on concurrency grounds.

  - label: "Skip this blocker for now"
    description: "Task stays BLOCKED_ON_PLAN. You can re-run /dev:resolve later or edit the file manually. Sibling blockers continue to be prompted."
    preview: |
      Skip outcome:
      · Resolution field kept as-is with a skip comment
      · Task remains BLOCKED_ON_PLAN
      · /dev:plan --resume WILL NOT run (any skipped blocker halts fold)
      · /dev:build refuses on this task
      · Re-run /dev:resolve OR edit backend-plan-blockers.md manually

multiSelect: false
```

### 4f. Collecting the answer

- **User picks an option** whose label starts with `Option <n>` → record `chosen_option: <n>`, `resolution_text: <n>`
- **User picks "Skip this blocker for now"** → record `chosen_option: SKIP`, `resolution_text: null`
- **User picks "Other" + types free text** (auto-provided by the tool) → record `chosen_option: CUSTOM`, `resolution_text: <user's typed text>`

Batch to memory. Do NOT write to disk yet — Stage 3 does the write in one atomic batch.

**Repeat for every OPEN PB-### across all blocker files.**

## 5. Stage 3 — Confirm + write

After collecting every resolution, present a summary to the user for final confirmation before writing to disk:

```
Resolutions collected for holiday-calendar-management (5 blockers):

  PB-1-001  →  Option 1 (active-only partial unique index)
  PB-1-002  →  Option 1 (hard reject NAME_TOO_LONG)
  PB-2-001  →  Option 1 (split auth fix into separate task)
  PB-2-002  →  Option 1 (Cancel + confirm-naming-holiday)
  PB-2-003  →  Custom — "1 + document baseline in qa/quality-gates.md"

Ready to write these to:
  features/holiday-calendar-management/dev/backend-plan-blockers.md
  features/holiday-calendar-management/dev/frontend-plan-blockers.md

Then invoke: /dev:plan --resume features/holiday-calendar-management

Proceed?  [y]es / [n]o (cancel, no changes written)
```

Use `AskUserQuestion` with `y/n` options; label = "Write and continue?"

**On `y`:**

For each blocker file, patch each PB-###'s Resolution field:
- If `chosen_option ∈ {1, 2, 3, ...}` → replace `_(fill in — write the option number OR describe your choice)_` with the option number verbatim (e.g. `1`)
- If `chosen_option == CUSTOM` → replace with the user's typed text verbatim
- If `chosen_option == SKIP` → leave placeholder text; add a comment line: `<!-- skipped by /dev:resolve at <ISO>; run /dev:resolve again OR edit manually -->`

Update the file's frontmatter:
- If ANY blocker was skipped → `status: RESOLVING` (partial)
- If ALL blockers resolved → `status: RESOLVING` (fold hasn't run yet)
- `last_updated: <ISO now>`

Write the files. Do NOT touch anything else in each file (options tables, watch items, description, formatting).

**On `n`:**

Print `Cancelled. No files written.` and stop. Set every blocker file's `status:` back to `OPEN` if it was `RESOLVING` from step 2.

## 6. Stage 4 — Invoke `/dev:plan --resume`

After successful write, invoke `/dev:plan --resume <task-ref>` inline (the command is another slash command in the same plugin — invoke it as if the user had typed it).

`/dev:plan --resume` reads the newly-filled Resolution fields, folds each into the analysis scratchpad per its category rule (`plugins/dev/commands/references/plan/blocker-fold.md`), logs each fold as `DEC-###`, sets `status: RESOLVED` on the plan-blockers file, then proceeds to Stage 4 (compose + MC push).

Stream `/dev:plan --resume`'s output to the user — they see the fold logs + compose + push happen inline.

## 7. Report at the end

Terminal output combines the /dev:resolve summary + the /dev:plan --resume result:

```
✓ /dev:resolve --plan holiday-calendar-management complete

5 blockers resolved:
  PB-1-001 → Option 1 (folded into backend-analysis.md § build_sequence step 1) → DEC-042
  PB-1-002 → Option 1 (folded into backend-analysis.md § build_sequence step 2) → DEC-043
  PB-2-001 → Option 1 (folded into frontend-analysis.md § build_sequence step 1) → DEC-044
             ⚠ Follow-up: raise separate task against PAGE-AUTH-01/02
  PB-2-002 → Option 1 (folded into frontend-analysis.md § build_sequence step 4,5) → DEC-045
  PB-2-003 → Custom (folded into frontend-analysis.md § test_strategy quality-gates) → DEC-046

Stage 4 (compose + push) ran cleanly:
  · subtask/backend/{description.md, implementation.md, status.md}   written
  · subtask/frontend/{description.md, implementation.md, status.md}  written
  · Subtask-7 (backend)  created  https://jetrix/…/Subtask-7
  · Subtask-8 (frontend) created  https://jetrix/…/Subtask-8

Local state:  PLANNED  (both sub-tasks)
MC status:    readyForDev  (both sub-tasks)

Next: /dev:build FEAT-HCAL-01-1  (backend)
      /dev:build FEAT-HCAL-01-2  (frontend)
```

## 8. Failure surfaces

- **No OPEN blockers** → early halt (§2) with the "nothing to resolve" message
- **User cancels at final confirm** → no writes, blocker files restored to `OPEN`
- **File-write error** (permission denied, disk full) → halt WITHOUT invoking /dev:plan --resume, name the file, tell user to fix and re-run
- **`/dev:plan --resume` fails** (fold error, precondition fail) → surface its error; the Resolution fields are already written so re-running /dev:resolve wouldn't ask again — instead the user runs `/dev:plan --resume` directly OR opens the file and edits

## 9. Guardrails

- Never invent a resolution — every write comes from a user choice (option number OR typed text OR explicit skip)
- Never modify anything in the file OTHER THAN the Resolution field + frontmatter `status` / `last_updated`
- Never push to MC directly — that's `/dev:plan --resume`'s Stage 4 responsibility
- Never resolve blockers on a task that's not `BLOCKED_ON_PLAN` — the file's `status: OPEN` is the authority
- Never proceed past Stage 3 (write) without an explicit `y` from the confirm prompt
- If the same PB-### appears in two files (rare edge case — deduplication should have happened at detection), warn and ask which file to keep

## 10. Skills / agents invoked

- No subagents (interactive, must run in the main session with the user)
- `AskUserQuestion` for each blocker + the final confirm
- `Read` + `Edit` for the plan-blockers files
- Delegates to `/dev:plan --resume` as its final step
