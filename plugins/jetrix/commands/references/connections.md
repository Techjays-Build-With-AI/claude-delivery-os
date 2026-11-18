# Recording the Solution's connections, and letting MC build the map

<!-- rule: connection-edges phrases: "full replace, not a merge" | "You collect structured edges. You do NOT write the map document." -->

Used by `/jetrix:project-setup` §3b.i (at creation) and `/jetrix:init` §14 → `references/init/connection-map.md`
§10a.i (when an existing Solution has no map yet). The flow is identical; only the moment differs.

**Run it whenever the Solution has 2+ apps and `connection_map_ref` is null.** A single app with
no external systems has nothing to connect, so skip it and say so.


**Ask while the apps are on screen.** Having just named every app and its type is the moment the
wiring is cheapest to ask about. Skip it and `.jetrix/connection-map.md` stays empty — and `/dev:plan` Stage 1 reads that file to work out which repos a feature touches
**before** it reads any feature frontmatter.

**You collect structured edges. You do NOT write the map document.** Mission Control's agent
synthesises it from the edges. Two authors for one Solution is exactly how the portal copy and
the local copy come to disagree.

**One app and no external systems → skip this section and say so.** A map of a single app with
nothing to connect carries no information.

#### Ask

```
1. Which app calls which, and over what?
     e.g. Nutrina Web -> Nutrina API over REST
2. Any external systems, and which app talks to each?
     e.g. Nutrina API -> Acumatica (ERP) over REST
3. For each edge: what flows over it, in one line?
     e.g. "nightly invoice sync"
```

Auth boundary and data-flow colour do **not** need their own questions — they belong in each
edge's `purpose`, which is where MC's agent reads them from.

#### Read before you write

```
mcp__project-mcp__project_get_connections(solution_id = <solutionId>)
```

**`project_replace_connections` is a full replace, not a merge.** Send the union of what came
back and what the teammate just described, or edges someone drew in the portal are silently
deleted.

#### Save the edges

```
mcp__project-mcp__project_replace_connections(
  solution_id = <solutionId>,
  connections = [
    { from: { project_id: "<webProjectId>" },
      to:   { project_id: "<apiProjectId>" },
      protocol: "REST",
      purpose: "Browser app calls the API for all supplier data" },
    { from: { project_id: "<apiProjectId>" },
      to:   { external: { name: "Acumatica", category: "ERP" } },
      protocol: "REST",
      purpose: "Nightly invoice sync" }
  ]
)
```

| Field | Rule |
|---|---|
| `from` / `to` | **exactly one** of `project_id` (an app) or `external: {name, category?}` — never both, never neither |
| `protocol` | `REST` · `GraphQL` · `gRPC` · `Event bus` · `SQL` · `File` · `WebSocket` · `Other` |
| `purpose` | required, 1–1000 chars — what flows and why |

Max 500 edges.

#### Build the map

```
mcp__project-mcp__project_build_connection_map(solution_id = <solutionId>)
```

**Order matters.** This synthesises from whatever edges are stored at that moment, so it runs
after the save, never before. It invokes an LLM upstream, so it is slower than the two calls
around it — say `· Building connection map…` rather than appearing to hang.

Once it returns, the Solution carries a `connection_map_ref`, and the caller's pull step fetches
the document to `.jetrix/connection-map.md` — `project-setup` §4 step 5, or `init` §13.

#### When something is missing

| State | Do |
|---|---|
| teammate skips the questions | record nothing, print `· No connections recorded — add them any time in the portal Connections tab` |
| an edge is only half-described | ask the one missing part. **Never guess a protocol** — an invented `GraphQL` is worse than an absent edge, because `/dev:plan` will believe it |
| save or build fails | the apps are already created, so do not unwind. Print the error, say the edges can be added in the portal, and continue to §4 |

