# Loop control — state model, retry limits, guardrails, escalation

The rules that keep the delivery loop controlled. Read this before running the loop. It defines the task **state model** (v2.2) and how it maps onto MC's status enum, the **retry and cycle limits**, the **permission and scope boundaries**, the **escalation rules**, and the **completion criteria**.

Authoritative state model reference: `delivery-os-conventions` §status. This file mirrors it for loop-runtime use.

---

## 1. Task state model (v2.2)

The dev loop tracks a fine-grained state in `dev/delivery-status.md`. In v2.2 the model simplified to six local states, driven by three commands (`/dev:plan` → `/dev:build` → `/dev:commit`):

```text
PLANNED ──(→BLOCKED_ON_PLAN if plan-blockers.md OPEN)──
   │                                         │
   ▼                                         ▼ (user resolves via /dev:plan --resume)
IN_PROGRESS  (build phase)              PLANNED
   │
   ▼
REVIEW  ──(MERGE_CONFLICT if Stage 7 halt)──
   │                                    │
   ▼                                    ▼ (user resolves via /dev:commit --resume)
DONE                                REVIEW

BLOCKED (execution-time) — reachable from any working state
```

| Local state | Meaning | MC status | Who sets it |
|---|---|---|---|
| PLANNED | `/dev:plan` complete, blockers resolved, ready to `/dev:build` | `readyForDev` | `/dev:plan` |
| BLOCKED_ON_PLAN | `dev/plan-blockers.md` has OPEN entries — user resolves at plan time | `blocked` | `/dev:plan` Stage 3.5 |
| IN_PROGRESS | `/dev:build` finished cleanly; ready for local verification + `/dev:commit` | `inProgress` | `/dev:build` (Stage 1 flip + Stage 11 finish) |
| REVIEW | `/dev:commit` finished cleanly; PR opened; awaiting human review | `devReview` | `/dev:commit` Stage 1 |
| MERGE_CONFLICT | `/dev:commit` Stage 7 semantic-context-merge halted for human resolution | `devReview` (unchanged) | `/dev:commit` Stage 7 |
| BLOCKED | Execution-time escalation (bounds exceeded, unresolvable finding, dependency gap) | `blocked` | any stage's escalation |
| DONE | PR merged | `done` | PR-merge webhook (v2.3) |

Transient intermediate labels used inside `/dev:build` (`IN_PLANNING` at Stage 1 mount, `IN_DEVELOPMENT` at Stage 5, `TESTING` at Stage 7) map to MC `inProgress` and are visible only in `dev/delivery-status.md` and progress broadcasts — they don't need MC round-trips.

`BLOCKED` returns to the state it left once the blocker resolves. `BLOCKED_ON_PLAN` is distinct from `BLOCKED` — it's specifically a plan-time decision the user must make; execution-time `BLOCKED` is a runtime escalation. Both map to MC `blocked`.

### Progress broadcasts (chat visibility) — mandatory

The state model above is not just for the files. **Every time the feature changes state, emit a one-line progress update in chat** *before* you continue working, so a human watching the run always knows where the loop is and whether it is moving. Writing to `dev/delivery-status.md` is not a substitute — the file is the record, the chat line is the signal. Do not wait until the end of the run to report.

Emit exactly one line per transition, in this format:

```text
▸ FEAT-<AREA>-NN · <FROM_STATE> → <TO_STATE> · <≤10-word note on what is happening now>
```

Examples:

```text
▸ FEAT-AUTH-03 · PLANNED → IN_PLANNING · /dev:build mounting context
▸ FEAT-AUTH-03 · IN_PLANNING → IN_DEVELOPMENT · plan ready, 6 files to touch
▸ FEAT-AUTH-03 · IN_DEVELOPMENT → TESTING · changes done, running validation suite
▸ FEAT-AUTH-03 · TESTING → IN_PROGRESS · all 12 acceptance rows green; local-runbook written
▸ FEAT-AUTH-03 · IN_PROGRESS → REVIEW · /dev:commit start, MC flipped to devReview
▸ FEAT-AUTH-03 · REVIEW → REVIEW (Stage 6 fix loop 1/3 on CR-B-002)
▸ FEAT-AUTH-03 · REVIEW → REVIEW · PR-247 opened, awaiting reviewer
```

Rules:

- **On the state change, not after.** Print the line the moment you set the new state, before doing the work of that state.
- **One line, no file dumps.** Keep the detail in `dev/`; the chat line is the headline only.
- **Long-running states get a heartbeat.** `IN_DEVELOPMENT`, `TESTING`, and Stage 6 fix loops can run a while. Within them, print a short `  ↳` sub-line when you enter a distinct phase — e.g. `  ↳ repair attempt 2/3 on <cause>` or `  ↳ running e2e suite` or `  ↳ semantic-context-merge downloading baseline` — so a long phase never looks stuck. This is a heartbeat, not per-file narration.
- **Silence is a signal of trouble.** If you cannot advance the state and are not emitting a heartbeat, you are stuck — treat that as an escalation trigger (§5), not something to work through silently.

### Explicit error / blocked broadcast — mandatory

When you set state `BLOCKED` (or a validation step produces a hard failure you cannot repair within the limits in §2), do **not** merely point the user at the escalation markdown. Print the failure inline in chat as a block, *in addition to* writing `dev/escalation-<n>.md`, so the human understands what happened without opening any file:

```text
⛔ FEAT-<AREA>-NN · BLOCKED at <STATE> (loop step <n>: <step name>)
   What failed : <precise failure, one or two lines>
   Tried       : <what was attempted — e.g. 3 focused repairs on <cause>, same failure>
   Impact      : <which acceptance criteria / features this stalls>
   Need        : <the decision required, with options and your recommendation>
   Continue    : <work that can safely proceed in parallel, or "none">
   Details     : dev/escalation-<n>.md
```

The inline block carries the same facts a good escalation note carries (§5); the file is the durable copy. A run that ends `BLOCKED` must leave this block as (or in) its final chat message — never a bare "blocked, see the file".

### State → BA/index vocabulary mapping

`features/feature-index.md` and each feature's `status.md` use the BA controlled values (`Proposed · Ready for Planning · In Development · In QA · UAT · Released · Blocked`). Keep the fine-grained loop state in `dev/delivery-status.md` and **mirror** it into the BA files using this mapping:

| v2.2 local state | BA status.md / feature-index value |
|---|---|
| PLANNED | Ready for Planning |
| BLOCKED_ON_PLAN | Blocked |
| IN_PROGRESS (build phase — transient IN_PLANNING / IN_DEVELOPMENT / TESTING) | In Development |
| REVIEW | In QA |
| MERGE_CONFLICT | In QA |
| BLOCKED | Blocked |
| DONE | Released |

When you update `status.md`, also set its *Development* progress row and *Last Updated*, and refresh the feature's row in `feature-index.md`. Never invent index states outside the BA vocabulary.

### MC Task status sync — driven by /dev:build and /dev:commit

MC status transitions are owned by the two commands (v2.2), NOT by autonomous background sync. The transitions:

```
mcp__task-mcp__update_task_status(
  task_object_id = <feature.md frontmatter jetrix_task_object_id>,
  status         = "readyForDev"  # /dev:plan end (PLANNED)
                 | "inProgress"   # /dev:build Stage 1 (build phase start)
                 | "devReview"    # /dev:commit Stage 1 (review start; PR raised at Stage 9)
                 | "blocked"      # any escalation (BLOCKED) OR plan-time blockers open (BLOCKED_ON_PLAN)
)
```

`DONE` / MC `done` is set by MC's GitHub webhook on PR merge (v2.3); the dev-agent never sets it.

Rules:

- Fires on the state transition inside each command's stage, right after writing `dev/delivery-status.md` and before the chat broadcast.
- Failures are **non-fatal** — log the error to `dev/implementation-log.md` and continue; the next explicit push will retry.
- MERGE_CONFLICT stays at MC `devReview` (it's a resolvable state, not a full block).

---

## 2. Retry and cycle limits

Hard limits — exceeding any of them means **escalate**, not "try once more":

- **Focused repair attempts per failure: 3.** A focused repair targets one identified cause and re-runs the narrow check first.
- **Broad validation cycles: 2.** A broad cycle is a full-suite re-run after focused fixes.
- **Auto-generated implementation plans per feature: 2.** If the second plan still yields no actionable path, escalate.
- **Scope-expansion attempts without human approval: 0.**

Record every attempt in `dev/implementation-log.md` (step, files, validation result, failure, next action). No blind repeated retries — if two attempts fix nothing, the third must be a *different* hypothesis or you escalate.

---

## 3. Permission boundaries — never without explicit human approval

The loop must **not**:

- Merge pull requests.
- Deploy to production.
- Delete production data.
- Modify secrets or credentials.
- Change infrastructure permissions.
- Disable or weaken security controls.
- Ignore, skip, or delete failing tests to go green.
- Bypass required code-review or approval steps.

If a task appears to require any of these, stop and escalate.

---

## 4. Scope boundaries

- Work **only** on files related to the selected feature.
- Document any genuine cross-feature impact in `dev/impacted-components.md`.
- Raise a **scope escalation before** modifying an unrelated module — never opportunistically.
- Avoid opportunistic refactoring unless it is necessary to complete the feature safely (and note it if so).

---

## 5. Escalation rules

Escalate — with a structured `dev/escalation-<n>.md` note (template in `dev-context-templates.md`), state `BLOCKED`, trackers updated — instead of guessing, whenever any of these occurs:

**Business & scope**
- Acceptance criteria unclear or contradictory.
- Implementation requires a product decision.
- Feature scope conflicts with another feature.
- New requirements emerge that aren't in the feature docs.
- A user workflow can't be determined from existing context.

**Technical**
- Required external API/service is unavailable.
- A schema change may cause data loss.
- Authn/authz rules are unclear.
- A breaking API-contract change is required.
- A dependency has incompatible versions.
- Existing architecture can't support the feature without major redesign.
- The repo build is already broken before your changes.

**Security & compliance**
- Sensitive-data handling is unclear.
- A security vulnerability is identified.
- The feature touches regulated data, audit logging, retention, consent, or permissions.
- Production credentials/secrets are required.
- The change could expose user data.

**Retry / stuck**
- The same test failure survives three focused repair attempts.
- Fixing one failure repeatedly creates regressions elsewhere.
- The root cause can't be isolated with available context.
- Validation needs external access the agent doesn't have.

A good escalation names what was attempted, the precise blocker, its impact (which acceptance criteria it stalls), the decision needed with options, a recommended option, and the work that can safely continue in parallel.

---

## 6. Completion criteria (v2.2 — split by command)

### `/dev:build` complete (IN_PROGRESS gate)

**Mandatory — all must hold:**
- Task scope implemented per `dev-plan.md`
- Every Required gate in `qa/quality-gates.md` passes (Stage 7)
- Every parent AC + BR + TS + NFR row in `dev/acceptance-map.md` is `✅ pass` OR properly `⏸ deferred-to-e2e` (Stage 8)
- Zero Critical security findings at build-time threshold (Stage 9)
- Every owned code-context unit flipped `origin: designed → implemented` with valid Source References (Stage 10)
- `dev/local-runbook.md` written (Stage 11)

Fails any → task stays `TESTING` or drops to `BLOCKED` via bounded fix loop escalation. Never advances to `IN_PROGRESS` on hope.

### `/dev:commit` complete (REVIEW gate = PR opened)

**Mandatory — all must hold:**
- Zero Critical AND zero High security findings at commit-time threshold (Stage 3)
- Zero Blocker AND zero Major code-review findings (Stage 4)
- Every acceptance-map row still `✅ pass` at commit-time re-verify OR valid `⏸ deferred-to-e2e` (Stage 5)
- Semantic-context-merge clean (Stage 7) — zero unresolved conflicts in `dev/context-merge-conflicts.md`
- Branch pushed successfully (Stage 8)
- PR raised with `dev/pr-summary.md` as body (Stage 9)

Fails any → Stage 6 fix loop OR halt with escalation. Never opens a PR on incomplete evidence.

**Optional — where the project requires them:**
- Accessibility checks pass (a11y gate in `qa/quality-gates.md`)
- Performance checks pass (perf NFR-declared thresholds)
- Feature-flag configuration documented in `dev/local-runbook.md`
- Release notes generated

A task that fails any mandatory criterion at either gate stays in its working state (or `BLOCKED` / `MERGE_CONFLICT`) — it does not advance because code was written.
