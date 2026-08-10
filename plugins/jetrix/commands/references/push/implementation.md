## Stage: `implementation` (implemented — uses task-mcp)

TL runs this AFTER `/tl:compose` writes per-feature `tl-plan.md` files (the buildable 9-section technical spec). Each MC Task's `implementationDetails` gets **that one file's body verbatim** — no concatenation, no unit-file walking, no manifest degradation. `/tl:compose` is responsible for producing a self-contained document sized under Mission Control's 60 KB cap; this stage only ships what compose produced. Status flips to `READY_FOR_DEV`. Does NOT touch BA-owned body fields.

If a feature folder has no `tl-plan.md`, this stage skips it with a clear message pointing the user at the right recovery command. Two cases:

- **This teammate hasn't composed yet locally** → run `/tl:compose <slug>` to generate `tl-plan.md` from the local graph.
- **The feature's `tl-plan.md` was pushed by a different teammate and this workspace hasn't pulled it** → run `/jetrix:pull task <ref>` (or `/jetrix:pull scope`) to fetch the composed plan from Jetrix.

Never compose silently, never guess, never fall back to the old concat-of-units mode.

### 2. Batch-read every feature's needed data in ONE Bash call

**Do NOT `Read` files individually.** For a workspace with N features, individual Reads mean N LLM turns per file at ~5-10s each — a 5-feature push burns 5+ minutes just reading. Instead, this single Bash call emits everything needed:

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

for dir in context/features/*/; do
  slug=$(basename "$dir")
  [[ "$slug" == "feature-index.md" ]] && continue
  [[ -f "$dir/feature.md" && -f "$dir/tl-plan.md" ]] || {
    if [[ -f "$dir/feature.md" && ! -f "$dir/tl-plan.md" ]]; then
      printf "===SKIP:%s:no-tl-plan===\n" "$slug"
    fi
    continue
  }

  fid=$(awk '/^feature_id:/{sub(/^feature_id:[[:space:]]*/, ""); sub(/[[:space:]"]+$/, ""); print; exit}' "$dir/feature.md")
  toid=$(awk '/^jetrix_task_object_id:/{sub(/^jetrix_task_object_id:[[:space:]]*/, ""); sub(/[[:space:]"]+$/, ""); print; exit}' "$dir/feature.md")

  [[ -z "$fid" ]]  && { printf "===SKIP:%s:no-feature-id===\n" "$slug"; continue; }
  [[ -z "$toid" ]] && { printf "===SKIP:%s:no-task-object-id===\n" "$slug"; continue; }

  # Strip frontmatter + CRLF-normalise. First two `---` lines bound the frontmatter.
  body=$(awk 'BEGIN{p=0; c=0} /^---\r?$/{c++; if(c==2){p=1; next}} p{print}' "$dir/tl-plan.md" | tr -d '\r')

  # Strip leading blank lines left after frontmatter removal.
  body=$(printf "%s" "$body" | awk 'NR==1 && /^[[:space:]]*$/ {skip=1; next} skip && /^[[:space:]]*$/ {next} {skip=0; print}')

  size=$(printf "%s" "$body" | wc -c)
  hash=$(printf "%s" "$body" | sha256sum | cut -d' ' -f1)

  # Emit one block per feature. Agent parses these markers.
  printf "===FEATURE:%s===\n" "$slug"
  printf "feature_id: %s\n" "$fid"
  printf "task_object_id: %s\n" "$toid"
  printf "size: %s\n" "$size"
  printf "hash: %s\n" "$hash"
  printf "===BODY-BEGIN===\n"
  printf "%s\n" "$body"
  printf "===BODY-END===\n"
done
```

**One Bash call. One LLM turn to parse.** The agent gets slug + feature_id + task_object_id + size + hash + full body for every feature that has both `feature.md` and `tl-plan.md`. Missing-file skips are surfaced with their own `===SKIP:<slug>:<reason>===` marker so the agent can report them without any extra file reads.

### 3. Skip reporting

For every `===SKIP:<slug>:<reason>===` marker from step 2, emit the exact user-facing message:

- `no-tl-plan` → `[skip] context/features/<slug>/ — no tl-plan.md. Run /tl:compose <slug> or /jetrix:pull task <slug>.`
- `no-feature-id` → `[skip] context/features/<slug>/ — feature.md has no feature_id frontmatter. Re-run /ba:features.`
- `no-task-object-id` → `[skip] context/features/<slug>/ — feature.md has no jetrix_task_object_id. Run /jetrix:push feature first.`

### 4. Verify each `===FEATURE:<slug>===` block from the batch

For each block emitted by step 2:

**(a) Body integrity.** The awk in step 2 already stripped frontmatter and CRLF. Sanity-check: body contains zero `\r`, and no line starts with a leaked frontmatter key (`doc_type:`, `schema_version:`, `produced_by:`, `feature_id:`, `composed_at:`, `inputs_hash:`).

**(b) Size cap — 60 000 char hard limit.** Mission Control's Joi validator on `implementationDetails` rejects anything longer, returning `{ok: false, updated: 0, error: "\"implementationDetails\" length must be less than or equal to 60000 characters long"}` and writing nothing.

The `size:` field from the batch is authoritative:
- `size > 60000` → **skip this feature and fail loud.** Do NOT truncate. Report:
  ```
  [skip] FEAT-XXX-YY — tl-plan.md is <N> chars, cap is 60000.
                     Split the feature via /tl:compose or /ba:features and re-run.
  ```
- `55000 < size ≤ 60000` → push, but warn: `[warn] FEAT-XXX-YY — <N> chars, near the 60 KB cap`.

**(c) Skip-unchanged.** Compare the `hash:` field from the batch against `sync-state.json[tasks/<feature_id>].implementation_hash`:

- Match → skip, print `[skip] TASK-<n> <slug> — unchanged (hash=<sha16>)`, do not call the MCP.
- Mismatch (or missing) → include this feature in the batched MCP call in step 5. Update sync-state on success (step 6).

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
      status: "readyForDev"
    }
  ]
)
```

Response per feature: `{slug, feature_id, task_object_id, task_number, version, ok}`.

Missing `task_object_id` returns `{ok: false, error: "…run /jetrix:push feature first"}` — the tool never creates tasks.

**ALWAYS check the per-feature `ok` field — never infer success from the call returning.** A rejected write still returns a normal-looking response envelope with `updated: 0` and `ok: false` on the individual row. Report `ok:false` rows as failures and leave their sync-state untouched so the next push retries them.

> **Known task-mcp defects (as of 2026-07-27) — do not misread these as your own failure:**
> - **Read tools return empty for tasks that demonstrably exist.** `feature_pull_bundle`, `feature_list_bundle` and `get_task_by_id_or_number` all return nothing for a Solution whose tasks are writable by object id; a raw-oid lookup fails upstream with `"Please select a solution to continue"`, suggesting a missing solution-context header on the read path. **Do not use a read tool to verify a push, and do not treat an empty read as evidence the write failed.** Verify from the write response's `ok`/`updated`/`task_number` instead — `task_number` is echoed from the stored record, so its presence proves the task was found.
> - **`version` comes back `null`** on every write, where scope-mcp and context-mcp both return an integer. Does not appear to affect the write; record `null` in sync-state rather than inventing a number.

### 6. Update sync-state — **incrementally, after EACH successful push**

**Do NOT batch sync-state writes to the end of the run.** For every feature whose `feature_update_implementation` returned `ok: true`, immediately:

1. Read `<workspace_root>/.jetrix/cache/sync-state.json` (MERGE, not replace).
2. Set the `implementation_hash` on that ONE feature's `tasks/<feature_id>` entry.
3. Write the merged object back.

Then move on to the next feature. This runs sync-state one write per successful push, not one at the end.

**Why incremental matters.** Implementation pushes relay 10–15 KB per feature through session context (the tool takes the spec as an inline string). On a 10-feature module that's ~150 KB total, and it's not unusual for the run to stop mid-way (session limits, network, an ambiguous input the agent surfaces). If sync-state is batched to the end and the run stops at 5/10:

- Sync-state has ZERO entries → next run re-pushes all 10, even the 5 that landed cleanly.
- 5 wasted network calls and each identical write bumps the Task's `version` field.

With incremental updates: the same interrupted run leaves sync-state with 5 entries. Next run computes fresh hashes, sees 5 matches, skips those, and pushes only the remaining 5. Clean resume.

**Report format.** Print progress per feature as you go, not one summary at the end:

```
[1/10] TASK-11 opening-balance-import      pushed   (12.4 KB, hash=<sha16>)
[2/10] TASK-14 leave-balance-administration skip     (unchanged, hash=<sha16>)
[3/10] TASK-16 leave-request-submission    pushed   (14.1 KB, hash=<sha16>)
[4/10] TASK-19 approvals-workflow          skip     (no tl-plan.md — run /tl:compose)
[5/10] TASK-22 monster-report              skip     (67.3 KB > 60 KB cap — split the feature)
```

Final report is a two-line summary — `updated: N`, `skipped: M`, `failed: K`, plus a list of any skips/failures with their reason.

### 7. Never fall back to the old concat mode

If a feature has no `tl-plan.md`, this stage **must not** silently reconstruct one by concatenating BA's `implementation-plan.md` + owned units. That path produced the "reads like a business user story" content Dharma flagged. The correct recovery is: tell the user to run `/tl:compose <slug>` and stop for that feature.

