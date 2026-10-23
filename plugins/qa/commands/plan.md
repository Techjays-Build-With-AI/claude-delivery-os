---
description: Turn an approved QA audit into a concrete test-setup plan and a draft quality-gate contract. Point it at the <repo>-audit-<timestamp>-approvals.md exported from the audit report; it reloads the matching audit, plans only the approved recommendations, and drafts qa/quality-gates.md. Plans, does not build — /qa:setup builds.
argument-hint: "<path-to-<repo>-audit-<timestamp>-approvals.md>"
---

# /qa:plan

You turn the human's **approved** audit recommendations into an actionable setup plan and a first draft of the quality gates. You plan, you don't build (that's `/qa:setup`). Delegate to the **`qa-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should be the path to an **approvals file** — `<repo>-audit-<auditId>-approvals.md`, exported from the interactive report (or hand-written in the same format). This is required.

- If no path is given, ask which approvals file to plan from and stop.
- If the path doesn't resolve, say so and ask for a valid one.
- The `<auditId>` in the filename and the file's `source_audit` frontmatter is the **join key** back to the original audit JSON.

## 2. Delegate

Invoke the **qa-agent** subagent. Pass it this instruction:

> Run `/qa:plan` using the `qa-test-setup` skill (plan phase) — follow `references/setup-guide.md`. Read the approvals file at `<path>`, take its `source_audit` and `repo`, and read the full `QAF-###` detail from the matching report’s `<script id="audit-data">` block in `qa/reviews/<repo>-audit-<auditId>.html` — the same way `/dev:review` reads its round back out of the page. There is no `.json` sidecar. Plan **only** the `Adopt` rows (note `Defer` as future, ignore `Skip`), honouring the human's chosen option per finding and never inventing a choice they left open. Write `qa/<repo>-setup.md` § `## Plan`: ordered setup steps (cheap-to-stand-up-first — runner → lint/format/type → coverage → CI → fixtures/mocks → e2e), tools/versions to install, config files, CI changes, coverage thresholds, and the smoke tests that will prove each layer runs. Then draft `qa/quality-gates.md` via the `qa-quality-gates` skill (schema in its `references/quality-gate-contract.md`), marked `harness_status: Draft`. Return the plan summary, the draft gates, and any decision the human still needs to make.
>
> Approvals file: `<path>`

## 3. Surface the result

Present the **setup-plan summary**: which `QAF-###` recommendations are being implemented (with the chosen tools), the ordered steps, the target thresholds, and any deferred/open decisions. If a decision is still open, lead with the question — `/qa:setup` guesses nothing, so an unanswered decision stops the build there rather than here.

Close with this block, filled in:

```
✓ Setup plan ready — <n> QAF adopted · <n> deferred · <n> skipped
  Stack:     <runner · lint · typecheck · coverage · e2e>
  Coverage:  <current %> → <target %>
  Plan  → qa/<repo>-setup.md
  Gates → qa/quality-gates.md   (Draft — /qa:setup promotes it to Active)

Next:
  /qa:setup                    build the harness and prove it green
```

Where a decision is still open, replace the `Next:` line with the question and say that `/qa:setup` cannot start until it is answered.
