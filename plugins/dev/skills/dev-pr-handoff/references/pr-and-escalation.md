# PR summary and escalation — field guide

How to fill the two handoff outputs well. Schemas are in the delivery loop's `references/dev-context-templates.md` (`pr-summary.md` §7, `escalation-<n>.md` §8); this is the guidance on *what makes each field good*.

---

## PR summary (`dev/pr-summary.md`)

A reviewer should be able to approve from this without reverse-engineering the diff.

- **Feature Purpose** — one or two sentences: what capability this adds and why, in business terms. Cite the `FEAT-<AREA>-NN`.
- **Scope of Changes** — what changed, grouped by area (frontend / backend / data / infra). State explicitly what is **out** of scope so the reviewer doesn't look for it.
- **Technical Approach** — the key design choices and why; link the `DEC-###` decisions. Note where you followed an existing pattern.
- **Affected Pages / APIs / Services** — cite the TL units (`PAGE-<AREA>-NN`, `EP-<AREA>-NN`, `ENT-<AREA>-NN`) so the reviewer can trace to the design.
- **Tests Run** — the suites executed and their result; link the run in `implementation-log.md`.
- **Acceptance Criteria Status** — inline or link the `acceptance-map.md` table. Every mandatory criterion must be `Passed` or human-`Waived`; a `Waived` row names who waived it.
- **Risks / Rollout Considerations** — migration order, feature-flag state, backward-compatibility notes, data backfill, anything to watch on deploy. Include the rollback path.
- **Open Follow-up Items** — known limitations, deferred edge cases, tech debt taken on — as explicit follow-ups, not surprises.
- **Reviewer Instructions** — where to focus review, how to run/verify locally, any manual check the reviewer should do.
- **Branch** — `feature/FEAT-<AREA>-NN-<slug>`.

**Gate before writing:** all mandatory completion criteria in `loop-control.md` must hold. If one doesn't, don't write the summary — return the feature to the loop or escalate. A PR summary is a claim that the feature is ready; only write it when that's true.

---

## Escalation (`dev/escalation-<n>.md`)

A decision-maker should be able to decide from this in one read, without a back-and-forth.

- **Feature / Current State** — the `FEAT-<AREA>-NN` and `BLOCKED`.
- **What Was Attempted** — the concrete steps already taken, so the human sees this isn't a first-question dodge. Shows the blocker is real.
- **Blocker** — the single precise thing that stops progress. Name the missing contract, the ambiguous rule, the unavailable service — not "it's unclear".
- **Impact** — what this stalls, in acceptance-criteria terms (which criteria can't be validated, what can't ship). This sets the urgency.
- **Decision Needed** — frame it as concrete, mutually exclusive **options** (1, 2, 3), not an open-ended "what should I do?". Each option should be actionable.
- **Recommended Option** — your pick and the one-line reason. You're not deciding the business, but a good recommendation speeds the human.
- **Work That Can Continue** — the parts of the feature that are safe to build in parallel while the decision is pending, so the block doesn't stall everything.

**Categories that must escalate** (from `loop-control.md`): unclear/contradictory acceptance criteria, product/architecture decisions, scope conflicts, unavailable external dependencies, data-loss-risk schema changes, unclear authz, breaking contract changes, incompatible dependency versions, security/compliance concerns, and the retry-exhaustion cases (same failure after 3 focused repairs, fix-causes-regression loops, unisolable root cause, missing external access).

Never downgrade one of these into a silent assumption to keep moving — a wrong guess on any of them costs more than the escalation.
