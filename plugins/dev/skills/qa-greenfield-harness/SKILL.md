---
name: qa-greenfield-harness
description: Auto-bootstrap the test harness (test dependencies, configs, minimal quality-gates.md) when /dev:build finds a greenfield project or an existing repo without a QA-owned qa/quality-gates.md. Fully automatic — never prompts the user. Deterministic per-stack matrix (see references/stack-matrix.md) picks idiomatic frameworks; writes test config files, updates package manifests, generates a minimal Active gates contract, and logs every choice to dev/test-decision.md for audit. Later /qa:audit → /qa:plan → /qa:setup can override interactively; this skill's job is to unblock the ongoing /dev:build without stopping.
---

# QA Greenfield Harness

You are auto-provisioning a test harness so `/dev:build` can proceed without prompting for framework choices or waiting for `/qa:setup` to run interactively. Fires from `/dev:build` Stage 4 when the QA harness gate finds no Active `qa/quality-gates.md`. Deterministic: same stack + same conditions → same choices, every time.

## Operating contract

Read the **`delivery-os-conventions`** contract if not in context. Your inputs:

- The target repository (from `/dev:build`'s repo resolution; sub-tasks scope to one repo)
- The detected stack (from `dev-stack-adaptive-implementation`'s `stack-detection.md` — run BEFORE this skill in `/dev:build`; check `dev/implementation-log.md` for the detected-stack block, OR re-run stack detection here if the block isn't present)
- Parent's `test-scenarios.md` — the E2E scenarios to seed as skeleton E2E tests
- Parent's `nfrs.md` — performance / coverage / security bars that map to gates

You write to:

- **The target repo:** test dependency manifest updates, test config files, `.gitignore` additions if needed, skeleton E2E test scenarios
- **The workspace:** `qa/quality-gates.md` — minimal Active harness contract; `dev/test-decision.md` — audit log of choices

## Trigger conditions

`/dev:build` Stage 4 invokes this skill when ANY of these hold:

1. `qa/quality-gates.md` does not exist
2. `qa/quality-gates.md` exists but `harness_status: Draft` (never went through `/qa:setup`)
3. `<repo>/context/code-context/` is empty or ≤ 3 source files (skeleton repo — greenfield indicator)

If `harness_status: Broken` — do NOT bootstrap. Route to `/qa:health` instead per `/dev:build` Stage 4 §Broken handling.

## The 5-step bootstrap

### Step 1 — Confirm layer (frontend / backend / mobile / db)

From the detected framework, classify:

- **Frontend:** React, Vue, Angular, Svelte, Next.js, Nuxt, SvelteKit, Remix, Astro
- **Backend:** Express, NestJS, Fastify, FastAPI, Django, Flask, Spring Boot, ASP.NET Core, Gin, Echo, Fiber
- **Mobile:** Flutter, React Native
- **DB:** Migrations-only repos (SQL scripts, Prisma-only) — treat as backend-ish

Mixed frontend+backend in one repo (Next.js full-stack) → treat as frontend (use frontend matrix) since UI E2E covers most acceptance-map rows.

### Step 2 — Pick from the matrix

Read **`references/stack-matrix.md`** and pick the row that matches `(layer, framework)`. Each row names:

- Unit test framework
- Integration / contract test tools
- E2E framework
- Coverage tool
- Optional bench tool

**Deterministic — always pick the row.** No fallback to "developer preference" — that's what `/qa:audit` is for later.

### Step 3 — Install dependencies

Using the package manager detected in Phase 1 of `dev-stack-adaptive-implementation` (`pnpm` / `npm` / `yarn` / `bun` / `pip` / `poetry` / `uv` / etc.), install the framework's dev dependencies.

Actual command examples (run in the target repo):

```bash
# TS + Vitest + Playwright (frontend)
pnpm add -D vitest @vitest/coverage-v8 @testing-library/react @testing-library/user-event @playwright/test
pnpm exec playwright install --with-deps chromium

# Python + pytest + httpx (backend)
poetry add --group dev pytest pytest-cov pytest-asyncio httpx

# Go + testify (backend)
go get -u github.com/stretchr/testify/require
```

Log every command run (not just declared) to `dev/test-decision.md` under `commands_executed:`.

### Step 4 — Write test config files

Minimal working configs. See **`references/gates-template.md`** for exact contents per framework. Examples:

- **Vitest:** `vitest.config.ts` with coverage provider, test-file glob, JSDOM env for React
- **Playwright:** `playwright.config.ts` with 1 project (chromium), reporter, base URL from env
- **pytest:** `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` with test-file glob + coverage settings
- **Jest:** `jest.config.js` — same purpose

Also update `.gitignore` for coverage output folders (`coverage/`, `.nyc_output/`, `htmlcov/`, `playwright-report/`).

### Step 5 — Write `qa/quality-gates.md`

Per **`references/gates-template.md`** — one file, `harness_status: Active`, Required table listing the exact commands to run for each gate:

```
qa/quality-gates.md  →  6-8 Required gates depending on layer
```

**Coverage floor:** 60% for greenfield (aggressive but achievable; developer can bump later via `/qa:setup`).

### Step 6 — Write `dev/test-decision.md`

Under the task's `dev/` folder — per-task audit log:

```yaml
---
doc_type: test-decision
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>            # OMIT for parent-alone
subtask_repo: <repo-slug>
bootstrapped_at: <ISO>
bootstrapped_by: qa-greenfield-harness
---

# Test harness decisions for <task>

## Detected stack

<from dev/implementation-log.md detected_stack block>

## Layer detected

<frontend | backend | mobile | db>

## Frameworks chosen (from stack-matrix.md)

| Category | Framework | Rationale (from matrix) |
|---|---|---|
| Unit | Vitest | Idiomatic for Vite + React repos; fast HMR-integrated |
| Integration | Supertest | Standard for Node HTTP integration |
| E2E | Playwright | Modern replacement for Cypress; multi-browser |
| Coverage | @vitest/coverage-v8 | Native to Vitest |

## Files written

- vitest.config.ts (new)
- playwright.config.ts (new)
- .gitignore (updated — added coverage/, playwright-report/)
- qa/quality-gates.md (new — 6 Required gates)

## Commands executed

- pnpm add -D vitest @vitest/coverage-v8 @testing-library/react @testing-library/user-event @playwright/test
- pnpm exec playwright install --with-deps chromium

## Overridable via

- /qa:audit — interactive harness assessment
- /qa:plan → /qa:setup — swap frameworks / change coverage floor

## Notes

Every choice is deterministic per stack-matrix.md. If your team prefers Jest over Vitest (or Cypress over Playwright), run /qa:audit → /qa:plan to swap. This bootstrap unblocks /dev:build for the current feature without requiring that setup first.
```

## Hard rules

**Rule 1 — Never prompt.** Every decision comes from `references/stack-matrix.md`. Deterministic. Auditable. No user pause. This is the ONE rule the whole skill exists to preserve.

**Rule 2 — Deterministic per stack.** Same stack + same layer → same frameworks. Every time. If the matrix has two equally-valid options, the matrix picks one as canonical; the skill never rolls dice.

**Rule 3 — Minimal, not maximal.** The generated harness runs ONE unit + ONE integration + ONE E2E gate. Coverage at 60%. No security scanning, no dependency vulnerability scanning, no performance benchmarks — those come from `/qa:setup`'s interactive plan later. This skill's job is UNBLOCK, not ideal.

**Rule 4 — Don't overwrite existing configs.** If `vitest.config.ts` already exists, do NOT clobber. Merge minimally: if key required options are missing, add them; if they exist with different values, leave alone and log a warning to `test-decision.md`.

**Rule 5 — Don't touch source files.** This skill only writes test configs + gates + updates package manifests. No source code changes. The dev-plan step-writing is `dev-stack-adaptive-implementation`'s job.

**Rule 6 — Log every command actually run.** Not "would run" — actually run. If a `pnpm add` fails (network, permission), surface the error, halt Stage 4, do NOT proceed to `/dev:build` Stage 5.

**Rule 7 — `harness_status: Active` after successful bootstrap.** Not `Draft` — the harness IS active from this run's perspective. `/qa:audit` later marks it as bootstrap-generated if it wants to distinguish.

**Rule 8 — E2E skeletons from parent's `test-scenarios.md`.** For frontend layer only — generate ONE skeleton E2E test file with placeholder `test.skip(...)` blocks per parent TS scenario. The developer's `/dev:build` fills them in during Stage 6.

## Completion criteria

Bootstrap complete when:

- All dependencies installed successfully (exit code 0 on package manager commands)
- All config files present
- `qa/quality-gates.md` exists with `harness_status: Active` and the Required table populated
- `dev/test-decision.md` written under the task's `dev/`
- A trial run of the unit test command (from Required table) exits successfully (even if there are 0 tests yet — the framework runs)

If ANY of the above fails → set `qa/quality-gates.md` `harness_status: Draft`, write an error to `test-decision.md`, and escalate to `/dev:build`'s error handling. Do NOT lie about `Active` — future runs must be able to trust the file.

## Skills / agents invoked

- Reads `dev-stack-adaptive-implementation`'s `references/stack-detection.md` output — via existing `dev/implementation-log.md` block
- Runs shell commands via the shell tool — direct, no MCP
- No subagent delegation — everything runs in the dev-agent's own context

## Principles

- **Automatic, always.** No user prompts inside a `/dev:build` run.
- **Deterministic, per stack.** Same input → same output.
- **Minimal, not ideal.** Unblocks the build; leaves ideal setup for `/qa:setup`.
- **Loud on failure.** Config write fail = halt. Never silently downgrade to `Draft` and hope.
- **Auditable.** Every choice logged to `dev/test-decision.md` with rationale.
- **Overridable by QA.** This skill's output is a starting point, not a final answer. `/qa:audit` inspects; `/qa:plan` proposes changes; `/qa:setup` applies them.
