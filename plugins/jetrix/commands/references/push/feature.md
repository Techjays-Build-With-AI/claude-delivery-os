## Stage: `feature` (implemented — uses task-mcp)

Creates ONE MC Task per `context/features/<slug>/` folder. Features are grouped into MC Lists by resolved `list_name` — one Task per feature, one MC List per unique `list_name` value, one `feature_upsert_bundle` call per group (task-mcp's `solution_slug` parameter carries the resolved List name for that batch). First push per Task = POST (create); repush = PUT (update by `jetrix_task_object_id` stored in `feature.md` frontmatter).

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

Before walking, verify `context/features/` exists and has at least one feature folder with a `feature.md`. Two failure modes to handle explicitly:

- **`context/features/` doesn't exist** — halt with:
  ```
  ✗ /jetrix:push feature requires the BA feature breakdown.
    This workspace has no context/features/ folder.
    Run one of:
      /ba:features                 (generate the breakdown from local scope)
      /jetrix:pull scope           (pull an existing breakdown from Jetrix)
    Then re-run /jetrix:push feature.
  ```
- **Folder exists but a feature is missing required BA files** (e.g. no `feature.md`, or no `acceptance-criteria.md` — the seven tab-critical files) — halt for that feature with:
  ```
  ✗ /jetrix:push feature: feature '<slug>' is missing required BA files.
    Missing:
      context/features/<slug>/business-rules.md
      context/features/<slug>/nfrs.md
    Run one of:
      /jetrix:pull scope           (pull all feature folders from Jetrix)
      /jetrix:pull task <ref>      (pull just this feature)
      /ba:features <slug>          (regenerate locally from scope)
    Then re-run /jetrix:push feature.
  ```
- **Never silently skip** a feature just because a file is missing. Silent skips ship half-tasks; explicit halts let the user fix and retry.

Only after all prereq checks pass do you walk the folders in step 2.

### 2. Walk feature folders — Bash + Read (small files, OK to read)

Feature files are small (each `.md` is a few KB). Reading them is fine — bytes DO enter Claude's context here because we need to parse sections. Use ONE Bash call to list folders + hash for skip-unchanged; then `Read` per file to extract sections.

```bash
#!/usr/bin/env bash
set -e
PROJECT_ROOT="<absolute project_root>"
cd "$PROJECT_ROOT"

for dir in context/features/*/; do
  slug=$(basename "$dir")
  [[ "$slug" == "feature-index.md" ]] && continue
  # concat hash of all 6-7 files in the folder
  hash=$(cat "$dir"*.md 2>/dev/null | sha256sum | cut -d' ' -f1)
  echo "$slug|$hash"
done
```

Parse into `[{slug, content_hash}]`.

### 3. Per feature — read local files + assemble the wire fields

For each folder that needs push (content_hash differs from `sync-state.json[<slug>].contentHash`):

**(a) Read the BA-authored files** (feature folder contents — small, `Read` is fine). The BA templates now produce tab-shape content directly, so **no stripping, regex-cleaning, or reshaping is needed at push time.** The push is a passthrough for five files and a two-line concatenation for the two merge pairs.

| Local file | Read purpose | Special notes |
|---|---|---|
| `feature.md` | Frontmatter (identity + metadata) + body (Description tab: Objective / In Scope / Out of Scope) | Frontmatter carries `title` (human-readable task title), `feature_id`, `initiative`, `slug`, `list_name` (optional — MC List routing), `use_cases`, `mapped_*`, `depends_on_features`, `status`, `priority`, `jetrix_task_id`, `jetrix_task_object_id`. Task title = `frontmatter.title` (falls back to H1 line if a legacy file still carries one, then to `slug` — but new templates author `title:` in frontmatter and never carry an H1). List routing resolved in (b) below. |
| `workflow.md` | Body (Workflow section — user flows + mermaid) | Concatenated into `description` at (b). |
| `business-rules.md` | Body verbatim | Sent as-is. |
| `acceptance-criteria.md` | Body verbatim | Sent as-is. Templates now author it as three grouped tables directly. |
| `nfrs.md` | Body verbatim | Sent as-is. If the file is missing, send `""`. |
| `test-scenarios.md` | Body verbatim | Sent as-is. If the file is missing, send `""`. |
| `dependencies.md` | Body (Depends on + Assumptions) | Concatenated with `open-questions.md` into `assumptions` at (b). |
| `open-questions.md` | Body (Open questions bullet list) | Concatenated with `dependencies.md` into `assumptions` at (b). |
| `implementation-plan.md` | Not read | Local-only. Never pushed. |
| `status.md` | Not read | Local-only. Never pushed. |

**(b) Assemble the wire fields** — five verbatim, two merges. Nothing else.

```
title              = <frontmatter.title of feature.md>
                     ↳ fallback: <H1 of feature.md body> if frontmatter.title absent
                     ↳ fallback: <frontmatter.slug> if neither is present

description        = <feature.md Objective section (from "## Objective" up to but not including "## In Scope")>
                   + "\n\n## Workflow\n\n"
                   + <workflow.md body — minus frontmatter, minus H1>
                   + "\n\n"
                   + <feature.md In Scope + Out of Scope sections (from "## In Scope" to end of body)>
                     ↳ If feature.md has no "## In Scope" heading (legacy or authored without scope):
                       fall back to <feature.md body> + workflow (old order). Warn the author —
                       the reader loses the "scope after workflow" affordance that AC / test-scenarios
                       rely on when they cite "email notifications are out of scope, so a toast is shown".

business_rules     = <business-rules.md body — minus frontmatter, minus H1>

acceptance_criteria = <acceptance-criteria.md body — minus frontmatter, minus H1>

nfrs               = <nfrs.md body — minus frontmatter, minus H1>
                     or "" if the file is missing

test_scenarios     = <test-scenarios.md body — minus frontmatter, minus H1>
                     or "" if the file is missing

assumptions        = <dependencies.md body — minus frontmatter, minus H1>
                   + (open-questions.md body starts with "— none."
                        ? "\n\n**Open questions** " + <open-questions.md body>
                        : "\n\n**Open questions**\n\n" + <open-questions.md body>)
```

**Frontmatter → metadata** (populates task metadata for the dependency-check gate in `/dev:build`):

```
metadata = {
  externalId:          <frontmatter.feature_id>,
  externalInitiative:  <frontmatter.initiative>,
  externalSlug:        <frontmatter.slug>,
  dependsOnFeatureIds: <frontmatter.depends_on_features (list)>,
  useCases:            <frontmatter.use_cases (list)>,
}
```

**Resolve `list_name` per feature** — this determines which MC List the Task lands under. Fallback chain:

```
list_name = <frontmatter.list_name of feature.md>
            ↳ fallback: <frontmatter.mapped_scope with the "§X.Y " prefix stripped>
                        e.g. "§3.2 Supplier Management" → "Supplier Management"
            ↳ fallback: <frontmatter.initiative>            (kebab-case is fine; MC List names are free text)
            ↳ fallback: <solution_slug from project.json>   (last-resort; no feature is orphaned)
```

Compute the pattern strip as: if `mapped_scope` starts with `§`, drop everything up to and including the first whitespace character; trim the remainder. Every feature ends up with a non-empty `list_name`. Two features with the same resolved `list_name` share one MC List; task-mcp's find-or-create against `List.name` handles both cases.

**One targeted transform — file-path strip on every wire field before sending.** Local BA files may contain filesystem navigation aids (`see business-rules.md`, `[code › ...]`, backticked code paths). Those help the BA author cross-check while authoring, but they're meaningless to a Jetrix reader who has no filesystem. After assembling each wire field, apply `strip_file_paths()` (defined below) to `description`, `business_rules`, `acceptance_criteria`, `nfrs`, `test_scenarios`, and `assumptions`. Do NOT apply to `implementation_details` (TL-authored, already clean) or to `metadata` / `title` (structured, no prose).

```
def strip_file_paths(text):
    # File-reference prose  ("… — see foo.md.", "(see foo.md)", "see `foo.md`")
    text = re.sub(r'\s+—\s+see\s+[a-zA-Z0-9_-]+\.md\.?', '', text)
    text = re.sub(r'\s*\(see\s+[a-zA-Z0-9_-]+\.md\)\.?', '', text)
    text = re.sub(r'see\s+`[a-zA-Z0-9_-]+\.md`', '', text)

    # Bracketed provenance / citation callouts — internal-analysis debris.
    # Whitelist of known analysis tags followed by ` › `, ` > `, or a
    # space + content. Stripped entirely — no user prompt, no per-tag
    # decision. Add more tags to this list as they surface in BA output.
    #
    # NEVER matches ID-only bracket forms like [BR-1], [AC-3], [WF-021],
    # [FEAT-XYZ-01] — those don't have space/›/> after the tag, so the
    # regex's content-required clause skips them.
    text = re.sub(
        r'\[(?:code|SIMULATED|TL|QA|BA|DEBUG|NOTE|REVIEW|TODO|FIXME|INTERNAL)[ ›>][^\]]+\]',
        '', text,
    )

    # BA-internal ID references — SRC (source recording), EX (worked example),
    # DEC (design decision log entry). All three are BA-authoring aids that
    # point at local artefacts (recordings, scope-doc examples, decision-log
    # entries) the Jetrix reader has no access to. Strip in both bracketed
    # forms ([SRC-001], [SRC-001 › 00:34:50], [EX-001], [DEC-014]) and bare
    # forms (`SRC-001`, `DEC-014` mentioned in prose).
    text = re.sub(r'\[(?:SRC|EX|DEC)-\d+(?:[ ›>][^\]]*)?\]', '', text)
    text = re.sub(r'\b(?:SRC|EX|DEC)-\d+\b', '', text)

    # Mid-content analysis-tag citations — the same TAG › content pattern
    # but embedded INSIDE a larger bracket instead of at the start.
    # Example: [BR-013, SIMULATED › scope-review-...responses.md DEC-014, ...]
    # The outer bracket contains a legitimate BR-013 that must survive,
    # so we can't strip the whole bracket. Instead strip just the
    # "TAG › filename..." clause up to the next comma or bracket close.
    text = re.sub(
        r'\b(?:SIMULATED|TL|QA|BA|DEBUG|NOTE|REVIEW|TODO|FIXME|INTERNAL|code)\s*[›>]\s*[^,\]\n]+',
        '', text,
    )

    # Bare .md/.js/.ts/etc filename mentions in prose (usually leftover from
    # a partial strip — e.g. "— see status.md and open-questions.md" gets
    # the "— see status.md" head stripped and leaves "and open-questions.md"
    # dangling). Strip any bare word ending in a common code extension.
    text = re.sub(
        r'\b[a-zA-Z][a-zA-Z0-9_-]*\.(md|js|ts|jsx|tsx|py|go|java|rb|rs|kt|swift|json|yaml|yml)\b\.?',
        '', text,
    )

    # Backticked code paths — must contain "/" to distinguish from bare filenames
    text = re.sub(
        r'`(src|controllers|models|routes|components|pages|endpoints|entities|api|utils|services|app|lib)/[^`]+`',
        '', text,
    )

    # Backticked bare filenames with code extensions
    text = re.sub(
        r'`[a-zA-Z0-9_-]+\.(md|js|ts|jsx|tsx|py|go|java|rb|rs|kt|swift)`',
        '', text,
    )

    # Cleanup: aggressively remove the punctuation debris left behind after
    # stripping file paths. When "see foo.md" or "(see foo.md, DEC-012)"
    # gets its file citation stripped, we can be left with empty parens,
    # orphan commas, empty backticks, extra spaces. Clean all of it in
    # this pass so downstream never sees the debris.
    #
    # CRITICAL RULE for the agent running the push: **NEVER prompt the
    # user about debris.** Apply this cleanup silently and continue.
    # A slightly-imperfect punctuation output is always preferable to
    # halting the push flow with an "is this OK?" question — the value
    # of a fast push beats perfect punctuation. If any edge case slips
    # through, ship it; the reader will still understand the content.

    # 1. Empty backtick runs (ALL variants — 2, 3, or 4 backticks with
    #    optional whitespace between). When a filename inside backticks
    #    gets stripped, we're left with `` or ` ` or `  ` etc.
    text = re.sub(r'`{2,4}(?=\s|[.,;:!?)\]}]|$)', '', text)  # orphan ``, ```, ```` before whitespace/punct/EOL
    text = re.sub(r'(?<=[\s\(\[\{—])`{2,4}', '', text)       # orphan ``, ```, ```` after whitespace/opening bracket/em-dash
    text = re.sub(r'`\s+`', '', text)                        # `  ` (backticks separated by whitespace)
    text = re.sub(r'``', '', text)                           # remaining plain empty double-backticks

    # 2. Empty enclosures created by removed content
    text = re.sub(r'\(\s*[,;:]?\s*\)', '', text)      # () (,) (;) — empty parens
    text = re.sub(r'\[\s*[,;:]?\s*\]', '', text)      # [] etc.
    text = re.sub(r'\{\s*[,;:]?\s*\}', '', text)

    # 3. Orphan punctuation at boundaries inside enclosures
    text = re.sub(r'\(\s*,\s*', '(', text)            # "(, DEC-012" → "(DEC-012"
    text = re.sub(r'\s*,\s*\)', ')', text)            # "DEC-012, )"  → "DEC-012)"  ← the "(deferred, )" case
    text = re.sub(r'\[\s*,\s*', '[', text)
    text = re.sub(r'\s*,\s*\]', ']', text)

    # 4. Em-dash + orphan debris  ("word — , DEC-012" → "word — DEC-012")
    text = re.sub(r'(—|--)\s*,\s*', r'\1 ', text)     # "— , foo" → "— foo"
    text = re.sub(r',\s*(—|--)\s*', r' \1 ', text)    # "foo , —" → "foo — "

    # 4a. Orphan "and" left after stripping the phrase that came before it.
    # "— see status.md and open-questions.md" → strips head → "and " left over.
    # These conservative patterns catch "and" only when it's clearly hanging
    # at the end of a clause (before a sentence-ending punctuation or
    # bracket close), not when "and X" is legitimate prose.
    text = re.sub(r'\s+and\s*\.', '.', text)          # " and." → "."
    text = re.sub(r'\s+and\s*,', ',', text)           # " and," → ","
    text = re.sub(r'\s+and\s*(?=[)\]])', '', text)    # " and)" → ")"
    text = re.sub(r'—\s+and\s*(?=[.,;:!?])', '', text)  # "— and." → "."

    # 5. Broken "see X, Y" → "Y" (leftover "see" or "see ," after strip)
    text = re.sub(r'\bsee\s*,\s*', '', text, flags=re.IGNORECASE)   # "see , foo" → "foo"
    text = re.sub(r'\bsee\s*(?=[)\]])', '', text, flags=re.IGNORECASE)  # "see )" → ")"
    text = re.sub(r'—\s*see\s*(?=[.,;:!?)\]]|$)', '', text, flags=re.IGNORECASE)  # "— see." → ""

    # 6. Standard punctuation debris
    text = re.sub(r',\s*,+', ',', text)               # ",,, " → ","
    text = re.sub(r';\s*;+', ';', text)               # ";;;" → ";"
    text = re.sub(r'\s+([\.,;:!?])', r'\1', text)     # " ,"  → ","
    text = re.sub(r'([\.,;:!?])\s+([\.,;:!?])', r'\1\2', text)  # ",." variants collapsed
    text = re.sub(r'(—|--)\s*\.', '.', text)          # "foo —." → "foo."

    # 7. Whitespace cleanup
    text = re.sub(r' {2,}', ' ', text)                # multi-space → single
    text = re.sub(r'[ \t]+\n', '\n', text)            # trailing space before newline
    text = re.sub(r'\n{3,}', '\n\n', text)            # keep max one blank line

    # Rescue: test-scenarios header sometimes ships as `| # | Scenario ...`
    # despite the template saying `| No. |`. The bare `#` at the start of a
    # table cell trips the UI's markdown normaliser, which treats it as a
    # heading marker and splits the header row. Convert defensively — no
    # user prompt, no template violation report; just fix it before the wire.
    text = re.sub(r'\|\s*#\s*\|\s*Scenario\s*\|', r'| No. | Scenario |', text)

    return text.strip()
```

**Never stripped — IDs pass through untouched:** `BR-N`, `AC-N`, `NFR-<label>`, `WF-###`, `DATA-###`, `INT-###`, `PAGE-<AREA>-NN`, `EP-<AREA>-NN`, `ENT-<AREA>-NN`. These are the cross-tab reference mechanism inside Jetrix and must survive push. `SRC-###`, `EX-###`, and `DEC-###` are BA-internal references (recording citations, worked-example anchors, decision-log entries) — those DO get stripped because the Jetrix reader has no access to those local artefacts.

**Rewritten at push, not stripped — `FEAT-<AREA>-NN` → `TASK-<n>`.** BA authors reference sibling features by their feature-id (`FEAT-LEAV-02`). To a Jetrix reader, that id is opaque — they can't click it, can't look it up. What they CAN use is the MC task number. So push rewrites every `FEAT-<AREA>-NN` mention in prose to `TASK-<n>` using the `feature_id → task_number` map, built from:

1. **`.jetrix/cache/sync-state.json`** — every previously-pushed feature has `tasks/<feature_id>.taskNumber`. Build the map once at the top of the push flow.
2. **Batch responses as the push proceeds** — task-mcp processes features serially (per its taskNumber race guard), so by the time feature 3 pushes, features 1 and 2 already have `task_number` in the response. Add each response's task_number to the map incrementally so later features in the same batch resolve their cross-refs correctly.

```
def rewrite_feat_to_task(text: str, task_num_by_feat: dict) -> str:
    """Rewrite bare `FEAT-<AREA>-NN` mentions in prose to `TASK-<n>`.
    Preserves feature-ids that don't yet have a task_number — those
    are cross-refs to features not yet pushed. They resolve naturally
    on a subsequent push once the target feature has a task_number."""
    def replace(match):
        feat_id = match.group(0)
        task_num = task_num_by_feat.get(feat_id)
        return f'TASK-{task_num}' if task_num else feat_id
    return re.sub(r'\bFEAT-[A-Z]+-\d+\b', replace, text)
```

**Apply order:** `strip_file_paths(...)` FIRST (removes debris + file paths), then `rewrite_feat_to_task(..., task_num_by_feat)` on the same six fields (`description`, `business_rules`, `acceptance_criteria`, `nfrs`, `test_scenarios`, `assumptions`). The rewrite runs AFTER the strip so that a stray `FEAT-XXX-NN` inside a bracketed callout (which would have been stripped) doesn't get pointlessly looked up.

**Unresolved FEAT-ids stay as-is.** If a referenced feature has never been pushed (no `task_number` in the map), the `FEAT-XXX-NN` remains in the prose. Next push after that feature is created will resolve it. Do NOT strip unresolved FEAT-ids — that would silently lose the cross-reference.

**Feature-ids stay in metadata.** `metadata.externalId` (the pushed feature's own id) and `metadata.dependsOnFeatureIds` (list of feature-ids this feature depends on) are unaffected. Metadata is machine-readable, not user-facing prose — it carries the round-trip identity for pull.

**No content reshaping otherwise** — no bullet-to-table conversion, no framework rewriting, no heading fixes. BA templates author the tab-shape directly; the strip only removes filesystem noise. If a local file contains something the strip *can't* handle (framework names, provenance callouts, feature-id headings), that's still a **BA template violation** — surface it back to the author, do NOT try to strip silently.

**Section-aware concatenations only** — `description` = `feature.md` Objective + `## Workflow` heading + `workflow.md` body + `feature.md` In-Scope + Out-of-Scope sections (workflow injected between Objective and Scope so AC / test-scenarios can cite the scope points naturally). `assumptions` = `dependencies.md` + `**Open questions**` separator + `open-questions.md` (inline `— none.` form when the questions body starts with it). Everything else is byte-verbatim EXCEPT for the two mandatory passes: `strip_file_paths()` (removes file citations + provenance debris) and `rewrite_feat_to_task()` (converts `FEAT-<AREA>-NN` → `TASK-<n>` using the sync-state task-number map).

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

      status: "todo",
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
| `implementation_details` | Implementation | Not written here — `feature_update_implementation` writes it after `/tl:compose` produces `tl-plan.md`. |
| — | (no tab) | `implementation-plan.md` and `status.md` are local-only, never pushed. |

Response per feature: `{slug, feature_id, task_object_id, task_number, version, action ('created' | 'updated' | 'recreated'), ok}`. `recreated` means the cached `task_object_id` no longer existed in MC (deleted server-side) so a new task was created; the response also carries `previous_task_object_id`.

### 5. Write-back — patch feature.md frontmatter

For each `ok:true` result whose `action` is `'created'` or `'recreated'`: patch `context/features/<slug>/feature.md`'s YAML frontmatter to set `jetrix_task_id: <task_number>` and `jetrix_task_object_id: <task_object_id>`. (`recreated` means the previously-cached task was deleted server-side and a new one was made — overwrite the stale ids exactly like a first-time create.) Use `sed` via Bash — do NOT re-Read the file just to write it back.

### 6. Update `context/features/feature-index.md`

Add/update the `Task ID` column so rows show `TASK-<taskNumber>` next to each feature slug. (This file is scope-stage; push it separately via `/jetrix:push scope` after — sync-state will pick up the change.)

### 7. Update `.jetrix/cache/sync-state.json`

**MERGE, do not replace.** Read the current file (contains scope/context/other keys), set/update only the `tasks/<feature_id>` keys you just pushed, and write the merged object back. Under `tasks/<feature_id>`, record:
```json
{
  "taskNumber": 42,
  "taskObjectId": "<oid>",
  "slug": "user-auth",
  "contentHash": "<sha256 from step 2>",
  "version": <from response>,
  "lastPushed": "<iso>"
}
```

Report per-feature: `created` / `updated` / `recreated` (previous task was gone server-side; a new task was created and the cached ids replaced) / `skipped (unchanged)` / `failed`.

