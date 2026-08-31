## Stage 1 — Code-context readiness

**Purpose.** Guarantee the feature's owned units (pages, endpoints, entities) all resolve to real unit files and are linked to this `FEAT-<id>` in the three layer indexes. If not, auto-plan them via the TL. Same graph verification `/dev:build` used to do inline — relocated here so `/dev:plan` owns planning end-to-end.

**Runs per-feature**, in parallel across the target set (outer axis, see `plan.md` §11). Each feature's Stage 1 runs its own inner-axis parallelism (indexes + units checked concurrently).

**On completion:** feature is either **PLANNED** (graph resolves + linked) — proceed to Stage 2 — or **BLOCKED** — escalation written, feature dropped from the batch and reported at end.

---

### 1a. Detection — "is this feature already planned?"

Presence of the `context/frontend|backend|database` folders is *not* sufficient. Verify the actual units, in order:

1. **Read `.jetrix/connection-map.md`** if present — the workspace-level solution architecture doc pulled by `/jetrix:init`. It names each app (repo) with its role, the Wiring edges between them (e.g. `Frontend → Backend over REST`), the auth boundary, external integrations, and data-flow notes. Use this to establish which repos are involved in this feature's plan even before reading feature-level frontmatter. Missing / empty → not a hard stop; just note "no connection-map — cross-repo trace is graph-only".

2. **Read the feature's `feature.md`** and collect what it declares in the frontmatter:
   - `related_pages: [PAGE-<AREA>-NN, ...]`
   - `related_apis: [EP-<AREA>-NN, ...]`
   - `related_entities: [ENT-<AREA>-NN, ...]`
   Backend-only features declare no pages — skip the page layer for them. If any of these three lists is entirely missing from frontmatter and no analogue is present in the body's "Related …" sections, treat as **not planned** and jump to §1b.

3. **Load the three TL layer indexes in each involved repo** (parallel — one per (repo, layer)):
   - `<repo>/context/code-context/frontend/frontend-index.md` (or the domain-specific split; see the code-context conventions)
   - `<repo>/context/code-context/backend/backend-index.md`
   - `<repo>/context/code-context/database/database-index.md`
   Repos derived from `.jetrix/cache/repolocation.json`. Skip a repo whose path is `SKIPPED` — that layer is unavailable, log it and treat any unit that would live there as `[HELD · repo unavailable]`.
   If a repo's index file is missing locally (fresh clone, unfamiliar repo), ask the user to `git pull` inside it or run `/tl:code-map` to bootstrap. Log as `PARTIAL_INDEX` — surfaces at the checkpoint.

3. **For every declared unit, verify two things (parallel per unit):**
   - **Resolves** — the unit file exists at the path the index row points to (open the index, find the row matching the id, `test -f` the file path).
   - **Linked** — this feature's `FEAT-<AREA>-NN` appears in the unit file's `Used by Features:` cell OR in the corresponding index row's `Used by Features` column (word-boundary match — an id embedded in a longer id doesn't count).

4. **Verdict:**
   - **Planned** — every declared page/endpoint/entity resolves AND is linked to this `FEAT-id`. Proceed to §1c (repo count) then Stage 2.
   - **Partially planned** — some declared units are missing from the graph, unresolved, or unlinked. Treat as *needs planning* (§1b re-runs planning to fill gaps; the TL skill updates in place and won't duplicate existing units).
   - **Not planned** — no indexes present in any involved repo, OR none of the feature's declared units are in the graph.

---

### 1b. Auto-plan when not (or partially) planned

Delegate to the TL and continue — no human pause. `/dev:plan`'s auto-plan hop follows the same rules `/dev:build`'s planning gate used to.

1. **Delegate to the tl-agent subagent** scoped to this **one** feature folder, with the standard `tl-feature-planning` instruction (the same work `/tl:plan <feature>` does): map the feature's declared pages / APIs / data-entities to real, linked unit files under `context/frontend|backend|database`, reusing existing units and minting new `PAGE-/EP-/ENT-<AREA>-NN` where needed, wiring links both ways, logging `DEC-###` design decisions, updating the three indexes, and running the link-integrity check.
   - If subagent delegation isn't available, run the `tl-feature-planning` skill directly on the feature.
2. **Re-verify by re-running §1a detection.** It must now return **planned**.
3. **Carry the result forward** — note in `dev/plan-run.md` that the feature was auto-planned (units created / reused, `DEC-###` logged, any open questions the TL raised) so the human checkpoint (§1d) sees the design that was generated.

**Fallbacks and limits:**

- **TL agent unavailable** → do NOT invent the graph. Set feature `BLOCKED`, write escalation note pointing at "run `/tl:plan <feature>` first", drop this feature from the batch, continue.
- **TL planning can't complete** (undecided design point: missing integration contract, unknown auth model) → `tl-feature-planning` itself escalates with blocking open questions. Carry those up as the feature's Stage 1 escalation; do NOT compose on a half-graph.
- **Re-verify still fails after ONE planning pass** → escalate rather than looping planning indefinitely. Respects the "2 plans per feature" ceiling from `feature-delivery-loop`; auto-plan counts as one.

---

### 1c. Derive the inputs for the sub-task decision

Once §1a returns **planned**, compute the two signals Stage 2 needs:

- **Repos touched** — union of every owned unit's `Source Reference` file path resolved against `.jetrix/cache/repolocation.json`. Deduplicate to a set of repo slugs.
- **Task type** — from the parent Task's MC `taskType` field (fetched in Stage 0 identity resolution; if it's stale or missing, refetch via `task-mcp.get_task_by_id_or_number`).

Both signals get written to this feature's `dev/plan-run.md` under a `stage-1-results:` block so Stage 2 (and the checkpoint) reads them without re-computing.

---

### 1d. Feed the consolidated checkpoint

Stage 1 doesn't prompt — the **consolidated user checkpoint fires between Stage 1 and Stage 2** across ALL targeted features at once. Write this feature's row to the checkpoint payload in `.jetrix/dev/batch-runs/plan-run-<ts>.md`:

```yaml
- feature_id: FEAT-SUP-001
  task_number: Feature-4
  title: Supplier Onboarding
  task_type: feature
  repos_touched: [backend, frontend, mobile]
  split_decision: split                       # from applying §6a rule in Stage 2 preview
  planned_subtasks:
    - {number: 1, repo: backend}
    - {number: 2, repo: frontend}
    - {number: 3, repo: mobile}
  auto_plan_triggered: true                   # true if §1b ran
  partial_index_warnings: []                  # from §1a step 2
  status: STAGE_1_COMPLETE
```

The orchestrator (`plan.md`) waits until every feature reports `STAGE_1_COMPLETE` (or fails) before printing the checkpoint and prompting.

---

### 1e. Failure handling

Any Stage 1 failure isolates the feature — it does NOT halt the batch:

- **Planning gate fails** (auto-plan can't complete) → write `dev/escalation-<n>.md`, set status `BLOCKED_STAGE_1`, log to `plan-run.md`, drop from Stage 2.
- **Repo missing** → log as `SKIPPED_REPO_MISSING`, treat affected units as `[HELD · repo unavailable]` in Stage 2's compose; don't fail the feature entirely.
- **Any exception** → catch, log to `plan-run.md` with the stack, mark feature `BLOCKED_STAGE_1`, continue the batch.

Report at end of run summarises: `planned N/M · auto-planned K · blocked-at-stage-1 J`.

---

### Progress log format (`dev/plan-run.md`, per feature)

Every Stage 1 pass appends to this feature's `plan-run.md`:

```yaml
stage-1:
  status: RUNNING                            # RUNNING | DONE | BLOCKED
  started_at: 2026-08-29T14:22:00Z
  indexes_loaded:                            # per (repo, layer)
    - {repo: backend,  layer: backend,  ok: true}
    - {repo: backend,  layer: database, ok: true}
    - {repo: frontend, layer: frontend, ok: true}
  units_verified:
    resolved_and_linked: 12
    partially_linked:    0
    not_resolved:        0
  auto_plan_triggered: false
  finished_at: 2026-08-29T14:22:47Z
```

`--resume` uses `stage-1.status: DONE` to skip this stage on the next run.

---

### Skills / agents invoked

- **`tl-agent` subagent** running the **`tl-feature-planning` skill** — only when §1b fires (feature not planned or partially planned). Same skill `/tl:plan` uses standalone; unchanged.

Never invoke `tl-feature-compose` from Stage 1 — that's Stage 2's job.
