---
description: Register the delivery-os MCP servers on your machine. Runs `claude mcp add` for each canonical MCP (project-mcp, scope-mcp, task-mcp) pointing at production URLs. Pass `--staging` to ALSO register `-staging` variants; pass `--local` to ALSO register `-local` variants pointing at localhost (for MCP contributors running the Python servers themselves). Idempotent — safe to re-run.
argument-hint: "[--staging] [--local]"
---

# /delivery-os:setup

One-shot setup for delivery-os MCP servers. Replaces the 3-6 manual `claude mcp add` calls a teammate would otherwise run per machine per environment.

Without any flag → registers only **production** MCPs. That's the normal case for real work.

```
Available after setup:
  ✓ project-mcp     → production
  ✓ scope-mcp       → production
  ✓ task-mcp        → production
```

With `--staging` → also registers `-staging` variants alongside prod, so a developer/tester can pass `--staging` on any downstream command (`/jetrix:pull scope --staging`, `/ba:scope --staging`, etc.) to hit staging without touching config.

```
Available after setup --staging:
  ✓ project-mcp          → production
  ✓ scope-mcp            → production
  ✓ task-mcp             → production
  ✓ project-mcp-staging  → staging
  ✓ scope-mcp-staging    → staging
  ✓ task-mcp-staging     → staging
```

With `--local` → also registers `-local` variants pointing at `http://127.0.0.1:<port>/mcp`. Only useful for teammates who run the Python MCP servers themselves (contributors changing scope-mcp / task-mcp / project-mcp source). Combines with `--staging` — passing both registers prod + staging + local, six variants total.

```
Available after setup --local:
  ✓ project-mcp        → production
  ✓ scope-mcp          → production
  ✓ task-mcp           → production
  ✓ project-mcp-local  → http://127.0.0.1:8788/mcp
  ✓ scope-mcp-local    → http://127.0.0.1:8789/mcp
  ✓ task-mcp-local     → http://127.0.0.1:8792/mcp
```

Then commands accept `--local` the same way they accept `--staging` — e.g. `/jetrix:pull scope --local` routes tool calls to `mcp__scope-mcp-local__*` so you can iterate against your locally-running server without touching production.

## Canonical MCP list

These three MCPs are what delivery-os plugins call today. If a new MCP joins (deliverable-mcp, jira-mcp, etc.), add a row to the table below and this command handles it automatically on next run.

| Name          | Production URL                                                                | Staging URL                                                                       | Local URL                          |
|---------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|------------------------------------|
| `project-mcp` | `https://project-mcp-prod-423614975588.asia-south1.run.app/mcp`               | `https://project-mcp-staging-771850316307.asia-south1.run.app/mcp`                | `http://127.0.0.1:8788/mcp`         |
| `scope-mcp`   | `https://scope-mcp-prod-423614975588.asia-south1.run.app/mcp`                 | `https://scope-mcp-staging-771850316307.asia-south1.run.app/mcp`                  | `http://127.0.0.1:8789/mcp`         |
| `task-mcp`    | `https://task-mcp-prod-423614975588.asia-south1.run.app/mcp`                  | `https://task-mcp-staging-771850316307.asia-south1.run.app/mcp`                   | `http://127.0.0.1:8792/mcp`         |

`context-mcp` intentionally not included — delivery-os doesn't use it today. Add a row if that changes.

**Local ports** match what each MCP's `run.py` binds by default:
  - `project-mcp` → `8788` (see `project-mcp/app/config.py`)
  - `scope-mcp` → `8789` (see `scope-mcp/app/config.py`)
  - `task-mcp` → `8792` (see `task-mcp/CLAUDE.md`)

## 1. Parse the argument

```
/delivery-os:setup [--staging] [--local]
```

- No argument → **production-only mode**. Register the three prod MCPs.
- `--staging` → register prod AND `<name>-staging` variants pointing at staging URLs.
- `--local` → register prod AND `<name>-local` variants pointing at localhost.
- `--staging --local` → all three sets — prod, staging, and local (six variants).
- Anything else → print the usage block above and stop.

## 2. Check what's already registered

Run ONE Bash call to see current state:

```bash
claude mcp list 2>&1
```

Parse the output for each canonical MCP name (and their `-staging` variants if the `--staging` flag was passed). Record which are already registered. Skip re-adding those — this makes the command idempotent (safe to re-run) and lets a teammate rebalance their config without conflict.

## 3. Register the missing ones

For each MCP that is NOT already registered, run **one Bash call** in this shape:

```bash
claude mcp add --transport http <name> <url>
```

`--transport http` is required — the delivery-os MCPs are HTTP streamable-http servers, not stdio processes.

Concrete calls the command will make (production-only mode):

```bash
claude mcp add --transport http project-mcp https://project-mcp-prod-423614975588.asia-south1.run.app/mcp
claude mcp add --transport http scope-mcp   https://scope-mcp-prod-423614975588.asia-south1.run.app/mcp
claude mcp add --transport http task-mcp    https://task-mcp-prod-423614975588.asia-south1.run.app/mcp
```

If `--staging` was passed, ALSO run:

```bash
claude mcp add --transport http project-mcp-staging https://project-mcp-staging-771850316307.asia-south1.run.app/mcp
claude mcp add --transport http scope-mcp-staging   https://scope-mcp-staging-771850316307.asia-south1.run.app/mcp
claude mcp add --transport http task-mcp-staging    https://task-mcp-staging-771850316307.asia-south1.run.app/mcp
```

If `--local` was passed, ALSO run:

```bash
claude mcp add --transport http project-mcp-local http://127.0.0.1:8788/mcp
claude mcp add --transport http scope-mcp-local   http://127.0.0.1:8789/mcp
claude mcp add --transport http task-mcp-local    http://127.0.0.1:8792/mcp
```

Skip any of the nine that the pre-check in §2 flagged as already registered.

## 4. First OAuth handshake

The FIRST invocation of any tool from a newly-registered MCP triggers Claude Code's OAuth flow — the browser opens, teammate signs in to Jetrix, consent, token cached locally. All three prod MCPs share the same auth server, so one sign-in covers everything. Nothing this command does; happens automatically the first time a `mcp__project-mcp__*`, `mcp__scope-mcp__*`, or `mcp__task-mcp__*` tool is called.

If `--staging` was passed, the staging MCPs share a **separate** auth server (different Cloud Run environment), so the FIRST staging call also triggers a sign-in. One extra browser flow per teammate per environment — not per command.

If `--local` was passed, each local MCP has its OWN OAuth server bound to `127.0.0.1:<port>` — the first tool call on each local variant triggers a browser flow against localhost. That's normal for local dev. Skip local setup on machines that aren't running the Python servers themselves.

## 5. Report

Print a summary that mirrors the "Available after setup" block from the top of this file, tagged with:

- `+ added`     — MCP was newly registered by this run
- `= already`   — MCP was already registered; skipped
- `✗ failed`    — `claude mcp add` returned non-zero. Print the CLI's error message on the same line and continue with the rest — never abort halfway.

Example (production-only mode, second run):

```
Delivery-OS MCP setup complete.

  = project-mcp     (production)
  = scope-mcp       (production)
  + task-mcp        (production)      ← newly added

Next: use commands normally (e.g. /jetrix:init, /ba:scope). No further setup needed.
```

Example (`--staging` mode, first run):

```
Delivery-OS MCP setup complete.

  + project-mcp             (production)
  + scope-mcp               (production)
  + task-mcp                (production)
  + project-mcp-staging     (staging)
  + scope-mcp-staging       (staging)
  + task-mcp-staging        (staging)

Next: normal commands use production. Pass `--staging` on any command to
hit staging (e.g. /jetrix:pull scope --staging).
```

Example (`--local` mode, first run):

```
Delivery-OS MCP setup complete.

  + project-mcp           (production)
  + scope-mcp             (production)
  + task-mcp              (production)
  + project-mcp-local     (http://127.0.0.1:8788/mcp)
  + scope-mcp-local       (http://127.0.0.1:8789/mcp)
  + task-mcp-local        (http://127.0.0.1:8792/mcp)

Next: start your local Python MCP servers (`python run.py` in each repo),
then pass `--local` on any command to route to them (e.g.
/jetrix:pull scope --local).
```

If ANY row failed, print a short note at the bottom telling the teammate to retry that specific line, e.g. `claude mcp add --transport http task-mcp <url>`. Do not attempt an automatic retry — a failure is usually a config or network issue the teammate has to see.

## What this command does NOT do

Kept deliberately narrow:

- **No environment switching.** If you need to move a machine from prod to staging or back, use `claude mcp remove <name>` then re-run this command. Adding a `switch` command would just wrap those two steps — not worth a separate command yet.
- **No status readout.** `claude mcp list` already prints what's registered. Not worth a wrapper.
- **No un-register / cleanup.** `claude mcp remove <name>` is a one-liner and covers rarely-used cleanup needs.
- **No project-level `.mcp.json` writing.** This command registers MCPs at the user scope (default `claude mcp add`), which is what teammates want — same MCPs across every workspace they open on their machine. If you need per-project overrides, use `claude mcp add --scope project <name> <url>` manually.

If any of those turn out to be daily pain, add a follow-up command later. For now: one command, one flag, two paths.
