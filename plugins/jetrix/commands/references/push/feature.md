## Stage: `feature` (implemented — uses task-mcp)

Creates ONE MC Task per `features/<slug>/` folder. Features are grouped into MC Lists by resolved `list_name` — one Task per feature, one MC List per unique `list_name` value, one `feature_upsert_bundle` call per group (task-mcp's `solution_slug` parameter carries the resolved List name for that batch). First push per Task = POST (create); repush = PUT (update by `jetrix_task_object_id` stored in `feature.md` frontmatter).

### ⚠️ Operating rule for the agent running this stage — NEVER prompt the user mid-push

The push is a mechanical operation, not a design conversation. Once it starts, **carry it to completion or halt with a specific "run X first" error** — those are the only two outcomes.

Explicitly forbidden mid-push behaviors:

- **Do NOT ask** how to handle debris, stripped content, ambiguous punctuation, edge-case regex matches, or "the strip might have removed something meaningful."
- **Do NOT ask** which strip variant to apply, whether to preserve a specific citation, or how to interpret the spec.
- **Do NOT open interactive AskUserQuestion prompts** during any step of this stage.
- **Do NOT plan the run in detail before executing** — walk feature folders, hash-check, apply the transforms in-order, call the MCP, write back. That's the flow. Elaborate plans (enumerating every regex hit, listing per-file line-counts, verifying every field before push) are wasted turns; the push happens and reports what happened.

If the strip regex + cleanup pass at step 3(b) below leaves any punctuation debris, **ship the debris**. A slightly-imperfect punctuation output is preferable to halting for a design decision. The user can always re-generate via `/ba:features` if they don't like the result. If a bracketed citation contains meaningful prose that the strip discards (rare edge case with `[SIMULATED › ...]` and similar), that's tolerable loss — the user has told us this posture explicitly. Note it in the final report; do not stop.

The only allowed halt is a **prereq failure** (see §1a below) — missing BA files, missing project.json, unreachable task-mcp. All of those tell the user to `/jetrix:pull X` or `/ba:features` and stop cleanly. Nothing else halts.

### 1a. Prereq check — do NOT crash on missing files, tell the user what to pull

Before walking, verify `features/` exists and has at least one feature folder with a `feature.md`. Two failure modes to handle explicitly:

- **`features/` doesn't exist** — halt with:
  ```
  ✗ /jetrix:push feature requires the BA feature breakdown.
    This workspace has no features/ folder.
    Run one of:
      /ba:features                 (generate the breakdown from local scope)
      /jetrix:pull scope           (pull an existing breakdown from Jetrix)
    Then re-run /jetrix:push feature.
  ```
- **Folder exists but a feature is missing required BA files** (e.g. no `feature.md`, or no `acceptance-criteria.md` — the seven tab-critical files) — halt for that feature with:
  ```
  ✗ /jetrix:push feature: feature '<slug>' is missing required BA files.
    Missing:
      features/<slug>/business-rules.md
      features/<slug>/nfrs.md
    Run one of:
      /jetrix:pull scope           (pull all feature folders from Jetrix)
      /jetrix:pull task <ref>      (pull just this feature)
      /ba:features <slug>          (regenerate locally from scope)
    Then re-run /jetrix:push feature.
  ```
- **Never silently skip** a feature just because a file is missing. Silent skips ship half-tasks; explicit halts let the user fix and retry.

Only after all prereq checks pass do you walk the folders in step 2.

### 2. Walk + read + assemble every feature — ONE Bash+Python call

**Do NOT `Read` each feature's files individually.** For 20 features that's 160 `Read` tool round-trips ≈ 5-10 minutes wall-clock. Instead, invoke the plugin's script — it walks `features/*/`, reads each folder's `.md` files, applies every transform (`strip_file_paths` + `rewrite_feat_to_task`), resolves `list_name` per feature (fallback chain), detects blocker signals, groups by `list_name`, skips folders whose hash matches sync-state, and emits ONE JSON blob ready to hand to `feature_upsert_bundle`.

```bash
# v2.3.2: staging path moved from .jetrix/cache/ → .jetrix/staging/
# Rationale: .jetrix/cache/ holds PERSISTENT plugin state (sync-state, repolocation).
# Push assembled JSON is TRANSIENT — regenerated every push, contains a full copy
# of every changed feature's content (title + description + BR + AC + NFR + TS +
# assumptions + metadata). Living in cache/ implied durability + hid its size
# (20 KB per changed feature). Staging/ signals transient staging + gets cleaned
# up after the push cycle completes (§ Cleanup at the end of this file).
ASSEMBLED="<workspace_root>/.jetrix/staging/push-features.json"
mkdir -p "$(dirname "$ASSEMBLED")"

python "$CLAUDE_PLUGIN_ROOT/scripts/assemble-features.py" \
  --project-root  "<absolute project_root>" \
  --sync-state    "<workspace_root>/.jetrix/cache/sync-state.json" \
  --solution-slug "<solution_slug from project.json>" \
  --output        "$ASSEMBLED"
```

**Note on skip-unchanged.** The assembled JSON contains ONLY features whose folder hash changed since the last push (per `sync-state.json` `contentHash`). Features already in sync appear in the `skipped_unchanged` list, not in `groups[].features` — so the JSON scales with CHANGE, not with total feature count. On a re-push with nothing changed, the JSON's `groups` array is empty, ~500 bytes total.

Optional narrowing: append `--slug user-auth --slug password-reset` to push only specific folders (rest of the flow is unchanged; skip-unchanged still applies).

Claude reads the ONE JSON blob and drives the rest of the flow from it:

```json
{
  "solution_slug": "PluginTest",
  "groups": [
    {"list_name": "Supplier Management", "features": [<payload>, ...]},
    {"list_name": "Compliance Review",   "features": [<payload>, ...]}
  ],
  "skipped_unchanged":      ["feat-a", "feat-b"],
  "halts":                  [{"slug": "foo", "reason": "missing required files: acceptance-criteria.md"}],
  "solution_slug_fallback": ["feat-x"]
}
```

- **Halts** → report each with the reason and stop. Do not push any feature if `halts` is non-empty. Recovery messages are the same ones the current §1a spec prescribes (`/ba:features` or `/jetrix:pull scope`), keyed off the reason string.
- **Skipped unchanged** → report in the final summary, no MCP calls for these.
- **Solution-slug fallback** → interactive prompt in §3a below.
- **Groups** → one `feature_upsert_bundle` call per group in §4 below.

Each `<payload>` in a group is already the exact shape `feature_upsert_bundle` expects — `feature_id`, `slug`, `initiative`, `task_object_id` (from frontmatter, `null` for creates), `title` (fallback chain applied), the six body wire-fields with strip + FEAT→TASK rewrite applied, `metadata`, `status` (`"blocked"` if any local blocker signal fired, else `"todo"`), and `priority`. There's also a `_local_content_hash` field per payload — carry it through the MCP call verbatim (the response side reads it back into `apply-feature-responses.py` for sync-state).

### 3a. Warn on solution-slug List fallback (before pushing)

The `list_name` fallback chain (implemented in `scripts/assemble-features.py` — `frontmatter.list_name` → `mapped_scope` with `§X.Y ` stripped → `initiative` → solution_slug) uses the solution slug as the last-resort catch-all. If ANY feature resolves to that fallback, don't silently push them there — they'd all pile up in a List named after the solution ("Plugin_Test"-style), which is what caused the "why did all my tasks land here?" report.

Use the `solution_slug_fallback` list from the assembled JSON (§2) as the exact set to prompt about — those are the slugs that got the fallback. Don't re-derive the check here.

If yes, print:

```
⚠ N feature(s) will land in List "<solution_slug>" (last-resort fallback —
  no list_name / mapped_scope / initiative set on:
    • user-authentication
    • password-reset

  Options:
    [1] Continue — push these features into the solution-slug List
    [2] Provide a shared list_name to use for these N features
    [3] Cancel — set list_name in each feature.md frontmatter and retry

Choice:
```

- **[1]** — continue with the fallback (current behavior).
- **[2]** — prompt for a name, use it as the `solution_slug` argument for that group's `feature_upsert_bundle` call. Optionally offer to write the name back into each feature's frontmatter as `list_name:` so the next push doesn't re-prompt.
- **[3]** — exit cleanly, no features pushed. User adds `list_name:` to each `feature.md` and re-runs.

Features that resolved to a real (non-fallback) `list_name` skip this prompt entirely.

### 3b. Permission-aware halt

If any MCP call returns `{ok: false, error: "permission_denied", required_permission: "<name>"}`, halt cleanly:

```
✗ Push failed — your role is missing permission '<name>'.
  Ask your Techjays admin to grant it, then re-run /jetrix:push feature.
```

Do not retry the failed feature. Continue pushing OTHER features (permission errors are usually per-operation, not per-feature — so a `task.create` denial on one push means every push will fail; but for safety, keep processing and surface each denial). At the end, report the union of failures so the user knows exactly what to fix.

### 4. Grouped MCP calls — one `feature_upsert_bundle` per resolved `list_name`

Group features by their resolved `list_name` (from step 3(b) above). Emit **one MCP call per group** — the `solution_slug` parameter carries the List name for that batch. All features in the same group land under the same MC List (find-or-create by name). task-mcp requires no change: it already uses `solution_slug` verbatim as the List name for find-or-create.

```
# Example — 10 features resolving to 3 distinct list_names → 3 MCP calls

mcp__task-mcp__feature_upsert_bundle(
  solution_id = <from project.json>,
  solution_slug = "Supplier Management",   // ← resolved list_name for this group
  features = [
    {
      feature_id: "FEAT-AUTH-001",
      slug: "user-auth",
      initiative: "user-portal",
      task_object_id: "<from frontmatter, if present>",  // omit for create

      // The six BA-owned tab fields — passthrough / two-merge output from step 3(b).
      title:               "<frontmatter.title of feature.md, e.g. 'Supplier Onboarding'>",
      description:         "<feature.md Objective + '\n\n## Workflow\n\n' + workflow.md body + '\n\n' + feature.md In-Scope+Out-of-Scope — the reordering puts scope AFTER workflow so AC / test-scenarios can cite it naturally>",
      business_rules:      "<business-rules.md body verbatim>",
      acceptance_criteria: "<acceptance-criteria.md body verbatim>",
      nfrs:                "<nfrs.md body verbatim, or ''>",
      test_scenarios:      "<test-scenarios.md body verbatim, or ''>",
      assumptions:         "<dependencies.md + '\n\n**Open questions**\n\n' + open-questions.md, OR '\n\n**Open questions** ' + '— none. <reason>' when there are no questions — matches v2 shape>",

      // Metadata — populates task.metadata for downstream flows (dev:build dep check, etc.)
      metadata: {
        externalId:          "FEAT-AUTH-001",
        externalInitiative:  "user-portal",
        externalSlug:        "user-auth",
        dependsOnFeatureIds: ["FEAT-USER-001"],
        useCases:            ["AUTH-UC-01", "AUTH-UC-02"],
      },

      status: "<'blocked' if any blocker signal fires per the rule above; else 'todo'>",
      priority: "..."
    },
    ...
  ]
)

# ... then repeat for the next group:
mcp__task-mcp__feature_upsert_bundle(
  solution_id = <from project.json>,
  solution_slug = "Compliance Review",     // ← next resolved list_name
  features = [ ... features in this group ... ]
)

# ... etc, one call per unique list_name.
```

**Grouping is deterministic** — features iterate in a stable order (`feature_index.md` row order), so groups are formed by first-appearance of each `list_name`. This keeps push logs and MC List creation order predictable across runs.

**Do NOT send** — these fields are legacy and reserved for MC-specific renders that we no longer duplicate from BA output:

- `scope`, `dependencies`, `open_questions` — their content already lives inside `description` and `assumptions` respectively.
- `technical_flow`, `journeys` — MC's Execution Flow tab can be repopulated later via a targeted structured push if needed; the mermaid diagram in `description` covers the Description-tab render.

**Field-to-tab map:**

| Field | MC Tab | Source |
|---|---|---|
| `description` | Description | `feature.md` Objective + `workflow.md` (Workflow section + mermaid) + `feature.md` In-Scope + Out-of-Scope, joined at push. Order: Objective → Workflow → In Scope → Out of Scope. |
| `business_rules` | Business Rules | `business-rules.md`, verbatim |
| `acceptance_criteria` | Acceptance Criteria | `acceptance-criteria.md`, verbatim |
| `nfrs` | NFRs | `nfrs.md`, verbatim |
| `test_scenarios` | Test Scenarios | `test-scenarios.md`, verbatim |
| `assumptions` | Dependencies (tab labelled Dependencies in UI) | `dependencies.md` (Depends on + Assumptions) + `open-questions.md` (Open questions bullets), joined at push |
| `implementation_details` | Implementation | Not written here — `feature_update_implementation` writes it after `/dev:plan` produces `tl-plan.md` (which invokes the `tl-feature-compose` skill internally in Stage 2). |
| — | (no tab) | `implementation-plan.md` and `status.md` are local-only, never pushed. |

Response per feature: `{slug, feature_id, task_object_id, task_number, version, action ('created' | 'updated' | 'recreated'), ok}`. `recreated` means the cached `task_object_id` no longer existed in MC (deleted server-side) so a new task was created; the response also carries `previous_task_object_id`.

### 5. Apply responses — write-back frontmatter + sync-state (ONE Bash+Python call)

Concatenate every `feature_upsert_bundle` response (one per list_name group in §4) into a single JSON list, dump it to disk, then invoke the plugin's apply script. It patches feature.md frontmatter (for `created`/`recreated` rows) and updates sync-state — merge-safe, one script call, constant cost.

Carry the `_local_content_hash` field from each payload verbatim through the MCP round-trip into the response row, so the apply script writes the correct contentHash into sync-state.

```bash
# v2.3.2: responses staging moved to .jetrix/staging/ + explicit cleanup
RESPONSES="<workspace_root>/.jetrix/staging/push-features-responses.json"
mkdir -p "$(dirname "$RESPONSES")"

cat > "$RESPONSES" <<'JETRIX_RESP_EOF'
[
  {"slug":"user-auth","feature_id":"FEAT-AUTH-001","task_object_id":"6a61...","task_number":42,"version":1,"action":"created","ok":true,"_local_content_hash":"<sha256 from assemble step>"},
  ...one row per feature across every group...
]
JETRIX_RESP_EOF

python "$CLAUDE_PLUGIN_ROOT/scripts/apply-feature-responses.py" \
  --responses         "$RESPONSES" \
  --project-root      "<absolute project_root>" \
  --sync-state        "<workspace_root>/.jetrix/cache/sync-state.json" \
  [--subtask-responses "<workspace_root>/.jetrix/staging/push-subtasks-responses.json"]
```

### Cleanup — remove all staging files after successful apply (v2.3.2)

```bash
# Delete every staging file this push cycle wrote — they're transient by design.
# sync-state.json is the ONLY persistent record of what was pushed (contentHash
# per feature/subtask + task_object_id + lastPushed). If a re-push runs, the
# assemble script recomputes the hash from source .md files fresh and compares
# against sync-state.
rm -f "<workspace_root>/.jetrix/staging/push-features.json"
rm -f "<workspace_root>/.jetrix/staging/push-features-responses.json"
rm -f "<workspace_root>/.jetrix/staging/push-subtasks-responses.json"
# Remove the staging dir if it's empty (leaves it if other flows staged files)
rmdir "<workspace_root>/.jetrix/staging" 2>/dev/null || true
```

**Migration from v2.3.1 and earlier** — if `.jetrix/cache/.push-features.json` or `.push-features-responses.json` still exist from a previous push (they were persistent in the old layout), delete them once now:

```bash
rm -f "<workspace_root>/.jetrix/cache/.push-features.json"
rm -f "<workspace_root>/.jetrix/cache/.push-features-responses.json"
rm -f "<workspace_root>/.jetrix/cache/.push-subtasks-responses.json"
```

Pass `--subtask-responses` when §7 has run and produced a
`subtask_upsert_bundle` response bundle (per-parent or list-of-parents
shape — see §7). The script handles both parent-feature rows AND sub-task
rows in one call, merge-safe.

The script:
- Patches `features/<slug>/feature.md`'s frontmatter — sets `jetrix_task_id`
  + `jetrix_task_object_id` + (v2.1) `jetrix_task_number` (MC display form
  like `Feature-4`, used by `/dev:plan` Stage 0 lookup) for rows whose
  `action` is `created` or `recreated`. Never re-Reads the file for this
  (regex-based rewrite).
- (v2.1) Patches each sub-task's tab files (`subtask/<repo>/{description,
  implementation, status}.md`) with `jetrix_subtask_object_id` +
  `jetrix_subtask_number` when `--subtask-responses` is provided. Resolves
  `subtaskRepo` from the response's `metadata.subtaskRepo`, falling back to
  matching the sub-task's `subtask_number` frontmatter against local
  folders.
- Writes per-feature entries under `tasks/<feature_id>` in sync-state with
  `taskNumber`, `taskObjectId`, `slug`, `contentHash` (from
  `_local_content_hash`), `version`, `lastPushed`. Merge-safe.
- (v2.1) Writes per-sub-task entries under `subtasks/<subtask_object_id>`
  with `taskNumber`, `taskObjectId`, `parentTaskObjectId`, `featureId`,
  `subtaskRepo`, `subtaskNumber`, `contentHash`, `version`, `lastPushed`.
  Preserves existing `implementationHash` (written by
  `apply-implementation-responses.py`).
- Prints per-row status to stdout — `recorded` / `patched` / `failed` — with
  separate counts for features vs sub-tasks.

### 6. Update `features/feature-index.md`

Add/update the `Task ID` column so rows show `TASK-<taskNumber>` next to each feature slug. (This file is scope-stage; push it separately via `/jetrix:push scope` after — sync-state will pick up the change.)

Report per-feature: `created` / `updated` / `recreated` (previous task was gone server-side; a new task was created and the cached ids replaced) / `skipped (unchanged)` / `failed`.

### 7. Sub-task handling (v2.1+)

After parent features are pushed, walk `features/<slug>/subtask/<repo>/` for each pushed parent whose folder exists on disk. This handles sub-tasks that `/dev:plan` composed and the current push wave should publish.

**Which command pushes sub-tasks — `/dev:plan` or `/jetrix:push feature`?**

Both paths reach the same MC endpoint (`task-mcp.subtask_upsert_bundle`), so
there is no risk of duplicate creates — the tool is idempotent via
`metadata.externalId`. The difference is *when*:

- **`/dev:plan` Stage 2 (§2e)** — pushes immediately, right after composing.
  This is the primary flow for the developer who runs `/dev:plan` themselves.
  Local sub-task folders and MC end up in sync in one command.
- **`/jetrix:push feature` (this stage, §7)** — pushes sub-tasks a teammate
  composed via `/dev:plan --dry-run` (skipped MC calls) or received via
  `/jetrix:pull scope` and edited locally. This is the *re-sync* path.

For a teammate who pulls a workspace fresh, runs `/dev:plan` normally, and
never touches `--dry-run`, this stage's §7 is effectively a no-op on
sub-tasks — `assemble-features.py`'s skip-unchanged (via
`sync-state.subtasks/<subtask_object_id>.contentHash`) skips every sub-task
that Stage 2 already published. Bandwidth cost is `subtask_list` (one MCP
call per parent to build the skip check) plus zero writes.

**Detection.** For each parent feature just pushed successfully (`ok: true, action: created|updated|recreated`), check whether `features/<slug>/subtask/<repo>/` folders exist locally. Skip the sub-task step entirely for features with no local `subtask/` directory — they are parent-alone (unchanged behaviour).

**Assembly.** Extend the assemble script call in §2 to also emit a `subtasks_by_parent` map — for each parent slug, a list of sub-task payloads assembled from each `subtask/<repo>/description.md` + `implementation.md` + frontmatter (skip-unchanged via `_local_content_hash` on the concatenation of the two files). Each payload matches `task-mcp.subtask_upsert_bundle`'s input schema:

```json
{
  "subtasks_by_parent": {
    "supplier-onboarding": [
      {
        "subtask_object_id": null,                       // present on update
        "title":             "Supplier Onboarding — backend",
        "description":       "<description.md body, frontmatter stripped>",
        "implementation_details": "<implementation.md body, frontmatter stripped>",
        "acceptance_criteria": "",                       // deliberately empty
        "test_scenarios":      "",
        "metadata": {
          "externalId":       "FEAT-SUP-001-1",
          "parentExternalId": "FEAT-SUP-001",
          "subtaskNumber":    1,
          "subtaskRepo":      "backend",
          "source":           "ai",
          "aiGenerated":      true
        },
        "status": "todo",
        "_local_content_hash": "sha256:..."
      },
      ...
    ]
  }
}
```

**Idempotency call before upsert.** For each parent slug in `subtasks_by_parent`, call `task-mcp.subtask_list(solution_id, parent_task_id=<parent's task_object_id from §5 response>)`. Match each local sub-task to an existing MC sub-task by `metadata.externalId`:
- Match → include the returned `task_object_id` in that sub-task's `subtask_object_id` field → PUT
- No match → leave `subtask_object_id: null` → POST

**Push.** One `task-mcp.subtask_upsert_bundle` call per parent (one call, N sub-tasks in a batch):

```
mcp__task-mcp__subtask_upsert_bundle(
  solution_id    = <from project.json>,
  parent_task_id = <parent's jetrix_task_object_id from §5>,
  subtasks       = <the list assembled above>
)
```

**Response write-back.** For each successful result row:
- Patch that sub-task's frontmatter files (`description.md`, `implementation.md`, `status.md`) with `jetrix_subtask_object_id: <task_object_id>` and `jetrix_subtask_number: <task_number>`.
- Update sync-state `subtasks/<subtask_object_id>` entry (see the top-level task-mcp addition spec for shape).

Rows with `ok: false` → log the error, mark that sub-task's `status.md` `current_state: BLOCKED`, continue with siblings (per-item isolation).

**Report.** Extend the final summary with a per-parent sub-task line: `sub-tasks created: 3 / updated: 0 / failed: 0 / skipped-unchanged: 0`.

