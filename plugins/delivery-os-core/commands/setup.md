---
description: Register the delivery-os MCP servers on your machine — always under their canonical short names (project-mcp, scope-mcp, task-mcp). No flag → prod URLs. `--staging` → staging URLs. `--local` → localhost. One environment per machine; to switch, `claude mcp remove <name>` then re-run. Idempotent — safe to re-run.
argument-hint: "[--staging | --local]"
---

# /delivery-os:setup

One-shot setup for delivery-os MCP servers. Replaces the three manual `claude mcp add` calls a teammate would otherwise run per machine.

**One name, one URL.** The delivery-os plugins call `mcp__project-mcp__*`, `mcp__scope-mcp__*`, `mcp__task-mcp__*` — always the short name. This command registers those three names and points them at whichever URL matches the flag. A machine picks **one** environment at a time (prod / staging / local); switching means removing and re-registering.

## Modes

```
/delivery-os:setup            → point short names at PRODUCTION      (normal case)
/delivery-os:setup --staging  → point short names at STAGING         (testers / QA)
/delivery-os:setup --local    → point short names at localhost:8788+ (MCP contributors)
```

Only one of `--staging` or `--local` at a time. `--staging --local` is rejected.

## Canonical MCP list

| Name          | Production URL                                                                | Staging URL                                                                       | Local URL                          |
|---------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|------------------------------------|
| `project-mcp` | `https://project-mcp-prod-423614975588.asia-south1.run.app/mcp`               | `https://project-mcp-staging-771850316307.asia-south1.run.app/mcp`                | `http://127.0.0.1:8788/mcp`         |
| `scope-mcp`   | `https://scope-mcp-prod-423614975588.asia-south1.run.app/mcp`                 | `https://scope-mcp-staging-771850316307.asia-south1.run.app/mcp`                  | `http://127.0.0.1:8789/mcp`         |
| `task-mcp`    | `https://task-mcp-prod-423614975588.asia-south1.run.app/mcp`                  | `https://task-mcp-staging-771850316307.asia-south1.run.app/mcp`                   | `http://127.0.0.1:8792/mcp`         |

`context-mcp` intentionally not included — delivery-os doesn't call it today.

**Local ports** match what each MCP's `run.py` binds by default:
  - `project-mcp` → `8788`
  - `scope-mcp` → `8789`
  - `task-mcp` → `8792`

## 1. Parse the argument

```
/delivery-os:setup [--staging | --local]
```

- No argument → **production**. Register the three names against prod URLs.
- `--staging` → **staging**. Register the three names against staging URLs.
- `--local` → **local**. Register the three names against localhost URLs.
- `--staging --local` → reject with `Pick one: --staging or --local, not both.` and stop.
- Anything else → print the modes block above and stop.

Pick the URL set for the mode and hold it as `target_urls = { "project-mcp": "...", "scope-mcp": "...", "task-mcp": "..." }`.

## 2. Check what's already registered

Run ONE Bash call:

```bash
claude mcp list 2>&1
```

Parse the output. For each canonical name, record:
- **registered + URL matches the mode's target** → skip (`= already at <mode>`)
- **registered but URL is a DIFFERENT environment** → skip and add a warning to the final report (`⚠ project-mcp is registered at STAGING, but this run targeted PRODUCTION — leave it as-is, or remove and re-run`)
- **not registered** → add (`+ added <mode>`)

**Do NOT re-point a name that already resolves to a different environment.** Removing an existing registration would break active sessions and lose the cached OAuth token; the teammate has to make that call explicitly with `claude mcp remove`.

## 3. Register the missing ones

For each canonical name whose row in §2 said `+ added`, run one Bash call:

```bash
claude mcp add --transport http <name> <url>
```

`--transport http` is required — the delivery-os MCPs are HTTP streamable-http servers, not stdio.

Concrete calls in **production** mode:

```bash
claude mcp add --transport http project-mcp https://project-mcp-prod-423614975588.asia-south1.run.app/mcp
claude mcp add --transport http scope-mcp   https://scope-mcp-prod-423614975588.asia-south1.run.app/mcp
claude mcp add --transport http task-mcp    https://task-mcp-prod-423614975588.asia-south1.run.app/mcp
```

`--staging` and `--local` use the same three names against the staging / local URLs in the table above.

## 4. Kick off the OAuth handshake

`claude mcp add` only stores a name → URL row in `~/.claude.json`. It does NOT sign the teammate in. The first tool call from each MCP triggers a browser-based OAuth flow — that's when the actual Jetrix login happens and a token gets cached locally.

**Do this next, in this exact order:**

```
1. In THIS Claude Code session, run one MCP tool to force the handshake.
   The safest one is a read that has no side effects — pick either:

     /jetrix:init             (tries project_list_solutions → triggers OAuth)
     mcp__project-mcp__project_list_solutions   (direct tool call)

2. A browser tab will open pointing at the MCP's authorization server:
     Production →  project-mcp-prod-423614975588.asia-south1.run.app
     Staging    →  project-mcp-staging-771850316307.asia-south1.run.app
     Local      →  127.0.0.1:8788

3. Sign in to Jetrix with the teammate's normal credentials.
   Grant the consent screen — this authorizes Claude Code to call the MCP
   on the teammate's behalf. Token gets cached in ~/.claude.json.

4. Repeat steps 1-3 for scope-mcp and task-mcp:
     mcp__scope-mcp__scope_list_documents solution_id=<anything>
     mcp__task-mcp__list_all_lists solution_id=<anything>

   (In practice, running /jetrix:project-setup end-to-end touches all
   three MCPs — one setup command triggers all three handshakes back
   to back, so a teammate rarely notices the split.)
```

**Only ONE sign-in per MCP per environment.** After that the cached token gets reused until it expires (long-lived by design). Second and third runs of any command hit the MCP silently — no browser.

**Switching envs re-triggers OAuth.** Staging has a separate auth server from prod (different Cloud Run environment); switching a machine via remove + re-setup drops the cached token, so the next tool call opens the browser again. Same for `--local` (each local MCP binds its own OAuth server on 127.0.0.1).

**If the browser doesn't open** (headless machine, sandbox, remote SSH): Claude Code prints an auth URL in the terminal instead. Copy it, open on another device with a browser, sign in, paste the resulting code back into Claude Code's prompt. Same three MCPs, same three handshakes.

**Something failed silently?** Check `claude mcp list` — a `! Needs authentication` next to a name means the token isn't cached yet. Run any tool that hits that MCP and complete the browser flow.

## 5. Report

Print a summary tagged with:

- `+ added`     — newly registered by this run
- `= already`   — already at the requested URL; skipped
- `⚠ mismatch`  — already registered but at a different environment; NOT touched
- `✗ failed`    — `claude mcp add` returned non-zero. Print the CLI's error message on the same line and continue with the rest — never abort halfway.

Example (production, first run, clean machine):

```
Delivery-OS MCP setup complete — production.

  + project-mcp     (production)
  + scope-mcp       (production)
  + task-mcp        (production)

NEXT — sign in to each MCP (one-time per environment):

  A browser tab will open the first time each MCP is called. Sign in
  to Jetrix, grant consent, and Claude Code caches the token. After
  that, you're done.

  Fastest way: run /jetrix:project-setup — it touches all three MCPs
  back-to-back, so all three OAuth flows fire in one session.

  Or trigger them one by one:
    mcp__project-mcp__project_list_solutions
    mcp__scope-mcp__scope_list_documents solution_id=<any>
    mcp__task-mcp__list_all_lists solution_id=<any>

  Verify anytime with:  claude mcp list
  (Names showing `! Needs authentication` still need the browser step.)
```

Example (production request, but names are already registered against staging):

```
Delivery-OS MCP setup — NOTHING CHANGED.

  ⚠ project-mcp   already registered → STAGING (this run targeted production)
  ⚠ scope-mcp     already registered → STAGING (this run targeted production)
  ⚠ task-mcp      already registered → STAGING (this run targeted production)

The short names are already registered but point at a different environment
than this run targeted. That was intentional on the previous setup, so this
command left them alone — swapping URLs would drop the cached OAuth token
and could break active work.

To repoint this machine at production, run:

  claude mcp remove project-mcp
  claude mcp remove scope-mcp
  claude mcp remove task-mcp
  /delivery-os:setup

To confirm the current mode is what you want, leave them as-is.
```

Example (`--staging`, second run, all good):

```
Delivery-OS MCP setup complete — staging.

  = project-mcp     (already at staging)
  = scope-mcp       (already at staging)
  = task-mcp        (already at staging)

Next: normal commands use the staging environment (that's what these MCPs
resolve to on this machine). If `claude mcp list` shows
`! Needs authentication` on any name, run the corresponding tool once
to trigger the OAuth browser flow (see §4).
```

If any row failed (`✗`), print a short note at the bottom telling the teammate to retry that specific line, e.g. `claude mcp add --transport http task-mcp <url>`. Do not automatically retry — a failure is usually a config or network issue the teammate has to see.

## What this command does NOT do

- **Environment switching by force.** If §2 finds a name already registered at a different environment, this command leaves it alone. Switching means `claude mcp remove <name>` then re-run — that's a one-liner but it's the teammate's call, because it drops the cached OAuth token for that MCP.
- **Suffixed variants (`project-mcp-staging`, `scope-mcp-local`).** Old iterations of this doc created those; they were dead weight because the plugins only ever call `mcp__project-mcp__*` (the bare name). Removed.
- **Status readout.** `claude mcp list` already prints what's registered. Not worth a wrapper.
- **Un-register / cleanup.** `claude mcp remove <name>` is a one-liner.
- **Project-scope registration.** This command registers at **user scope** (default `claude mcp add`), so the MCPs are available in every workspace on the machine. If you're running the command inside a workspace, watch out for `--scope project` being the effective default in some Claude Code versions — pass `--scope user` explicitly if the result lands under a project block in `~/.claude.json`.
