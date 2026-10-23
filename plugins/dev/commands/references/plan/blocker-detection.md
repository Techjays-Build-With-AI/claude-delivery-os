## Stage 3 — Blocker detection (v2.3 refactor — was Stage 3.5 sub-phase)

**Purpose.** Surface every plan-time decision the user must make BEFORE Stage 4 (compose + push) runs. Because Stage 4 refuses to write `implementation.md` on open blockers, this stage gates the compose. Any unknown, ambiguous, or "figure-out-later" item detected here becomes a **`PB-###` Plan Blocker** written to `units/<repo>/plan-blockers.md` (sub-task) or `units/<repo>/plan-blockers.md` (parent-alone) for user resolution.

**v2.3 refactor note:** in v2.2 this ran AFTER a half-baked `implementation.md` was already composed + pushed to MC. In v2.3 this runs on the Stage 2 analysis scratchpad (`units/<repo>/analysis.md`) BEFORE any `implementation.md` exists — so a blocker never leaves a partial file behind.

**Runs per task** (parent-alone → once; split feature → once per sub-task, IDs prefixed with sub-task number: `PB-1-###`, `PB-2-###`).

**On completion:** either NO blockers (task proceeds to Stage 4 compose+push) OR `plan-blockers.md` written and task set to `blocked` (MC `blocked`), user resolves, re-runs `/dev:plan --resume`.

---

### 5.1 Detection sources (union of all six)

Scan each source; every hit generates a candidate blocker. Deduplicate by target-file + issue; a single unknown can be surfaced by multiple sources.

**Dedup across the batch, not just within a task.** Some findings are facts about the repository or the project, not about the feature that happened to trip over them — a base branch missing code that sits on another branch, an unmapped repo, an absent shared helper, a pending `DEC-###` merge. Asked per feature, one such fact becomes N identical questions; the user in front of them cannot tell it is the same decision each time.

So before minting, classify: does the answer depend on **this feature**, or would it be identical for every feature in the batch? Batch-wide answers are minted **once**, against the first task that surfaced them, and every other affected task records `Blocked by <that PB>` and carries on. Ask it once, at the batch checkpoint, with the list of features it gates — never once per feature.

**And check whether it is already decided.** A finding whose answer is written in a `DEC-###` in `shared-context/decision-log.md` is not an open question: cite the decision, record it as an assumption per §5.3.0, and do not ask.

#### Source 1 — `units/<repo>/analysis.md` scratchpad `[HELD]` markers + `TBD` / `unknown` entries (Stage 2 output)

For parent-alone target: `features/<slug>/units/<repo>/analysis.md`.
For sub-task target: `features/<slug>/units/<repo>/analysis.md`.

Also grep the corresponding TL brief (`features/<slug>/tl-plan.md`) for `[HELD]` markers that made it into TL's rollup but weren't reconciled by Stage 2 analysis.

Grep patterns:

```
\[HELD[^\]]*\]                    # e.g. [HELD · waiting on OQ-005]
\bTBD\b                          # bare TBD
<\?>|<UNKNOWN>|<NEEDS[^>]*>      # explicit placeholder tokens
NEEDS:                           # e.g. "NEEDS: exact endpoint URL"
\[SET REQUIRED\]                 # env var placeholder
```

For each hit: extract the line's context (~30 chars either side) and the `##` section it lives under.

#### Source 2 — BA `dependencies.md` § `## Open questions` "Blocks build" rows (v2.3.3 skip-resolved)

Read `features/<slug>/dependencies.md` § `## Open questions`. Look at BOTH the frontmatter `open_questions:` YAML array AND body table rows. Match rows where the `impact` / `Impact` field (case-insensitive) starts with:

- `Blocks build`
- `Blocks implementation`
- `Blocks estimate` (an older BA classifier; treat same as Blocks build)

**Skip rows whose `status` is already `Resolved`** (v2.3.3 — `blocker-fold.md` §6.3 sets `status: Resolved` on upstream OQs when the corresponding PB is folded via `/dev:plan --resume` OR `/dev:resolve --plan`). A re-detection pass on a task that already had blockers resolved must NOT re-raise the same OQs — that would create an infinite loop.

Extract each unresolved matching row's `OQ-###` id, question text, and Impact.

#### Source 3 — BA `shared-context/integrations.md` unresolved entries

Read `shared-context/integrations.md`. Look for `INT-###` rows where ANY of these fields is missing / empty / `TBD` / `?`:

- `endpoint` (URL)
- `auth` (auth mechanism)
- `request_schema` (or "request shape")
- `response_schema`
- `error_codes`

**Filter:** only surface entries this task's `implementation.md` actually references. An unresolved `INT-###` for a different feature is not this task's blocker.

#### Source 4 — `shared-context/system-landscape.md` role/actor gaps

Read `shared-context/system-landscape.md`. If this task's parent `feature.md` declares an actor role in `users:` frontmatter (e.g. `operations-coordinator`), verify the role is defined in `system-landscape.md`'s Actors section with:

- Description
- Permission scope (what they can do)
- Authentication mechanism

Missing OR listed as `TBD` → blocker.

#### Source 5 — `analysis.md` § `impact_matrix` `unknown` entries

**Read `analysis.md`, not `implementation.md`.** Blocker detection runs at Stage 3, and `implementation.md`
is composed at Stage 4 — it does not exist yet. The v2.3 stage reorder moved the compose after detection and
left this input list behind, so the source read a file that had not been written and silently found nothing.
The impact matrix it wants is a block of the Stage 2 scratchpad, which is where it has always actually lived.

Read the impact analysis. In any of the 12 dimensions, entries marked `unknown` (not `N/A`) are blockers. `N/A` is a legitimate decision (dimension doesn't apply); `unknown` means we didn't figure it out.

#### Source 6 — `discussion.md` § `## Comments` unresolved threads

Read `discussion.md` § `## Comments` in the task's own folder (`features/<slug>/`,
`features/<slug>/units/<repo>/`, or `tasks/<slug>/`). Pulled from Mission
Control by `/dev:plan` §2c; absent when the task has no discussion, which is
the normal case — skip silently.

A root-level thread marked `**UNRESOLVED**` is a question a teammate asked on
the ticket that nobody answered. Treat each as a candidate blocker: extract
its `[C-###]` id, the author, and the thread text including its replies (a
reply may already contain the answer without anyone having marked the thread
resolved — judge on content, and if the thread reads as settled, record it as
an assumption rather than a blocker).

**Skip threads marked resolved** — same rule as Source 2. A resolved thread is
a closed decision, and re-raising it would loop on every re-run.

Cite the comment id in the minted blocker's Source line (`comments.md C-12`)
so the user can find the conversation in MC. When the user resolves the `PB`,
the answer can be posted back to the thread with
`task-mcp.task_comment_post` and the thread closed with
`task-mcp.task_comment_resolve` — both optional, never automatic.

---

### 5.2 Heuristic checks per dev-plan step

For each ordered step in `implementation.md`, apply these questions. Any YES → mint a blocker.

| Question | Blocker if YES |
|---|---|
| Does this step call an external system whose contract isn't in `shared-context/integrations.md`? | Yes — missing integration contract |
| Does this step apply a business rule whose edge case isn't decided in `requirements/<slug>/registers/business-rules.md`? | Yes — unclear BR edge case |
| Does this step require a config value (env var, credential, URL) not documented in `shared-context/technology-stack.md`? | Yes — missing config |
| Does this step have two or more implementations that would produce different observable behaviour? | Yes — undecided implementation choice |
| Does this step reference a schema field whose type/nullability/constraint isn't unambiguous in the TL entity file OR BA data register? | Yes — ambiguous schema |
| Does this step require an authn/authz check that isn't declared in `system-landscape.md` or `nfrs.md`? | Yes — undecided auth |
| Does this step need UI copy the parent BA files don't provide (specific error message text, button label, etc.)? | Yes — missing copy |
| Does this step depend on another feature that isn't in this batch AND isn't marked as already-shipped? | Yes — unclear cross-feature ordering |

**Stylistic questions are NOT blockers** — code-review skill covers those. Function naming, whitespace, import order, comment format — none of those block build; they're addressed at commit-time.

---

### 5.2a Ticket-vs-code reconciliation (non-feature targets)

A BA feature is a specification — it describes something that does not exist yet, so there is nothing to contradict. A bug, story, or ad-hoc task is a **claim about code that already exists**, and the claim can simply be wrong: filed against stale behaviour, already fixed, mis-attributed, or describing intended design as a defect.

Silently planning against a wrong claim produces a confident fix for the wrong problem. So after reading the code-context units for the ticket's area, reconcile the ticket against what the code actually does, and mint a blocker on any mismatch:

| Question | Blocker if YES |
|---|---|
| Do the Steps to Reproduce reference a route, screen, or handler that doesn't exist in the code-context graph? | Yes — repro path not found |
| Does the code already implement the Expected Result on the described path? | Yes — possibly already fixed |
| Does the described symptom contradict what the code plainly does, so the real fault is elsewhere? | Yes — symptom/root-cause mismatch |
| Is the Expected Result a change to behaviour the code implements deliberately (explicit branch, documented rule, covering test)? | Yes — working-as-designed dispute |
| Is the Description silent on, or contradicted by, the condition that actually triggers the fault? | Yes — description does not match code |

**These are always user-confirmed, never auto-resolved.** Do not "correct" the ticket from the code, and do not implement what you believe was meant. You are reading a human's report of a real observation; the code may be right and the report stale, or the report right and your reading of the code wrong. Only the user can settle which. Mint the blocker with:

- what the ticket claims, quoted from the tab it came from;
- what the code shows, cited as `file:line` from the code-context unit;
- options that always include **"ticket is right — my reading is wrong, plan the fix as filed"**, so the user can overrule the analysis without editing the ticket.

Never mint one of these off the ticket text alone — a mismatch claim is only as good as the code reading behind it. If the relevant area has no code-context coverage, that is a *missing context* blocker, not a mismatch.

---

### 5.3 Blocker minting

#### 5.3.0 First decide whether it is a blocker at all

**A detected unknown is not automatically a blocker.** Without this test every `TBD` in an analysis
scratchpad became a `PB-###`, and a 19-feature batch produced 46 of them — "which fields are
mandatory at registration", "two calendar days or two working days", "wording of the 401 and 403
messages". Those are answerable from the scope and the repo; handing all 46 back as questions turns
planning into an interrogation and buries the few that genuinely need the client.

BA already draws this line — its ledger carries `Accepted (assumed)` beside `Open`, and most rows
end up assumed. Planning needs the same line.

For each detected issue, in order:

1. **Can it be settled from context you already hold?** The scope and its registers, an existing
   convention in the repo, a prior `DEC-###`, or the ecosystem default for the stack. If step 3
   below could draft a recommended option, you can almost always take that option instead of asking.
2. **If yes, is it safe to assume?** It is NOT safe, and you mint a blocker regardless, when the
   decision moves **money**, changes **who can see or do what**, alters a **stored schema** or an
   **external contract**, or carries legal, compliance or data-retention weight. Those stay
   blockers even when an obvious answer exists, because an obvious wrong answer is expensive.
3. **If it is safe, record an assumption — do not mint.** Append an `ASM-###` to
   `requirements/<slug>/ledger.md` (`kind: assumption`, `Status: Accepted (assumed)`) citing the
   analysis line it came from, note it in `implementation.md`, and **list it in the plan summary**
   under `Assumed (N)` with its one-line rationale. An assumption the user never sees is a guess;
   an assumption they can read and overturn is a decision made on their behalf.

Copy, wording, naming, file layout, library choice where the repo has no convention, and ordering
that no acceptance criterion pins are **assume-by-default**. Permissions, pricing, retention,
schema and third-party contracts are **blocker-by-default**.

Only an issue that fails this test reaches the minting steps below.

#### 5.3.1 Mint

For each detected issue that survives dedup **and** §5.3.0:

1. **Mint the next ID** for THIS task:
   - Parent-alone: `PB-001`, `PB-002`, ... (sequential per task, append-only across runs)
   - Sub-task N: `PB-<N>-001`, `PB-<N>-002`, ... (per-sub-task sequence with sub-task prefix)
2. **Determine the category** from §5.1/§5.2 (integration / auth / schema / config / BR-edge / dependency / etc.)
3. **Find (or draft) options** with a recommendation:
   - For an integration missing a contract: recommend option 1 (use documented internal service if any exists in `system-landscape.md`)
   - For an ambiguous BR: recommend option 1 (whichever reading matches `requirements/<slug>/registers/business-rules.md` most literally)
   - For a config value: recommend option 1 (existing convention in the repo if any; else industry default)
   - Include a "Trade-off" line per option — never present options without stakes
   - **An option that drops something the analysis cited as used must say so in its trade-off.** If the scratchpad recorded a field, column or parameter as read — by a fallback, a downstream caller, anything — and an option removes it, the trade-off names it and what breaks. A recommendation that quietly discards a dependency the same run discovered is worse than no recommendation, because the citation makes it look considered.
4. **Blocks:** list which AC / BR / TS / dev-plan step is blocked, so the user sees the downstream impact

---

### 5.4 Writing `units/<repo>/plan-blockers.md`

Write to:
- Parent-alone: `features/<slug>/units/<repo>/plan-blockers.md`
- Sub-task: `features/<slug>/units/<repo>/plan-blockers.md` (repo-slug prefix — v2.3 flat dev/ convention)
- Non-feature ticket: `tasks/<slug>/units/<repo>/plan-blockers.md` (never split, so never repo-prefixed)

**Frontmatter:**

```yaml
---
doc_type: plan-blockers
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>            # OMIT for parent-alone
subtask_repo: <repo-slug>      # OMIT for parent-alone
generated_at: <ISO>
status: OPEN                   # OPEN | RESOLVING | RESOLVED
last_updated: <ISO>            # updated on --resume folds
---
```

**Body — one `## PB-<id>` section per blocker:**

```markdown
## PB-001 — <short title of the blocker>

**Detected in:** <source-file + section>
**Category:** integration-contract | auth-model | schema-ambiguity | config-unknown | br-edge-case | dependency-choice | data-flow | copy | cross-feature-ordering
**Blocks:** <what downstream item(s) this blocks — AC-X / BR-Y / dev-plan step Z / migration>
**Suggested owner:** <ba | tl | dev | product | infra>   ← who's best positioned to answer

**Description**
<1–3 paragraphs stating the problem cleanly. Cite the exact file/section where the ambiguity or gap lives. Do not restate the whole feature — just the specific gap.>

**Options** (with recommendation)

| # | Option | Trade-off |
|---|---|---|
| 1 (recommended) | <option 1 body> | <trade-off text> |
| 2 | <option 2 body> | <trade-off text> |
| 3 | <option 3 body if applicable> | <trade-off text> |

**Resolution:**
_(fill in — write the option number OR describe your choice)_

**Applied at plan-fold:**
_(auto-filled by /dev:plan --resume — do not edit)_

---
```

**Ordering.** Blockers are ordered by dev-plan step they block (step 1 first, step N last). Within the same step, integration contracts come before schema decisions come before UI copy — the natural build order.

---

### 5.5 State transitions on write

After writing `plan-blockers.md` with `status: OPEN`:

1. Update `status.md`:
   ```yaml
   status: blocked
   phase: plan-blockers
   blocker_file: units/<repo>/plan-blockers.md
   blocker_count: <N>
   ```
2. Update `units/<repo>/status.md § ## Run history` `stage-3` block:
   ```yaml
   stage-3:
     status: BLOCKED
     blockers_detected: <N>
     blockers_file: units/<repo>/plan-blockers.md
     finished_at: <ISO>
   ```
3. Push MC status → `blocked` via `task-mcp.update_task_status` (with a status_reason field if the schema supports it: `"blocked on plan-time decisions"`)
4. Append a `DEC-###` row to `shared-context/decision-log.md` — one row noting "plan-blockers surfaced" (not per-blocker; per-run)

---

### 5.6 Halting output

Print the halt message per `/dev:plan` command §7-blocker-halt (see `plugins/dev/commands/plan.md`). The message names every `PB-###`, the file path, and the two possible next actions (resolve or escalate to BA/TL).

Never proceed past Stage 3 with an OPEN `plan-blockers.md`. Never proceed to Stage 3.5's Finalise sub-step until either (a) blockers file didn't exist / had 0 blockers, or (b) the file `status: RESOLVED` after a `--resume` fold.

---

### 5.7 On `/dev:plan --resume` — behaviour when `plan-blockers.md` exists

If Stage 3.5 finds an existing `plan-blockers.md`:

- Read every `## PB-<id>` section
- For each: is the `Resolution:` field non-empty AND not the placeholder text `_(fill in — ...)_`?
- **All resolved** → set `status: RESOLVING`, hand off to `blocker-fold.md` reference
- **Some unresolved** → halt with a targeted message listing the unresolved PBs; keep `status: OPEN`
- **None exist / all `Applied at plan-fold:` already filled** → nothing to do; task already in `readyForDev`, continue to Stage 3.5's finalise sub-step

Fold logic lives in [`blocker-fold.md`](blocker-fold.md) — see that file for the per-category deterministic edit rules.

---

### 5.8 Idempotency

Re-running `/dev:plan` (not `--resume`) on a task that already has `plan-blockers.md`:

- **Do NOT wipe the file** — user's Resolutions are precious.
- Re-run detection (§5.1 + §5.2). For each newly-detected issue, mint the next `PB-###` (append). For issues previously blocked that no longer appear (BA answered the question in `dependencies.md` § `## Open questions` etc.), leave the old PB in place with a note appended: `> Detected as resolved-upstream at <ISO>; leaving in file for audit.`
- Update `last_updated:` frontmatter
- If any new blockers were minted with unresolved Resolution → task stays `blocked`

---

### Skills / agents invoked from this reference

None. Blocker detection is orchestration logic — all reads are direct file reads, all writes are direct file writes, no subagent delegation. Runs inline as part of `/dev:plan` Stage 3.

The user's response (filling in Resolutions and re-running `--resume`) delegates the actual fold to [`blocker-fold.md`](blocker-fold.md).
