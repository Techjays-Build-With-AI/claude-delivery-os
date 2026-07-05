---
description: Turn an approved QA audit into a concrete test-setup plan and a draft quality-gate contract. Point it at the test-audit-<timestamp>-approvals.md exported from the audit report; it reloads the matching audit, plans only the approved recommendations, and drafts qa-output/quality-gates.md. Plans, does not build — /qa:setup builds.
argument-hint: "<path-to-test-audit-<timestamp>-approvals.md>"
---

# /qa:plan

You turn the human's **approved** audit recommendations into an actionable setup plan and a first draft of the quality gates. You plan, you don't build (that's `/qa:setup`). Delegate to the **`qa-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should be the path to an **approvals file** — `test-audit-<auditId>-approvals.md`, exported from the interactive report (or hand-written in the same format). This is required.

- If no path is given, ask which approvals file to plan from and stop.
- If the path doesn't resolve, say so and ask for a valid one.
- The `<auditId>` in the filename and the file's `source_audit` frontmatter is the **join key** back to the original audit JSON.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run `/qa:plan` using the `qa-test-setup` skill (plan phase) — follow `references/setup-guide.md`. Read the approvals file at `<path>`, take its `source_audit`, and reload `qa-output/test-audit-<auditId>.json` for the full `QAF-###` detail. Plan **only** the `Adopt` rows (note `Defer` as future, ignore `Skip`), honouring the human's chosen option per finding and never inventing a choice they left open. Write `qa-output/test-setup-plan.md`: ordered setup steps (cheap-to-stand-up-first — runner → lint/format/type → coverage → CI → fixtures/mocks → e2e), tools/versions to install, config files, CI changes, coverage thresholds, and the smoke tests that will prove each layer runs. Then draft `qa-output/quality-gates.md` via the `qa-quality-gates` skill (schema in its `references/quality-gate-contract.md`), marked `harness_status: Draft`. Return the plan summary, the draft gates, and any decision the human still needs to make.
>
> Approvals file: `<path>`

## 3. Surface the result

Present the **setup-plan summary**: which `QAF-###` recommendations are being implemented (with the chosen tools), the ordered steps, the target thresholds, and any deferred/open decisions. Link to `qa-output/test-setup-plan.md` and the draft `qa-output/quality-gates.md`. Tell the user to review, then run `/qa:setup` to build the harness. If a decision is still open, lead with the question.
