---
title: Code Map — Architecture
audience: Technical leads, engineers, business analysts
status: current
---

# Code Map — Architecture

The code context is the system's model of what exists in the software and how it connects. It is
what lets planning reuse instead of duplicate, lets the BA stop asking about behaviour the product
already has, and lets any agent answer a question about the codebase in a handful of reads.

---

## 1. Architecture

### 1.1 Two origins, one graph

```
  BROWNFIELD                                 GREENFIELD
  repository exists                          no code yet
        │                                          │
        │ /tl:code-map                             │ /dev:plan (forward planning)
        ▼                                          ▼
   read the real code                        plan from the feature
   derive units                              create units
   mark AS-BUILT + confidence                mark DESIGNED
        │                                          │
        └──────────────────┬───────────────────────┘
                           ▼
            <repo>/context/code-context/
            endpoints · pages · entities
            bidirectionally linked
                           │
                           │ /dev:build stage 10 flips designed → implemented
                           │ /dev:commit stage 7 merges against baseline
                           ▼
                  tl-read-code-context
                  ≤ 5 reads, cited answers
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   BA question       planning reuse     any codebase
   screening                            question
```

One graph, two provenances, always distinguishable. A unit derived from code carries a confidence
and a source citation; a unit derived from a plan carries `designed` until the code lands.

### 1.2 Where it lives

The tree is written **inside the mapped repository**, not in the workspace:

```
  <repo>/context/code-context/
  ├── README.md
  ├── code-context-index.md        cross-layer summary — the entry point
  ├── map-coverage.md              what is mapped and what is not
  ├── backend/
  │   ├── _overview.md
  │   ├── backend-index.md         domain map + unit table
  │   └── domains/<domain>/endpoints/<slug>.md
  ├── frontend/
  │   ├── _overview.md
  │   ├── frontend-index.md
  │   └── pages/<area>/<slug>.md
  └── database/
      ├── _overview.md
      ├── database-index.md
      └── {tables,collections,views,procedures,functions,triggers}/<slug>.md
```

**Why inside the repo.** The context travels with the code, diffs in the same pull request, and
cannot drift onto a different branch than the code it describes. A workspace-level registry
(`.jetrix/code-map-registry.md`) names each mapped repository and resolves cross-repo links.

Only the layers and kind-folders the repository actually has are created.

### 1.3 Unit anatomy

An endpoint unit records:

| Section | Carries |
|---|---|
| `## Summary` | What this operation is for, in business terms |
| `## Contract` | Request shape, response shapes |
| Validation | Each rule and **where it is enforced** |
| Business logic | Ordered steps, transaction boundaries, idempotency guards, failure behaviour |
| `## Data Access` | Every database object touched, with the access mechanism |
| `## Called by` | Which pages or services call it |
| `## Related Units` | Lateral links |
| `## Source References` | File citations into the real code |

Pages and entities follow the same shape with their own middle sections. Links are
**bidirectional** — a page names its endpoints, and each endpoint names its callers — so the graph
can be walked from any node in either direction.

---

## 2. Process

### 2.1 Reverse mapping — three passes

```
  PASS 1  DISCOVERY        enumerate cheaply
          ├─ detect the stack
          ├─ derive business domains (account, billing, supplier, …)
          ├─ load any existing context
          └─ enumerate units from declarative sources — prefer an
             authoritative registry over guessing from folders

  PASS 2  DETAIL           one unit at a time
          ├─ read the handler, follow into services and repositories
          ├─ capture contract, validation, logic, data access
          └─ cite source files; record a confidence

  PASS 3  SYNTHESIS        make it findable
          ├─ write each layer index: domain map + unit table
          ├─ one-line summaries that mirror the unit files
          └─ respect the index budget — one readable pass
```

**Depth rule.** Write the logic as ordered steps until further depth stops changing a reader's
understanding. This is a map, not a transcription. Where logic is genuinely too intricate to
summarise faithfully, say so and cite the file rather than writing a lossy version.

### 2.2 Grouping by domain, not by framework

Units are clustered into **business domains**, not mirrored from the repository's folder tree. A
reader looking for "how invoicing works" should find one folder, not three framework layers to
cross-reference.

### 2.3 Retrieval — index-first

The design target is explicit: **find the right file in three cheap reads, never a grep across
source.**

```
  root index  →  layer index  →  the one unit file
```

| Question shape | Entry point |
|---|---|
| Solution architecture, cross-repo wiring, auth boundary | `.jetrix/connection-map.md` |
| Unit lookup — `EP-`, `PAGE-`, `ENT-` | That layer's index |
| Feature trace | Connection map first, then the feature's related units |
| Cross-reference walk — who calls X, what X touches | The unit at the source of the walk |
| Decision archaeology | `shared-context/decision-log.md` |

The budget is **five file reads on the hot path.**

### 2.4 What it does not answer

| Question | Why not |
|---|---|
| BA scope, TL reviews, QA audits | Different artifacts, different folders |
| Write code, run tests, plan a feature | Those are the dev and QA commands |
| "Show me the contents of this known file" | A direct read is faster |

---

## 3. Best-practice checks

**Never fabricate a relationship.** Where the code cannot ground a link, the unit records an open
question instead of a plausible edge.

**Prefer declarative sources.** An authoritative route registry beats inferring endpoints from
folder names. Guessing produces units that look authoritative and are wrong.

**Never write secrets.** Credentials, connection strings, tokens and customer data never enter the
tree. The tree is committed; anything in it is published to everyone with repository access.

**Cite everything.** Every answer names the unit id and the file path it came from. A unit id
alone is not a citation — the reader must be able to jump to source and verify.

**Report disagreement rather than resolving it.** When the graph and the source disagree, the
answer names the discrepancy: the graph may be stale (needs a re-map) or the code may have drifted
(needs a context merge). Picking a side silently is worse than either.

**Read-only on the code.** The mapping changes nothing in the repository except the
`code-context/` tree it authors.

---

## 4. Evidence and confidence

| Signal | What it records |
|---|---|
| `origin` | `as-built` (derived from code) or `designed` → `implemented` (planned then built) |
| `confidence` | How certain the derivation is |
| Commit stamp | Which commit the mapping was taken from |
| `## Source References` | File citations backing each claim |
| `map-coverage.md` | What is mapped and what is explicitly not |

**Coverage is reported, not implied.** A repository that was partially mapped says so, so nobody
mistakes an unmapped area for an empty one.

### 4.1 Review before landing

The tree is committed on its own branch with a pull request against the branch that was mapped.
A few hundred generated files are reviewed rather than appearing on the main line unseen.

---

## 5. Freshness — the operational argument

The graph stays true because the delivery loop maintains it:

| Event | Effect |
|---|---|
| `/dev:build` stage 10 | Units flip `designed → implemented` |
| `/dev:commit` stage 7 | Branch units merge against the baseline, field by field |
| `/tl:code-map` re-run | Re-derives as-built units from the current commit |

Code that lands **through the loop** keeps the map current automatically. Code that bypasses the
loop — a direct edit, a merge that skipped commit — makes the map confidently wrong, which is
worse than having no map.

This is the strongest operational reason to route all work through the loop.

---

## 6. Who consumes it

| Consumer | Uses it for |
|---|---|
| `/dev:plan` | Reuse existing endpoints and entities instead of duplicating them |
| `/ba:scope`, `/ba:resolve` | Screen questions — never ask about behaviour the product already has |
| `/qa:audit` | Understand what the code does without grepping source |
| `/dev:commit` stage 7 | Merge branch context against baseline |
| Any question about the codebase | Cited answers in five reads |

---

## 7. Boundaries

The code map **authors context from code**. It does not modify or run the repository, does not
write features (features stay BA-owned), does not invent relationships it cannot see, and does not
commit to the mapped branch directly.
