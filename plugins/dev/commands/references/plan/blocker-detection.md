## Stage 3 — Blocker detection (v2.3 refactor — was Stage 3.5 sub-phase)

**Purpose.** Surface every plan-time decision the user must make BEFORE Stage 4 (compose + push) runs. Because Stage 4 refuses to write `implementation.md` on open blockers, this stage gates the compose. Any unknown, ambiguous, or "figure-out-later" item detected here becomes a **`PB-###` Plan Blocker** written to `dev/<repo>-plan-blockers.md` (sub-task) or `dev/plan-blockers.md` (parent-alone) for user resolution.

**v2.3 refactor note:** in v2.2 this ran AFTER a half-baked `implementation.md` was already composed + pushed to MC. In v2.3 this runs on the Stage 2 analysis scratchpad (`dev/<repo>-analysis.md`) BEFORE any `implementation.md` exists — so a blocker never leaves a partial file behind.

**Runs per task** (parent-alone → once; split feature → once per sub-task, IDs prefixed with sub-task number: `PB-1-###`, `PB-2-###`).

**On completion:** either NO blockers (task proceeds to Stage 4 compose+push) OR `plan-blockers.md` written and task set to `BLOCKED_ON_PLAN` (MC `blocked`), user resolves, re-runs `/dev:plan --resume`.

---

### 5.1 Detection sources (union of all five)

Scan each source; every hit generates a candidate blocker. Deduplicate by target-file + issue; a single unknown can be surfaced by multiple sources.

#### Source 1 — `dev/<repo>-analysis.md` scratchpad `[HELD]` markers + `TBD` / `unknown` entries (Stage 2 output)

For parent-alone target: `features/<slug>/dev/analysis.md`.
For sub-task target: `features/<slug>/dev/<repo>-analysis.md`.

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

#### Source 2 — BA `open-questions.md` "Blocks build" rows

Read `features/<slug>/open-questions.md`. Look for table rows where the `Impact` cell (case-insensitive) starts with:

- `Blocks build`
- `Blocks implementation`
- `Blocks estimate` (an older BA classifier; treat same as Blocks build)

Extract the row's `OQ-###` id, question text, and Impact.

#### Source 3 — BA `ba/registers/integrations.md` unresolved entries

Read `ba/registers/integrations.md`. Look for `INT-###` rows where ANY of these fields is missing / empty / `TBD` / `?`:

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

#### Source 5 — `implementation.md §3 Impacted components` `unknown` entries

Read the impact analysis. In any of the 12 dimensions, entries marked `unknown` (not `N/A`) are blockers. `N/A` is a legitimate decision (dimension doesn't apply); `unknown` means we didn't figure it out.

---

### 5.2 Heuristic checks per dev-plan step

For each ordered step in `implementation.md`, apply these questions. Any YES → mint a blocker.

| Question | Blocker if YES |
|---|---|
| Does this step call an external system whose contract isn't in `ba/registers/integrations.md`? | Yes — missing integration contract |
| Does this step apply a business rule whose edge case isn't decided in `ba/registers/business-rules.md`? | Yes — unclear BR edge case |
| Does this step require a config value (env var, credential, URL) not documented in `shared-context/technology-stack.md`? | Yes — missing config |
| Does this step have two or more implementations that would produce different observable behaviour? | Yes — undecided implementation choice |
| Does this step reference a schema field whose type/nullability/constraint isn't unambiguous in the TL entity file OR BA data register? | Yes — ambiguous schema |
| Does this step require an authn/authz check that isn't declared in `system-landscape.md` or `nfrs.md`? | Yes — undecided auth |
| Does this step need UI copy the parent BA files don't provide (specific error message text, button label, etc.)? | Yes — missing copy |
| Does this step depend on another feature that isn't in this batch AND isn't marked as already-shipped? | Yes — unclear cross-feature ordering |

**Stylistic questions are NOT blockers** — code-review skill covers those. Function naming, whitespace, import order, comment format — none of those block build; they're addressed at commit-time.

---

### 5.3 Blocker minting

For each detected issue that survives dedup:

1. **Mint the next ID** for THIS task:
   - Parent-alone: `PB-001`, `PB-002`, ... (sequential per task, append-only across runs)
   - Sub-task N: `PB-<N>-001`, `PB-<N>-002`, ... (per-sub-task sequence with sub-task prefix)
2. **Determine the category** from §5.1/§5.2 (integration / auth / schema / config / BR-edge / dependency / etc.)
3. **Find (or draft) options** with a recommendation:
   - For an integration missing a contract: recommend option 1 (use documented internal service if any exists in `system-landscape.md`)
   - For an ambiguous BR: recommend option 1 (whichever reading matches `ba/registers/business-rules.md` most literally)
   - For a config value: recommend option 1 (existing convention in the repo if any; else industry default)
   - Include a "Trade-off" line per option — never present options without stakes
4. **Blocks:** list which AC / BR / TS / dev-plan step is blocked, so the user sees the downstream impact

---

### 5.4 Writing `dev/plan-blockers.md`

Write to:
- Parent-alone: `features/<slug>/dev/plan-blockers.md`
- Sub-task: `features/<slug>/dev/<repo>-plan-blockers.md` (repo-slug prefix — v2.3 flat dev/ convention)

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
   current_state: BLOCKED_ON_PLAN
   blocker_file: dev/plan-blockers.md
   blocker_count: <N>
   ```
2. Update `dev/plan-run.md` `stage-3` block:
   ```yaml
   stage-3:
     status: BLOCKED
     blockers_detected: <N>
     blockers_file: dev/plan-blockers.md
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
- **None exist / all `Applied at plan-fold:` already filled** → nothing to do; task already in `PLANNED`, continue to Stage 3.5's finalise sub-step

Fold logic lives in [`blocker-fold.md`](blocker-fold.md) — see that file for the per-category deterministic edit rules.

---

### 5.8 Idempotency

Re-running `/dev:plan` (not `--resume`) on a task that already has `plan-blockers.md`:

- **Do NOT wipe the file** — user's Resolutions are precious.
- Re-run detection (§5.1 + §5.2). For each newly-detected issue, mint the next `PB-###` (append). For issues previously blocked that no longer appear (BA answered the question in `open-questions.md` etc.), leave the old PB in place with a note appended: `> Detected as resolved-upstream at <ISO>; leaving in file for audit.`
- Update `last_updated:` frontmatter
- If any new blockers were minted with unresolved Resolution → task stays `BLOCKED_ON_PLAN`

---

### Skills / agents invoked from this reference

None. Blocker detection is orchestration logic — all reads are direct file reads, all writes are direct file writes, no subagent delegation. Runs inline as part of `/dev:plan` Stage 3.

The user's response (filling in Resolutions and re-running `--resume`) delegates the actual fold to [`blocker-fold.md`](blocker-fold.md).
