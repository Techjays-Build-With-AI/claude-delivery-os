## Blocker fold — Stage 3 sub-phase on `/dev:plan --resume` (v2.3 refactor)

**Purpose.** Fold user-resolved `PB-###` decisions into the Stage 2 analysis scratchpad (`dev/<repo>-analysis.md`) so that when Stage 4 (compose + push) runs on --resume, it produces `implementation.md` with the resolutions baked in — no half-baked file, no post-hoc patch.

### Original header (v2.2)

Blocker fold — runs on `/dev:plan --resume` when `plan-blockers.md` has resolutions

**Purpose.** Take each `PB-###` with a filled `Resolution:` and apply it deterministically to the Stage 2 analysis scratchpad (`dev/<repo>-analysis.md`) — specifically the `build_sequence` and `impact_matrix` blocks + any relevant register. Log each fold as a `DEC-###`. Never re-plan, never reason about "how the answer applies" — the blocker's Options table already names the edit; the fold executes it.

**Runs from `/dev:plan --resume`** after [`blocker-detection.md`](blocker-detection.md) §5.7 confirms every `PB-###` has a non-empty `Resolution:`.

**On completion:** `plan-blockers.md` `status:` → `RESOLVED`, every PB has its `Applied at plan-fold:` field filled, delivery-status → `PLANNED`, MC → `readyForDev`.

---

### 6.1 Interpret each Resolution

Iterate blockers in file order. For each `PB-<id>`:

1. Read the `Resolution:` field.
2. **If it's a single option number** (e.g. `1`, `2`, `3`):
   - Apply the option verbatim from the Options table
3. **If it's free text**:
   - Match against option bodies — take the closest option by phrase overlap
   - If the match is unambiguous → apply that option
   - If ambiguous (matches two options roughly equally) → **halt fold on this PB** with a note added to the file: `> Resolution ambiguous — matches options 1 and 2. Please write a specific option number or reword.` Task stays `BLOCKED_ON_PLAN`.
   - If matches no option (user chose something new) → **treat as custom resolution**: apply the user's words verbatim to the target field, and log a `DEC-###` with a note "User chose custom resolution — not one of the pre-suggested options."

Never guess when the resolution is ambiguous; the point of this loop is *not* asking during build.

---

### 6.2 Per-category fold rules

Each blocker's `**Category:**` field decides which fold rule applies. All fold rules are deterministic — take the resolution, apply to specific fields, log the DEC.

#### 6.2.1 `integration-contract`

**Target files:** analysis scratchpad `dev/<repo>-analysis.md` (blocks: `build_sequence`, `impact_matrix`) + `ba/registers/integrations.md` (if the resolution provides missing fields)

**Fold rule:**
1. In `ba/registers/integrations.md`: locate the `INT-###` row, fill missing fields from the resolution (endpoint, auth, request/response schema)
2. In the analysis scratchpad `dev/<repo>-analysis.md` `build_sequence:` block: locate the step that references the integration, replace `[HELD]` / `TBD` with the concrete API call details from the resolution
3. In the analysis scratchpad `dev/<repo>-analysis.md` `impact_matrix:` block: fill the `Integrations` dimension with the resolved endpoint + auth mechanism
4. Log: `DEC-<###>: Resolved integration <INT-###> per PB-<id> — <one-line summary of the option>`

**Example — PB-001 resolution "1":**
- Option 1 = "Use internal compliance service at `https://compliance.acme.internal/v1/duplicate-check`, Bearer auth via `COMPLIANCE_TOKEN`"
- Fold updates INT-001 row's endpoint + auth fields
- Fold updates implementation.md step 3 from `[HELD] call compliance service` to `POST https://compliance.acme.internal/v1/duplicate-check with { tax_id, country } — Authorization: Bearer <COMPLIANCE_TOKEN>`
- Fold updates implementation.md §2 Impacted components §Integrations with `INT-001 Compliance service · endpoint · Bearer auth`
- Log DEC-042

#### 6.2.2 `schema-ambiguity`

**Target files:** analysis scratchpad `dev/<repo>-analysis.md` (blocks: `build_sequence`, `impact_matrix`) + TL entity file (`<repo>/context/code-context/database/entities/<slug>.md`)

**Fold rule:**
1. In the TL entity file: update the `## Structure` table with the resolved column type / nullability / constraint
2. In the analysis scratchpad `dev/<repo>-analysis.md` `build_sequence:` block: update the migration step with the resolved schema
3. In the analysis scratchpad `dev/<repo>-analysis.md` `impact_matrix:` block: update `Database` dimension to reflect the resolved schema
4. Log: `DEC-<###>: Resolved schema ambiguity <field> per PB-<id> — <one-line summary>`

#### 6.2.3 `auth-model`

**Target files:** `implementation.md` + `shared-context/system-landscape.md` (Actors section) + TL endpoint files if endpoints check the role

**Fold rule:**
1. In `system-landscape.md`: add or complete the role's Description + Permission scope + Authentication mechanism per the resolution
2. In `implementation.md`: update every step that touches auth with the resolved model
3. In each TL endpoint file that enforces the role: update `## Permissions` section
4. Log: `DEC-<###>: Resolved auth model for <role> per PB-<id> — <one-line summary>`

#### 6.2.4 `config-unknown`

**Target files:** `implementation.md` + `shared-context/technology-stack.md` + `dev/local-runbook.md` (creates one if absent — this is the developer-facing env var log)

**Fold rule:**
1. In `technology-stack.md`: append the env var / config value to the Configuration section with (name, purpose, example value, source-of-value)
2. In `implementation.md`: update the step that needed the config with the concrete variable name + how to obtain the value
3. If the resolution says *"user must set locally"* → note the variable in `dev/local-runbook.md` under `Environment / config setup` with `[SET REQUIRED]` marker (for `/dev:build` Stage 11 to consume)
4. Log: `DEC-<###>: Resolved config value <name> per PB-<id>`

#### 6.2.5 `br-edge-case`

**Target files:** `implementation.md` + `ba/registers/business-rules.md` (updates the BR entry)

**Fold rule:**
1. In `ba/registers/business-rules.md`: locate the `BR-###` row, append the resolved edge case to the Statement column (e.g. `"...duplicate submissions after 24h are treated as new submissions"`)
2. In `implementation.md`: update every step that enforces this BR with the resolved edge-case handling
3. Log: `DEC-<###>: Resolved BR-<###> edge case per PB-<id> — <one-line summary>`

#### 6.2.6 `dependency-choice`

**Target files:** `implementation.md` + `shared-context/technology-stack.md` + `qa/quality-gates.md` (if the dep affects a test framework)

**Fold rule:**
1. In `technology-stack.md`: append the dependency to Libraries section with (name, version, purpose)
2. In `implementation.md`: update every step that uses the dep with the concrete library name
3. If it's a testing lib: also update `qa/quality-gates.md` Required section
4. Log: `DEC-<###>: Chose <library> per PB-<id>`

#### 6.2.7 `data-flow`

**Target files:** `implementation.md` + TL entity files + `implementation.md §2 Impacted components`

**Fold rule:**
1. In the involved TL entity files: update the `## Business Purpose` and cross-references to reflect which is source of truth
2. In `implementation.md`: update the step that reads / writes with the correct source
3. In the analysis scratchpad `dev/<repo>-analysis.md` `impact_matrix:` block: update `Database` dimension
4. Log: `DEC-<###>: Data flow — <field> source of truth is <entity> per PB-<id>`

#### 6.2.8 `copy`

**Target files:** `implementation.md` (specifically §5 User-facing surfaces step or §3 Operations refusals table)

**Fold rule:**
1. In `implementation.md`: replace the placeholder copy with the resolved text verbatim
2. Log: `DEC-<###>: Copy for <surface> per PB-<id> — "<first 60 chars of text>..."`

#### 6.2.9 `cross-feature-ordering`

**Target files:** `implementation.md` + `features/<slug>/dependencies.md` (parent's BA file)

**Fold rule:**
1. In `dependencies.md`: append the resolution (either "FEAT-USER-01 is already shipped in v1.2" OR "we mock the user service via `MockUserService`")
2. In `implementation.md`: update any dependent step with the resolved approach
3. If mocking: add a step for the mock in the dev-plan
4. Log: `DEC-<###>: Cross-feature dep <FEAT-…> resolved per PB-<id> — <approach>`

---

### 6.3 UNIVERSAL upstream BA sync (v2.3.3 — runs after per-category fold, for every PB regardless of category)

**The problem this closes.** Blocker detection (`blocker-detection.md` §5.1 Source 2 + Source 4) reads BA `open-questions.md` "Blocks build" rows and mints PB-### blockers from them. If the fold only updates the analysis scratchpad + BA registers (per §6.2's per-category rules), the upstream BA files still say `status: Open` — so a re-run of `/dev:plan` would re-detect the SAME blocker and re-halt the task. The DEC-### logged in `shared-context/decision-log.md` doesn't propagate back to `open-questions.md`; upstream stays stale.

**The fix.** For EVERY resolved PB-### (regardless of category), also update the upstream BA source that produced it — close out the OQ-###, CLR-###, ASM-### that PB references, so blocker-detection.md doesn't re-raise it next run.

**Fold rule — runs FOR EVERY resolved PB:**

1. **Parse the PB's `Detected in:` line** for referenced IDs matching the pattern `(OQ|CLR|ASM|CON|SQ|DEC|BR|AC|EP|PAGE|ENT|INT|DATA|SRC)-[A-Z0-9-]+\d+`.

2. **For each referenced ID, look it up in upstream files:**

   a. `features/<slug>/open-questions.md` — frontmatter `open_questions:` array + body bullets
   b. `ba/scope.md` — narrative mentions
   c. `ba/registers/<register>.md` — where `<register>` matches the ID prefix (e.g. `BR-###` → `business-rules.md`)
   d. `shared-context/decision-log.md` — DEC-### entries (append-only, never edit past DECs)

3. **When a match is found, update it deterministically:**

   For `open-questions.md` (structured YAML frontmatter):
   ```yaml
   # BEFORE:
   - id: OQ-HCAL-01
     question: What should happen when a submitted holiday name exceeds 100 characters...
     owner: BA / Client
     impact: Determines the validation rule...
     status: Open

   # AFTER (Resolved via PB-1-002, DEC-043 — Option 1):
   - id: OQ-HCAL-01
     question: What should happen when a submitted holiday name exceeds 100 characters...
     owner: BA / Client
     impact: Determines the validation rule...
     status: Resolved
     resolved_at: 2026-08-31T15:15:00Z
     resolved_by: PB-1-002
     resolution: "Option 1 — Hard reject with 400 NAME_TOO_LONG; fixed refusal message 'Holiday name must be 100 characters or fewer.'"
     related_dec: DEC-043
   ```

   For the corresponding body bullet in `open-questions.md`:
   ```markdown
   # BEFORE:
   - **Name length beyond 100 chars** — what happens on a submission longer than the confirmed limit? Owner: BA / Client. `OQ-HCAL-01`

   # AFTER:
   - **Name length beyond 100 chars** — what happens on a submission longer than the confirmed limit? Owner: BA / Client. `OQ-HCAL-01` **✓ Resolved by DEC-043 (via PB-1-002) — hard reject with `400 NAME_TOO_LONG`**
   ```

   For `ba/scope.md` (narrative document):
   - **DO NOT auto-edit narrative prose.** Long-form scope text is BA's authored work; automatic edits risk breaking sentence flow.
   - **Instead, log to `dev/scope-sync-todos.md`**: a running list of scope.md sections that reference the resolved ID, so the BA can update them by hand or via `/ba:scope --refresh`.
   - Format:
     ```markdown
     - `OQ-HCAL-01` resolved by DEC-043 — scope.md lines 62-63 mention this OQ; update those references when /ba:scope runs
     ```

   For `ba/registers/<register>.md`:
   - Only if the PB's category-specific fold rule (§6.2) already touches this file — do NOT double-write
   - Otherwise no change (registers are canonical for their own IDs, not for OQ resolution)

4. **Never mutate a DEC-###** — decisions are append-only. If the PB references an existing DEC in its `Detected in:` line, that DEC is CITED not modified.

5. **Log the upstream sync** in the PB's `Applied at plan-fold:` line under a new `upstream_synced:` sub-field:
   ```
   Applied at plan-fold: 2026-08-31T15:15:00Z · applied to: dev/backend-analysis.md § build_sequence step 2 · logged as DEC-043 · upstream_synced: [open-questions.md OQ-HCAL-01 → Resolved]
   ```

**Watch items — recorded but NOT resolved by the fold:**

If a PB references an ID marked in its own file as "watch item / not blocking" (e.g. the PB-1-001 file says "ASM-004 is a watch item, not a blocker"), the fold does NOT update ASM-004's status — because ASM-004 was never the source of a blocker; it's a documentation record. The upstream sync only closes upstream refs that DIRECTLY produced a PB via `blocker-detection.md`.

---

### 6.4 Writing back the fold

For each successfully-folded PB:

1. **Fill `Applied at plan-fold:`** in the PB section — one line: `<ISO timestamp> · applied to: <file1>:<section>, <file2>:<section> · logged as DEC-<###> · upstream_synced: [<id> → Resolved, ...]`
2. **Append `> Resolved <ISO>` under the section separator** (keeps the file readable when re-opened)

For the whole file after all PBs folded:

3. Set frontmatter `status: RESOLVED` + `last_updated: <ISO>`
4. Add a `## Resolution summary` section at the top (below the "How to resolve" intro) — one line per fold:
   ```
   ## Resolution summary

   - PB-001 → resolved (option 1) at 2026-08-31T14:33:11Z · DEC-042 · upstream: OQ-HCAL-01 closed in open-questions.md
   - PB-002 → resolved (custom text) at 2026-08-31T14:33:12Z · DEC-043 · upstream: none referenced
   ```

---

### 6.4 On any fold error

If a fold rule can't complete (target file missing, target section not found, etc.):

- **Do NOT partial-fold** — the whole `--resume` run halts on this PB
- Leave `Resolution:` intact (user's work is preserved)
- Leave `Applied at plan-fold:` empty (never lie about applying)
- Set frontmatter `status: OPEN` (roll back from RESOLVING)
- Write an `> Error at <ISO>: <what went wrong>` line under the PB
- Halt with a message pointing at the failed PB

Rationale: half-folded plans are worse than un-folded plans. A file we didn't finish patching would produce mysterious build failures later.

---

### 6.5 After all folds succeed

1. Re-run `/dev:plan` Stage 3.5 detection (§5.1 + §5.2 in [`blocker-detection.md`](blocker-detection.md)) — a fold might have revealed new blockers (e.g. resolving one config value revealed another that hadn't been checked because the first was blocking)
   - If new blockers detected: mint them, append to `plan-blockers.md` (do NOT touch existing resolved PBs), set frontmatter back to `OPEN`, halt again
   - If no new blockers: continue to step 2
2. Update `status.md`:
   ```yaml
   current_state: PLANNED
   blocker_file: dev/plan-blockers.md    # kept for audit
   blocker_count: 0                       # unresolved count
   ```
3. Update `dev/plan-run.md`:
   ```yaml
   stage-3:
     status: DONE
     blockers_folded: <N>
     folded_at: <ISO>
   ```
4. Push MC status → `readyForDev` via `task-mcp.update_task_status`
5. Print the success message from [`plan.md`](../../plan.md) §7-resume-success

---

### 6.6 Idempotency of fold

Re-running `/dev:plan --resume` after all PBs are already folded (`status: RESOLVED`, all `Applied at plan-fold:` filled):

- Detect: nothing to do
- If any target file has been hand-edited since the fold and NO LONGER matches what the fold applied → warn but don't re-fold (the user's hand-edit takes precedence)
- Continue to Stage 3.5's finalise sub-step normally

Re-running with changed Resolution values (user changed their mind):

- Detect: old `Applied at plan-fold:` is set but a `Resolution:` value differs from what was applied
- Log a new `DEC-###` recording the change
- Re-fold (per §6.2 category rules) — the new resolution overwrites the old fold's target-file edits
- Update `Applied at plan-fold:` with the new timestamp + new DEC-###

---

### Skills / agents invoked from this reference

None. Fold is deterministic file surgery per rules in §6.2 — no subagent delegation, no LLM reasoning about "how the answer fits." The rules ARE the reasoning.
