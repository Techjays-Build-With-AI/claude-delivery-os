---
description: Score a built project's production maturity across four domains — Code Quality & Maintainability, Test Quality & Verifiability, Infrastructure & Operations, and Security — and produce a scored, interactive report with per-finding evidence. Runs a read-only preflight that detects the stack and checks the mandatory QA baseline is in place (reminds/routes to /qa:audit when it isn't), consumes the project's own enforced tooling output first, tags every finding evidenced or attested, and reports a maturity score plus a separate Audit Confidence. Read-only — installs nothing, changes nothing. Point it at a repo, or let it use the current workspace.
argument-hint: "<repo=<path>> [strict-baseline]  |  (blank = current workspace)"
---

# /tl:maturity

You score how production-ready a built project is and hand the human an evidence-backed maturity report — you change nothing. Delegate the work to the **`tl-agent`** subagent, which runs `tl-maturity-audit` in its own context.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **`repo=`** path (default: the current workspace / project repo). If there's no resolvable repository, say so and ask the user to point you at one rather than auditing nothing.
- An optional **`strict-baseline`** flag. When present, the audit stops at preflight and routes to QA if the mandatory baseline is unmet, instead of scoring in degraded mode.

## 2. Preflight the QA baseline (remind / route)

Before the full evaluation, the audit checks whether the mandatory tooling baseline is in place — it reads `qa-output/quality-gates.md` (`baseline_status`) and the active `baseline-profile.md`. Behaviour:

- **Baseline met** → proceed to the full evaluation.
- **Baseline unmet, default mode** → the audit **still runs**, but surfaces a banner naming the unmet `BL-##` items and recommending `/qa:audit` → `/qa:setup`, and scores in **degraded mode** at a reduced Audit Confidence (un-measurable checks are marked `not measured`, never guessed).
- **Baseline unmet, `strict-baseline`** → **do not score.** Report the unmet baseline, point the user at `/qa:audit` → `/qa:setup`, and stop.

The maturity audit never establishes the baseline itself — that's QA's job. It reminds and routes.

## 3. Delegate

Invoke the **tl-agent** subagent. Pass it this instruction:

> Run a read-only project maturity audit using the `tl-maturity-audit` skill — follow `references/preflight-and-evidence.md`, `references/domain-rubric.md`, `references/stack-bindings.md`, and `references/report-template.md`. Preflight first: detect the stack(s), establish the project profile (UI? datastore? external API? blast radius?), and read `qa-output/quality-gates.md` + the active `baseline-profile.md` to determine baseline status. If the baseline is unmet: in default mode proceed in degraded mode with a banner and reduced Audit Confidence; in `strict-baseline` mode stop and route to `/qa:audit` → `/qa:setup`. Then score the four domains (Code Quality & Maintainability, Test Quality & Verifiability, Infrastructure & Operations, Security) — consuming the project's OWN enforced tooling output first (SARIF, lint, coverage from `quality-gates.md`), falling back to ephemeral Tier-1 scanners only where the project has none, and collecting attestations for what no tool can see. Score each applicable sub-area /10 on the present→enforced→passing ladder; mark inapplicable sub-areas N/A; mark un-measurable ones `not measured` (never 0, never a guess). Back every deduction with a stable `MAT-###` finding tagged `evidenced`/`attested`, with an evidence ref and `routesTo: qa` where the fix is baseline/harness work. Compute the overall score (average of applicable domains), the tier (letting any Blocker cap it), and a **separate** Audit Confidence (share of applicable checks evidenced by a tool). Build one structured data object, read a run timestamp from the system clock, write the `tl-output/maturity-<timestamp>.json` sidecar first, then generate the interactive `.html` with the bundled UTF-8-safe injector (`node assets/inject.js assets/report.html tl-output/maturity-<timestamp>.json __MATURITY_DATA__ tl-output/maturity-<timestamp>.html` — never hand-assemble the HTML) and the `.md` artifact. Change no repository files, install nothing into the repo. Return the overall score, tier, Audit Confidence + split, the domain scorecard, the top `MAT-###` findings, the baseline status, and links.
>
> Repository: `<repo or current workspace>` · Mode: `<default | strict-baseline>`

## 4. Surface the result

Present the **overall maturity score and tier**, the **Audit Confidence** (with the evidenced/attested/not-measured split — flag it if a high score rests on low confidence), the domain scorecard, and the top `MAT-###` findings (Blockers/Majors first) with their recommendations. Call out the **baseline status** up front — if it's unmet, lead with the route to `/qa:audit` → `/qa:setup`. Link to `tl-output/maturity-<timestamp>.html` (interactive) and `.md`. Keep it tight — the per-domain detail lives in the report.
