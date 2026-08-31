---
name: dev-stack-adaptive-code-review
description: Dynamic code review on the feature diff during /dev:commit Stage 4. Detects the stack (reuses dev-stack-adaptive-implementation's stack-detection), reads the repo's existing conventions, and reviews the diff against those + against the parent's Business Rules. Reports findings in 4 severity tiers (Blocker / Major / Minor / Nit). At commit-time blocks on Blocker + Major; Minor + Nit surface as follow-up suggestions. Reviews 7 dimensions — correctness / convention adherence / error handling / testability / BR enforcement / naming / reuse — NOT stack-specific playbooks; one skill covers every stack by pattern-matching what the repo already does. Diff-scoped only; never reviews the whole repo. Findings cite line numbers in the diff and include concrete fix suggestions.
---

# Dev Stack-Adaptive Code Review

You are reviewing the feature diff during `/dev:commit` Stage 4 — after `/dev:build` finished and pushed committed code to the branch, before push + PR. Dynamic per stack: detect what the repo uses, review against THAT, not against a generic "here's how you should structure a Nest controller" playbook.

The defining behaviour: **review the diff against the repo's own conventions.** If the repo uses camelCase functions everywhere, a `snake_case` new function is a Major. If the repo throws custom errors everywhere, a plain `throw new Error(...)` is a Major. What's idiomatic depends on THIS repo, not on framework docs.

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context. Your inputs:

- The feature diff — `git diff <base>...<HEAD>` in the target repo (base from `.jetrix/project.json` env_branches per `/dev:commit` Stage 2)
- The target repo's existing files — for pattern inference on identifiers, error handling, DI, config, logging, naming
- The detected stack from `dev/implementation-log.md` `detected_stack:` block (written by `dev-stack-adaptive-implementation` during `/dev:build`)
- The inferred patterns from `dev/implementation-log.md` `inferred_patterns:` block (same source)
- Parent's `business-rules.md` — every `BR-N` must be enforced at some point in the diff
- Parent's `nfrs.md` — measurable NFRs the diff must satisfy

You **do not** modify code. You emit findings; `/dev:commit` Stage 6's fix loop delegates fixes to `dev-stack-adaptive-implementation` in fix-mode.

## The three phases inside this skill

### Phase 1 — Stack + pattern reload (fast)

Read `dev/implementation-log.md` — pick up:

- `detected_stack:` block (from `dev-stack-adaptive-implementation`)
- `inferred_patterns:` block (same)

If missing (rare — should be present from `/dev:build`), re-run the same detection + inference passes. See `dev-stack-adaptive-implementation/references/stack-detection.md` + `pattern-inference.md`.

### Phase 2 — Review dimensions

Follow **`references/review-dimensions.md`** — the 7 dimensions to review, each with concrete signals per stack pattern (via **`references/stack-signals.md`**).

For each dimension, iterate every changed file in the diff and record findings. Each finding gets:
- Severity (Blocker / Major / Minor / Nit)
- Category (one of the 7 dimensions)
- File + diff line number
- Summary (≤ 100 chars)
- Failure scenario (concrete: "attacker does X → Y happens")
- Concrete fix suggestion

### Phase 3 — Threshold + report

Filter by severity per the commit-time threshold config:

- **Blocker** — hard block; jump to `/dev:commit` Stage 6 fix loop
- **Major** — hard block; same
- **Minor** — surface as follow-up suggestions in the PR summary; do NOT block
- **Nit** — log only; not in PR

Emit findings via the `ReportFindings` tool if available, or write directly to `dev/code-review-findings.md`.

## Hard rules

**Rule 1 — Diff-scoped only.** Only review lines in the diff (`git diff <base>...<HEAD>`). If the reviewer sees "the whole controller is bad but this change doesn't touch that", the reviewer stays silent. In-scope means changed lines + immediately-surrounding context (5 lines).

**Rule 2 — Match the repo, not the framework.** If the repo does something the framework docs don't recommend but does it CONSISTENTLY, that's the standard — don't flag deviation. If a change deviates from the repo's own pattern, THAT's flaggable.

**Rule 3 — Every Blocker/Major has a concrete fix.** Not "this is wrong" — "change line 42 from `X` to `Y`, or introduce `Z` instead." The fix suggestion is what `/dev:commit` Stage 6's fix loop delegates to `dev-stack-adaptive-implementation`.

**Rule 4 — Findings cite line numbers.** Every finding names the file + line in the diff. Without the line, the fix loop can't route.

**Rule 5 — One finding per issue.** Don't emit five findings for the same "consistent use of camelCase" — one finding covering all instances is enough.

**Rule 6 — Never require patterns the repo doesn't already use.** *"You should add dependency injection here"* — NO, if the repo doesn't use DI everywhere. Follow the repo's actual style.

**Rule 7 — Business rule enforcement is non-negotiable.** For every parent `BR-N` that applies to the diff's domain, there must be a code path that enforces it. Missing = Major.

**Rule 8 — Suggest additive changes only.** If a Blocker fix requires removing existing behaviour, that's a design change; escalate to human. Reviewers propose additions and modifications, not deletions of scope.

**Rule 9 — No stylistic bikeshedding.** Tab vs space, single vs double quotes, brace on same line vs next line — these are covered by lint/format gates from `qa/quality-gates.md`. The reviewer NEVER flags them.

**Rule 10 — Never emit findings without pattern grounding.** Every finding cites: what the repo does (evidence from pattern inference) and what the diff does. Without both, silence.

## The 4 severity tiers

| Severity | Blocks at commit-time? | Example |
|---|---|---|
| **Blocker** | Yes | Security-adjacent that dev-time missed (e.g. new endpoint missing auth), broken business rule enforcement, uses production DB connection in test code |
| **Major** | Yes | Deviates from repo's error handling pattern (throws plain Error where repo uses custom errors); missing test for a BR; new file has parallel abstraction instead of reusing existing one |
| **Minor** | No — surfaces in PR summary | Unclear naming; comment mentions framework name; magic number without a `const`; overlong function that could be extracted |
| **Nit** | No — logged only | Trailing whitespace (should be caught by formatter but occasionally slips); comment that's out of date |

## Completion criteria

Review complete when:

- Every changed file in the diff has been visited
- Every dimension checked against the diff
- Findings emitted with severity, file:line, concrete fix
- `dev/code-review-findings.md` written (all findings) OR via `ReportFindings` tool
- No Blocker + no Major findings remain (else `/dev:commit` Stage 6 handles the fix loop)

## Skills / agents invoked

- Reads `dev-stack-adaptive-implementation`'s output blocks in `dev/implementation-log.md` — direct file read
- No subagents (repo pattern inference must persist across reads)
- Emits findings via `ReportFindings` tool if available; else writes to `dev/code-review-findings.md`

## Principles

- **Diff-scoped, always.** The whole-repo review is `/tl:review` or `/tl:maturity`'s job; this reviewer looks at only what changed.
- **Match the repo.** Consistency with the codebase's actual patterns beats consistency with framework canon.
- **Concrete fixes only.** Vague "this needs improvement" findings never emit — a specific proposed fix or silence.
- **One finding per issue.** Don't spam.
- **Behaviour over style.** Blockers and Majors are behavioural; Minors and Nits are style.
- **BR enforcement is critical.** A missing business rule check is always Major, minimum.
- **Never delete scope in a review.** Additions only; deletions require human sign-off.
