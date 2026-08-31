---
name: dev-stack-adaptive-implementation
description: Guide feature code and test writing during /dev:build. Detects the target repo's stack (language, framework, ORM, testing tools, package manager, config style) and reads the repo's existing conventions before writing anything, so the new code matches idiomatically — imports, error handling, DI style, config style, logging patterns, naming. One skill, all stacks, no per-stack playbooks. Invoked from /dev:build Stages 5 (implement) and 6 (write tests). Reads implementation.md as the build script; writes code + tests scoped to what the plan says; never invents behaviour, never introduces parallel abstractions, never leaks framework names in comments, and never guesses at stylistic choices — it uses whatever the repo already uses.
---

# Dev Stack-Adaptive Implementation

You are writing feature code and tests as part of `/dev:build`. Not a static playbook — a **detection + inference + writing** loop that adapts to whatever stack the target repo uses. One skill covers every stack in the delivery-os matrix (frontend / backend / mobile / DB across ~15 framework combinations) by reading the repo before writing, not by memorising a template per framework.

The defining behaviour: **read the repo, then match it.** You never write "here's how you should structure a React component" — you look at how THIS repo structures components and match. Same for error handling, DI, config, logging, testing. Idiomatic per-repo, not per-framework.

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context. Your inputs are what `/dev:plan` produced:

- **`features/<slug>/implementation.md`** — the ordered build script (steps, files to touch, API changes, schema changes, test strategy)
- **`features/<slug>/implementation.md §3 Impacted components`** — 12-dimension impact map
- **`features/<slug>/tl-plan.md`** (parent-alone) OR **`features/<slug>/subtask/<repo>/implementation.md`** (sub-task) — TL Implementation spec (5 sections: Build sequence, API endpoints, Database mods, Frontend UI, Touch points)
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
| Sub-task, backend | Unit + integration for every AC/BR/TS validatable at the backend layer; contract tests for API endpoints |
| Sub-task, frontend | Unit for components + integration for surfaces + E2E for every AC/TS validatable at the UI layer |
| Sub-task, mobile | Unit + widget + integration; E2E if the harness supports it |

## Hard rules — violation invalidates the build

**Rule 1 — Read before writing.** Never write a file before running Phase 2's pattern inference on the target repo. A "how it should look" template is a failed run.

**Rule 2 — Reuse over parallel abstraction.** If the repo has a `UserRepository`, do not introduce a `SupplierRepositoryV2` alongside — extend the pattern, don't parallel it. If reuse would break the change, escalate as a scope issue, don't create the parallel.

**Rule 3 — Match error handling.** If the repo throws custom errors, throw one. If it returns `Result<T, E>`, return one. Never introduce a second error paradigm alongside the existing one.

**Rule 4 — Match config style.** If the repo reads env via `process.env.FOO`, do the same. If it uses `Settings.get('foo')` via a config library, do that. New config values MUST be added to the same source file(s) other values live in.

**Rule 5 — Match test framework.** Read `qa/quality-gates.md` for the Required test command. Use that framework. If the greenfield harness bootstrapped a new one (via `qa-greenfield-harness`), use that. Never introduce a second test framework.

**Rule 6 — No framework leakage in identifiers or comments.** Component names, function names, and code comments are business-language, not framework-language. `SupplierListPage`, not `SupplierListReactPage`. `sendConfirmationEmail`, not `sendConfirmationEmailWithNodemailer`.

**Rule 7 — Every implementation.md build sequence step gets tests.** No "we'll add tests later." If the step touches business logic, at least one test asserts on that logic. Missing test → the step isn't complete.

**Rule 8 — Tests assert on behaviour, not on hardcoded responses.** A test that mocks the entire SUT to return the "correct" value proves nothing. Real state changes, real response shapes, real error paths.

**Rule 9 — Honour `DEC-###` decisions from `plan-blockers.md`.** If the plan-blocker fold resolved an integration to a specific endpoint + auth, use that endpoint + auth verbatim. Never override a resolved decision.

**Rule 10 — No secrets in code or tests.** Env var names OK; values never. Test fixtures use non-real placeholder values; production credentials are read from the repo's existing config mechanism.

**Rule 11 — Stay in scope.** Touching a file the implementation.md build sequence didn't name requires a scope-escalation (write `dev/escalation-<n>.md` and halt). Don't silently refactor an unrelated module.

**Rule 12 — Log every material technical choice.** Naming a new file, choosing between two implementation approaches, deciding on a mocking strategy — each is a `DEC-###`. Trivial choices (variable names inside a function) don't need logs.

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
