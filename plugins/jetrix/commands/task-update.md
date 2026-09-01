---
description: Surgically update an existing MC task after discussion. Loads the task's current state (implementation.md / description.md / sub-tasks), takes user-described changes conversationally, drafts each as a targeted patch against the specific section or sub-task it belongs to, batches every change into ONE review + confirm step, applies all diffs locally, pushes to MC via task-mcp with read-back verify, and updates sync-state. NEVER rewrites a whole file to change one line. Never touches sections the user didn't ask about. Respects the v2.3.16+ 8-section frame — refuses to add retired sections (§Coverage, Assumptions heading, Business flow). Accepts a single MC task number (Task-N, Feature-N, Subtask-N), a local feature slug or folder path, or the internal FEAT-<AREA>-NN id. Runs 6 stages: identity → load current state → conversation loop → confirm → apply + push + read-back verify → report with URLs.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | FEAT-<AREA>-NN>"
---

# /jetrix:task-update — surgical task-content patch after discussion

You are the interactive task-update entry point. The user has an existing MC task (parent + optionally sub-tasks) and wants to change specific content after talking it through with you. Your job is to COLLECT their change intent conversationally, DRAFT each edit as a targeted patch (never a whole-file rewrite), PREVIEW everything for confirmation, APPLY the patches locally, PUSH to MC, and VERIFY the push via read-back per v2.3.17 §4f.i.

Read the **`delivery-os-conventions`** skill first if not in context — the v2.3.16 8-section frame, v2.3.17 read-back verify contract, and MC's react-markdown + remark-gfm rendering requirements from Rule 0d.

**Single invariants:**
1. **Patch, don't rewrite.** Never regenerate a whole section to change one line. Use `Edit` with precise `old_string` / `new_string`. If the user's change genuinely requires restructuring a whole section, say so and ask for confirmation before doing that specifically.
2. **Batch, don't per-edit push.** Collect ALL changes in memory across the conversation. Push ONCE at the end after a single confirm.
3. **Respect the frame.** No retired sections (`## 7. Coverage`, `**Assumptions.**`, `§ Business flow`, `§ How to verify locally`). No Deferred to E2E status. If the user asks to add one of these, explain why the frame doesn't have it (per SKILL.md changelog v2.3.10 / v2.3.15 / v2.3.16) and offer the in-context alternative.
4. **Respect BA / Shared contract boundaries.** BA-owned content (parent AC/BR/TS in acceptance-criteria.md, business-rules.md, test-scenarios.md) is not editable via this command — the user runs `/ba:*` commands for that. §8 Shared contract inherits VERBATIM across every sub-task in a split; a change to §8 in one sub-task must apply to ALL sub-tasks per Rule 11.3.

---

## 1. Parse arguments

`$ARGUMENTS`:

- MC task number: `Task-N`, `Feature-N`, `Subtask-N`
- Local feature slug: `holiday-calendar-management`
- Local feature folder: `features/holiday-calendar-management`
- Internal id: `FEAT-<AREA>-NN`

Blank arg → tell the user this command requires a target and stop; unlike `/dev:plan`, there's no "next-READY" pick that makes sense for an update.

## 2. Stage 0 — Identity resolution

Same 4-way resolution as `/dev:plan` Stage 0 — see [`plan.md`](../../dev/commands/plan.md) §2a. Determine:

- `task_kind` (parent-alone or split-parent or sub-task)
- `feature_id`, `feature_slug`, `feature_folder`
- For a parent: whether it has sub-tasks (read `subtask/` folder)
- For a sub-task: parent's task_object_id + this sub-task's task_object_id + repo

Log to `dev/task-update-run.md` (created in §3 below):

```yaml
stage_0:
  target_arg: <user's arg>
  resolved_kind: parent-alone | split-parent | sub-task
  feature_id: FEAT-<AREA>-NN
  feature_slug: <slug>
  parent_task_object_id: <MC _id>
  subtask_targets:      # sub-tasks this run may touch — populated in §4 as user names them
    - subtask_object_id: <MC _id>
      subtask_number: <N>
      repo: <repo-slug>
```

If the target cannot be resolved (feature slug not found locally, or MC task doesn't exist) → halt with `blocker: target-not-resolvable` + which path was searched.

## 3. Stage 1 — Load current state

Read from disk:

- **Parent-alone:**
  - `features/<slug>/implementation.md` — the 8-section plan
  - `features/<slug>/status.md` — current MC status + local state
  - `features/<slug>/feature.md` and other BA files — read-only reference
- **Split-parent:**
  - `features/<slug>/tl-plan.md` — parent rollup (Sub-tasks table + Touch points)
  - `features/<slug>/status.md`
  - `features/<slug>/subtask/<repo>/{description.md, implementation.md, status.md}` per sub-task
- **Sub-task:**
  - `features/<slug>/subtask/<repo>/{description.md, implementation.md, status.md}`
  - `features/<slug>/tl-plan.md` — parent rollup as reference

Also read from MC (light — one call per tab that may get touched):

- `task-mcp.get_task_by_id_or_number(solution_id, parent_task_object_id)` → parent's current MC state
- `task-mcp.subtask_list(solution_id, parent_task_object_id)` → sub-tasks with current tab bodies

**Reconcile local vs MC.** Compute SHA-256 of each local tab body vs the MC-returned body. If they differ:
- If local is newer (later `updated_at` in frontmatter) → warn: `"Local <file> is ahead of MC. If you continue, MC will be updated to match local + your changes."`
- If MC is newer → warn: `"MC <task> is ahead of local. Someone updated MC directly since the last /dev:plan or /jetrix:task-update. Options: (a) pull MC's version to local first via /jetrix:pull scope, then re-run this command; (b) continue anyway and OVERWRITE MC's edits."` Ask for explicit choice.

Create `dev/task-update-run.md` and initialize:

```yaml
---
doc_type: task-update-run
schema_version: 1.0
produced_by: jetrix
feature_id: FEAT-<AREA>-NN
started_at: <ISO>
---

## Stage 1 — Load
loaded_files:
  - path: features/<slug>/implementation.md
    local_sha256: <hash>
    mc_sha256: <hash>
    parity: match | local-ahead | mc-ahead
  - ...
```

## 4. Stage 2 — Conversation loop (collect change intent)

Print an opening prompt to the user:

```
✓ Loaded task <task-ref>

  Feature: <slug>
  Kind:    <parent-alone | split-parent | sub-task>
  Sections available to update:
    § implementation.md:  §1 Build sequence · §2 Impacted components ·
                          §3 Operations · §4 Stored data · §5 Surfaces ·
                          §6 Touch points · §7 Risks and rollback ·
                          §8 Shared contract
    § description.md:     (sub-task only) User story · Scenarios · Business rules ·
                          Refusals · Out of scope · Related user stories

  Tell me what needs to change. You can:
    - Describe one change at a time or list several
    - Point at a section (e.g. "in §5 add a loading skeleton")
    - Point at a sub-task (e.g. "in backend §3 POST /holidays, change the 409 message")
    - Point at a specific line/table row you want reworded

  When you're done listing changes, say "that's all" or "ready" and I'll show
  every change as a diff before pushing anything.
```

Then run a **collection loop**. Each turn:

1. **User describes a change** (may reference multiple sections/sub-tasks in one message)
2. **You (Claude)** parse the intent:
   - Which file? (parent implementation.md / sub-task implementation.md / sub-task description.md / tl-plan.md)
   - Which section?
   - Is this a text edit (word/phrase), a row edit (add/change/remove a table row), or a structural edit (add a new sub-heading, split a section)?
3. **Clarify if ambiguous.** Ask ONE targeted question if you need to:
   - `"In §5, I see two <Domain>Panel places — the props table row for currentUserId, or the Rendered states line? Which one?"`
   - `"You said 'refusal message' — which endpoint's refusal table? POST /holidays or DELETE /holidays/:id?"`
4. **Frame check.** If the user's change would violate an active rule, push back with the specific rule + the in-context alternative:
   - `"§7 Coverage was removed in v2.3.16 — coverage lives in §1 Satisfies column + qa/quality-gates.md tier pool + dev/acceptance-map.md at build time. Do you want to add the AC-N reference to a §1 build step's Satisfies list instead?"`
   - `"An Assumptions heading in §7 was retired in v2.3.15 — boring decisions live in-context at §3 Invariants/Authz or §5 Effects/on-success. Where should 'no pagination' live: §3's list operation Invariants line, or §5's Panel Effects line?"`
   - `"Adding a business-rationale sentence ('This ensures the audit trail stays intact') is a Rule 3 rationale-starter. The FACT you want to preserve is `is_removed=false rows are invisible to the uniqueness check` — I can add that to §4 Stored data as a declaration hazard note. OK?"`
5. **Draft the specific diff** (not the whole file). Store in memory as a `pending_changes` list entry:
   ```yaml
   - id: CHG-001
     file: features/<slug>/subtask/backend/implementation.md
     section: §3 Operations exposed and consumed / POST /holidays / Refusals table
     kind: table-row-edit
     old_string: |
       | 409 | date already has a holiday | "Holiday already exists on this date." |
     new_string: |
       | 409 | date already has a holiday | "A holiday is already scheduled for this date. Please choose another date." |
     rationale: <user's own words paraphrased in ONE line — for audit only, does not enter the file>
   ```
6. **Acknowledge briefly** (`"Got it — refusal message on the 409 row updated."`) and continue the loop.

Loop continues until the user says `"that's all"`, `"ready"`, `"done"`, `"go ahead"`, or equivalent. Do NOT push per-edit.

**Frame violations that HALT the loop entirely (v2.3.16+ rules):**
- User wants to add a `## 7. Coverage` heading → refuse; offer §1 Satisfies alternative
- User wants to add an `**Assumptions.**` heading → refuse; offer in-context clause per Rule 11.13 §5
- User wants to add a `# Business Goal` H1 → refuse; that belongs on Description tab
- User wants to add a Deferred to E2E status → refuse; explain E2E is a covered tier, not a deferral

**Cross-scope changes the loop MUST catch:**
- Change to §8 Shared contract in one sub-task → the SAME change must apply to every sub-task in the split (Rule 11.3 verbatim inheritance). Prompt: `"§8 Shared contract inherits verbatim across all sub-tasks. This change will apply to backend + frontend + mobile. Confirm? [y/n]"`. On `y`, add the same diff to every sub-task's implementation.md.
- Change to a shared TL context unit (endpoint file, entity file, page file) — if the change is really about the CONTRACT (not just the plan's summary of it), tell the user: `"That's a change to the endpoint contract (EP-<AREA>-NN in <repo>/context/code-context/…). Update the TL unit file directly OR run /tl:code-map for a full re-map. This command is for TASK content, not source-of-truth units."`

## 5. Stage 3 — Review + confirm

Once the user signals done, print the full change set:

```
Ready to apply <N> changes:

  CHG-001  [features/<slug>/subtask/backend/implementation.md]
           §3 Operations / POST /holidays / Refusals table
           - | 409 | date already has a holiday | "Holiday already exists on this date." |
           + | 409 | date already has a holiday | "A holiday is already scheduled for this date. Please choose another date." |

  CHG-002  [features/<slug>/subtask/frontend/implementation.md]
           §5 <Domain>Panel / Rendered states line
           - Loading: spinner. Refusal 500: message + Retry(refetch()). Refusal 400/404: message, no Retry. Empty: "No items yet." Populated: one <Domain>Row per element.
           + Loading: skeleton (3 placeholder rows). Refusal 500: message + Retry(refetch()). Refusal 400/404: message, no Retry. Empty: "No items yet." Populated: one <Domain>Row per element.

  CHG-003  [features/<slug>/subtask/backend/implementation.md,
             features/<slug>/subtask/frontend/implementation.md]   ← applied to BOTH (§8 shared contract)
           §8 Shared contract / Time and locale row
           - Wire time format ISO-8601 UTC; formatting in user's locale via formatTimestamp.js
           + Wire time format ISO-8601 UTC; date-only fields (e.g. holiday date) sent as YYYY-MM-DD without time component

Files touched:  2 sub-task implementation.md files
MC tasks:       Subtask-2 (backend), Subtask-3 (frontend)
Read-back:      will verify after each push (v2.3.17 §4f.i)

Apply and push?  [y]es / [n]o (cancel, no changes written) / [e]dit CHG-N (revise one before applying)
```

Use `AskUserQuestion` for the y/n/e answer.

- **`y`** → proceed to §6
- **`n`** → print `Cancelled. No files touched.` and stop
- **`e CHG-N`** → drop CHG-N from the list, return to §4 conversation loop asking the user to describe the revised version

## 6. Stage 4 — Apply locally

For each `pending_changes` entry, apply the diff via `Edit` tool with the exact `old_string` / `new_string`. Order:

1. Sub-task implementation.md files first (deepest content, most likely edits)
2. Sub-task description.md files second
3. Parent tl-plan.md third (only if a change references it — rare, mostly for split-count / sub-task order)
4. Parent implementation.md fourth (parent-alone case only)
5. `status.md` last — bump `updated_at` and increment `local_version` frontmatter field on each touched file

On any `Edit` failure (old_string not found → someone changed the file between Stage 1 read and now):
- HALT — do NOT apply partial patches
- Report: `"CHG-N failed: old_string not found in <file>. Someone changed it between load and apply. Re-run /jetrix:task-update <target> to refresh."`
- Roll back any patches already applied in this run

Log every applied CHG to `dev/task-update-run.md`:

```yaml
stage_4:
  changes_applied:
    - id: CHG-001
      file: features/<slug>/subtask/backend/implementation.md
      applied_at: <ISO>
      local_char_delta: +42
    - ...
```

## 7. Stage 5 — Push to MC + read-back verify (v2.3.17 §4f.i)

For each touched file, push the FULL updated tab body:

- Parent implementation.md → `task-mcp.feature_update_implementation(solution_id, task_object_id, implementation_details, status="unchanged")`
- Sub-task implementation.md → `task-mcp.subtask_update_implementation(solution_id, parent_task_object_id, subtasks=[{subtask_object_id, implementation_details}])`
- Sub-task description.md → `task-mcp.subtask_upsert_bundle(solution_id, parent_task_object_id, subtasks=[{subtask_object_id, description}])` (upsert with existing id = PUT)
- Parent description (if changed) → `task-mcp.feature_upsert_bundle(solution_id, solution_slug, features=[{task_object_id, description}])`

**After every push (mandatory per v2.3.17 §4f.i):**

1. Read the pushed content back via task-mcp:
   - Sub-task Implementation → `task-mcp.subtask_list(solution_id, parent_task_object_id)`, locate row by subtask_object_id, read `implementation_details`
   - Parent Implementation → `task-mcp.get_task_by_id_or_number(...)`, read `implementationDetails`
2. Compute SHA-256 of local-sent vs server-returned (both normalized: strip trailing whitespace, CRLF → LF, ensure UTF-8)
3. **Match** → record BOTH hashes in `sync-state.json` under this task's `implementation_details_hash`; log `readback: ok` to `dev/task-update-run.md`
4. **Mismatch** → do NOT record any hash; log `readback: mismatch` + local/server lengths + first diff offset; print big warning:
   ```
   ⚠ MC read-back mismatch on <task-ref> after CHG-<ids>
     Local sent:    <N> chars, sha256 <hash>
     Server stored: <M> chars, sha256 <hash>
     First difference at byte offset <offset>.

     Push returned ok:true but MC stored a different payload. sync-state
     unchanged; next /dev:plan or /jetrix:task-update run will re-push
     from the current local state.
   ```
5. Do NOT retry automatically. Report and continue to §8.

## 8. Stage 6 — Report with URLs (per Rule 7.0)

Print the final summary — every task line MUST show its MC UI URL from the response `view_url` field (never construct locally):

```
✓ /jetrix:task-update <task-ref> complete

<N> changes applied across <M> files:
  CHG-001  ✓ applied + pushed + verified
  CHG-002  ✓ applied + pushed + verified
  CHG-003  ✓ applied + pushed + verified  (bundled across 2 sub-tasks)

MC tasks (verified):
  ↳ Feature-1 (parent)      https://mission-control.techjays.com/task/6a94fe0e...   ✓ verified (5,953 chars)
  ↳ Subtask-2 (backend)     https://mission-control.techjays.com/task/6a95e0a0...   ✓ verified (2,343 + 32,491 chars)
  ↳ Subtask-3 (frontend)    https://mission-control.techjays.com/task/6a95e0a1...   ✓ verified (2,432 + 39,522 chars)

Read-back verification: 3/3 pushes byte-identical (v2.3.17 §4f.i)

Files touched locally (not yet committed):
  - features/<slug>/subtask/backend/implementation.md
  - features/<slug>/subtask/frontend/implementation.md
  - features/<slug>/subtask/backend/status.md    (updated_at bumped)
  - features/<slug>/subtask/frontend/status.md   (updated_at bumped)

Next:
  · Review the local file diffs
  · Commit the local changes:    git add features/<slug> && git commit -m "update <task-ref>: <one-line summary>"
  · If /dev:build was already in-flight for this task, re-run once the local commit is on the working branch
```

If ANY read-back mismatched, elevate a `⚠ Verification failures` section BEFORE the "Next:" block naming each failed push and telling the user to re-run.

Also write the same content to `dev/task-update-run.md` under `## Stage 6 — Report`.

## 9. Failure modes + rollback

| Failure | Behavior |
|---|---|
| Stage 0: target unresolvable | Halt before any read; message names the arg + which resolution paths failed |
| Stage 1: local + MC parity conflict | Prompt user for choice (pull-first vs overwrite); halt if declined |
| Stage 2: user violates frame rule | Refuse the specific change with the rule reference + in-context alternative; do NOT halt the loop, keep collecting other changes |
| Stage 3: user picks `n` | Nothing written; halt cleanly |
| Stage 4: Edit fails (old_string missing) | HALT; roll back any patches already applied this run (revert the Edits by tracking each and re-applying reverse); report which file/CHG failed |
| Stage 5: push fails | Report per push; leave local files as-is (they already reflect the intended state); user re-runs when MC is reachable |
| Stage 5: read-back mismatch | Report per push; DO NOT update sync-state hashes for that task |

## 10. Guardrails

- **Never** rewrite a whole section to change one line. Always `Edit` with precise `old_string`. If a genuine restructure is needed, ask the user explicitly and confirm before applying.
- **Never** push per-edit. All changes batch into ONE push cycle after user confirms.
- **Never** touch BA-owned files (`acceptance-criteria.md`, `business-rules.md`, `test-scenarios.md`, `nfrs.md`, `dependencies.md`, `open-questions.md`, `feature.md`, `workflow.md`). Those are read-only reference for this command; the user runs `/ba:*` commands for BA edits.
- **Never** touch TL context units (`<repo>/context/code-context/…`). If a change is really about the source-of-truth contract, direct the user at the TL unit file or `/tl:code-map`.
- **Never** update MC status (`todo → inProgress`, `inProgress → devReview`). This command is content-only. Status transitions belong to `/dev:build` / `/dev:commit` / MC UI.
- **Never** update `qa/quality-gates.md`. That's `/qa:setup` / `/qa:health` scope.
- **Never** construct MC URLs locally from `.jetrix/project.json`. Always read `view_url` from the task-mcp response per Rule 7.0.
- **Never** violate v2.3.16 frame rules (adding retired sections). Refuse with rule reference + in-context alternative.
- **Never** compose a whole new file body via LLM. Section edits only. A whole-file compose is `/dev:plan`'s job.

## 11. Skills / agents / tools invoked

- No subagents — this command runs in the main session interactively with the user (needs `AskUserQuestion` and back-and-forth conversation)
- `AskUserQuestion` for the final Stage 3 confirm + any Stage 4 rollback/retry prompts
- `Read` for Stage 1 file loads
- `Edit` for Stage 4 patches (never `Write` for full files)
- `task-mcp` tools for Stage 5:
  - `get_task_by_id_or_number` — Stage 1 MC state load
  - `subtask_list` — Stage 1 MC state load
  - `feature_update_implementation` — Stage 5 parent Implementation tab push
  - `subtask_update_implementation` — Stage 5 sub-task Implementation tab push
  - `subtask_upsert_bundle` — Stage 5 sub-task Description tab push (with existing id = PUT)
  - `feature_upsert_bundle` — Stage 5 parent Description push (rare)

## 12. What this command deliberately does NOT do

- Does not run `/dev:plan` again — this is a targeted patch, not a re-plan
- Does not touch git — the local files change; the user commits them separately (or lets `/dev:build` pick up the change)
- Does not push to MC's `main` env — dev env only (matches `/dev:plan` Stage 4 behavior; per user memory rule "env promotion is MC's merge agent")
- Does not run compose or lint rules — this is a surgical patch, not a compose. Rule 0 / Rule 0a / Rule 0d apply only when generating fresh content, which this command doesn't do. However, if a user's patch would introduce a retired-concept string (e.g. adds `## 7. Coverage`), refuse it in Stage 2 with the rule reference — same halt list as Rule 0a but at intent-collection time, not post-write.
- Does not trigger read-back verify for BA / TL context files — this command doesn't touch them.

---

## Example session

```
$ /jetrix:task-update Subtask-2

✓ Loaded task Subtask-2

  Feature: holiday-calendar-management
  Kind:    sub-task (backend of a split feature)
  Sections available: §1 Build sequence · §2 Impacted components · §3 Operations ·
                      §4 Stored data · §5 Surfaces · §6 Touch points ·
                      §7 Risks and rollback · §8 Shared contract
                      + description.md 6-section shape

Tell me what needs to change. When you're done listing changes, say "ready".

user: in §3, the POST /holidays 409 refusal message is too vague. Change it to
      say something like "A holiday is already scheduled for this date. Please
      choose another date."

Claude: Got it — updating the 409 refusal row in §3 POST /holidays.
        (CHG-001 collected)

user: also, the wire contract in §8 for time/locale — right now it just says
      ISO-8601 UTC. For dates specifically (the holiday date), we want
      YYYY-MM-DD without a time component. Because otherwise a user in a
      different timezone sees the wrong day.

Claude: Right — that's a real cross-timezone bug. This is a §8 Shared contract
        change so it inherits verbatim across backend + frontend + mobile.
        I'll apply the same edit to all three sub-tasks. Confirm? [y/n]
user: yes

Claude: Got it. (CHG-002 collected, will bundle to all 3 sub-tasks.)

user: one more thing — in the frontend §5, the Panel's Rendered states line
      should use a skeleton, not a spinner, during loading.

Claude: The frontend sub-task's §5 <Domain>Panel Rendered states line. Loading:
        skeleton (3 placeholder rows) instead of spinner. Confirm the row shape?
        [y/n]
user: yes, and use "3 placeholder rows" as the specific text

Claude: Got it. (CHG-003 collected.)

user: ready

Claude: Ready to apply 3 changes:

  CHG-001  [features/holiday-calendar-management/subtask/backend/implementation.md]
           §3 Operations / POST /holidays / Refusals table
           - | 409 | date already has a holiday | "Holiday already exists on this date." |
           + | 409 | date already has a holiday | "A holiday is already scheduled for this date. Please choose another date." |

  CHG-002  [backend + frontend + mobile implementation.md]  ← §8 Shared contract, verbatim to all 3
           §8 Shared contract / Time and locale row
           - Wire time format ISO-8601 UTC; formatting in user's locale via formatTimestamp.js
           + Wire time format ISO-8601 UTC; date-only fields (e.g. holiday date) sent as YYYY-MM-DD without time component to avoid cross-timezone day-shift bugs

  CHG-003  [features/holiday-calendar-management/subtask/frontend/implementation.md]
           §5 <Domain>Panel / Rendered states line
           - Loading: spinner. Refusal 500: message + Retry(refetch()). Refusal 400/404: message, no Retry. Empty: "No items yet." Populated: one <Domain>Row per element.
           + Loading: skeleton (3 placeholder rows). Refusal 500: message + Retry(refetch()). Refusal 400/404: message, no Retry. Empty: "No items yet." Populated: one <Domain>Row per element.

Files touched:  3 sub-task implementation.md files
MC tasks:       Subtask-2 (backend), Subtask-3 (frontend), Subtask-4 (mobile)
Read-back:      will verify after each push

Apply and push?  [y]es / [n]o / [e]dit CHG-N
user: y

[applies Edits locally, pushes to MC, runs read-back verify per §4f.i]

✓ /jetrix:task-update Subtask-2 complete

3 changes applied across 3 files:
  CHG-001  ✓ applied + pushed + verified
  CHG-002  ✓ applied + pushed + verified  (bundled to backend + frontend + mobile)
  CHG-003  ✓ applied + pushed + verified

MC tasks (verified):
  ↳ Subtask-2 (backend)   https://mission-control.techjays.com/task/6a95e0a0...   ✓ verified (2,343 + 32,491 chars)
  ↳ Subtask-3 (frontend)  https://mission-control.techjays.com/task/6a95e0a1...   ✓ verified (2,432 + 39,522 chars)
  ↳ Subtask-4 (mobile)    https://mission-control.techjays.com/task/6a95e0a2...   ✓ verified (2,187 + 28,145 chars)

Read-back verification: 3/3 pushes byte-identical (v2.3.17 §4f.i)

Files touched locally (not yet committed):
  - features/holiday-calendar-management/subtask/backend/implementation.md
  - features/holiday-calendar-management/subtask/frontend/implementation.md
  - features/holiday-calendar-management/subtask/mobile/implementation.md
  - features/holiday-calendar-management/subtask/*/status.md (updated_at bumped)

Next:
  · Review the local file diffs
  · Commit:  git add features/holiday-calendar-management && git commit -m "update holiday-calendar: 409 message + date wire format + panel loading skeleton"
```
