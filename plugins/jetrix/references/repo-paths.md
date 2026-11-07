# Resolving local repo paths — ask, don't scan

Every skill that needs to reach into a repo (`tl-feature-planning` (internal), `/dev:plan` Stage 2 compose,
`/dev:build`, and any other) uses the same rule to find the absolute path
of an app's local clone. The paths live in
`<workspace>/.jetrix/cache/repolocation.json`, which `/jetrix:init` step 9
seeds — keyed by `projectId`.

## Two kinds of "no path"

| State | Written as | Asked again? |
|---|---|---|
| the teammate does not work on this app | `"SKIPPED"` | **no** — except on an explicit refresh (rule 4) |
| the repo does not exist yet | **key omitted** | **yes**, every run |

Collapsing these is the bug worth avoiding. A greenfield app whose repo `/tl:scaffold` has
not created yet is *undecided*, not declined — writing `SKIPPED` there means no command ever
offers to bind it once the code exists.

The asymmetry in rule 4 is deliberate: a feature command that nags about a repo the user
declined is noise, but a teammate who typed `/jetrix:pull` is asking what changed, and a repo
that has since been cloned is exactly that.

## Contract

```
Need a local path for projectId "<pid>"?

1. Read <workspace_root>/.jetrix/cache/repolocation.json.
2. If it contains "<pid>": "<absolute path>" AND that folder exists → use it. Done.
3. If it contains "<pid>": "<absolute path>" AND the folder is missing →
     ask the user:
       "Your recorded path for <projectName> (<old-path>) doesn't exist.
        New absolute path, or 'skip'?"
     Update the JSON with the answer.
4. If it contains "<pid>": "SKIPPED" → the user opted out of this repo.
     Skip silently; do NOT ask again.
     EXCEPTION: an explicit refresh (/jetrix:pull, /jetrix:init) MAY re-offer it
     once — the user typing a refresh IS the request to revisit. Every other
     caller honours the skip in silence.
5. If "<pid>" is not in the JSON at all → ask the user:
       "Where's the <projectName> (<projectType>) repo on your laptop?
        Absolute path, or 'skip' if you don't work on this app."
     Update the JSON with the answer.

NEVER scan the filesystem (no `find`, no `git grep`, no $HOME walk). The
teammate knows where their repos live; ask them.
```

## Writing the JSON — read → merge → write

Every update is a **merge**, not a replace. Example:

```json
// before
{
  "68e1..proj-1..": "/Users/alice/Code/acme-frontend",
  "68e1..proj-2..": "SKIPPED"
}

// after user answers "/Users/alice/Code/acme-mobile" for proj-3
{
  "68e1..proj-1..": "/Users/alice/Code/acme-frontend",
  "68e1..proj-2..": "SKIPPED",
  "68e1..proj-3..": "/Users/alice/Code/acme-mobile"
}
```

Preserve every existing entry. Never overwrite the whole file with a
partial map.

## When you write, tell the teammate

One line per change, terse:

```
✓ set acme-mobile → /Users/alice/Code/acme-mobile
· acme-cron skipped, will fall back to workspace-level notes
```

## When a required repo ends up SKIPPED

That's not an error — proceed against workspace-level notes for that
repo's units and log a `DEC-###` explaining the skip. A later re-run
after the teammate clones the repo will pick it up automatically.

## Project name / type lookup

Read `<workspace_root>/.jetrix/project.json`. Its `apps[]` array has one
entry per app with `projectId`, `name`, and `projectType` — that's what
you use in the ask-user prompts.
