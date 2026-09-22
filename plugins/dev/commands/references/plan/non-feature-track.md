# `/dev:plan` — non-feature track (bug · story · task · epic)

Loaded by `plan.md` §2a.1 **only** when the resolved target is not a BA feature.
A feature run never reads this file, and a run that lands here never reads the
BA-feature stages (§2c BA-file check, split decision, sub-task compose) — those
describe inputs this target does not have.

Everything below replaces §2c through §4 for this target. `/dev:build` and
`/dev:commit` then run unchanged except for their run-file paths.

---

A ticket that never came from `/ba:features` has no `features/<slug>/` folder and must not be given a synthetic one. It lives at `tasks/<slug>.md` — one file, carrying only the tabs its type owns — and plans from there.

**Resolve the file.** If `tasks/<slug>.md` isn't on disk, auto-run `/jetrix:pull task <ref>` (its §7 fallback handles non-features). Still nothing → mark the target `SKIPPED_NO_SOURCE` and continue with the batch.

**Read order — graph first, source last** (`delivery-os-conventions` §6a):

1. `.jetrix/connection-map.md` — only when the ticket spans repos, to establish which are involved and how they talk.
2. `<repo>/context/code-context/` via **`tl-read-code-context`** — this is how you find the area. Never grep the repo to locate it; the graph carries validation rules, business logic and data-access that no single source file states.
3. The source files the units cite — **last**, and only for what the graph cannot answer.

The graph's job is to narrow; it is not always sufficient to *conclude*. A bug is usually a line-level defect — a missing null check, an ordering mistake, a wrong operator — and the unit summarises behaviour rather than reproducing lines. So the unit tells you the fault is in this handler; confirming *why* is exactly the "line-level detail the unit cites but doesn't reproduce" case §6a permits. Open the cited file then, having already narrowed to it.

What this rules out is starting in the source. Grepping for the symptom across the repo, before the graph has told you which unit owns the behaviour, is the contract violation §6a names — and for a bug it is also how you end up fixing the first plausible match instead of the actual cause.

No code-context for the area → do not fall back to grepping the whole repo. Mint a *missing context* blocker pointing at `/tl:code-map`, per `blocker-detection.md` §5.2a.

**Per-type input check** — this replaces §2c. Each type has a different definition of "enough to plan", taken from MC's `TASK_TYPE_TAB_CONFIG`:

| `task_type` | Required to plan | Acceptance source at build |
|---|---|---|
| `bug` | Steps to Reproduce **and** Expected Result non-empty | Expected Result |
| `story` | Acceptance Criteria non-empty | Acceptance Criteria |
| `task` · `epic` | Acceptance Criteria non-empty | Acceptance Criteria |

Missing a required input → do **not** invent it. Write a `PB-###` blocker into `tasks/<slug>/dev/plan-blockers.md` naming the empty tab, set the target `BLOCKED_ON_PLAN`, and continue the batch. `/dev:resolve --plan` walks it exactly as it does for features.

**Where the planned content is written — the ticket file is the push source of truth.**

Plan **writes back into `tasks/<slug>.md`**, then publishes it through the existing `/jetrix:push task` path as the last step of the same run. Routing the push through that path rather than calling `feature_upsert_bundle` reuses tab-splitting, identity, the stale-write guard, and the per-type gate instead of duplicating them.

```
tasks/<slug>.md               ← ticket AND push source. Plan edits this in place.
tasks/<slug>/dev/
  analysis.md                 ← reasoning, never pushed
  implementation.md           ← build's copy, keeps paths + unit ids
  plan-blockers.md
  status.md
```

Write-back rules for `tasks/<slug>.md`:

- **Frontmatter is identity — never rewrite it.** `feature_id`, `slug`, `jetrix_task_object_id`, `task_object_id`, `task_type` came from the pull and are what make the next push an *update* rather than a duplicate. `assemble-tasks.py` halts without `feature_id`, and `task_upsert_bundle` rejects a payload missing it.
- **Edit tab bodies under their existing `## Heading`.** `assemble-tasks.py` splits the body on those headings into tab fields; a heading the type doesn't own is dropped server-side with a `dropped_tabs` warning.
- **Only add headings the type owns.** A `bug` has Description, Steps to Reproduce, Actual Result, Expected Result and Implementation; only `epic` and `story` have Scope. A heading the type lacks writes a field the MC UI never renders.
- **Never touch `## Actual Result`.** It records what the reporter observed. Sharpen Expected Result and Steps to Reproduce if the investigation clarified them; leave the observation as filed.

**How `implementation.md` is composed, and where it lands.**

**First write the analysis scratchpad — compose refuses without it.** `tl-feature-compose` treats a missing scratchpad as a hard precondition failure, because §1, §2, §7 and §8 are built from it; without one the run either stops before composing or produces free-form prose instead of the frame. A filed ticket has no Stage 2 of its own, so produce the scratchpad here, at `tasks/<slug>/dev/analysis.md`, in the shape the skill's input contract specifies:

```yaml
---
doc_type: analysis-scratchpad
schema_version: 1.0
produced_by: dev
feature_id: <the ticket's feature_id, e.g. TASK-11>
task_number: 11
task_type: bug
generated_at: <ISO>
---
build_sequence:        # → §1
  - step: "..."
    files: ["Modified: <path>"]
    units: [PAGE-...]
    satisfies: [EXP-1]     # bug: Expected Result ids; else AC/BR ids
    notes: "..."
impact_matrix:         # → §2  (N/A is a valid value, use it freely)
  frontend: <impact>
  backend: N/A
  database: N/A
  ...
risks_and_rollback:    # → §7
  risks:
    - description: "..."
      severity: low | medium | high
```

Fill it from the graph-first read above — the units you opened, the files they cite, what the change touches. `N/A` is the right answer for most dimensions on a small fix; write it rather than omitting the key.

Then compose with **`tl-feature-compose` in implementation mode — the same §1–§8 frame a feature gets**, against that scratchpad plus the ticket's tabs and the code-context units. Write the result to `tasks/<slug>/dev/implementation.md`. `/dev:build` reads it from there.

**If compose still refuses, that is a real halt — do not hand-write the plan instead.** A prose substitute looks like progress and silently drops the file targets, rollback lever, and `Satisfies` links the build depends on. Report the refusal and why.

**The frame is not optional for small work.** A one-line CSS fix gets §1 through §8 exactly as a multi-repo feature does:

| | |
|---|---|
| §1 Build sequence | ordered steps table (`# / Step / Files / Units / Satisfies`) + mermaid step-graph. **Files names the concrete path per step** (`Modified: src/components/Home.css`). |
| §2 Impacted components | the impact matrix, dimensions picked for the repo shape |
| §3 Operations | `None.` when the change exposes or consumes none |
| §4 Stored data | `None.` when nothing is persisted |
| §5 User-facing surfaces | the page or screen the change is visible on |
| §6 Touch points | Reuse / New table |
| §7 Risks and rollback | risks table + out of scope + the cheapest rollback lever |
| §8 Shared contract | invariants the change must not break; `None.` if it stands alone |

A section that genuinely doesn't apply is **one line — `None.`** — never a paragraph explaining why, and never a missing heading. That is how the frame stays scannable and how a reader can tell "nothing here" apart from "nobody thought about it".

**Never write the plan as prose.** Free-form paragraphs — "four colour values change and nothing else is touched" — carry the same facts in a shape nothing can parse: no step order, no file targets, no rollback lever, no `Satisfies` links back to the acceptance criteria. They also render as a wall of text in the Mission Control tab, where the feature frame renders as tables and a step-graph. A bug's plan is read by the same people, in the same tab, and gets the same shape.

**Then write it into the ticket under a `## Implementation` heading, for every type.** Every task type carries an Implementation tab, so a bug's plan is as visible on the board as a feature's. There is no type for which the plan stays hidden, and no separate command to publish it — the same `/dev:plan` run that composed it puts it in the ticket file.

The ticket's `## Implementation` section and `dev/implementation.md` carry **the same content, paths included**. The Implementation tab is a build spec — `conventions` §6b exempts it from the reader-facing strip, and `tl-feature-compose` Rule 1 *requires* concrete paths in §1's Files column, §4, §5 and §6. Only §8 Shared contract stays path-free.

The reader-facing strip applies to Description, Steps to Reproduce, Actual Result and Expected Result — not here. A build sequence that says "give the sign-in page a flag" without naming `Modified: src/components/Home.jsx` is not buildable and not reviewable; that is the failure mode this exemption exists to prevent.

**Which Description shape this ticket gets.** Implementation is one frame for every type; Description is not, and that is deliberate — a bug report and a user story are different kinds of statement, and forcing either into the other's shape destroys it. Pick by `task_type`:

| `task_type` | Description shape | Why |
|---|---|---|
| `story` | `tl-feature-compose` **description mode** — the 6-section user-story format (User story · User scenarios · Business rules · What users see when refused · Out of scope · Related) | A story *is* a user story. It gets the same shape a feature's sub-task gets. |
| `bug` | The reporter's text verbatim, with `### Analysis` appended below | Nobody *wants* a crash. "As a user, I want the button to be black" is a fiction that discards what was actually observed. |
| `task` · `epic` | The filer's statement of the work, with `### Analysis` appended | Ad-hoc work is stated, not story-shaped. Don't invent a role and a benefit that nobody wrote. |

For the `story` path, the compose skill's formatting rules apply unchanged — `##` headings only, business vocabulary, no status codes, field names, file paths, framework names, tables, code fences, or mermaid. Its inputs come from the ticket's own tabs rather than a `feature.md`, since there isn't one.

**Updating Description from the analysis.**

The analysis usually learns something worth recording — root cause, the file that actually owns the fault, why the obvious fix is wrong. That belongs in Description, which every type has.

- **Never overwrite what the reporter wrote.** Their text is the primary observation and the only account of what a human actually saw. Keep it verbatim and append below it.

- **Tab content is reader-facing — strip file paths, framework names, and provenance.** This is `delivery-os-conventions` §6b, which applies to every producer and every task type, not a rule specific to this track. A ticket is read by designers, QA, and PMs in the Mission Control UI; `src/components/Home.css:1-7`, `PAGE-AUTH-01`, `PB-003 / DEC-003` and `FND-15` mean nothing to them and date the moment the code moves. Never put these on a tab:

  | Never on a tab | Where it goes instead |
  |---|---|
  | file paths, line numbers | `dev/analysis.md`, `dev/implementation.md` |
  | unit ids (`PAGE-…`, `EP-…`, `ENT-…`) | `dev/analysis.md` |
  | blocker / decision ids (`PB-###`, `DEC-###`) | `dev/plan-blockers.md`, decision log |
  | finding ids, framework and file names | `dev/analysis.md` |

  Describe what a person sees and what will change:

  ```
  ## Description
  <reporter's original text, untouched>

  ### Analysis
  <What the affected element actually is, in UI terms — its visible label and
  where it appears. What it looks like today. What will change, and anything
  that needs a human's nod, such as removing a deliberate visual design.>
  ```

  `/dev:build` gets its precision from `dev/implementation.md`, which keeps every path and id. The ticket carries the decision; the plan carries the co-ordinates.

- **An unrelated defect found while investigating is not an edit to this ticket.** Report it in the run summary so the user can file it separately. Appending it to a Description makes it invisible to triage and confusing to whoever reads this ticket.

- **Only record what the code supports.** An unsupported guess belongs in `dev/analysis.md`, not on the ticket where it reads as established fact to everyone else.
- **A contradiction is a blocker, not an edit.** If the analysis disagrees with the ticket, do not rewrite the ticket to match your reading — mint the `PB-###` per `blocker-detection.md` §5.2a and let the user settle it. Sharpening wording is fine; changing the claim is not.
- **`## Actual Result` stays as filed**, always. It is the observation, not a conclusion.

**Publish it — `/dev:plan` does this itself, as the last step.** A filed ticket is not left half-planned on disk waiting for a second command; the plan is on the board when the run finishes, exactly as it is for a feature. Run the existing task push against this one file:

```
/jetrix:push task <task-number>
```

**Report it so the user knows it is already done.** The whole point of publishing inside the run is that there is nothing left for them to do — say that plainly and give them the link, rather than listing what changed and leaving them to wonder whether it reached the board. Read the URL from the push response's `view_url` (`plan.md` §7 Rule 7.0 — never construct it locally):

```
✓ Task-11 planned and published to Mission Control

  Description      analysis appended below the reporter's text
  Expected Result  sharpened
  Implementation   written
  Actual Result    untouched

  ↳ https://<mc>/task/6ab14494440dd357a0c78442   ✓ verified

  Already up to date on the board — nothing to push.
  Next:  /dev:build 11
```

Rules for that block, same as the feature track's:

- **Every line that names the ticket carries its URL.** If you print a `task_object_id` without one, the summary is incomplete — recompute and re-render before printing.
- **State that it is already published**, in those words. "Pushed" alone reads like a step they still have to take.
- Name every tab you changed *and* the ones you deliberately did not, so the reporter's untouched text is visibly untouched.
- On a stale-write refusal or `--dry-run`, the same block says so instead: what is on disk, what is **not** on the board, and the exact command to reconcile.

The push is a full-field update: `task_upsert_bundle` replaces each tab it sends. That is why the write-back preserves the reporter's text rather than emitting only the new analysis — whatever is in the file after `/dev:plan` becomes the ticket.

**Two cases where it does not publish**, both of which must be stated in the summary rather than passed over:

- `--dry-run` → compose and write locally, touch nothing in Mission Control.
- The push is refused as a stale write (someone edited the ticket in MC since your last pull) → leave the local work in place, report the conflict, and tell the user to `/jetrix:pull task <n>`, reconcile, and re-push. Never force it.

**Never split a non-feature into sub-tasks.** `bug`, `story`, and `subtask` are in MC's `PLANNING_NOT_REQUIRED_TYPES`; a bug is a point fix. Plan the parent alone and skip the split confirmation checkpoint for these targets — there is nothing to confirm.

**Push only the tabs the type owns.** From `TASK_TYPE_TAB_CONFIG`: every type carries Description and Implementation; `bug` adds Steps to Reproduce, Actual Result and Expected Result; only `epic` and `story` carry Scope. Sending a key the type does not own writes content the MC UI never renders, so the work looks saved and is unreachable. `task_upsert_bundle` drops out-of-type tabs server-side and returns `dropped_tabs` + a `warning` — treat either as a compose bug on our side, not as a normal outcome, and report it in the run summary.
