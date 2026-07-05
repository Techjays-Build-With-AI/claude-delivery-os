# Loop control — state model, retry limits, guardrails, escalation

The rules that keep the delivery loop controlled. Read this before running the loop. It defines the feature **state model** and how it maps onto the shared BA/index vocabulary, the **retry and cycle limits**, the **permission and scope boundaries**, the **escalation rules**, and the **completion criteria**.

---

## 1. Feature state model

The dev loop tracks a fine-grained state in `dev/delivery-status.md`:

```text
BACKLOG → READY_FOR_DEV → IN_PLANNING → BLOCKED → IN_DEVELOPMENT
        → TESTING → REVIEW_FIXES → READY_FOR_PR → HUMAN_REVIEW
        → APPROVED → MERGED → RELEASED
```

| State | Meaning | Who moves it |
|---|---|---|
| BACKLOG | Feature exists but is not ready for implementation. | BA / TL |
| READY_FOR_DEV | Sufficient context, approved for development. | TL / human |
| IN_PLANNING | Agent is reading context and preparing the implementation plan. | dev |
| BLOCKED | Cannot continue without a decision, dependency, or clarification. | dev |
| IN_DEVELOPMENT | Agent is actively making code changes. | dev |
| TESTING | Automated and manual validation is running. | dev |
| REVIEW_FIXES | Agent is resolving validation failures or review feedback. | dev |
| READY_FOR_PR | Implementation and validation complete; handoff prepared. | dev |
| HUMAN_REVIEW | PR is waiting for human review/approval. | dev → human |
| APPROVED | Human reviewer approved the implementation. | human |
| MERGED | Code merged into the target branch. | human |
| RELEASED | Deployed and release validation complete. | human / deploy skill |

`BLOCKED` is reachable from any working state and returns to the state it left once the blocker resolves. The agent owns transitions up to `HUMAN_REVIEW`; `APPROVED`/`MERGED`/`RELEASED` are human- or deploy-owned and the dev agent only records them.

### Progress broadcasts (chat visibility) — mandatory

The state model above is not just for the files. **Every time the feature changes state, emit a one-line progress update in chat** *before* you continue working, so a human watching the run always knows where the loop is and whether it is moving. Writing to `dev/delivery-status.md` is not a substitute — the file is the record, the chat line is the signal. Do not wait until the end of the run to report.

Emit exactly one line per transition, in this format:

```text
▸ FEAT-<AREA>-NN · <FROM_STATE> → <TO_STATE> · <≤10-word note on what is happening now>
```

Examples:

```text
▸ FEAT-AUTH-03 · READY_FOR_DEV → IN_PLANNING · reading BA + TL context
▸ FEAT-AUTH-03 · IN_PLANNING → IN_DEVELOPMENT · plan ready, 6 files to touch
▸ FEAT-AUTH-03 · IN_DEVELOPMENT → TESTING · changes done, running validation suite
▸ FEAT-AUTH-03 · TESTING → REVIEW_FIXES · 2 of 14 acceptance checks failing
▸ FEAT-AUTH-03 · REVIEW_FIXES → TESTING · focused fix applied, re-running suite
▸ FEAT-AUTH-03 · REVIEW_FIXES → READY_FOR_PR · all checks green, preparing PR
```

Rules:

- **On the state change, not after.** Print the line the moment you set the new state, before doing the work of that state.
- **One line, no file dumps.** Keep the detail in `dev/`; the chat line is the headline only.
- **Long-running states get a heartbeat.** `IN_DEVELOPMENT`, `TESTING`, and `REVIEW_FIXES` can run a while. Within them, print a short `  ↳` sub-line when you enter a distinct phase — e.g. `  ↳ repair attempt 2/3 on <cause>` or `  ↳ running e2e suite` — so a long phase never looks stuck. This is a heartbeat, not per-file narration.
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

`context/features/feature-index.md` and each feature's `status.md` use the BA controlled values (`Proposed · Ready for Planning · In Development · In QA · UAT · Released · Blocked`). Keep the fine-grained loop state in `dev/delivery-status.md` and **mirror** it into the BA files using this mapping, so the index the whole team reads stays accurate without inventing new vocabulary:

| Dev loop state | BA status.md / feature-index value |
|---|---|
| READY_FOR_DEV | Ready for Planning |
| IN_PLANNING, IN_DEVELOPMENT, TESTING, REVIEW_FIXES | In Development |
| READY_FOR_PR, HUMAN_REVIEW | In QA |
| APPROVED | UAT |
| MERGED, RELEASED | Released |
| BLOCKED | Blocked |

When you update `status.md`, also set its *Development* progress row and *Last Updated*, and refresh the feature's row in `feature-index.md`. Never invent index states outside the BA vocabulary.

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

## 6. Completion criteria (gate to READY_FOR_PR)

**Mandatory — all must hold:**
- Feature scope is implemented.
- Required acceptance criteria are validated with evidence (or formally waived by a human).
- Relevant tests pass; build and static checks pass.
- Required documentation is updated.
- No unresolved critical or high-severity defect remains.
- No unresolved blocker remains.
- The feature tracker reflects the latest status.
- The PR summary is prepared.

**Optional — where the project requires them:**
- Accessibility checks pass.
- Performance checks pass.
- Security review passes.
- End-to-end tests pass.
- Feature-flag configuration is documented.
- Release notes are generated.
- Monitoring and alerts are configured.

A feature that fails any mandatory criterion stays in its working state (or `BLOCKED`) — it does not advance to `READY_FOR_PR` because code was written.
