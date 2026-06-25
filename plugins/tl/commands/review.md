---
description: Review a technical specification (architecture / system design / HLD / SRS) document for an applied AI system and produce a scored review report. Pass the document path or link; the TL agent scores each area out of 10 with concrete issues and suggestions and writes a timestamped interactive spec-review-<timestamp>.html plus the matching .md artifact to tl-output/ (so repeated runs never overwrite each other).
argument-hint: "<path-or-link-to-spec-doc> [out=<output-prefix>]"
---

# /tl:review

You are the entry point for a Technical Lead specification review. Parse the arguments and **delegate the actual review to the `tl-agent` subagent**, which runs in its own context and does the document-heavy reading and scoring.

## 1. Parse arguments

`$ARGUMENTS` should contain:
- A **document reference** — a path to a `.md` / `.docx` / `.pdf` spec, or a link (e.g. Google Drive). This is required.
- An optional **`out=<prefix>`** to override the report location/prefix (default `tl-output/spec-review`; beside the document if there's no Delivery OS workspace). A run timestamp is **always** appended, so the actual files are `<prefix>-<timestamp>.html` and `<prefix>-<timestamp>.md` and repeated reviews never collide.

If no document is given, ask the user which spec to review and stop. If the path doesn't resolve, say so and ask for a valid one rather than guessing.

## 2. Delegate

Invoke the **tl-agent** subagent with the document reference and output path. Pass it this instruction:

> Review the technical specification at `<doc-ref>` using the `tl-spec-review` skill. Read the whole document first. Determine whether the system uses an LLM/AI and whether it spans multiple systems, then score each applicable review area out of 10 — Overview, Architecture & System Design, Feature Flows & System Sequencing, Data Schema, API Contracts, Libraries; and (if AI is involved) Observability & Traceability, Evals, Feedback Loops, AI Compliance; plus Infrastructure, CI/CD & Release Management, and Cost Projection. Back every deduction with a finding (severity Blocker/Major/Minor/Nit) and a concrete suggestion, note real strengths, compute the overall score and readiness verdict, read a run timestamp (`YYYY-MM-DD-HHMMSS`) from the system clock, and write both the interactive `<prefix>-<timestamp>.html` (inject the review JSON into the bundled `assets/report.html`) and the `<prefix>-<timestamp>.md` artifact (default prefix `tl-output/spec-review`) per the report template. Mark non-applicable areas N/A with a one-line reason. Return the executive summary, scorecard, and links to both timestamped files.

## 3. Surface the result

When the agent returns, present its **executive summary and scorecard**: the overall score, the readiness verdict, the scorecard table, and the top 3–5 gating findings (Blockers/Majors first) with their suggested fixes. Link to both report files and point the user to `spec-review.html` as the interactive one to open in a browser. Keep it tight — the per-area detail lives in the report.
