# Loop control — state model, retry limits, guardrails, escalation

The rules that keep the delivery loop controlled. Read this before running the loop. It defines the task **state model** (v2.2) and how it maps onto MC's status enum, the **retry and cycle limits**, the **permission and scope boundaries**, the **escalation rules**, and the **completion criteria**.

Authoritative state model reference: `delivery-os-conventions` §status. This file mirrors it for loop-runtime use.

---

## 1. Task state model

A task carries **two fields**. `status` is the shared value — the same seven in `status.md`, in Mission
Control, and on any other tracker. `phase` is local detail, never pushed, and only meaningful next to a
status. Full contract in `delivery-os-conventions` §5; this is the loop-runtime view.

```text
status: readyForDev          ──(plan-blockers.md OPEN)──▶  status: blocked
phase:  planned                                            phase:  plan-blockers
   │                                                          │
   │  /dev:build                       /dev:plan --resume ◀───┘
   ▼
status: agentExecuting   phase: implementing  (Stages 3–6)
                         phase: testing       (Stages 7–10)
   │
   ▼  Stage 11
status: inProgress       phase: built          ──▶ ready for /dev:commit
   │
   │  /dev:commit (Stage 3 flips status)
   ▼
status: devReview        phase: pr-open        ──(Stage 7 halt)──▶  phase: merge-conflict
   │                                                                    │
   │  PR merged                              /dev:commit --resume ◀─────┘
   ▼
status: done

status: blocked · phase: escalated — reachable from any working state
```

| `status` | `phase` | Meaning | Who sets it |
|---|---|---|---|
| `readyForDev` | `planned` | `/dev:plan` complete, blockers resolved, ready to `/dev:build` | `/dev:plan` |
| `blocked` | `plan-blockers` | `plan-blockers.md` has OPEN entries — the user decides at plan time | `/dev:plan` Stage 3.5 |
| `agentExecuting` | `implementing` | `/dev:build` Stages 3–6 | `/dev:build` |
| `agentExecuting` | `testing` | `/dev:build` Stages 7–10 | `/dev:build` |
| `inProgress` | `built` | `/dev:build` finished cleanly; ready for `/dev:commit` | `/dev:build` Stage 11 |
| `devReview` | `pr-open` | `/dev:commit` finished; PR opened; awaiting human review | `/dev:commit` Stage 3 |
| `devReview` | `merge-conflict` | Stage 7 semantic-context-merge halted for human resolution | `/dev:commit` Stage 7 |
| `blocked` | `escalated` | Execution-time escalation (bounds exceeded, unresolvable finding, dependency gap) | any stage |
| `done` | — | PR merged | PR-merge webhook |

**Why `phase` exists at all.** Three pairs share a status and must not share a gate:

- `blocked` + `plan-blockers` routes to `/dev:plan --resume`; `blocked` + `escalated` does not — it needs a
  human to unpick a runtime failure. `/dev:build` refuses both, with different messages.
- `devReview` + `merge-conflict` has **no PR yet** — Stage 7 runs before Stage 8/9 push+PR. `/dev:fix-review`
  requires `pr-open`; sending it at a merge conflict would look for a PR that was never opened.
- `inProgress` + `built` means the build finished. `agentExecuting` means one is still running, and
  `/dev:commit` must not start on top of it.

`phase` is **never pushed** — Mission Control has no field for it and no other tracker needs one. Changing
phase within one status needs no tracker round-trip, which is why the build loop can move through
`implementing → testing` without touching the network.

A task at `blocked` returns to the status it left once the blocker clears.

### Progress broadcasts (chat visibility) — mandatory

The state model above is not just for the files. **Every time the feature changes state, emit a one-line progress update in chat** *before* you continue working, so a human watching the run always knows where the loop is and whether it is moving. Writing to `status.md` is not a substitute — the file is the record, the chat line is the signal. Do not wait until the end of the run to report.

Emit exactly one line per transition, in this format:

```text
▸ FEAT-<AREA>-NN · <FROM_STATE> → <TO_STATE> · <≤10-word note on what is happening now>
```

Examples:

```text
▸ FEAT-AUTH-03 · readyForDev → agentExecuting · /dev:build mounting context
▸ FEAT-AUTH-03 · agentExecuting → agentExecuting · plan ready, 6 files to touch
▸ FEAT-AUTH-03 · agentExecuting → agentExecuting · changes done, running validation suite
▸ FEAT-AUTH-03 · agentExecuting → inProgress · all 12 acceptance rows green; `pr-summary.md` § `## How to verify` written
▸ FEAT-AUTH-03 · inProgress → devReview · /dev:commit start, MC flipped to devReview
▸ FEAT-AUTH-03 · devReview → devReview (Stage 6 fix loop 1/3 on CR-B-002)
▸ FEAT-AUTH-03 · devReview → devReview · PR-247 opened, awaiting reviewer
```

Rules:

- **On the state change, not after.** Print the line the moment you set the new state, before doing the work of that state.
- **One line, no file dumps.** Keep the detail in `dev/`; the chat line is the headline only.
- **Long-running states get a heartbeat.** Phases `implementing` and `testing`, and Stage 6 fix loops, can run a while. Within them, print a short `  ↳` sub-line at each distinct step — e.g. `  ↳ repair attempt 2/3 on <cause>` or `  ↳ running e2e suite` or `  ↳ semantic-context-merge downloading baseline` — so a long phase never looks stuck. This is a heartbeat, not per-file narration.
- **Silence is a signal of trouble.** If you cannot advance the state and are not emitting a heartbeat, you are stuck — treat that as an escalation trigger (§5), not something to work through silently.

### Explicit error / blocked broadcast — mandatory

When you set state `BLOCKED` (or a validation step produces a hard failure you cannot repair within the limits in §2), do **not** merely point the user at the escalation markdown. Print the failure inline in chat as a block, *in addition to* writing `units/<repo>/status.md § ## Run history (a BLOCKED entry)`, so the human understands what happened without opening any file:

```text
⛔ FEAT-<AREA>-NN · BLOCKED at <STATE> (loop step <n>: <step name>)
   What failed : <precise failure, one or two lines>
   Tried       : <what was attempted — e.g. 3 focused repairs on <cause>, same failure>
   Impact      : <which acceptance criteria / features this stalls>
   Need        : <the decision required, with options and your recommendation>
   Continue    : <work that can safely proceed in parallel, or "none">
   Details     : units/<repo>/status.md § ## Run history (a BLOCKED entry)
```

The inline block carries the same facts a good escalation note carries (§5); the file is the durable copy. A run that ends `BLOCKED` must leave this block as (or in) its final chat message — never a bare "blocked, see the file".

### State → BA/index vocabulary mapping

Each feature's `status.md` uses the BA controlled values (`Proposed · Ready for Planning · In Development · In QA · UAT · Released · Blocked`). Keep the fine-grained loop state in `status.md` and **mirror** it into the BA files using this mapping:

| v2.2 local state | BA status.md value |
|---|---|
| readyForDev | Ready for Planning |
| blocked | Blocked |
| inProgress (build phase — transient agentExecuting / agentExecuting / agentExecuting) | In Development |
| devReview | In QA |
| devReview | In QA |
| BLOCKED | Blocked |
| DONE | Released |

When you update `status.md`, also set its *Development* progress row and *Last Updated*, and refresh the feature's row in the breakdown table in the run summary. Never invent index states outside the BA vocabulary.

### MC Task status sync — driven by /dev:build and /dev:commit

MC status transitions are owned by the two commands (v2.2), NOT by autonomous background sync. The transitions:

```
mcp__task-mcp__update_task_status(
  task_object_id = <feature.md frontmatter jetrix_task_object_id>,
  status         = "readyForDev"  # /dev:plan end (readyForDev)
                 | "inProgress"   # /dev:build Stage 1 (build phase start)
                 | "devReview"    # /dev:commit Stage 1 (review start; PR raised at Stage 9)
                 | "blocked"      # any escalation (BLOCKED) OR plan-time blockers open (blocked)
)
```

`DONE` / MC `done` is set by MC's GitHub webhook on PR merge (v2.3); the dev-agent never sets it.

Rules:

- Fires on the state transition inside each command's stage, right after writing `status.md` and before the chat broadcast.
- Failures are **non-fatal** — log the error to `units/<repo>/status.md § ## Run history` and continue; the next explicit push will retry.
- devReview stays at MC `devReview` (it's a resolvable state, not a full block).

---

## 2. Retry and cycle limits

Hard limits — exceeding any of them means **escalate**, not "try once more":

- **Focused repair attempts per failure: 3.** A focused repair targets one identified cause and re-runs the narrow check first.
- **Broad validation cycles: 2.** A broad cycle is a full-suite re-run after focused fixes.
- **Auto-generated implementation plans per feature: 2.** If the second plan still yields no actionable path, escalate.
- **Scope-expansion attempts without human approval: 0.**

Record every attempt in `units/<repo>/status.md § ## Run history` (step, files, validation result, failure, next action). No blind repeated retries — if two attempts fix nothing, the third must be a *different* hypothesis or you escalate.

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
- Document any genuine cross-feature impact in `implementation.md §2 Impacted components`.
- Raise a **scope escalation before** modifying an unrelated module — never opportunistically.
- Avoid opportunistic refactoring unless it is necessary to complete the feature safely (and note it if so).

---

## 5. Escalation rules

Escalate — with a structured `units/<repo>/status.md § ## Run history (a BLOCKED entry)` note (template in `dev-context-templates.md`), state `BLOCKED`, trackers updated — instead of guessing, whenever any of these occurs:

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
- Task scope implemented per `implementation.md`
- Every Required gate in `qa/quality-gates.md` passes (Stage 7)
- Every parent AC + BR + TS + NFR row in `units/<repo>/status.md § ## Acceptance` is `✅ pass` OR properly `⏸ deferred-to-e2e` (Stage 8)
- Zero Critical security findings at build-time threshold (Stage 9)
- Every owned code-context unit flipped `origin: designed → implemented` with valid Source References (Stage 10)
- `units/<repo>/pr-summary.md § ## How to verify` written (Stage 11)

Fails any → task stays `agentExecuting` or drops to `BLOCKED` via bounded fix loop escalation. Never advances to `inProgress` on hope.

### `/dev:commit` complete (REVIEW gate = PR opened)

**Mandatory — all must hold:**
- Zero Critical AND zero High security findings at commit-time threshold (Stage 3)
- Zero Blocker AND zero Major code-review findings (Stage 4)
- Every `## Acceptance` table row still `✅ pass` at commit-time re-verify OR valid `⏸ deferred-to-e2e` (Stage 5)
- Semantic-context-merge clean (Stage 7) — zero unresolved conflicts in `dev/context-merge-conflicts.md`
- Branch pushed successfully (Stage 8)
- PR raised with `units/<repo>/pr-summary.md` as body (Stage 9)

Fails any → Stage 6 fix loop OR halt with escalation. Never opens a PR on incomplete evidence.

**Optional — where the project requires them:**
- Accessibility checks pass (a11y gate in `qa/quality-gates.md`)
- Performance checks pass (perf NFR-declared thresholds)
- Feature-flag configuration documented in `units/<repo>/pr-summary.md § ## How to verify`
- Release notes generated

A task that fails any mandatory criterion at either gate stays in its working state (or `BLOCKED` / `devReview`) — it does not advance because code was written.
