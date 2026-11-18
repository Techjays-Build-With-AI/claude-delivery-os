# Known-task dimensions — which of the eleven apply when the work is a task, not a discovery

A **known task** is work on a system that already exists, where the business intent is
settled and what is unsettled is behaviour: a change, a fix, a small addition. A **client
requirement** is the opposite — the system may not exist, and what is unsettled is what the
business wants at all.

The scope template asks every module for all eleven §3.x sub-headings *"even if 'None'"*. That
is right for a discovery and wrong for a task: a ticket is silent on current state, on AI, on
integrations, and `ba-extraction` turns silence into a `CLR`. The result is a questions
document asking a team whether their own running product integrates with anything.

**This file decides applicability for known-task mode only.** Client-requirement mode does not
read it and is unchanged — all eleven, every time.

## What declares the mode

`/ba:scope` asks once and writes `work_type` into the scope's frontmatter
(`delivery-os-conventions` §2). `/ba:review` and `/ba:resolve` read it; neither re-asks.

**A scope carrying `work_type` is written at `schema_version: 1.4`**, the version that
introduced the field. Writing the field under an older version produces a document whose
frontmatter claims a contract that does not contain it — the template's own `1.1` and whatever
the previous round wrote are both wrong once this field is present. Set it on write.

## The code graph is the evidence, and without it there is none

Known-task mode marks dimensions `not-applicable` **because the running code already answers
them**. That claim needs the graph behind it.

**The gate is the graph, never the registry.** A greenfield project built through Delivery OS
has a full context tree and usually no registry at all — `tl-feature-planning` authored its
units and `/dev:build` Stage 10 flipped them to `implemented`, and no reverse-map ever ran.
Reading the registry alone and stopping on its absence tells a team with a mapped product to
map it. Look for the tree:

| What you find | What happens |
|---|---|
| a registry row for the task's area | read it through `tl-read-code-context` — proceed |
| no row, but `<repo>/context/code-context/` holds units for the area | derive the row per `tl-code-map` `references/registry-from-context.md`, push it, then proceed |
| no context tree for the area at all | **say so and stop**: *"known-task mode needs the code context — run `/tl:code-map` for `<repo>`, then re-run"* |

Only the third row stops, and it stops because nothing short of reading the code can produce a
graph that is not there. The second is a prerequisite step, not a halt.

**Judge the tree you find, do not assume it.** A unit still at `implementation_state: Planned`
describes intent, not behaviour, and answers no dimension — treat that area as unmapped. The
dimensions below rest on units that are `Implemented`.

Never mark a dimension `not-applicable` on the strength of the mode alone. Without the graph
the mode is just a way to ask fewer questions, which is worse than asking irrelevant ones.

## The eleven

| § | Dimension | Known task | Why |
|---|---|---|---|
| 3.x.1 | Current → Future State | **not-applicable** | the graph *is* the current state — actors, triggers, the systems touched. Asking a team to narrate it is asking them to transcribe their own code |
| 3.x.2 | In Scope / Out of Scope | **applicable** — reframed | not "which invoice types" but **blast radius**: which units this changes, and which adjacent ones it deliberately leaves alone |
| 3.x.3 | Module Master Flow | **not-applicable** — unless 3.x.4 is applicable, and then author it **for the new routes only** | the flow exists and the graph holds it, so redrawing it is transcription. Where the task does add a route, the flow is the one thing that shows where it joins the existing ones. **These two rows move together and never disagree** |
| 3.x.4 | Use Cases | **not-applicable** unless the task adds a materially-new route | one route changing is a business rule, not a new use case. A genuinely new route — a selection mode, a new bulk operation, a new entry point to existing behaviour — is a route, and it is authored. Changing what an existing route does is not |
| 3.x.5 | Functional Requirements | **applicable** — reduced | keep the capability line. **Drop `Resp.` and `Pri.`**: one ticket has nothing to rank against and everything on it is Must |
| 3.x.6 | AI / Automation | **not-applicable** unless the task names a model, inference or classification step | |
| 3.x.7 | Business Rules | **applicable** — primary | the existing rules are in the unit. The question is the **collision**: *"your change rejects on duplicate; the endpoint already permits one when the parent differs — which wins?"* |
| 3.x.8 | Data Fields | **applicable** — narrowed | the entity unit declares today's fields. Ask only about what the task adds: source, mandatory or optional, and what happens when it is missing |
| 3.x.9 | Integrations | **not-applicable** unless the task crosses a system boundary | `connection-map.md` and the endpoint units already name the externals — read them rather than asking |
| 3.x.10 | Exception Handling | **applicable** — primary | see below. This is where most known-task questions should come from |
| 3.x.11 | Acceptance Criteria | **applicable** — primary | what "done" means still has to be agreed, and it is what a build is later validated against |

**A `not-applicable` dimension is authored as "None" in §3.x and raises no `CLR`.** It leaves
the scope structurally complete and the questions document quiet. Record the evidence on every
one — the unit ids read, or the condition that did not hold — exactly as a `Covered` call
carries its citation. A `not-applicable` asserted without evidence is a guess.

**Never mark `not-applicable` because the source was thin.** Silence in a ticket about a field
the task plainly touches is a gap, and a gap is a question. Only the rows above, with their
stated evidence, are not-applicable.

**Write the evidence, never the mode.** The scope document goes to a client. It may say *"None.
The current state is the running product: PAGE-TASK-01 shows …"* — that is evidence, and it
reads as confidence. It may **never** name `work_type`, `known-task`, `not-applicable`, these
sweeps, this file, or a rule it is working around, and it never addresses the reviewer. A
sentence like *"known-task mode treats the master flow as not-applicable, but this task adds new
routes, so it is authored"* is the agent narrating its own instructions inside a client
deliverable; it also means two rows above disagreed and the document is where that was resolved.
If a rule seems to conflict, resolve it the way the rows say and write only the outcome — and if
it genuinely cannot be resolved, raise it as a `CLR`, which is what the ledger is for.

## Where known-task questions come from

In a discovery the questions come from silence in the material. For a known task they come from
**the distance between what the graph holds and what the task says** — which is a richer
source, and the reason this mode raises fewer but sharper questions rather than simply fewer.

Four sweeps over the units the task touches:

| Sweep | The question it produces |
|---|---|
| **enumerated values** — a status, type, kind or state field on a touched entity | *"`Task.status` carries `todo · inProgress · blocked · done`; the task names two. What is the behaviour for the other two?"* |
| **existing guards** — validation, permission and precondition checks on a touched endpoint | *"the endpoint already rejects when the owner differs; does the new path inherit that or bypass it?"* |
| **declared failure paths** — the refusal codes a touched endpoint already returns | *"400, 403 and 409 are declared today; which of them can the new input produce, and what should the caller see?"* |
| **reverse links** — what else points at a unit this task changes, **and what those things derive from it** | *"three pages read this endpoint; does the response change affect them, and is that in scope or out?"* · *"the page keeps a count that moves on add, edit and delete — a bulk action is none of those, so what updates it?"* |

**The reverse-link sweep does not stop at the first hop.** A direct caller is the easy half; the
costly misses are one hop further out, in **state something else derives from the unit** — a
cached count, a badge, a summary, a stored filter, a denormalised field, an aggregate. Derived
state is maintained by a named set of operations, and **a task that adds a new operation is
outside that set by default**. So for every unit the task touches, ask what is computed from it
and *when that recomputation fires*: if the trigger list names the operations individually and
the new one is not among them, the derived value goes stale and nothing in the code will say so.
A count that moves on "add, edit and delete" does not move on a bulk action. Follow the link to
whatever holds the number, not just to whoever calls the endpoint.

Each becomes an ordinary `CLR-###` in `ledger.md` (kind: question) and reaches
`client-questions.md` through the normal path. **Cite the unit ids the question came from** —
`EP-`/`PAGE-`/`ENT-` — so the reader can see it was derived from their system and not invented.

A question any of these four sweeps already answers is not asked. That rule is the same one
`ba-scope-review` applies when it screens a question against the code: the running system
answering it is the reason to drop it.

## Scoring

Unchanged. `not-applicable` already leaves the divisor and suppresses the question — see
`ba-scope-review` SKILL.md step 7 for the formula and the boundedness caps, which this mode
does not alter. For a known task, **boundedness is whether the blast radius is stated**: a task
that never says which units it touches is `Unbounded` and capped accordingly, however clearly
its purpose reads. The smaller divisor is what lets a well-specified task reach a true score;
the cap is what stops a thin one being flattered by it.
