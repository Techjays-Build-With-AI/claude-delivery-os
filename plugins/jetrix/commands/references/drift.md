## Drift detection — local files vs sync-state

Shared helper referenced by `/jetrix:push`, `/jetrix:pull`, and `/dev:build`. Answers "what have I changed locally since last sync with Jetrix, and does the user want to push those changes before this command continues?"

### Reference point

`.jetrix/cache/sync-state.json` stores per-key hashes. Two per feature (BA content vs TL implementation), one per scope / context doc:

```json
{
  "tasks/<feature_id>": {
    "contentHash":         "sha256:...",  // hash of the 8 BA files concatenated
    "implementation_hash": "sha256:...",  // hash of tl-plan.md body (frontmatter stripped)
    "taskNumber": 42, "taskObjectId": "<oid>", "lastPushed": "<iso>"
  },
  "documents/<path>": {"contentHash": "sha256:...", "lastPulled": "<iso>"}
}
```

**If `sync-state.json` itself is missing** (fresh clone, never pushed) → treat every file as "new". Continue silently — no prompt on first-ever run.

For every file the current command touches:

- Missing sync-state entry → **new** (never pushed)
- Hash matches → **clean**
- Hash differs → **drifted** (local ahead of Jetrix)

### Which files to hash for which command

| Command | Files to hash | Compare against |
|---|---|---|
| `/jetrix:push feature` | 8 BA files: `feature.md`, `workflow.md`, `business-rules.md`, `acceptance-criteria.md`, `nfrs.md`, `test-scenarios.md`, `dependencies.md`, `open-questions.md` — per feature folder | `tasks/<feature_id>.contentHash` |
| `/jetrix:push implementation` | `tl-plan.md` body (frontmatter stripped) per feature folder | `tasks/<feature_id>.implementation_hash` |
| `/dev:build <target>` | BOTH sets above, for the target feature folder only | Both keys above; drift on either → drifted |
| `/jetrix:pull scope\|context` | Every file the pull would overwrite (per manifest) | `documents/<path>.contentHash` |

### One Bash call for the whole set

Never `Read` files individually to hash them — that burns turns. One bash loop:

```bash
for f in <paths>; do
  if [[ -f "$f" ]]; then
    printf "%s|%s\n" "$f" "$(sha256sum "$f" | cut -d' ' -f1)"
  else
    printf "%s|MISSING\n" "$f"
  fi
done
```

Parse; compare each hash to `sync-state.json[key].contentHash`.

### Present drift + prompt

If drift is empty → continue silently. No prompt.

If drift is non-empty:

```
⚠ Local changes not yet on Jetrix:
    ● features/user-auth/feature.md       (drifted, last push 2d ago)
    ● features/user-auth/dependencies.md  (new — never pushed)
    ● features/user-auth/tl-plan.md       (drifted, last push 15m ago)

  Continue? (y = build with local as-is / s = stop and let me push first): 
```

- **y** → continue the current command against local state. Note in the run summary: `⚠ drift ignored: <count> files`.
- **s** → stop cleanly. Print exactly the recommended push and re-run:
  ```
  Run: /jetrix:push feature <slug>
  Then re-run: /dev:build FEAT-<AREA>-NN
  ```
  Exit the current command; do not proceed.

### Where drift check is invoked

- **`/jetrix:push feature`** and **`/jetrix:push implementation`** — no prompt needed (the push IS the sync); use drift detection to skip clean files and only send drifted ones. Show "N drifted, M clean, skipping M" summary at the top.
- **`/jetrix:pull scope|context`** — before overwriting, warn if a local file about to be replaced has drift: `⚠ local file <path> has unpushed changes; overwrite? (y/N)`. Default no. Skipping keeps the local drift; user decides when to push.
- **`/dev:build <target>`** — at the start of the readiness gate. Check the target feature's folder for drift; prompt as above. Do not check other features' folders (would be noise).

### Update rule

`sync-state.json` is written ONLY after a **successful push** (per step 6 of each push flow) or a **successful pull** (per step 4 of each pull flow). A "continue with drift" choice does NOT update sync-state — next run still sees the same drift, still prompts.
