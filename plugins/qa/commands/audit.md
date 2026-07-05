---
description: Assess a repository's testing setup and produce a scored, interactive gap report the human reviews and approves — read-only, changes nothing. Scores unit, integration, e2e, coverage, lint, format, type-check, CI, fixtures, mocking, contract testing, and conventions; records each gap as a QAF-### finding with a recommendation and recommended option; renders an HTML + Markdown + JSON report. Point it at a repo, or let it use the current workspace.
argument-hint: "<repo=<path> | (blank = current workspace)>"
---

# /qa:audit

You assess how testable a repository is and hand the human a decision surface — you change nothing. Delegate the work to the **`qa-agent`** subagent, which runs `qa-test-audit` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain an optional **`repo=`** path (default: the current workspace / project repo). If there's no resolvable repository at all, say so and ask the user to point you at one rather than auditing nothing.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run a read-only test-readiness audit using the `qa-test-audit` skill — follow `references/audit-rubric.md` and `references/report-template.md`. Detect the stack and existing test tooling from the repo (manifests, scripts, CI config, test dirs); read `context/features/` / `ba-output/scope.md` and `context/project/` where present to know what must be testable. Score each applicable rubric area /10, mark inapplicable areas N/A, and record every gap as a stable `QAF-###` finding — severity (`Blocker`/`Major`/`Minor`/`Nit`), what's missing, why it matters to the dev delivery loop, a recommendation, a recommended option with a one-line rationale grounded in the detected stack, and an effort estimate. Compute the readiness score (average of applicable areas) and verdict (`Not testable`/`Major gaps`/`Workable`/`Solid`), letting any Blocker cap it. Build one structured audit object, read a run timestamp from the system clock, and render `qa-output/test-audit-<timestamp>.html` (inject the JSON into `assets/report.html`), `.md`, and the `.json` sidecar. Change no repository files. Return the score, verdict, scorecard, top `QAF-###` gaps, and links.
>
> Repository: `<repo or current workspace>`

## 3. Surface the result

Present the **test-readiness score and verdict**, the scorecard, and the top `QAF-###` gaps with their recommendations. Link to `qa-output/test-audit-<timestamp>.html` (interactive) and `.md`. Tell the user to open the report, set **Adopt / Skip / Defer** per finding, **Export approvals**, and run `/qa:plan` with the exported approvals file. Lead with the biggest blocker if the repo isn't testable.
