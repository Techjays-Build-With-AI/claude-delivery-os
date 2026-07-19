---
description: Publish local work up to Jetrix (the source of truth). The deliberate "commit" half of the working-copy model — the user does all analysis locally in .jetrix/cache/, and when they are satisfied, pushes it to Jetrix. Idempotent by stable id (upsert, never duplicate), transactional (propose → preview a diff → commit), and safe (pull-before-push so it never silently overwrites a change made in Jetrix). Writes only through the Jetrix MCP. This is the ONLY path that mutates Jetrix from local.
argument-hint: "[--scope] [--features] [--context] [--dry-run] [--yes]"
---

# /delivery-os:jetrix-push

You are **publishing local work to Jetrix**. Everything the user produced locally (scope, registers, feature breakdown, technical context) lives in `.jetrix/cache/` as a working copy; this command commits the changed items up to Jetrix, which is the source of truth everyone else reads. Pushing is a **deliberate act** — treat it like a code commit, not an autosave. Read the `delivery-os-conventions` skill (§1.b *Jetrix binding*) first if it is not already in context.

## 1. Preconditions

- The repo must be bound (`.jetrix/project.json` with a resolved `project_id`) and the **Jetrix MCP** connected. If not, stop and say so — a push cannot fabricate a target.
- Never write via curl/scripts — only the Jetrix MCP write tools. (Bind the exact tool names in `delivery-os-conventions` §1.b once the Jetrix MCP is confirmed; design for a `propose_write` → `commit_write` / `cancel_write` transactional shape.)

## 2. Parse scope

`$ARGUMENTS` selects what to publish. **No args = push all changed sections.**

| Flag | Publishes |
|------|-----------|
| *(none)* | Every changed section: `scope` (+ registers), `features`, `context`. |
| `--scope` / `--features` / `--context` | Just that section. |
| `--dry-run` | Do steps 3–4 and print the diff, then **stop without writing**. |
| `--yes` | Skip the interactive confirmation in step 5 (for non-interactive/CI use). Use with care. |

## 3. Pull-before-push (conflict safety)

Before computing anything to write, do an **incremental pull** (`/delivery-os:jetrix-pull` on the selected sections) to bring the cache's baseline current with Jetrix. Then, for each local item, compare three states using the manifest `id_map`:
- **local** (the working copy), **base** (what was last pulled, per the cached hash), **remote** (Jetrix now).

Classify each item:
- *local changed, remote unchanged* → **safe to push** (update).
- *new local id with no `jetrix_id`* → **safe to push** (create).
- *remote changed, local unchanged* → nothing to push (the pull already updated the cache).
- *both changed* → **CONFLICT**. Do not overwrite. List these items and stop (or, if `--yes`, skip only the conflicted items and report them). Resolving conflicts is a human decision — never silently clobber a Jetrix edit.

## 4. Build the transaction (upsert by stable id)

For every safe-to-push item, prepare a Jetrix write keyed by its **stable local id** (`INTK-AI-02`, `WF-001`, `FEAT-SUP-001`, `PAGE-…`, `EP-…`, `ENT-…`), which is stored on the Jetrix record as an external key:
- `jetrix_id` present in `id_map` → **update** that record.
- no `jetrix_id` → **create**, and record the returned `jetrix_id` back into `id_map`.

Map local records to their Jetrix object types (requirement, workflow, business-rule, data-entity, integration, example, assumption, clarification, feature, page, endpoint, entity, decision), preserving relationships (feature → requirements, endpoint → entity, etc.) and source citations. The rendered `scope.md` is a projection — push the underlying **records**, not the document blob.

## 5. Preview and commit

Open the write transaction with `propose_write` and show the user a compact **diff**: counts and identities of creates/updates per section (e.g. "Scope: +3 requirements, ~1 workflow (WF-002); Features: ~FEAT-SUP-001"), plus any conflicts held back. Then:
- `--dry-run` → print the diff and **cancel** the transaction. Write nothing.
- otherwise → ask for confirmation (unless `--yes`), then `commit_write`. On any error, `cancel_write` and report — never leave a half-applied push.

## 6. After commit

Update the manifest: set each pushed item's `hash`/`base` to the just-committed state and its `jetrix_id`, and stamp the section `fetched_at`. Print what was created/updated per section, the new Jetrix state, and any conflicts the user still needs to resolve. Jetrix is now the published truth for those items; downstream agents will read them on their next pull.

Keep it **idempotent**: pushing again with no local changes must be a no-op (every item already maps and matches).
