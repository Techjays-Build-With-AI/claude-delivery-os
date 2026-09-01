---
name: dev-stack-adaptive-implementation
description: Guide feature code and test writing during /dev:build. Detects the target repo's stack (language, framework, ORM, testing tools, package manager, config style) and reads the repo's existing conventions before writing anything, so the new code matches idiomatically — imports, error handling, DI style, config style, logging patterns, naming. One skill, all stacks, no per-stack playbooks. Invoked from /dev:build Stages 5 (implement) and 6 (write tests). Reads implementation.md as the build script; writes code + tests scoped to what the plan says; never invents behaviour, never introduces parallel abstractions, never leaks framework names in comments, and never guesses at stylistic choices — it uses whatever the repo already uses.
---

# Dev Stack-Adaptive Implementation

You are writing feature code and tests as part of `/dev:build`. Not a static playbook — a **detection + inference + writing** loop that adapts to whatever stack the target repo uses. One skill covers every stack in the delivery-os matrix (frontend / backend / mobile / DB across ~15 framework combinations) by reading the repo before writing, not by memorising a template per framework.

The defining behaviour: **read the repo, then match it.** You never write "here's how you should structure a React component" — you look at how THIS repo structures components and match. Same for error handling, DI, config, logging, testing. Idiomatic per-repo, not per-framework.

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context. Your inputs are what `/dev:plan` produced:

- **`features/<slug>/implementation.md`** (parent-alone) OR **`features/<slug>/subtask/<repo>/implementation.md`** (sub-task) — the 8-section stack-agnostic build spec (§1 Build sequence, §2 Impacted components, §3 Operations exposed and consumed, §4 Stored data changes, §5 User-facing surfaces, §6 Touch points, §7 Risks and rollback, §8 Shared contract). v2.3.16 removed §7 Coverage — plan-time coverage lives in §1 Satisfies column + qa/quality-gates.md tier pool; build-time evidence in dev/acceptance-map.md.
- **`features/<slug>/implementation.md §2 Impacted components`** — 12-dimension impact map (stack-agnostic dimensions per v2.3.11)
- **`features/<slug>/tl-plan.md`** (split parent's rollup only) — Sub-tasks table + parent-level Touch points
- **Parent BA files** — `feature.md`, `workflow.md`, `acceptance-criteria.md`, `business-rules.md`, `nfrs.md`, `test-scenarios.md` — the VALIDATION CONTRACT you write tests against
- **`features/<slug>/dev/plan-blockers.md`** (if present, `status: RESOLVED`) — the resolved `DEC-###` decisions to honour
- **The target repository** — its existing files, `coding-standards.md`, `shared-context/technology-stack.md`, `package.json` / `pyproject.toml` / etc.
- **`qa/quality-gates.md`** — the harness contract (Required gates, exact test commands, coverage floor). Read via [Stage 4 QA gate](../../commands/references/build/stage-4-qa-gate.md).

You write to the **target repo** — real code, real tests, on the branch `/dev:build` Stage 3 created.

## The three phases inside this skill

### Phase 1 — Stack detection (before any code write)

Follow **`references/stack-detection.md`** — a deterministic ladder that identifies language, framework, ORM, testing framework, package manager, config style. File-based signals only; no LLM guessing.

Record the detected stack in `dev/implementation-log.md` under a `detected_stack:` block.

### Phase 2 — Pattern inference (10 targeted reads, no more)

Follow **`references/pattern-inference.md`** — read ≤ 10 existing files in the repo to establish:

- Folder structure conventions
- Import style (absolute vs relative; alias patterns)
- Error handling style (try/catch + custom errors vs Result vs exception)
- DI style (constructor injection vs framework container vs manual instantiation)
- Config style (env vars via which mechanism; secrets storage)
- Logging style (console vs library; structured vs unstructured; log levels used)
- Testing patterns (setup/teardown style, fixture location, mocking approach)
- Naming (camelCase vs snake_case vs PascalCase per identifier kind)

**Never assume defaults.** If the repo has no observable pattern for one of these (e.g. no existing tests to infer testing style), fall back to what the framework's official documentation recommends — and log the fallback as a `DEC-###`.

### Phase 3 — Code + test writing (per implementation.md build sequence step)

For each ordered step in `implementation.md`:

1. Read the TL unit files this step touches (endpoint/entity/page files under `<repo>/context/code-context/`)
2. Locate or create the target source files, using the naming convention inferred in Phase 2
3. Write the code idiomatically per Phases 1 + 2
4. Immediately write the tests for THIS step (see `references/test-patterns.md`)
5. Log the step + any material technical choice as `DEC-###` in `shared-context/decision-log.md`

**Test scope per task kind** (from `/dev:build` Stage 6 spec):

| Task kind | Tests written |
|---|---|
| Parent-alone (single-repo) | Unit + integration + e2e for every AC + TS the feature declares |
| Sub-task, backend | Unit + integration for every AC/BR/TS validatable at the backend layer; contract tests for every operation exposed in §3 |
| Sub-task, frontend | Unit for components + integration for surfaces + E2E for every AC/TS validatable at the UI layer |
| Sub-task, mobile | Unit + widget + integration; E2E if the harness supports it |

## Hard rules — violation invalidates the build

**Rule 1 — Read before writing.** Never write a file before running Phase 2's pattern inference on the target repo. A "how it should look" template is a failed run.

**Rule 2 — Reuse over parallel abstraction.** If the repo has a `UserRepository`, do not introduce a `SupplierRepositoryV2` alongside — extend the pattern, don't parallel it. If reuse would break the change, escalate as a scope issue, don't create the parallel.

**Rule 3 — Match error handling.** If the repo throws custom errors, throw one. If it returns `Result<T, E>`, return one. Never introduce a second error paradigm alongside the existing one.

**Rule 4 — Match config style.** If the repo reads env via `process.env.FOO`, do the same. If it uses `Settings.get('foo')` via a config library, do that. New config values MUST be added to the same source file(s) other values live in.

**Rule 5 — Match test framework.** Read `qa/quality-gates.md` for the Required test command. Use that framework. If the greenfield harness bootstrapped a new one (via `qa-greenfield-harness`), use that. Never introduce a second test framework.

**Rule 6 — No framework leakage in identifiers or comments.** Component names, function names, and code comments are business-language, not framework-language. `SupplierListPage`, not `SupplierListReactPage`. `sendConfirmationEmail`, not `sendConfirmationEmailWithNodemailer`.

**Rule 7 — 100% coverage from the stack tier pool. Every implementation.md build sequence step gets tests AT EVERY APPLICABLE TIER (v2.3.16 sharpened).** No "we'll add tests later." No "deferred to E2E." Every §1 step that touches business logic gets at least one test AT EVERY TIER declared as `Required` for the step's concern class in `qa/quality-gates.md`. Missing tier coverage → the step isn't complete.

**Where the tier pool comes from:**
- `qa/quality-gates.md` `harness_status: Ready` — Required tiers declared for each capability class. Read directly.
- `qa/quality-gates.md` `harness_status: Stack-Inferred` (user chose Skip at `/dev:plan` §1e) — Required tiers inferred from stack detection and written into the file at plan time. Read directly. Same 100% coverage bar for the new feature; the "Stack-Inferred" marker only signals that the tier pool wasn't confirmed by QA audit, not that coverage is optional.

**Concern → tier mapping (this skill reads the `qa/quality-gates.md` tier declaration and matches per step):**

| Concern class | Tiers this step MUST cover |
|---|---|
| Data-integrity (uniqueness, foreign-key, transaction boundary, invariant) | Unit + Integration + Concurrency |
| Operation contract (endpoint / RPC / queue message / job trigger) | Unit + Integration + Contract |
| User-facing surface (page / screen / CLI command) | Unit + Component + E2E |
| Refusal-code path (400/403/404/409/500 variants) | Unit (branch) + Integration (roundtrip) + Component or E2E (user-visible outcome for consumer sub-tasks) |
| Cross-layer flow (spans two or more sub-tasks) | E2E (owned by the sub-task authoring `tests/e2e/…`) |
| Idempotency / retry (background job / consumer / async producer) | Unit + Idempotency + Retry-behaviour |
| Accessibility (interactive surface with a11y NFR) | Component + Accessibility |
| Performance (NFR-declared latency or throughput target) | Load |

**Cross-layer E2E ownership:** the sub-task whose `implementation.md §1` names the `tests/e2e/<flow>.spec.<ext>` file OWNS the E2E test. Other sub-tasks reference it in `§6 Touch points` as a Cross-sub-task row and do NOT re-implement it. For a split feature, this is typically the frontend/UI-owning sub-task, or a dedicated e2e/ folder declared in `qa/quality-gates.md`.

**How to write tests per tier at each build-sequence step:**

1. Read the step from `implementation.md §1 Build sequence` — extract the Satisfies IDs.
2. For each Satisfies ID: cross-match to a concern class (Data-integrity, Operation contract, etc.).
3. From `qa/quality-gates.md` tier pool for this sub-task's capability class, list the Required tiers.
4. Intersect: {concern-class tiers} ∩ {Required tiers for capability class}. Write a test at every tier in the intersection.
5. Log each test file + test name + tier in `dev/implementation-log.md` per step.

**Halt cases:**
- Step's Satisfies IDs have zero tests at any applicable tier → this step is INCOMPLETE. Do not mark complete; escalate as `dev/escalation-<n>.md` if the tier can't be reached without harness support.
- `qa/quality-gates.md` missing entirely → refuse to write code; escalate `blocker: quality-gates-missing`. Point at `/dev:plan` §1e to author it (Yes or Skip path both produce a valid file).

**dev/acceptance-map.md is the evidence artifact** built at Stage 8 — one row per parent AC/BR/TS with test-file references, tier, Pass/Fail status. The plan does NOT list test-file paths; only Stage 8 does.

**Rule 8 — Tests assert on behaviour, not on hardcoded responses.** A test that mocks the entire SUT to return the "correct" value proves nothing. Real state changes, real response shapes, real error paths.

**Rule 9 — Honour `DEC-###` decisions from `plan-blockers.md`.** If the plan-blocker fold resolved an integration to a specific endpoint + auth, use that endpoint + auth verbatim. Never override a resolved decision.

**Rule 10 — No secrets in code or tests.** Env var names OK; values never. Test fixtures use non-real placeholder values; production credentials are read from the repo's existing config mechanism.

**Rule 11 — Stay in scope.** Touching a file the implementation.md build sequence didn't name requires a scope-escalation (write `dev/escalation-<n>.md` and halt). Don't silently refactor an unrelated module.

**Rule 12 — Log every material technical choice.** Naming a new file, choosing between two implementation approaches, deciding on a mocking strategy — each is a `DEC-###`. Trivial choices (variable names inside a function) don't need logs.

**Rule 13 — Standards-aware writing. Every write is checked against `shared-context/coding-standards.md` BEFORE the file is saved, not after.** The declared limits in `coding-standards.md` §6 (function complexity budget), §7 (duplication policy), §8 (recursion policy), §9 (constants & magic values), §10 (state & side effects), §12 (anti-patterns forbidden) are treated as HARD constraints on the code this skill produces — not as review suggestions to be caught later.

For every function or block about to be written:

1. **Complexity walk.** Count the distinct branches (`if`, `switch`, `case`, ternary, boolean-operator short-circuits) — if the count would exceed `§6` cyclomatic limit, split BEFORE writing. Do not write past-limit and rely on review.
2. **Length + nesting check.** If the function would exceed `§6` line limit or nesting depth, split BEFORE writing.
3. **Parameter arity check.** If the signature would exceed `§6` parameter limit — or boolean-flag sub-limit — restructure BEFORE writing (config object, split call sites, strategy object).
4. **Recursion check.** If the write uses recursion, verify against `§8` recursion policy: is this stack's policy tail-call-safe / memoized-required / iteration-only for unbounded input? If policy requires iteration, write iteration. If policy permits recursion, the recursive function still MUST document its base case, termination proof, and worst-case depth per `§8`.
5. **Duplication check.** Before writing a block that looks similar to something already in the diff or in a file the diff references, check the delta. If the near-identical span meets or exceeds `§7` limit, extract the shared shape into a helper BEFORE writing the second occurrence.
6. **Magic value check.** Any numeric or string literal outside the neutral small set (`0`, `1`, `-1`, `""`, `null`, `true`, `false`) goes into a named constant per `§9`. Do not inline a threshold, a URL, a timeout value.
7. **Anti-pattern check.** Before finalizing a function/class/file, sanity-check against `§12`'s forbidden list — god unit doing multiple unrelated concerns, wrapper with one caller, silent catch, comment-code mismatch, dead code. If a hit, restructure BEFORE writing.
8. **State & side-effect check.** External IO, time, randomness, config reads go through the injection mechanism `§10` names. Do not hardcode.

If a limit CANNOT be met without a real architectural change (splitting the sub-task, altering the plan, adding an abstraction not in implementation.md's `§6 Touch points`), escalate as `dev/escalation-<n>.md` — do NOT write past-limit code and add a `TODO: refactor later` comment. Past-limit code accepted at write time becomes review debt, then production debt.

(Note: §-refs in Rule 13 above point to `shared-context/coding-standards.md`'s sections — not to implementation.md sections. Only this closing paragraph's `§6 Touch points` reference points at implementation.md's §6.)

**Rule 14 — `shared-context/coding-standards.md` is a hard precondition.** If the file is missing OR any of §6, §7, §8, §9, §10, §12 is blank or absent, this skill REFUSES to write code. The escalation goes to `dev/escalation-<n>.md` with `blocker: coding-standards-missing`, naming which sections are missing. The fix goes upstream to `tl-project-scaffold` (greenfield) or an explicit standards-authoring step (brownfield) — never inline a guessed standard here. Rationale: without declared limits, Rule 13 has nothing to check against and Dimension 8 in review has nothing to enforce; the "100% engineering standard" guarantee collapses to "we hoped for the best."

## Completion criteria

A implementation.md build sequence step is complete when:

- The code implementing it is written to the target file(s)
- At least one test asserts on the step's business behaviour
- The tests are runnable (import path resolves, no syntax errors)
- `implementation-log.md` records: step ID, files touched (paths + line counts), tests added (paths + test names), any `DEC-###` logged

A feature is `/dev:build`-ready-to-execute-tests (i.e. Stage 6 done) when every implementation.md build sequence step is complete per the above.

## Skills / agents this skill invokes

- No subagents — this skill runs in the dev-agent's own context, since it must maintain repo mental state across many file reads
- Reads `qa/quality-gates.md` — no MCP call, direct file read
- Reads the target repo files directly

## Principles

- **Read before write.** Every stack detection, pattern inference, and code decision is grounded in the repo's existing state, not in a template.
- **Reuse over invent.** Existing abstractions in the repo win by default.
- **Business language, not framework language.** Naming, comments, and documentation stay at the business level.
- **Test with the code.** No feature-complete claim without tests written in the same run.
- **Honour prior decisions.** `DEC-###` and resolved `PB-###` blockers are given — never revisit them silently.
- **Stay in scope.** The implementation.md build sequence names every file to touch; nothing else moves without a scope escalation.
- **Escalate, don't guess.** A genuine ambiguity that the plan didn't resolve is a scope escalation, not a coin flip in code.
