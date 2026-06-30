---
description: Review a BA scope document the way a paranoid Business Analyst would before estimate or sign-off. Pass the scope path (defaults to ba-output/scope.md); the BA agent breaks it down feature by feature, interrogates each for under-specification, validates it against the client's shared examples, scores each feature out of 10, and writes a timestamped interactive scope-review-<timestamp>.html dashboard plus the matching .md and .json to ba-output/scope-reviews/ (so repeated runs never overwrite each other).
argument-hint: "[<path-to-scope-doc>] [out=<output-prefix>]"
---

# /ba:review

You are the entry point for a Business Analyst **scope review**. Parse the arguments and **delegate the actual review to the `ba-agent` subagent**, which runs in its own context and does the document-heavy reading, interrogation, and scoring.

## 1. Parse arguments

`$ARGUMENTS` may contain:
- An optional **scope document reference** — a path to a `.md` / `.docx` / `.pdf` scope, or a link. If omitted, default to `ba-output/scope.md` when a Delivery OS workspace is present.
- An optional **`out=<prefix>`** to override the report location/prefix (default `ba-output/scope-reviews/scope-review`; beside the document if there's no Delivery OS workspace). A run timestamp is **always** appended, so the files are `<prefix>-<timestamp>.{html,md,json}` and repeated reviews never collide.

If no scope can be located (no path given and no `ba-output/scope.md`), ask the user which scope to review and stop. If a given path doesn't resolve, say so and ask for a valid one rather than guessing.

## 2. Delegate

Invoke the **ba-agent** subagent with the scope reference and output path. Pass it this instruction:

> Run a **scope review** of the scope document at `<doc-ref>` using the `ba-scope-review` skill — act as a paranoid Business Analyst. Read the whole scope first, then load the scope knowledge base (`ba-output/example-register.md` and the other registers, `clarification-log.md`, `contradiction-log.md`, `shared-context/`) when a workspace exists. Decompose the scope into features/modules and, for each, judge coverage across the nine Techjays D&D dimensions (current→future, in/out scope, functional reqs, AI/automation, business rules, data fields, integrations, exceptions, acceptance), interrogate every under-specified point into concrete questions (e.g. "login screen" → which auth method? email vs social vs OTP vs SSO? personal vs corporate email? verification, lockout, MFA, session, roles?), and validate the feature against the client's examples (Pass/Partial/Conflict/No-examples, citing EX ids). Score each feature out of 10 on coverage depth, give every question a severity (Blocker/Major/Minor/Nit), compute the overall score and scope-readiness verdict (any Blocker caps it), read a run timestamp (`YYYY-MM-DD-HHMMSS`) from the system clock, and write the interactive `<prefix>-<timestamp>.html` (inject the review JSON into the bundled `assets/report.html`), the `<prefix>-<timestamp>.md` artifact, and the `<prefix>-<timestamp>.json` sidecar (default prefix `ba-output/scope-reviews/scope-review`) per the report template. Return the executive summary, the feature scorecard, and links to the files.

## 3. Surface the result

When the agent returns, present its **executive summary and feature scorecard**: the overall score, the scope-readiness verdict, the scorecard table, and the top 3–5 gating questions (Blockers/Majors first) with the scope addition each needs. Link to the report files and point the user to `scope-review-<timestamp>.html` as the interactive dashboard to open in a browser — and note they can respond to each question inside it and click "Export responses" to drive `/ba:resolve`. Keep it tight — the per-feature detail lives in the report.
