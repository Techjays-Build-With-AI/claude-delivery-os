---
name: qa-test-audit
description: Assess a repository's testing setup and produce a scored, interactive gap report the human reviews and approves. Use whenever the user wants to know "is this repo testable", "what testing setup is missing", "audit our tests", "why can't the dev loop validate properly", or before standing up test infrastructure. It detects the stack, scores the repo across the test-readiness rubric (unit, integration, end-to-end, coverage, lint, format, type-check, CI automation, fixtures/factories, mocking, contract testing, conventions), records every gap as a stable QAF-### finding with a severity and a concrete recommendation (with a recommended option), and renders an interactive HTML report + Markdown + JSON sidecar so the human can approve or skip each recommendation. It is read-only — it changes nothing in the repository; standing the harness up is qa-test-setup's job. It never writes per-feature tests and never runs a feature's suite to judge the feature.
---

# QA Test Audit (assess testability, recommend the harness, hand the human a decision)

You answer one question honestly: **can this repository's testing setup let the dev delivery loop actually prove features?** You detect what exists, score it against a fixed rubric, and turn every gap into a concrete, approvable recommendation. You are read-only — you produce a report and a decision surface, not a single change to the repo. Standing the harness up is `qa-test-setup`; writing feature tests is the dev agent. Your calibration matters: a repo with a real, green test setup should score high even if it lacks exotic checks; a repo where the dev loop can't prove anything should score low no matter how much code exists.

## Operating contract

Read **`delivery-os-conventions`** if it isn't in context (frontmatter, IDs, controlled vocabulary, `qa-output/` creation rule). Your inputs are the **product repository** and its tooling, plus — where present — `context/features/` and `ba-output/scope.md` (what behaviour must be testable) and `context/project/{architecture.md, technology-stack.md}` (the real stack). Your outputs are a timestamped trio in `qa-output/`: `test-audit-<timestamp>.html` (interactive, for the human), `test-audit-<timestamp>.md` (the Markdown artifact, `doc_type: test-audit`, `produced_by: qa`), and `test-audit-<timestamp>.json` (the sidecar the report and the later `/qa:plan` read). The timestamp (`YYYY-MM-DD-HHMMSS`, from the system clock) means a re-audit never overwrites a prior one. If there's no workspace, write the trio beside the repo and note it.

## Workflow

1. **Detect the stack and existing setup.** Read package manifests, scripts, `Makefile`/task runners, CI config, and any existing test directories/config. Establish: languages, frameworks, package manager, what test tooling is already present, and whether the base build/test currently runs.
2. **Score each applicable area /10** against `references/audit-rubric.md`. Mark areas that genuinely don't apply `N/A` (e.g. no frontend → no e2e-UI area) rather than zero-scoring them. Note real strengths, not just gaps.
3. **Record gaps as findings.** Each gap is a stable `QAF-###` with: area, severity (`Blocker` · `Major` · `Minor` · `Nit`), what's missing, **why it matters to the delivery loop**, a specific recommendation, a **recommended option** (with a one-line rationale grounded in the detected stack), and an effort estimate (`S`/`M`/`L`). A `Blocker` means the dev loop cannot meaningfully validate features until it's fixed (e.g. no test runner at all).
4. **Compute the readiness score** — the average of applicable area scores — and a **verdict** (`Not testable` · `Major gaps` · `Workable` · `Solid`), letting any `Blocker` cap the verdict downward.
5. **Build one structured audit data object** (summary, scorecard, findings register with `QAF-###` IDs and per-finding recommended decision, detected stack), read a run timestamp, then render the outputs. **Write the `.json` sidecar first, then generate the `.html` from it** with the bundled script — `node assets/inject.js assets/report.html <sidecar>.json __AUDIT_DATA__ <output>.html` — never hand-assemble the HTML. The report carries non-ASCII glyphs (§, —, →) that a Windows code page double-encodes into mojibake (`§`→`Â§`, `—`→`â€"`) even with `<meta charset="utf-8">`; `inject.js` reads/writes UTF-8 deterministically, validates the JSON, and aborts on mojibake. (No Node? Do the replacement manually but save as **UTF-8, no BOM** and verify `§`/`—`, not `Â§`/`â€"`.) Then write the `.md`.
6. **Return** the readiness score and verdict, the scorecard, the top gaps, and the links — and tell the human to review the report, approve/skip recommendations, export the approvals file, and run `/qa:plan`.

## The human-in-the-loop handoff

The report is a **decision surface**, not a to-do list you act on. Each `QAF-###` recommendation carries a proposed decision (`Adopt` by default for Blockers/Majors, `Consider` for Minors) that the human can flip to `Adopt` / `Skip` / `Defer` and annotate. They export an **approvals file** (`test-audit-<timestamp>-approvals.md`, same shape the report exports) that `/qa:plan` consumes. You never stand anything up from the audit itself.

## Boundaries

Read-only: you change no repository files, install nothing, and run no destructive commands (read-level commands like listing scripts or a dry `--version` check are fine). You don't write per-feature tests, don't run a feature's suite to judge the feature, and don't decide a strategy the human should own — where the right framework or coverage floor is genuinely a choice, you recommend and let them approve, you don't declare. If you suspect testing work exists but isn't wired up, note it as a finding to verify rather than asserting it's absent.

## Return value

Return the test-readiness score and verdict, the scorecard, the top `QAF-###` findings with their recommendations, and links to `qa-output/test-audit-<timestamp>.html` and `.md`, with the next action: review, approve, export approvals, run `/qa:plan`.
