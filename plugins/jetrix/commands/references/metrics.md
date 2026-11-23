# Recording a Delivery OS metric

<!-- rule: metrics-never-block phrases: "A metric must never block delivery" | "You count and send. You do not do the arithmetic." -->

Eight call points across `ba`, `dev`, `qa` and `tl`, all through one tool. **You count and send. You do
not do the arithmetic** — Mission Control's summary endpoint computes every rate and average, so
a command that tries to compute its own produces a second answer that disagrees with the page.

```
mcp__task-mcp__metrics_record(
  solution_id = <project.json solutionId>,
  event       = <one of the eight below>,
  values      = { … },
  project_id  = <apps[].projectId>,    # repo-scoped events
  feature_id  = <FEAT-<AREA>-NN>,      # feature-scoped events
  requirement_slug = <requirements/<slug>>,  # clarifications key; grouping on gaps
  task_id     = <the bug's MC _id>     # bugLink only
)
```

**A metric must never block delivery.** The call is the last thing a command does, never a gate.
On any failure — offline, server down, tool missing, not a Jetrix tracker — print one line
(`· metric not recorded (<reason>)`) and finish normally. Never retry, never prompt, and never
report the command as failed over it.

**Jetrix only.** `tracker.provider` is the gate: no other tracker has the endpoint. Skip silently
elsewhere; this is wiring, not work.

## The eight events

| Event | Raised by | `values` |
|---|---|---|
| `clarifications` | `/ba:scope` · `/ba:resolve`, end of the run | `round`, `roundId`, `answered`, `closed`, `open`, `superseded` |
| `gaps` | `/dev:build`, first start for the feature | `unitsTouched`, `appIds[]` |
| `planBlockers` | `/dev:plan`, end of the run | `pbRaised`, `pbResolved` |
| `firstPass` | `/dev:commit` end · `/dev:fix-review` | `firstPass`, `failedGate`, `appIds[]` — `firstPass` is **blocking gates only**: a Minor or Nit tidied in Stage 6's batched pass is still a pass (`commit.md` §10a) |
| `testability` | `/qa:audit` end | `score`, `verdict`, `areas{}` |
| `readiness` | `/tl:maturity` end | `score`, `domains{}`, `auditConfidence`, `weakestDomain` |
| `bugLink` | `/dev:plan` on a bug target | `{}` — the link is `feature_id` + `project_id` |
| `verification` | `/dev:commit` end | `findingsRaised`, `findingsFixed`, `acceptanceRows`, `acceptancePassed`, `acceptanceDeferred`, `coveragePct` — the evidence behind `firstPass` (`commit.md` §10b). `coveragePct` is **null, never 0**, when the repo has no coverage gate |

**Re-runs are expected and the server holds the rule, not you.** `gaps` and `planBlockers` keep
the first record because "before code" means before the first build; `firstPass` may flip to
`false` and never back; `testability`, `readiness` and `clarifications` keep every run, because
the trend is the point. Send the call every time and let the server decide — a command that tries
to detect its own re-run reads state it does not own.

## `clarifications` — the BA's ledger, counted by the BA

**The ledger belongs to whoever ran `/ba:scope`, and so does this call.** BA and dev are
different people on different days. A dev command reporting the BA's clarification work would
leave that work uncounted whenever a scoped requirement is never built, and it is exactly the
requirement nobody built that you most want to see.

**Keyed by the requirement, not the feature.** `requirements/<slug>/ledger.md` is keyed by
`Module`, and has no `FEAT-ID` column — there is no honest per-feature number to send. Send
`requirement_slug = <slug>` and no `feature_id`.

`ledger.md` (kind: question) carries `Status` values **`Open · Answered · Closed · Superseded`**.
Send all four counts; the page decides what to do with them. `answered + closed` is what was put
to the client and came back; `open` is still a risk rather than a gap caught. There is no
"resolved" status — do not invent one, and do not count rows by eye when the ledger states it.

**One row per round, because review → resolve is a loop.** `/ba:review` raises questions and
`/ba:resolve` settles them and stamps the next round; a requirement converges over several
passes, and that convergence is the measurement. Read `round` and `roundId` from the ledger's
`last_resolve_round` and the round marker on its rows. The server keeps every round, so never
try to update a previous one.

`/ba:review` and `/ba:features` do **not** send. Review writes a report and reads the ledger;
features reads it. Only the two commands that change the counts report them.

## `pbResolved` — count the run, not the file

`units/<repo>/plan-blockers.md` holds the blockers that were **deferred**. `/dev:plan` asks
blockers in conversation as they arise, folds the answered ones and plans on, so the file is
silent about every blocker the process handled well — counting it would score a clean run at
zero. Report `pbRaised` and `pbResolved` from the run you just did, inline answers included.

## `appIds` — which apps the feature touched

A feature touches an app when it has a unit folder for that repo, `features/<slug>/units/<repo>/`.
Map each `<repo>` to its `apps[].projectId` in `project.json` and send the ids, not the folder
names: the page filters by app, and a folder name is not an identity.

## `bugLink` — the link is found, never typed

On a bug target, `/dev:plan` already resolves which code units the fix touches. Each unit's
`## Used by Features` names the feature that owns it, and that is the link — nobody tags anything
by hand. **`Used by Features` reads `(as-built)` on every reverse-mapped unit until forward
planning links one**, so on a repo onboarded by `/tl:code-map` most bugs resolve to no feature at
all. That is the normal case there, not an error: send `bugLink` with `project_id` and no
`feature_id`, and the bug counts against the app alone.
