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

**Rule 2 — Reuse over parallel abstraction. Includes AUTH PATTERN reuse (v2.3.24).** If the repo has a `UserRepository`, do not introduce a `SupplierRepositoryV2` alongside — extend the pattern, don't parallel it. If reuse would break the change, escalate as a scope issue, don't create the parallel.

**Rule 2a — Auth-pattern alignment check (v2.3.24 — closes the Bearer null bug at write time).**

Before writing any code that makes a request to a gated endpoint (backend service call, or frontend/mobile API call), do the following alignment check — MECHANICALLY, not from memory:

1. Look up the endpoint in the TL code-context tree: `<repo>/context/code-context/backend/domains/<domain>/endpoints/<slug>.md`.
2. Read its `## Auth` section. Extract the `Client obtains via` code snippet + `Header format` string. These are the ONLY correct values for what the code you're about to write should emit.
3. When writing the request code, USE those values verbatim. Do NOT:
   - Substitute `localStorage.getItem(<key>)` if `Client obtains via` says `await auth.currentUser.getIdToken()`
   - Substitute a generic `"Bearer " + token` if `Header format` says `Authorization: Bearer <id-token>` where `<id-token>` is a specific credential class
   - Copy an auth pattern from a SIBLING file in the same repo that turns out to use a different mechanism — the endpoint's `## Auth` is the authority, not sibling code
4. If the endpoint's `## Auth` section is FREE-PROSE (unstructured) → **halt with `blocker: endpoint-auth-not-structured`**. The compose that produced the plan should have halted first via Rule 11.3 §8; if we're here, /tl:code-map needs re-running against the endpoint's source to produce structured `## Auth`.
5. If the `## Auth` `Server prerequisites` list env vars, those get flagged into `dev/local-runbook.md` §3 by Stage 11.

**Concrete example — the exact bug from the user's real run:**

Endpoint `/api/register` unit's `## Auth`:
```
- Token type: Firebase ID token
- Client obtains via: await firebase.auth().currentUser.getIdToken()
- Header format: Authorization: Bearer <id-token>
```

Correct client code (v2.3.24 — Rule 2a passes):
```javascript
const idToken = await firebase.auth().currentUser.getIdToken();
const response = await axios.post(`${BASE_URL}/api/register`, {}, {
  headers: { Authorization: `Bearer ${idToken}` }
});
```

Incorrect client code (v2.3.24 — Rule 2a HALTS):
```javascript
// BAD: doesn't call getIdToken(); reads a stale localStorage value that's
// been unset since the backend was hardened at commit 89b37c7
const response = await axios.post(`${BASE_URL}/api/register`, { email: userEmail });
// (missing headers entirely — halt)
```

or

```javascript
// BAD: sends "Bearer null" when localStorage is empty
const token = localStorage.getItem('jwtToken');
const response = await axios.post(url, {}, {
  headers: { Authorization: `Bearer ${token}` }
});
// (client acquisition doesn't match endpoint's `## Auth` `Client obtains via` — halt)
```

**Rule 3 — Match error handling.** If the repo throws custom errors, throw one. If it returns `Result<T, E>`, return one. Never introduce a second error paradigm alongside the existing one.

**Rule 4 — Match config style.** If the repo reads env via `process.env.FOO`, do the same. If it uses `Settings.get('foo')` via a config library, do that. New config values MUST be added to the same source file(s) other values live in.

**Rule 5 — Match test framework.** Read `qa/quality-gates.md` for the Required test command. Use that framework. If the greenfield harness bootstrapped a new one (via `qa-greenfield-harness`), use that. Never introduce a second test framework.

**Rule 6 — No framework leakage in identifiers or comments.** Component names, function names, and code comments are business-language, not framework-language. `SupplierListPage`, not `SupplierListReactPage`. `sendConfirmationEmail`, not `sendConfirmationEmailWithNodemailer`.

**Rule 7 — 100% coverage from the stack tier pool. Every implementation.md build sequence step gets tests AT EVERY APPLICABLE TIER (v2.3.16 sharpened; v2.3.23 anti-mock hardening).** No "we'll add tests later." No "deferred to E2E." No "mocked backend counts as integration." Every §1 step that touches business logic gets at least one test AT EVERY TIER declared as `Required` for the step's concern class in `qa/quality-gates.md`. Missing tier coverage → the step isn't complete.

**Rule 7.i — MOCKS DO NOT SATISFY INTEGRATION OR E2E TIERS (v2.3.23). This closes the "tests pass, real endpoint 401s" gap.**

A test that mocks the HTTP call, mocks the database, or mocks the auth middleware is a UNIT test — no matter what its file is named or where it lives. Claiming it as "Integration" or "E2E" in `dev/acceptance-map.md` is a FALSE COVERAGE CLAIM.

**Tier definitions (binding):**

| Tier | Real HTTP? | Real DB / real store? | Real auth middleware? | Real backend service running? | Real frontend service running? |
|---|---|---|---|---|---|
| Unit | No (mocked or in-process only) | No (in-memory / mocked) | No (mocked) | No | No |
| Component (frontend) | No (mocked axios/fetch) | N/A | N/A | No | No |
| Integration | **YES** | **YES** (real test DB — Postgres/Mongo/etc. — with fixtures, torn down after) | **YES** (real middleware runs) | **YES** (backend process actually started) | N/A |
| Contract | YES (real HTTP against a running service) | Any | Any | **YES** | N/A |
| Concurrency | YES (real DB roundtrip; multiple concurrent connections) | **YES** | Any | **YES** | N/A |
| E2E | **YES** | **YES** | **YES** | **YES** | **YES** (real browser or headless — Playwright / Cypress / Puppeteer against a running dev server) |

**If ANY column marked YES for the claimed tier is actually mocked → the test does NOT satisfy that tier.** It becomes a Unit test only. If Integration was the only claimed tier for an AC/BR/TS and the test is actually mocked, the AC/BR/TS is UNCOVERED. Acceptance-map.md row must be flagged.

**Rule 7.ii — Every test file MUST declare its `# tier:` at the top OR carry an obvious tier signature the compose can detect.** For test files under this build sequence's write:

```javascript
// tier: integration
// requires: backend-running, real-db, real-auth
```

or

```python
# tier: e2e
# requires: backend-running, frontend-running, playwright
```

If a test file's tier declaration doesn't match its actual behavior (e.g. declares `integration` but mocks axios), Rule 13 halts before writing.

**Rule 7.iii — Acceptance-map.md rows carry a `mocked` field per test evidence entry.** Schema:

```yaml
- id: AC-1
  status: Passed | Failed | Not-covered
  tier: Unit | Component | Integration | Contract | Concurrency | E2E
  evidence:
    - file: tests/holiday.controller.test.js
      test_name: creates_authenticated
      mocked: false            # real HTTP + real DB + real middleware
      external_processes_required: [backend-8080, postgres-test]
    - file: tests/holiday.mock.test.js
      test_name: unit_shape
      mocked: true             # unit-tier only; does not satisfy an Integration claim
      external_processes_required: []
  passed: false                # aggregate: false if ANY row's tier claim is contradicted by its mocked flag
```

**Rule 7.iv — Rule 13's write-time check enforces the mock/tier alignment.** BEFORE writing a test file, this skill's write-time pass:

1. Reads the intended tier declaration from Rule 7.ii's header
2. Detects imports/patterns that indicate mocking: `jest.mock(`, `vi.mock(`, `sinon.stub(`, `nock(`, `msw`, `axios-mock-adapter`, `unittest.mock`, `MagicMock`, `pytest.MonkeyPatch`, `mockery`, etc.
3. If `tier: integration` or higher AND ANY mocking-library import is used → HALT with escalation. Options: (a) remove the mock and use a real fixture, (b) demote the tier declaration to Unit and cover the higher tier with a separate test that actually runs against real infrastructure, (c) declare a documented exception in `qa/quality-gates.md` (e.g. "third-party payment provider mocked because we can't hit it in dev — separate contract-testing job runs against staging").

**Rule 7.v — Backend-running requirement for Integration/Contract/Concurrency/E2E tests.**

Before Stage 7 (Execute tests) runs any test file whose `tier:` header is `integration` / `contract` / `concurrency` / `e2e`:

1. Check the backend's own README + `package.json` scripts + `.env.example` for the actual startup requirement (env vars, dependent services, DB connection)
2. Attempt to start the backend (`npm run dev` / `python manage.py runserver` / equivalent) with a health-check timeout (max 30s)
3. If startup fails (missing env var, port conflict, DB unreachable) → HALT the test run for that tier, mark the tier as `Not-covered` in acceptance-map.md, DO NOT claim Passed. Escalate as `dev/escalation-<n>.md` with the missing prerequisites.

**Rule 7.vi — For consumer sub-tasks (frontend/mobile), the wire integration test hits the REAL backend running from the sibling sub-task's build.** If the sibling sub-task hasn't been built yet, the wire integration is `Not-covered` in this sub-task's acceptance-map, and the AC/BR/TS is marked `Deferred to cross-sub-task landing` — surfaced as a §6 Touch points cross-sub-task row: `Integration for AC-M owned by cross-sub-task landing test — closes when frontend + backend both merge to develop`.

This is DIFFERENT from the retired "Deferred to E2E" plan-time concept. Here it's a build-time evidence gap that resolves when both sub-tasks land, not a plan-time skip.

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

9. **Auth-header null-guard check (v2.3.24 — closes the Bearer null bug).** Scan every emitted line that constructs an `Authorization` header. Detect the anti-pattern where an interpolated value could be `null` / `undefined` / empty at runtime:
   - Regex on the emitted string: `Authorization.*Bearer\s*[\+\`\$][^;]*(localStorage\.getItem|sessionStorage\.getItem|cookies\.get|process\.env|getenv|.getVal|.getValue|.currentUser|.user|.token)`
   - For each match, verify the emitted code has a null-guard IMMEDIATELY around the acquisition (either `if (!token) throw ...` or `const token = <acquire>(); if (!token) return; ...` OR the acquisition is `await`ed on a promise that throws on absence per the auth library's contract).
   - If NO null-guard is present → HALT. The specific failure mode this catches: the value is `null` at runtime, the emitted code sends `Authorization: Bearer null`, the server's bearer-prefix check passes, `jwt.verify` fails, the user sees "session expired" when they were never signed in.
   - This is a Rule 12 anti-pattern (silent null-swallowing) applied specifically to auth headers because it's the highest-blast-radius instance of it.

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
