## Stage: `implementation` (implemented — uses task-mcp)

TL runs this AFTER `/tl:compose` writes per-feature `tl-plan.md` files (the buildable 9-section technical spec). Each MC Task's `implementationDetails` gets **that one file's body verbatim** — no concatenation, no unit-file walking, no manifest degradation. `/tl:compose` is responsible for producing a self-contained document sized under Mission Control's 60 KB cap; this stage only ships what compose produced. Status flips to `READY_FOR_DEV`. Does NOT touch BA-owned body fields.

If a feature folder has no `tl-plan.md`, this stage skips it with a clear message pointing the user at the right recovery command. Two cases:

- **This teammate hasn't composed yet locally** → run `/tl:compose <slug>` to generate `tl-plan.md` from the local graph.
- **The feature's `tl-plan.md` was pushed by a different teammate and this workspace hasn't pulled it** → run `/jetrix:pull task <ref>` (or `/jetrix:pull scope`) to fetch the composed plan from Jetrix.

Never compose silently, never guess, never fall back to the old concat-of-units mode.

### 2. Assemble every feature — ONE Bash+Python call

**Do NOT `Read` feature files individually.** Invoke the plugin's script — it walks `features/*/`, extracts `feature_id` + `jetrix_task_object_id` from each feature.md, strips frontmatter + CRLF + leading blanks from tl-plan.md, applies the 60 KB size gate, detects blocker signals, skips features whose hash matches `sync-state.implementation_hash`, and emits ONE JSON blob ready for `feature_update_implementation`.

```bash
ASSEMBLED="<workspace_root>/.jetrix/cache/.push-implementation.json"
mkdir -p "$(dirname "$ASSEMBLED")"

python "$CLAUDE_PLUGIN_ROOT/scripts/assemble-implementation.py" \
  --project-root "<absolute project_root>" \
  --sync-state   "<workspace_root>/.jetrix/cache/sync-state.json" \
  --output       "$ASSEMBLED"
```

Claude reads the ONE JSON blob:

```json
{
  "features": [
    {"feature_id": "FEAT-CLSF-01", "slug": "...", "task_object_id": "6a61...",
     "implementation_details": "...", "status": "readyForDev",
     "_local_impl_hash": "...", "_local_size": 14392}
  ],
  "skipped":  [{"slug": "foo", "reason": "no-tl-plan"|"no-feature-id"|"no-task-object-id"|"size-cap (67300 > 60000)"|"unchanged (hash=abcd...)"}],
  "warnings": [{"slug": "bar", "message": "58210 chars, near 60000 cap"}],
  "halts":    []
}
```

Every check the old §3/§4/§4a spec used to walk in Claude context is done inside the script:
  - Missing `tl-plan.md` / `feature_id` / `jetrix_task_object_id` → surfaced as `skipped.reason`
  - Body integrity — frontmatter/CRLF strip + leaked-frontmatter-key detection (surfaced as warnings)
  - 60 KB cap → surfaced as `skipped.reason = size-cap (...)`; the size-warn threshold (55K-60K) → warning
  - Skip-unchanged via `sync-state[tasks/<feature_id>].implementation_hash` vs freshly-computed body hash
  - Blocker-aware status — open-questions Impact starts with 'Blocks', dependencies unavailable/blocked/TBD, `[HELD]` in tl-plan.md → `status: "blocked"`; else `"readyForDev"`

### 3. Report skips + warnings before pushing

For each row in `skipped` and `warnings`, print the matching user-facing message. Emit these **before** the MCP call so the user sees them regardless of whether the MCP call runs:

- `reason == "no-tl-plan"` → `[skip] features/<slug>/ — no tl-plan.md. Run /tl:compose <slug> or /jetrix:pull task <slug>.`
- `reason == "no-feature-id"` → `[skip] features/<slug>/ — feature.md has no feature_id frontmatter. Re-run /ba:features.`
- `reason == "no-task-object-id"` → `[skip] features/<slug>/ — feature.md has no jetrix_task_object_id. Run /jetrix:push feature first.`
- `reason.startswith("size-cap")` → `[skip] <slug> — tl-plan.md is <N> chars, cap is 60000. Split the feature via /tl:compose or /ba:features and re-run.`
- `reason.startswith("unchanged")` → `[skip] TASK-<n> <slug> — unchanged (hash=<sha16>)` (task number pulled from sync-state if needed for the report)
- Any warning → `[warn] <slug> — <message>`

If `features` is empty (nothing needs push), print `nothing to push` and stop.

### 5. Single MCP call — use the dedicated implementation tool

**Use `feature_update_implementation`, NOT `feature_upsert_bundle`.** This tool's Pydantic schema accepts ONLY `task_object_id`, `implementation_details`, and `status`. It ignores every other field, so it is IMPOSSIBLE to accidentally clobber BA-owned tabs (description / businessRules / acceptanceCriteria / assumptions / nfrs / testScenarios). Do not fall back to `feature_upsert_bundle` for implementation pushes — that tool accepts BA fields and could wipe them if empty strings sneak in.

```
mcp__task-mcp__feature_update_implementation(
  solution_id = <from project.json>,
  features = [
    {
      feature_id: "FEAT-CLSF-01",                   // reporting only
      slug: "document-classification-extraction",   // reporting only
      task_object_id: "<from feature.md>",           // REQUIRED — this tool never creates
      implementation_details: "<tl-plan.md body from step 3b/c>",
      status: "<'blocked' if any blocker signal fires per 4a; else 'readyForDev'>"
    }
  ]
)
```

Response per feature: `{slug, feature_id, task_object_id, task_number, version, ok}`.

Missing `task_object_id` returns `{ok: false, error: "…run /jetrix:push feature first"}` — the tool never creates tasks.

**ALWAYS check the per-feature `ok` field — never infer success from the call returning.** A rejected write still returns a normal-looking response envelope with `updated: 0` and `ok: false` on the individual row. Report `ok:false` rows as failures and leave their sync-state untouched so the next push retries them.

> **Known task-mcp defects (as of 2026-07-27) — do not misread these as your own failure:**
> - **Read tools return empty for tasks that demonstrably exist.** `feature_pull_bundle`, `feature_list_bundle` and `get_task_by_id_or_number` all return nothing for a Solution whose tasks are writable by object id; a raw-oid lookup fails upstream with `"Please select a solution to continue"`, suggesting a missing solution-context header on the read path. **Do not use a read tool to verify a push, and do not treat an empty read as evidence the write failed.** Verify from the write response's `ok`/`updated`/`task_number` instead — `task_number` is echoed from the stored record, so its presence proves the task was found.
> - **`version` comes back `null`** on every write, where scope-mcp returns an integer. Does not appear to affect the write; record `null` in sync-state rather than inventing a number.

### 6. Apply response — sync-state update (ONE Bash+Python call)

`feature_update_implementation` returns all rows in one response, so sync-state can safely be batched to the end. Dump the response to disk and invoke the apply script — it updates `implementation_hash` per `tasks/<feature_id>` entry, merge-safe.

```bash
RESPONSES="<workspace_root>/.jetrix/cache/.push-implementation-responses.json"
mkdir -p "$(dirname "$RESPONSES")"

cat > "$RESPONSES" <<'JETRIX_RESP_EOF'
[
  {"feature_id":"FEAT-CLSF-01","slug":"...","task_object_id":"6a61...","task_number":11,"version":null,"ok":true,"_local_impl_hash":"<sha256>"},
  ...one row per feature from the MCP response (echo _local_impl_hash back from the payload)...
]
JETRIX_RESP_EOF

python "$CLAUDE_PLUGIN_ROOT/scripts/apply-implementation-responses.py" \
  --responses  "$RESPONSES" \
  --sync-state "<workspace_root>/.jetrix/cache/sync-state.json"

rm -f "$RESPONSES"
```

**Report format.** Print progress per feature (constructed from the response + `skipped`/`warnings` from step 2's assemble output):

```
[1/10] TASK-11 opening-balance-import       pushed   (12.4 KB, hash=<sha16>)
[2/10] TASK-14 leave-balance-administration skip     (unchanged, hash=<sha16>)
[3/10] TASK-16 leave-request-submission     pushed   (14.1 KB, hash=<sha16>)
[4/10] TASK-19 approvals-workflow           skip     (no tl-plan.md — run /tl:compose)
[5/10] TASK-22 monster-report               skip     (67.3 KB > 60 KB cap — split the feature)
```

Final line: `updated: N   skipped: M   failed: K` plus a list of skips/failures with their reasons.

### 7. Never fall back to the old concat mode

If a feature has no `tl-plan.md`, this stage **must not** silently reconstruct one by concatenating BA's `implementation-plan.md` + owned units. That path produced the "reads like a business user story" content Dharma flagged. The correct recovery is: tell the user to run `/tl:compose <slug>` and stop for that feature.

