# Deriving the registry from a context tree that already exists

`/tl:code-map` writes the registry as the last step of mapping a repository it has just read.
That is not the only way a workspace ends up with a code graph. A **greenfield** project built
through Delivery OS has one too: `tl-feature-planning` authored the units forward, and
`/dev:build` Stage 10 flipped them `designed` → `implemented` as each was built. The tree is
real, current and committed — it simply never went through a reverse-map, so no registry row
was ever minted.

**A missing registry is therefore not evidence of a missing graph.** Any consumer that treats
it as one tells a team with a fully mapped product to go map it.

This file is the derivation: how to mint registry rows from context trees that already exist,
reading **no source code at all**. It is cheap — a handful of index files — and it is lossless,
because every column the registry holds is already recorded somewhere in the tree or the
workspace wiring.

## When it applies

| Workspace state | What to do |
|---|---|
| registry exists with a row for the repo | nothing — read it |
| no registry (or no row), **and** `<repo>/context/code-context/` exists with units | **derive the row here**, then continue |
| no context tree for the repo | derivation is impossible — only `/tl:code-map` can read code. Say so and name it |

The third row is the only stop. Deriving a row for a repo with no tree would be inventing a
graph, which is the one thing this must never do.

## Frontmatter

The derived file is a `code-map-registry` like any other, so it carries that contract's
frontmatter unchanged — **`produced_by: tl` whoever ran the derivation**, because the document
type belongs to the TL layer and a consumer filtering by producer must still find it. Deriving
it from inside another command does not make it that command's document:

```yaml
---
doc_type: code-map-registry
schema_version: 1.3
produced_by: tl
status: Emerging
generated_at: YYYY-MM-DD
derived_from: registry-from-context     # present only on a derived registry
---
```

`derived_from` is the one added key. It is what tells a later `/tl:code-map` that these rows
were never read from code, so it reconciles them rather than treating them as its own prior
output.

## Where the file lives

`<workspace>/.jetrix/code-map-registry.md` — the `.jetrix/` root, beside `project.json` and
`connection-map.md`. **A file at the legacy `.jetrix/tl/code-map-registry.md` is read and moved
to the root**, because older scaffolds wrote it there; a stub carrying no rows is replaced
rather than preserved.

## Every column, and where it comes from

| Column | Source | Never |
|---|---|---|
| Repo key | `project.json` `apps[].projectSlug`, else the repo folder name | invented |
| Path | `cache/repolocation.json`, keyed by `projectId` | guessed from the repo name |
| Layers | which `code-context/<layer>/` directories exist | assumed from `projectType` |
| Code context root | `./code-context/` | — |
| Mapped at commit | `git rev-parse --short HEAD` in that repo | left blank |
| Last mapped | the newest unit-file modification date in the tree | today, when the tree is older |
| Units | counted from each layer index's `## Units` table | estimated |
| Source | `reverse-mapped` or `forward-planned` — see below | omitted |

**`Source` is not decoration.** A derived row describes a tree `/tl:code-map` has never read, so
a later run of it must reconcile that tree rather than assume its own provenance fields are
present. Read it from the units themselves: `origin: reverse-mapped` → `reverse-mapped`;
`origin: implemented` or `designed` → `forward-planned`. A tree holding both is
`reverse-mapped` for the rows that carry it and the mixed value is recorded as `mixed`.

**Area tokens** come from the unit ids already in the indexes — the `<AREA>` of every
`PAGE-/EP-/ENT-<AREA>-NN`. They are read, never minted: the ids exist, so the tokens are
already allocated, and minting a second one for a domain that has a token is the collision the
allocation table exists to prevent.

## What a derived row does not claim

A `forward-planned` row says *these units describe this repo and here is where they are*. It
does not say the code was read, and it carries no `map_confidence` — confidence is a property
of an inference, and nothing here was inferred. A unit whose `implementation_state` is still
`Planned` is counted in the table and **named in the row's note**, because a consumer reading
the graph as as-built needs to know which parts of it are not built yet.

## After writing

Push it the same way `/tl:code-map` does — the registry is workspace-level, so no repo's git
carries it and an unpushed one is invisible to every other machine:

    /jetrix:push scope code-map-registry.md

Then continue with whatever asked for the graph. **The derivation is a prerequisite step, not a
destination** — it never becomes the end of a run, and it never asks the user for permission to
read files they already have.
