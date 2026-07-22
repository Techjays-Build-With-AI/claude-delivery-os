---
description: Evaluate how efficiently you (or your team member) use Claude Code and generate an interactive HTML efficiency report. Reads the silently-collected session telemetry in ~/.claude/metrics/, infers each session's persona, judges upfront context quality and re-prompt friction against that persona's best practices, computes an adaptive 0–100 efficiency score with concrete strengths and improvement areas, and opens a dark-themed dashboard at ~/claude-usage-report.html. Read-only on telemetry; changes no code and runs no delivery work.
argument-hint: "[since=<YYYY-MM-DD>] [limit=<n most-recent sessions>] [session=<session-id>] [no-open]"
---

# /dev:usage-eval

You produce a **Claude Code usage & efficiency report** for the person running the command. This is an analytics/coaching command — it is independent of the feature-delivery loop and does **not** delegate to the dev-agent. Drive it directly with the **`dev-usage-eval`** skill.

## 1. Parse arguments

`$ARGUMENTS` are all optional:

- **`since=<YYYY-MM-DD>`** — only evaluate sessions created on/after this date.
- **`limit=<n>`** — evaluate only the `n` most recent sessions.
- **`session=<session-id>`** — evaluate a single session (the log file name in `~/.claude/metrics/`).
- **`no-open`** — write the report but don't try to open a browser (pass `--no-open` to the builder).

With no arguments, evaluate **all** sessions found in `~/.claude/metrics/`.

## 2. Run the evaluation

Invoke the **`dev-usage-eval`** skill. Following it:

1. Read the telemetry logs under `~/.claude/metrics/*.json` (written silently by the plugin's telemetry hooks). If the directory is missing or empty, tell the user no telemetry has been collected yet — the hooks accumulate data as they use Claude Code, so they should run a few normal sessions first — and stop. Do **not** fabricate sessions.
2. For each in-scope session, reconstruct the prompt/tool/stop sequence, infer the persona, and judge upfront context quality, iteration friction (good problem-solving vs. vague-instruction rework), and an adaptive 0–100 score graded against that persona's best practices. Give each session a letter grade and one line of feedback.
3. Assemble the evaluation payload (`score`, `primaryPersona`, `sessionsEvaluated`, `generatedAt`, `strengths[]`, `areasForImprovement[]`, `sessionSummary[]`).
4. Render the dashboard by running the builder (use the `--file` form for a long payload to avoid shell-quoting issues):

   ```bash
   node "$CLAUDE_PLUGIN_ROOT/scripts/build-dashboard.js" --file /tmp/usage-eval-payload.json
   ```

   Add `--no-open` if the user passed `no-open`.

## 3. Surface the result

Confirm the report was written to `~/claude-usage-report.html` and give the headline: overall efficiency score, primary persona, number of sessions analyzed, and the single highest-leverage improvement. Keep it tight — the detail lives in the report.
