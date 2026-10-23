---
description: Remove a finished requirement's local working copy, after checking what has and hasn't reached the tracker. Takes one or more requirement paths or slugs. Checks five things before touching anything — scope push, feature push, implementation push, dev state, open PRs — prints what is local-only and would be lost, then asks. Never deletes from the tracker, never touches shared-context/ or a product repo, never closes a PR. Removes the requirement's cache/sync-state.json rows in the same operation.
argument-hint: "<requirement-path-or-slug> [<more> …]"
---

# /jetrix:clear

Requirements finish. Clearing one should be a command, not an `rm -rf` — and it should refuse to be silent about what the tracker does not yet have.

It lives under `jetrix` rather than `ba` because **the sync boundary is what makes the check possible**. Only the bound tracker can say whether what is on disk also exists somewhere it will survive.

```
/jetrix:clear requirements/shift-timesheet
/jetrix:clear requirements/shift-timesheet requirements/payroll-export
/jetrix:clear shift-timesheet                 # a bare slug resolves to the folder
```

Read the `delivery-os-conventions` skill first if it isn't in context — §1.d covers slug resolution, §1.c the tracker block.

## 1. Resolve the targets

Each argument is a requirement path or a bare slug. Resolve every one **before checking anything**, so a typo is caught before any work is reported.

- Unknown slug → stop, listing the requirements that do exist. Never fuzzy-match: clearing the wrong requirement is unrecoverable from here.
- No arguments → list the requirements with their feature counts and ask which. Never default to "all" or to the most recent.
- `requirements/` doesn't exist → say the workspace has no requirements yet and stop.

## 2. Check five things

All five, for every target, before printing anything. A check that cannot run is reported as **unknown**, never as a pass — this is the one place where false comfort is expensive.

| Check | How | Reports |
|---|---|---|
| **Scope push** | Hash every file `/jetrix:push scope` sends — `scope.md`, `registers/*`, `ledger.md`, `sources.md` — against its `contentHash` in `cache/sync-state.json` | `✓ pushed` · `⚠ N unpushed` · `⚠ never pushed` |
| **Feature push** | Each `features/<slug>/` has a tracker ref in frontmatter and its content hash matches sync-state | the issue keys, or which features exist only locally |
| **Implementation push** | Each unit's `implementation.md` against the stored Implementation hash | per unit, by name — composed-but-never-pushed is the common case |
| **Dev state** | Every unit's `status.md` `status`, plus `git status` on its branch | anything not `DONE`, its branch, and the uncommitted file count |
| **Open PRs** | `gh` where available, on the branches this requirement's units recorded | open PR urls — clearing the folder does not close them |

**Dev state is checked separately from the three pushes, and that is the point.** A unit at `inProgress` with uncommitted work on a branch is not a sync problem, and no amount of pushing fixes it. Folded into "unpushed" it would read as something a push could solve.

**On a non-Jetrix tracker** the same five run. The refs are `tracker_issue_ref` rather than `jetrix_task_object_id`, resolved through `mapping.read_issue` on `tracker.mcp`; the hashes are the same sync-state rows either way. Where `mapping.read_issue` is `null`, report the push checks as **unknown** and say which tracker could not be queried — do not infer from local state alone.

**`gh` missing** → report open PRs as `unknown — gh not installed`, not as `✓ none`.

## 3. Print the report, then ask

Never clear without printing this first — **not even when everything is pushed and every feature is `DONE`.** It is one screen, and it is the only record of what existed.

```
Checking shift-timesheet before clearing…

  Scope            ✓ pushed        scope.md v3 · 5 registers · ledger
  Features         ✓ pushed        11 features → Feature-4 … Feature-14
  Implementation   ⚠ 2 unpushed    supplier-onboarding · outlet-discovery
  Dev state        ⚠ 1 in flight   supplier-onboarding/units/backend  inProgress
                                   branch feature/FEAT-SUP-001-…-backend
                                   18 files uncommitted
  Open PRs         ✓ none

Local-only — going if you clear
  reviews (3 rounds) · artifacts (8 summaries) · sources.md · ledger
  11 features' dev state — analysis, findings, run history

  1 · Push what is unpushed, then clear
  2 · Clear anyway — the 2 unpushed implementations and all local-only work are lost
  3 · Cancel
```

**Option 2 stays on the menu.** Clearing without pushing is a legitimate choice — a requirement that was explored and abandoned does not need to reach the tracker first. This command's job is to make sure the choice isn't made blind, not to prevent it.

**Name what is local-only every time**, even when all three pushes are clean. Reviews, artifacts, `sources.md`, `ledger.md` and every unit's dev audit are never pushed anywhere, so "everything pushed" still means losing them. Someone reading `✓ pushed` three times will assume otherwise unless told.

### Several at once

Check every path, then print one combined report and ask once.

```
/jetrix:clear requirements/shift-timesheet requirements/payroll-export requirements/vendor-portal

shift-timesheet    ⚠ 2 unpushed implementations · 1 unit inProgress
payroll-export     ✓ everything pushed · all 6 features DONE
vendor-portal      ⚠ never pushed — scope and 4 features are local only

  1 · Push what is unpushed, then clear all three
  2 · Clear only the clean one           payroll-export
  3 · Clear all three anyway
  4 · Cancel
```

**Option 2 exists because it is usually what someone means** — finish the tidy-up where it is safe and leave the rest for a decision. One dirty requirement never blocks the clean ones.

## 4. Clear

Remove `requirements/<slug>/` entirely — scope, `scope.html`, `sources.md`, `ledger.md`, `artifacts/`, `registers/`, `reviews/`, and `features/` with every unit's analysis, findings, status, PR summaries and discussion beneath it.

**Then remove that requirement's rows from `cache/sync-state.json`, in the same operation.** This is the part that bites if it is missed. `sources.md`'s hashes live there, and `/ba:scope` already warns about the shape of this failure: leave the hashes behind and the next requirement's sources are compared against the old one's, so **unchanged-looking files are skipped and the run quietly ingests nothing while reporting success.**

## 5. Never

Six rules, none negotiable.

- **Never clear without printing the report first.**
- **Never touch `shared-context/`.** Glossary, decision log, stakeholder map, system landscape, `data.md` and `integrations.md` are project-level truth that outlives any one requirement. `/ba:scope` draws this line; clear honours it.
- **Never touch a product repo.** Branches, uncommitted work and `context/code-context/` stay. Report them and stop there — removing a folder in `.jetrix/` is not a reason to touch someone's git state.
- **Never close a PR.** An open PR is reported with its url and left open. The branch outlives the requirement folder.
- **Never delete from the tracker.** Clear removes the local working copy. The issues, the scope document and the history stay on the board — that is the whole point of having pushed.
- **Never clear a requirement that was not named.** Not "and the empty one too", not "and its abandoned sibling".

Also kept, because they are not requirement work: `qa/` (repo-scoped), `tasks/` (non-requirement tickets), `project.json`, `connection-map.md`, `code-map-registry.md`, `cache/` itself.

## 6. Report

```
✓ Cleared shift-timesheet

  Removed   requirements/shift-timesheet/   11 features · 3 review rounds · 8 summaries
  Also      14 sync-state rows

  Kept      shared-context/ · qa/ · tasks/ · every product repo
  On the board   Feature-4 … Feature-14 and the scope document are untouched

Remaining requirements
  payroll-export    6 features
```

If an open PR was reported, repeat its url here — it is the one thing that outlives the clear and still needs a human.

Close with one line, chosen from what is left:

| | |
|---|---|
| Requirements remain | nothing to run — name them and stop. The workspace is still live. |
| That was the last one | `/ba:scope add "requirements in <path-or-link>"` to start the next one. |

Never print `/jetrix:init` as the next step. The workspace is still bound — `project.json`, `shared-context/`
and every repo survived the clear, and re-initialising would be undoing work the user did not ask to undo.

## What this replaces

There was no clear command. The nearest thing was `/ba:scope mode=full-refresh`, which backs up the previous `ba/` and overwrites — it made room by destroying, and the backup was the only safety net.

With `requirements/<slug>/` a second requirement no longer needs room made for it, so clearing stops being a side effect of starting over and becomes a deliberate command you run when a requirement is genuinely finished.
