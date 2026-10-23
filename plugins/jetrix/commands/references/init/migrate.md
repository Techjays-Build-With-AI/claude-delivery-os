# /jetrix:init — layout migration

Runs **before any tracker call**, on every init and every refresh. Idempotent: it short-circuits
when the layout is already current, so a re-run costs a directory listing.

**Never destructive.** Every step moves or renames; nothing is deleted. A workspace that fails
halfway is left readable, and the next run finishes the job.

## Two migrations, in this order

| From | To | Moves |
|---|---|---|
| **v1** — role folders under `.jetrix/<slug>/` | v2 | the `<slug>/` wrapper away |
| **v2** — one `ba/` per workspace | **v2.1** | `ba/` → `requirements/<slug>/` |

Run v1→v2 first; it produces the `ba/` that v2→2.1 then moves. A workspace already on v2.1 matches neither
and costs one directory listing.

---

## 1. v2 → v2.1 — `ba/` becomes a requirement

**Detect:** `.jetrix/ba/` exists. (On v2.1 it does not — `requirements/` does.)

**Why this cannot be skipped.** Every command now resolves `requirements/<slug>/`. A workspace left on v2 has its
scope at `ba/scope.md`, so the lookup finds nothing, the agent is told *"no requirements exist — run `/ba:scope`"*,
and it builds a **second scope beside the first**. The run reports success. Nothing downstream can tell.

**Name the requirement first.** In order, stop at the first that yields a value:

1. `Requirement:` in `ba/scope.md` front matter → slugify it (lowercase-kebab).
2. The scope's `# ` H1 → slugify.
3. `solutionSlug` from `project.json`.
4. Nothing readable → `requirement-1`, and **say so in the summary** so the user can rename the folder before
   anything references the slug.

**Then move — never copy, never delete:**

```
.jetrix/ba/scope.md            →  .jetrix/requirements/<slug>/scope.md
.jetrix/ba/scope.html          →  .jetrix/requirements/<slug>/scope.html
.jetrix/ba/artifacts/          →  .jetrix/requirements/<slug>/artifacts/
.jetrix/ba/reviews/            →  .jetrix/requirements/<slug>/reviews/
.jetrix/features/              →  .jetrix/requirements/<slug>/features/

.jetrix/ba/registers/data.md         →  .jetrix/shared-context/data.md
.jetrix/ba/registers/integrations.md →  .jetrix/shared-context/integrations.md
.jetrix/ba/registers/*               →  .jetrix/requirements/<slug>/registers/
```

`data.md` and `integrations.md` move **up**, not across: entities and integrations belong to the system, and
`tl-feature-planning` cites `DATA-###` when it mints `ENT-` units. Leaving them per-requirement would make
`DATA-001` mean two different things.

**Merge the four into two.** These are concatenations, not moves, so do them last and **append rather than
overwrite** — a partial run must never lose a row:

| From | Into | As |
|---|---|---|
| `ba/intake.index.md` | `requirements/<slug>/sources.md` | the rows as they stand |
| `ba/logs/indexing-assistance-needed.md` | `requirements/<slug>/sources.md` | `Status: Needs User Guidance` |
| `ba/logs/clarifications.md` | `requirements/<slug>/ledger.md` | `kind: question` |
| `ba/logs/contradictions.md` | `requirements/<slug>/ledger.md` | `kind: contradiction` |
| `ba/registers/assumptions.md` | `requirements/<slug>/ledger.md` | `kind: assumption` |

**Carry every ID across unchanged.** `CLR-021` stays `CLR-021`. They are append-only and cited from the scope,
the features and the decision log; renumbering during a migration silently breaks every citation.

**Leave behind, and say so:** `ba/client-questions.md`, `ba/open-questions.md`, `ba/logs/changes.md`,
`ba/intake-runs/`, `features/feature-index.md`, `features/tracker.md` and every
`features/<slug>/implementation-plan.md`. These became rendered views or were dropped. **Move them to
`.jetrix/_migrated-v2/` rather than deleting them**, and name the folder in the summary — the content is the
user's, and a migration is not the moment to decide they will not want it.

**Rewrite `cache/sync-state.json` keys** from the old paths to the new ones, and re-key `reports.scope` to
`reports["<slug>"].scope`. A stale key makes the next `/ba:scope` compare new sources against the old paths'
hashes, so unchanged-looking files are skipped and the run ingests nothing while reporting success.

**Report what moved**, file count and the slug chosen. A silent migration is indistinguishable from no migration.

---

## 2. v1 → v2 — drop the `<slug>/` wrapper

**Runs before any tracker call.** Detects the old v1 layout — where role folders lived under `.jetrix/<slug>/` — and moves them up to the workspace-level `.jetrix/`. Safe to re-run on a v2 workspace (short-circuits when nothing matches).

**Detection:** loop through every subfolder of `.jetrix/` (excluding `cache/`, `shared-context/`, `requirements/`, `ba/`, `features/`, `qa/`, `dev/`, `doc/`, `tasks/`). If a subfolder contains any of `ba-output/`, `tl-output/`, `qa-output/`, `dev-output/`, `doc-output/`, `shared-context/`, or `context/features/` — it's a v1 slug folder. Migrate it.

**Migration steps (per detected slug folder — usually exactly one):**

1. **Rename role folders (drop `-output` suffix):**
   ```
   .jetrix/<slug>/ba-output/    → .jetrix/ba/
   .jetrix/<slug>/tl-output/    → .jetrix/tl-reviews/
   .jetrix/<slug>/qa-output/    → .jetrix/qa/
   .jetrix/<slug>/dev-output/   → .jetrix/dev-legacy/   (see step 6)
   .jetrix/<slug>/doc-output/   → .jetrix/doc/
   ```

2. **Promote shared-context/ to the top level** (name unchanged, wrapper removed):
   ```
   .jetrix/<slug>/shared-context/ → .jetrix/shared-context/
   ```

3. **Promote features/ to top level:**
   ```
   .jetrix/<slug>/context/features/ → .jetrix/features/
   ```

4. **Move code-map registry under tl/:**
   ```
   .jetrix/<slug>/context/code-map-registry.md → .jetrix/code-map-registry.md
   ```

5. **Move artifacts/ under ba/:**
   ```
   .jetrix/<slug>/artifacts/ → .jetrix/requirements/<slug>/artifacts/
   ```

6. **Move `dev-legacy/feature-status.md` to each feature’s own `status.md`; delete the (now empty) `dev-legacy/`:**
   ```
   .jetrix/dev-legacy/feature-status.md → .jetrix/each feature’s own `status.md`
   rmdir .jetrix/dev-legacy/
   ```

7. **Group BA flat files into subfolders:**
   ```
   .jetrix/ba/requirement-register.md    → .jetrix/requirements/<slug>/registers/requirements.md
   .jetrix/ba/workflow-register.md       → .jetrix/requirements/<slug>/registers/workflows.md
   .jetrix/ba/use-case-register.md       → .jetrix/requirements/<slug>/registers/use-cases.md
   .jetrix/ba/business-rule-register.md  → .jetrix/requirements/<slug>/registers/business-rules.md
   .jetrix/ba/example-register.md        → .jetrix/requirements/<slug>/registers/examples.md
   .jetrix/ba/data-register.md           → .jetrix/shared-context/data.md
   .jetrix/ba/integration-register.md    → .jetrix/shared-context/integrations.md
   .jetrix/ba/assumption-register.md     → .jetrix/requirements/<slug>/ledger.md` (kind: assumption)
   .jetrix/ba/clarification-log.md       → .jetrix/requirements/<slug>/ledger.md` (kind: question)
   .jetrix/ba/contradiction-log.md       → .jetrix/requirements/<slug>/ledger.md` (kind: contradiction)
   .jetrix/ba/indexing-assistance-needed.md → .jetrix/requirements/<slug>/sources.md` (Status: Needs User Guidance)
   .jetrix/ba/change-log.md              → .jetrix/the review's “Since the last round” section
   .jetrix/ba/scope-reviews/             → .jetrix/requirements/<slug>/reviews/
   ```

8. **Group QA + DOC files:**
   ```
   .jetrix/qa/test-audit-*.{html,md,json}  → .jetrix/qa/reviews/
   .jetrix/doc/deck-*.pptx                 → .jetrix/doc/decks/
   .jetrix/doc/walkthrough-*.html          → .jetrix/doc/walkthroughs/
   .jetrix/doc/workflow-*.html             → .jetrix/doc/workflows/
   .jetrix/doc/board-*.html                → .jetrix/doc/boards/
   ```

9. **Delete empty v1-only folders:**
   ```
   .jetrix/<slug>/context/frontend/     (empty since Model B — the code graph moved to <repo>/context/code-context/)
   .jetrix/<slug>/context/backend/
   .jetrix/<slug>/context/database/
   .jetrix/<slug>/context/project/
   .jetrix/<slug>/context/               (wrapper, now empty)
   .jetrix/<slug>/                       (last)
   ```
   Only delete these if they are actually empty after the moves above. Non-empty folders stay put and print a warning.

10. **Rewrite sync-state keys** — `.jetrix/cache/sync-state.json` had per-file keys like `ba-output/scope.md`. Rewrite each key using the same rename table above (`ba-output/scope.md` → `requirements/<slug>/scope.md`, `ba-output/requirement-register.md` → `requirements/<slug>/registers/requirements.md`, etc.). Content hashes and Jetrix task IDs stay identical; only the string keys change.

11. **Report** — print a summary: `Migrated <slug>: <N> folders moved, <M> BA register/log files grouped, <K> sync-state keys rewritten.`

**Idempotency:** re-runs are safe. If none of the v1 markers are present, the whole section is a no-op. Each individual move is a `test -e OLD && ! -e NEW` guard.

**Failure handling:** if any step fails partway (e.g., file exists at both old and new location) — print the specific error, halt with `Migration incomplete. Fix the conflict listed above and re-run /jetrix:init.` and do NOT continue to §4. Never leave the workspace in a half-migrated state without telling the teammate.

---

## After either migration

Both produce a v2.1 layout, so **run the v1 steps first and then fall through into the v2→2.1 steps** — v1→v2
yields exactly the `ba/` that v2→2.1 expects. Doing them in one pass is what makes a two-version-old workspace
land correctly instead of half-migrated.
