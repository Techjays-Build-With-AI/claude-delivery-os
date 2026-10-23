---
description: Implement the approved test-setup plan — install and configure frameworks, wire CI, add fixtures/mocks and coverage thresholds, scaffold the e2e harness, prove a green smoke run, and finalize qa/quality-gates.md (the contract the dev loop verifies against). Works in an isolated branch; never weakens or deletes tests to go green; never writes per-feature tests or edits product logic; never merges or deploys.
argument-hint: "<(blank = use qa/<repo>-setup.md) | plan=<path>> [repo=<path>]"
---

# /qa:setup

You stand up the test harness the plan describes and **prove it runs green**, then finalize the quality-gate contract the dev delivery loop reads. Delegate to the **`qa-agent`** subagent, which runs `qa-test-setup` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain an optional **`plan=`** path (default: `qa/<repo>-setup.md` § `## Plan`) and an optional **`repo=`** path (default: the current workspace / project repo). If there's no setup plan, tell the user to run `/qa:audit` → `/qa:plan` first and stop — don't build without an approved plan.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run `/qa:setup` using the `qa-test-setup` skill (build phase) — follow `references/setup-guide.md`. Read `qa/<repo>-setup.md` § `## Plan`. Work in an isolated branch (`qa/test-setup-<n>`) with a clean working tree. **Ask which branch to cut it from before touching anything** — recommend `apps[].env_branches.dev` from `.jetrix/project.json` and let the user change it with `AskUserQuestion`, exactly as `/dev:plan` does for a feature branch. Never default silently: a harness built on the wrong base lands its PR in the wrong place and the mistake only shows at review. Refuse `main` / `master` / `production` outright — this flow always targets a mutable dev branch. Implement the plan step by step in stand-up order: install and configure each framework, add its config, wire package scripts and CI, add fixtures/factories and mocking utilities, set and **enforce** the approved coverage threshold, scaffold the e2e harness (base config + page-object/fixtures skeleton), and write the repo's `## Conventions` into `quality-gates.md § <repo>`. Add **example/smoke** tests only — never per-feature business-logic tests. After each piece run its command and confirm green; then run the full green-smoke sequence (install → lint → format:check → typecheck → unit → coverage(threshold) → build → e2e:smoke where applicable). **Run the exact command CI runs for every gate — same script, same flags, same config** (`setup-guide.md` §3). A local `coverage` that applies no threshold passes while CI fails on the same repo; that is two different commands wearing one name, and it is how a run reports green and then breaks CI. Prove the coverage gate actually **bites** — observe a non-zero exit below the floor once — rather than only that it runs. **Check every threshold against its measured value before running it** — `setup-guide.md` §3a. An existing repo is floored at its MEASURED coverage rounded DOWN (§2a): 4.49% takes `4`, never `5`. A floor above the measured number fails on untouched code from the first CI run onward. If the coverage gate fails and `floor > measured`, **correct the floor, log a `DEC-###` with both numbers, and re-run** — that is fixing a bar the code could never clear, not the forbidden lowering of one it did clear; the run history must say which. **Always push and raise the PR**, green or not — a harness that stays local is not a harness — but never report a red run as green: still-red means `harness_status: Blocked`, and the summary and PR body name the command, its exit code and its output. Honour the limits: 3 focused fixes per failing step, 2 broad smoke re-runs, 0 strategy guesses; **never** disable, skip, delete, or loosen a check/threshold to go green — that's an escalation with the trade-off named, written to `qa/<repo>-setup.md` § `## Run history`. Log each attempt in `qa/<repo>-setup.md` § `## Run history` and material decisions as `DEC-###`. **Gate inherited-finding checks on NEW findings, not existing ones** (`setup-guide.md` §3a): `BL-08` and `BL-09` run against history you did not write, so wire the scan, baseline what is there, and fail only on a new one. `npm audit --audit-level=high` red on 51 pre-existing advisories is the coverage-floor mistake again. **Never fix them here** — print `/dev:build --vulnerable`, the mode that does, and log the baselining as a `DEC-###`. Finalize `qa/quality-gates.md` via `qa-quality-gates`. **`harness_status` and `baseline_status` are separate fields**: `Active` when the smoke sequence ended green (a still-failing smoke gate is `Blocked`); a baselined mandatory item sets `baseline_status: Unmet` with its id in `baseline_unmet` and **leaves `harness_status` alone** — a red `BL-08` does not stop `/dev:build`. Do not merge or deploy. Return what was stood up, the green-smoke result, the `DEC-###` logged, and the finalized gates.
>
> Repository: `<repo or current workspace>` · Plan: `<plan path>`

## 3. Surface the result

Present what was **stood up** (frameworks, CI, coverage floor, e2e harness, conventions), the **green-smoke result**, the `DEC-###` decisions logged, and the finalized `qa/quality-gates.md`. If setup hit a blocker, lead with the decision needed (the escalation note) instead of a partial success.

Close with this block, filled in:

When the sequence ended green:

```
✓ Harness Active. Green smoke passed.
  Baseline:  Met
  Stood up:  <frameworks · CI · coverage floor · e2e · conventions>
  Gates:     <n> Required, <n> Required* pending a surface, <n> Optional
  DEC-###:   <decisions logged>
  PR:        <url>

First  Review and merge the PR — until it lands, the harness is not on <base>.

Then — pick the one that matches what you're doing
  /dev:build --tests-only repo=backend src/suppliers
      cover code that already exists. No plan needed, no production code
      written. Leave the path off to take the whole repo, risk-ranked.

  /ba:scope add "requirements in ./client-docs"
      the work starts from a requirement, not a ticket. A Drive link works
      here too.

  /dev:plan PAY-412
      you already have a ticket. Pull it first if it is not local —
      /jetrix:pull task PAY-412 (Jira, the tracker you bound at init).

  /dev:build --vulnerable repo=backend
      the scan flagged dependencies. Upgrades them against this harness,
      writes no feature code. Only when BL-08 was baselined.

  /qa:health
      re-check these gates any time. Nothing to do now.
```

When the harness is green but a **baseline** item is not — the common case on an existing repo, and the one
that must never be reported as a blocked harness:

```
✓ Harness Active. Green smoke passed.
⚠ Baseline Unmet — BL-08 (dependency scanning)
  Stood up:  Jest 29 · supertest + in-memory MongoDB · ESLint + Prettier ·
             coverage floor 52/52/6/33 · husky + gitleaks · Actions + Dependabot
  BL-08:     scan wired and gating NEW findings. 51 existing baselined
             (2 critical, 39 high; 18 in prod deps) — DEC-014
  PR:        <url>    CI is green; the harness is usable now.

First  Review and merge the PR.
Then   /dev:build --vulnerable repo=backend    — upgrades the 18, with this
       harness running against each one. Not part of setup: a framework major
       is a product change, smoke tests alone would not catch a regression.
```

**The PR is mergeable and CI is green.** That is the whole point of baselining: the gate catches the next
bad dependency, the existing ones are queued as real work, and nobody has to `--force` past a red check.

When a **smoke-sequence** gate is still failing — the harness itself — the PR still exists, and the reader
needs to know it is red before they open it:

```
⚠ Harness Blocked. PR raised, but CI will fail until this is fixed.
  Failing:   npm run coverage — exit 1
             Coverage for lines (4.49%) does not meet global threshold (5%)
  Floor:     5 set, 4.49 measured — see §3a: an existing repo floors at
             measured, rounded down. Correct it to 4 and re-run.
  Stood up:  <what did land>
  PR:        <url>
```

**Never print the plain ✓ shape for a run that ended red**, and never report `Active` over a failing
*harness* gate. Equally, **never report `Blocked` for a baseline item** — a red `BL-08` does not stop
`/dev:build`, and saying it does sends the reader to fix something that is not in their way. The PR
going up is not the same as the harness working, and a reader who conflates them merges a broken gate onto
the branch every teammate builds from.

**Fill every line with this workspace's real values** — the actual base branch, a real module in this repo, the tracker's own id form read from `project.json` (`delivery-os-conventions` §1.e.1). Never print `<task>`.

**Merging is the only ordered step.** The three below it are intents, not a sequence — the reader has one of them and the other two are noise to them.

**`/dev:build` is never the plain step after setup.** It halts without a `/dev:plan` plan (`build.md` §2, "run /dev:plan first"), so printing it bare sends the user into a refusal. `--tests-only` is the one exception — it writes no production code, so it needs no plan, and it is the single most useful thing to offer right after a harness goes green on a repo that already has code.

Name any **`Required*` gate whose condition holds but whose command is still `Not-configured`** — those are the tiers the dev loop will report as `tier-unavailable`, and they are gaps rather than opt-outs. It stops at the PR and **never merges**.
