# /jetrix:init — the closing report

What the run prints. It is the only part the user actually reads, so it names one next step
chosen from what the bind found — never a menu of every role.

## 12. Print summary

```
✓ Bound workspace to Jetrix project.

Workspace:     <workspace_root>
Solution:      <name>  (<solutionId>)
Slug:          <slug>
Type:          <type>
Environments:  dev, staging, prod

Apps (<N>):
  • <projectName>  (<projectType>)  →  <path or SKIPPED>
  • ...

Connection map:   <✓ pulled | · not built yet | ⚠ retry needed>
Delivery-OS tree: <✓ scaffolded | · skipped — run /delivery-os:init to seed>

Workspace layout:
  .jetrix/project.json
  .jetrix/connection-map.md       (if the portal built one)
  .jetrix/cache/                  (repolocation.json + sync-state.json)
  .jetrix/shared-context/         (seeded templates + baseline-profile)         [scaffold only]
  .jetrix/requirements/<slug>/     (created by /ba:scope)        [not scaffolded only]
  .jetrix/features/               (empty — per-feature bundles from /ba:features) [scaffold only]
  .jetrix/tl/                     (reviews/ maturity/ code-map-registry.md)     [scaffold only]
  .jetrix/qa/                     (audits/ health/ escalations/ + gates)        [scaffold only]
  .jetrix/doc/                    (decks/ walkthroughs/ workflows/ boards/)     [scaffold only]
  .jetrix/tasks/                                                                [scaffold only]

Next:
  <ONE action — see below. Never a menu of roles.>
```

**Name one next step, chosen from what the bind actually found.** A list of every role's entry point is not a next step; it is a menu, and it puts the decision back on someone who just asked the command to tell them.

| What the bind found | Print |
|---|---|
| repos on disk, none mapped | `/tl:code-map` — and why: until a repo is mapped, code questions are answered by searching source, and `/dev:build` cannot start because Stage 0 needs `shared-context/coding-standards.md` § `<repo>`, which the map authors |
| repos all mapped | `/ba:scope add "<where your client material lives>"` |
| no apps, or no repo linked | the portal step, then `/jetrix:init <project-ref> refresh` |
| no apps and no client material yet | `/ba:scope` — discovery needs no repos |

Where two are genuinely available — repos to map **and** material to scope — lead with the mapping and offer the other on one line beneath it. They are independent tracks, so neither blocks the other.

**One ordering rule overrides the table, on Jetrix.** With **more than one repo and no connection map**, Build map comes before `/tl:code-map` — the map reads each repo in isolation, so without the wiring a mobile API call has no declared backend counterpart and the cross-repo links come out unresolved rather than wired. Say so rather than listing both as equal gaps:

```
Next
  1 · portal → Connections → wire the 3 apps, Save, Build map
  2 · /jetrix:init <project-id> refresh
  3 · /tl:code-map

  Mapping before the wiring exists means every cross-repo link
  comes out unresolved, and re-mapping is the only fix.
```

A single-repo Solution has nothing to wire, so it goes straight to `/tl:code-map`. **On any other tracker this never arises** — §13 already drew the map from the user's own answers, so mapping can start immediately.

**Report what is missing, then carry on — never refuse over a gap.** A bind against a project with no apps, no connection map or no linked repo is a normal mid-engagement state, so name each gap and the step that fills it, and close with the exact line to run afterwards:

```
Gaps:
  · no apps on this project            portal → add one per repo
  · Admin panel has no linked repo     portal → that app → Integration tab
  · connection-map not built           portal → Connections → Build map

  Pick them up with:  /jetrix:init refresh
```

**A repo with no local path gets this block, verbatim, wherever it is hit.** It is the most common gap and the one that
stops the most commands — `/tl:code-map` cannot read the repo, `/dev:build` cannot branch in it, `/dev:commit` cannot
push from it — so every one of them prints the same two lines rather than its own wording:

```
Inhouse-server has no local path on this machine.

  /jetrix:init refresh        re-asks for it, and re-fetches anything else
                              the project has gained since the bind
```

On Jetrix the refresh also re-pulls apps, repo links and env branches from the Solution, so a repo linked in the portal
since the bind needs nothing typed. On any other tracker there is nothing upstream to fetch — the refresh simply
re-asks the paths, branches and wiring from §13/§13 with the current answers as defaults.

The one thing that does stop the run is a missing MCP for a non-default tracker (§6) — there is nothing to bind to, so nothing is written.

Suppress the `[scaffold only]` rows from the printed layout when `scaffolded=false`; instead print one line: `.jetrix/  (delivery-os tree not seeded — run /delivery-os:init to fill it in)`.

Keep it idempotent — a rerun for the same solutionId refreshes without clobbering hand-edits, migrates the connection-map to the new path if needed, re-attempts the connection-map download if the last run failed, and re-runs the scaffold seed (which is itself idempotent) to fill in any missing files.
