---
name: dev-stack-adaptive-code-review
description: Dynamic code review on the feature diff during /dev:commit Stage 4. Detects the stack (reuses dev-stack-adaptive-implementation's stack-detection), reads the repo's existing conventions, and reviews the diff against those + against the parent's Business Rules. Reports findings in 4 severity tiers (Blocker / Major / Minor / Nit). At commit-time blocks on Blocker + Major; Minor + Nit do not block but are still fixed, in Stage 6's single batched pass. Reviews 9 dimensions — correctness / convention adherence / error handling / testability / BR enforcement / naming / reuse / engineering standards / API design — NOT stack-specific playbooks; one skill covers every stack by pattern-matching what the repo already does. Diff-scoped only; never reviews the whole repo. Findings cite line numbers in the diff and include concrete fix suggestions.
---

# Dev Stack-Adaptive Code Review

You are reviewing the feature diff during `/dev:commit` Stage 4 — after `/dev:build` finished and pushed committed code to the branch, before push + PR. Dynamic per stack: detect what the repo uses, review against THAT, not against a generic "here's how you should structure a Nest controller" playbook.

The defining behaviour: **review the diff against the repo's own conventions.** If the repo uses camelCase functions everywhere, a `snake_case` new function is a Major. If the repo throws custom errors everywhere, a plain `throw new Error(...)` is a Major. What's idiomatic depends on THIS repo, not on framework docs.

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context. Your inputs:

- The feature diff — `git diff <base>..$SNAP` in the target repo, where `$SNAP` is the **review snapshot** the caller built (`references/common/review-snapshot.md`) and `<base>` is the branch confirmed at `/dev:commit` Stage 2. A caller that passes a branch ref instead of a snapshot on a freshly-built task hands this skill an empty diff — refuse rather than review nothing
- The target repo's existing files — for pattern inference on identifiers, error handling, DI, config, logging, naming
- The detected stack from `units/<repo>/status.md § ## Run history` `detected_stack:` block (written by `dev-stack-adaptive-implementation` during `/dev:build`)
- The inferred patterns from `units/<repo>/status.md § ## Run history` `inferred_patterns:` block (same source)
- Parent's `business-rules.md` — every `BR-N` must be enforced at some point in the diff
- Parent's `nfrs.md` — measurable NFRs the diff must satisfy

You **do not** modify code. You emit findings; `/dev:commit` Stage 6's fix loop delegates fixes to `dev-stack-adaptive-implementation` in fix-mode.

## The three phases inside this skill

### Phase 1 — Stack + pattern reload (fast)

Read `units/<repo>/status.md § ## Run history` — pick up:

- `detected_stack:` block (from `dev-stack-adaptive-implementation`)
- `inferred_patterns:` block (same)

If missing (rare — should be present from `/dev:build`), re-run the same detection + inference passes. See `dev-stack-adaptive-implementation/references/stack-detection.md` + `pattern-inference.md`.

### Phase 2 — Review dimensions

Follow **`references/review-dimensions.md`** — the 9 dimensions to review, each with concrete signals per stack pattern (via **`references/stack-signals.md`**).

For each dimension, iterate every changed file in the diff and record findings. Each finding gets:
- Severity (Blocker / Major / Minor / Nit)
- Category (one of the 9 dimensions)
- File + diff line number
- Summary (≤ 100 chars)
- Failure scenario (concrete: "attacker does X → Y happens")
- Concrete fix suggestion

### Phase 3 — Threshold + report

Filter by severity per the commit-time threshold config:

- **Blocker** — hard block; jump to `/dev:commit` Stage 6 fix loop
- **Major** — hard block; same
- **Minor** — does not block the gate; still routed to Stage 6's batched fix pass
- **Nit** — does not block; still routed to the same batched pass, and listed in the PR summary up to the display cap

**Not blocking is not the same as not fixed.** The threshold decides what stops the
pipeline; `stage-6-fix-loop.md` §6e.i decides what gets fixed, and its default at
every severity is `fixed`. Report each finding at its true severity and let that
stage dispose of it — never soften a severity to avoid the loop, and never assume
a Minor will be dropped.

Emit findings via the `ReportFindings` tool if available, or write directly to `units/<repo>/findings.md § ## Code review`.

## Hard rules

**Rule 1 — Diff-scoped only.** Only review lines in the diff (`git diff <base>..$SNAP`). If the reviewer sees "the whole controller is bad but this change doesn't touch that", the reviewer stays silent. In-scope means changed lines + immediately-surrounding context (5 lines).

**Read the changed files whole, then widen by one hop.** Reviewing only changed
lines ± 5 cannot see the two defect classes that have no changed line to attach to:

| Class | Why the narrow window misses it |
|---|---|
| **absence** — a missing null guard, auth check, error branch, validation | there is no line to point at; the defect is what is *not* there |
| **cross-file contract** — a caller now passes a nullable the callee never guards | each side is correct alone and wrong together |

So: open each changed file in full, and resolve its **immediate callers and
callees from the code-context graph** (`tl-read-code-context`) — one hop, not a
transitive crawl. The graph is the cheap way to do this: one index read gives the
callers without grepping the repository.

**Findings still only land on changed lines.** Widening is for *seeing*; the
finding must still cite a line this diff touched, or it is a pre-existing issue
and belongs in the summary as one.

**Graph thin or absent** — a greenfield repo at feature 1 — review the changed
files whole and record `scope_expansion: unavailable — graph has N links`. Never
report the same coverage on a thin graph as on a complete one.

**An empty diff is a refusal, not a pass.** Report `scope-empty` and stop. A review that inspected nothing must never return "no findings" — that reads as a clean bill of health and ends the search. State the scope in the findings header: the snapshot sha and the file count it covered.

**Rule 2 — Match the repo, not the framework — on STYLE only.** If the repo does
something the framework docs don't recommend but does it CONSISTENTLY, that's the
standard — don't flag deviation. If a change deviates from the repo's own pattern,
THAT's flaggable.

**This rule does not apply to Dimension 1 (correctness), security, or Dimension 5
(business-rule enforcement).** A repo that consistently omits a null guard is
consistently wrong, and a defect that mirrors existing bad practice is still a
defect. Say so where it is relevant — *"the surrounding code does this too"* — but
report it.

This is the suppression that hid two of five planted defects in a real run: the
reviewer was instructed not to report them.

**Rule 3 — Every Blocker/Major has a concrete fix.** Not "this is wrong" — "change line 42 from `X` to `Y`, or introduce `Z` instead." The fix suggestion is what `/dev:commit` Stage 6's fix loop delegates to `dev-stack-adaptive-implementation`.

**Rule 4 — Findings cite line numbers.** Every finding names the file + line in the diff. Without the line, the fix loop can't route.

**Rule 5 — One finding per issue — per DEFECT, not per theme.** Five instances of
one camelCase slip is one finding with an instance count. **Two different defects
are two findings even when they share a category.** A missing null guard in one
handler and a missing auth check in another are not "input validation"; merging
them reports one problem where there are two, and the second never gets fixed.

The test: *could these be fixed independently?* Yes → two findings. Always give
an instance count on a merged finding, so a reader can see what one row covers.

**Rule 6 — Never require patterns the repo doesn't already use.** *"You should add dependency injection here"* — NO, if the repo doesn't use DI everywhere. Follow the repo's actual style.

**Rule 7 — Business rule enforcement is non-negotiable.** For every parent `BR-N` that applies to the diff's domain, there must be a code path that enforces it. Missing = Major.

**Rule 8 — Suggest additive changes only — but still REPORT the finding.** A fix
that requires removing existing behaviour is a design change and escalates rather
than being applied. **Escalating is not the same as staying silent**: emit the
finding at its true severity with the escalation noted, so it reaches the
disposition gate like any other. A defect whose only fix is a deletion is still a
defect.

Reviewers propose additions and modifications, not deletions of scope — but they
report every defect they find, whatever its fix would require.

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
- `units/<repo>/findings.md § ## Code review` written (all findings) OR via `ReportFindings` tool
- No Blocker + no Major findings remain (else `/dev:commit` Stage 6 handles the fix loop)

## Skills / agents invoked

- Reads `dev-stack-adaptive-implementation`'s output blocks in `units/<repo>/status.md § ## Run history` — direct file read
- No subagents (repo pattern inference must persist across reads)
- Emits findings via `ReportFindings` tool if available; else writes to `units/<repo>/findings.md § ## Code review`

## Principles

- **Diff-scoped, always.** The whole-repo review is `/dev:review` or `/tl:maturity`'s job; this reviewer looks at only what changed.
- **Match the repo.** Consistency with the codebase's actual patterns beats consistency with framework canon.
- **Concrete fixes only.** Vague "this needs improvement" findings never emit — a specific proposed fix or silence.
- **One finding per issue.** Don't spam.
- **Behaviour over style.** Blockers and Majors are behavioural; Minors and Nits are style.
- **BR enforcement is critical.** A missing business rule check is always Major, minimum.
- **Never delete scope in a review.** Additions only; deletions require human sign-off.
