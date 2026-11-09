---
title: Delivery OS — Product Film, Narration Script v1
format: Split screen — LEFT = screen recording of real runs · RIGHT = animated architecture
runtime: ~9 minutes
scope: Foundation (project-setup · tl:scaffold · tl:code-map · QA) + BA · Dev · QA
status: draft for review
---

# Delivery OS — Narration Script

**Layout.** Left panel holds your screen recordings, playing at the moment the narration
describes them. Right panel holds the animated architecture. Neither panel ever runs alone —
the claim is on the right, the proof is on the left.

**Voice.** Calm, unhurried, declarative. No superlatives. The system is interesting because of
what it refuses to do, not because of what it promises.

---

## ACT 1 — THE PROBLEM

### Scene 1 · Cold open · 0:00–0:35

| | |
|---|---|
| **LEFT** | Black. Then a single cursor blinking in a terminal. |
| **RIGHT** | Five labelled boxes in a row, dim: `CLIENT CALL` · `SCOPE` · `TICKETS` · `CODE` · `RELEASE`. Between each pair, a thin gap. One by one the gaps light up red and a word fades in above each: *re-interpreted*. |

> Software delivery does not fail in the middle of a stage.
>
> It fails in the gaps between them. Between what the client said and what got scoped. Between
> what got scoped and what got planned. Between what got planned and what got built.
>
> Every one of those gaps is a handoff, and every handoff is a chance for meaning to drift.

**ON SCREEN:** `Delivery OS`

---

### Scene 2 · What it is · 0:35–1:15

| | |
|---|---|
| **LEFT** | Fast montage, 2 seconds each: a scope document scrolling, a scored review dashboard, feature folders appearing, a terminal building, a pull request opening. |
| **RIGHT** | The same five boxes — but now the gaps close. A continuous line draws left to right through all five, and a label rides along it: `one traceable object`. |

> Delivery OS is an operating system for the software delivery lifecycle.
>
> It takes a client conversation at one end and produces a reviewed, build-ready pull request at
> the other — and every artifact in between is a typed, identified object the next stage reads
> mechanically, instead of a document the next person has to interpret.
>
> It does not replace your team. It removes the places where your team loses information.

**ON SCREEN:** `Requirement  →  Build-ready PR`

---

## ACT 2 — GETTING CONNECTED

### Scene 3 · GRAPH 1 — The marketplace · 1:15–2:15

| | |
|---|---|
| **LEFT** | Real recording: `/plugin marketplace add`, then the install commands running, then `/` showing the commands appear in the menu. |
| **RIGHT** | **Node graph, built in four beats.** |

**Animation beats:**

```
BEAT 1   a single node drops in, centre:        [ MARKETPLACE ]

BEAT 2   two nodes descend and lock beneath it, drawn with a solid
         double line, each stamped REQUIRED:

                    [ MARKETPLACE ]
                     /           \
            [ delivery-os ]   [ jetrix ]
             shared contract   platform sync

BEAT 3   the frame splits into three lanes; a role avatar fades in
         at the head of each lane:

            ANALYST          DEVELOPER           QA
               |                 |                |
            [ ba ]           [ dev ]          [ qa ]
                                 |
                             [ tl ]  ← drawn automatically,
                                        labelled "required by dev"

BEAT 4   every role node draws a thin line back up to delivery-os.
         Caption under the graph: "one contract, many roles"
```

> Delivery OS ships as a plugin marketplace.
>
> Two installs are mandatory for everyone. The **core** carries the document contract — the
> shared vocabulary every role speaks. The **platform plugin** connects your workspace to wherever
> your work lives.
>
> After that, you install only your own role. An analyst takes the BA plugin. A developer takes
> the Dev plugin, which pulls in the Technical Lead plugin it depends on. A QA engineer takes QA.
>
> Nobody installs a tool they will never open. But because every plugin speaks the same contract,
> the analyst's output is the developer's input without anyone converting anything.

**ON SCREEN:** `2 mandatory · 1 per role`

---

### Scene 4 · GRAPH 2 — Connecting your project · 2:15–3:15

| | |
|---|---|
| **LEFT** | Real recording: the Jetrix portal — creating a Solution, then adding apps. Then the terminal running `/jetrix:project-setup`, the connection questions, and `/jetrix:init` binding the workspace. |
| **RIGHT** | **Node graph, three beats.** |

**Animation beats:**

```
BEAT 1   three tool logos arrive in a row, equal weight:

              [ Jetrix ]   [ Jira ]   [ ClickUp ]
                     \        |        /
                      \       |       /
                       [ DELIVERY OS ]

         caption: "bring your own tracker"

BEAT 2   Jetrix highlights; the others dim but stay visible.
         Beneath it, a small tree grows:

                    [ SOLUTION ]
                    /     |     \
               [ web ] [ api ] [ worker ]        ← apps

BEAT 3   dotted lines draw between the apps, each picking up a
         label as it lands:  REST · Event bus · SQL
         The whole tree pulses once and a tag attaches:
                    connection map ✓
```

> Delivery OS does not own your project management. It binds to it.
>
> Jetrix, Jira, ClickUp — the tracker you already use stays the tracker you use. Delivery OS reads
> from it and writes back to it.
>
> On Jetrix the shape is a Solution with applications inside it. You can create those by hand in
> the portal, or let the agent do it — one command walks you through the solution, the apps, and
> how they talk to each other.
>
> That last part matters more than it looks. Telling the system that the web app calls the API
> over REST, and the worker reads the same database, is what lets every later stage reason about
> your system instead of guessing at it.

**ON SCREEN:** `Your tracker. Your repos. One map.`

---

## ACT 3 — THE FOUNDATION

### Scene 5 · GRAPH 3 — The fork · 3:15–3:35

| | |
|---|---|
| **LEFT** | Hold on a single frame: two repository folders side by side — one empty, one full of files. |
| **RIGHT** | A single question node, then a split into two glowing paths. |

**Animation:**

```
                  [ DO YOU HAVE CODE? ]
                    /               \
                  NO                YES
                  /                   \
         [ GREENFIELD ]          [ BROWNFIELD ]
          build the base          map what exists
```

> Before any feature gets built, Delivery OS needs a foundation. Which foundation depends on one
> question.

---

### Scene 6 · Greenfield · 3:35–4:45

| | |
|---|---|
| **LEFT** | Real recording: `/tl:scaffold` — the stack questions being asked with recommendations, the repository materialising, the first green build. |
| **RIGHT** | **Nodes appear one at a time, each snapping into place with a soft click.** |

**Animation beats — build the chain left to right, one node per narration phrase:**

```
[ architecture ] → [ open decisions? ] → [ ASK, with a recommendation ]
      → [ skeleton ] → [ tooling: lint · format · types · test · build ]
      → [ design system: spacing · type · colour · motion ]
      → [ GREEN BUILD ✓ ]

Each decision node drops a small tag as it passes:  DEC-001  DEC-002  DEC-003
The tags fall into a tray at the bottom labelled "decision log".
```

> On a fresh project, the agent stands up the repository itself.
>
> It reads the architecture and separates what is already decided from what is still open. For
> anything open — the package manager, the test runner, the repository layout — it asks you, with
> a recommendation and the trade-off behind it. It never silently picks a stack.
>
> Every answer is logged, so six months from now "why this test runner?" has an answer with a date
> on it.
>
> Then it builds the skeleton, wires the tooling, and founds the design system — the spacing
> scale, the type scale, the colour tokens — **before the first screen exists.** Because the first
> screen anyone writes becomes the precedent for every screen after it.
>
> It finishes on a green build. Not a configured build. A green one.

**ON SCREEN:** `Every stack choice: asked, not assumed`

---

### Scene 7 · Brownfield · 4:45–5:45

| | |
|---|---|
| **LEFT** | Real recording: `/tl:code-map` running, the context tree being written, the PR raised against the mapped branch. |
| **RIGHT** | **A dense unreadable blob resolving into a clean graph.** |

**Animation beats:**

```
BEAT 1   a chaotic cloud of ~200 unlabelled file dots, drifting

BEAT 2   the dots pull into three horizontal bands:
            FRONTEND   pages
            BACKEND    endpoints
            DATABASE   tables · views · procedures

BEAT 3   the bands re-sort into vertical business domains:
            account · billing · supplier
         Each unit lights up a confidence badge and a source citation.

BEAT 4   links draw between units — page → endpoint → table — in both
         directions. Caption: "3 reads to any answer"
```

> On an existing codebase, the agent does the opposite. It reads what is already there.
>
> It derives every page, every endpoint — its contract, its validation, its business logic, and
> every database object it touches — and every table, view and procedure. Then it groups them by
> business domain rather than by framework folder.
>
> Everything it writes is marked as-built, with a confidence and a citation back to the real file.
> Where the code cannot support a conclusion, it records an open question instead of inventing a
> relationship.
>
> The result lives inside your repository and travels with your code.

**ON SCREEN:** `Read-only on your code`

---

### Scene 8 · Quality gates · 5:45–6:20

| | |
|---|---|
| **LEFT** | Real recording: `/qa:audit` producing the scored report, the human approving, `/qa:setup` running to a green suite. |
| **RIGHT** | A dial sweeping up through scored areas, then a contract document sealing. |

**Animation:**

```
fifteen small bars fill one at a time:
  unit · integration · e2e · coverage · lint · format · types · CI
  fixtures · mocking · contract · conventions · async · concurrency · state

each incomplete bar drops a tag:  QAF-003  QAF-007  QAF-011
→ a HUMAN APPROVES stamp lands on the report
→ bars refill green
→ a sealed document slides out:  qa/quality-gates.md
→ two arrows leave it, pointing at  [ BUILD ]  and  [ COMMIT ]
```

> The last piece of the foundation is deciding what "verified" means.
>
> QA scores the repository across fifteen areas and turns every gap into a finding with a
> recommendation. **You approve them** — the audit produces a decision surface, not a work order.
>
> Then it builds the harness and proves it green, and publishes one machine-readable contract.
>
> From that point on, every build and every commit is checked against that file. Not against
> somebody's memory of what good looks like.

**ON SCREEN:** `One-time setup. Done.`

---

## ACT 4 — THE WORKING LOOP

### Scene 9 · Transition · 6:20–6:30

| | |
|---|---|
| **LEFT** | The three foundation recordings shrink into small tiles and slide to the top of the frame, greying out. |
| **RIGHT** | Three foundation nodes dim and lock with a padlock icon. Below them, three fresh role lanes light up: **ANALYST · DEVELOPER · QA**. |

> That was the foundation. You do it once.
>
> From here, everyone works in their own lane.

---

### Scene 10 · The analyst · 6:30–7:40

| | |
|---|---|
| **LEFT** | Real recording: `/ba:scope` registering sources, the scope document building, the scored review dashboard, questions being answered inside it, `/ba:resolve` closing them, feature folders appearing. |
| **RIGHT** | **A funnel, narrowing.** |

**Animation beats:**

```
BEAT 1   raw material pours in at the top — transcripts, emails,
         spreadsheets, a recording. Each gets a tag as it lands:
            SRC-001  SRC-002  SRC-003

BEAT 2   each source passes a depth filter and is stamped with how
         deeply it will be read:
            DEEP ANALYSIS · SAMPLE · REFERENCE ONLY

BEAT 3   a grid forms: features down the side, nine dimensions across
         the top. Cells fill green / amber / grey.
         Grey cells are labelled "not applicable" and visibly leave
         the calculation.

BEAT 4   a score lands per feature. Amber cells each emit a question
         chip: CLR-012, CLR-013 … chips fly to a CLIENT panel.

BEAT 5   answers fly back. Chips turn green. The grid refills.
         The score moves — and a small caption follows it:
            "8.3  ← CLR-012, CLR-031"

BEAT 6   a gate closes across the bottom. It opens only when the
         conditions clear, and feature folders drop through.
```

> The analyst feeds in whatever the client gave them, in whatever form it arrived.
>
> Every source is registered and weighted. A one-hour discovery call and a four-thousand-file
> archive do not deserve the same attention, and the system records that judgment instead of
> burying it.
>
> Then it interrogates the scope the way a sceptical analyst would — nine business dimensions,
> feature by feature. A dimension that does not apply is removed from the calculation, not scored
> as a failure.
>
> Every gap becomes a question with an owner and a consequence. The client answers inside the
> report. Each answer is **adjudicated, not accepted** — resolved, or logged as an explicit
> assumption, or sent back with specific follow-ups.
>
> And every score that moves carries the reason it moved.
>
> Only then does a gate open and the scope become feature folders. A blocker cannot be waved
> through.

**ON SCREEN:** `Scored. Traceable. Gated.`

---

### Scene 11 · The developer · 7:40–8:50

| | |
|---|---|
| **LEFT** | Real recording: `/dev:plan` with a blocker being answered, `/dev:build` running its stages, `/dev:commit` executing tests and raising the PR. |
| **RIGHT** | **Three chambers in series, each with a gate at its exit.** |

**Animation beats:**

```
CHAMBER 1  PLAN
   feature folder enters → maps onto existing context units
   (reused units glow; new ones are drawn fresh)
   → anything undecided pops out as a card: PB-001, PB-002
   → the cards are answered by a human avatar and slot back in
   → an 8-section plan slides out

CHAMBER 2  BUILD
   code is written step by step alongside its tests
   a TEST MAP table assembles, one row per assertion
   each row is checked: file exists ✓ · test exists ✓ · runnable ✓
   acceptance rows appear, all marked:  ⏳ pending

CHAMBER 3  COMMIT
   the suite RUNS — ⏳ flips to ✅ one row at a time
   three gates light in sequence:
       SECURITY   ·   CODE REVIEW   ·   ACCEPTANCE
   a finding appears, the gate goes red, a FIX LOOP spins,
   the gate clears
   → the context graph merges
   → PULL REQUEST ✓
```

> The developer's loop has three stages and a hard refusal at each entry.
>
> Planning maps the feature onto what already exists, so the system reuses an endpoint instead of
> building a second one. Anything that would make a developer stop and ask is surfaced **now**, as
> a blocker, answered by a human, and folded into the plan. Build is never interrupted, because it
> is never allowed to start without everything it needs.
>
> Build writes the code and the tests, and produces a map proving every claim has a test behind
> it — but it does **not** run them. Every acceptance row leaves build marked *pending*.
>
> Commit is the only thing that executes. It runs the suite, flips pending to pass, and puts the
> work through security review, code review, and acceptance re-verification. When a gate finds
> something, the fix loop is **mandatory and recorded** — and the push refuses if a finding was
> never addressed.
>
> One executor. One origin for the claim that something passes.

**ON SCREEN:** `Build declares. Commit proves.`

---

## ACT 5 — WHY IT MATTERS

### Scene 12 · The three payoffs · 8:50–9:40

| | |
|---|---|
| **LEFT** | Three short clips, ~6 seconds each: a codebase question answered instantly with citations · a rich ticket opening in the tracker · the review dashboard full of specific questions. |
| **RIGHT** | Three cards flipping in, one per payoff. |

**CARD 1 — Context that compounds**

```
   BEFORE   [ grep ] → [ grep ] → [ read ] → [ read ] → [ guess ]
   AFTER    [ index ] → [ layer ] → [ the one file ]   ✓ cited
```

> The first payoff is that the system stops rediscovering your codebase.
>
> Every question about what exists is answered from a map built once and kept current by the loop
> itself — three reads, with a citation you can jump to. Nobody re-derives how billing works every
> time someone asks.

**CARD 2 — Tickets that can be built**

```
   VAGUE TICKET                    DELIVERY OS TICKET
   "Add supplier onboarding"       acceptance criteria · business rules
                                   NFRs · test scenarios · dependencies
                                   open questions, owned
                                   → traced back to the client sentence
```

> The second is that a ticket arrives buildable.
>
> Not a title and a hopeful sentence. A folder with what done means, which rules must hold, what
> happens on the unhappy path, and what is still unknown — marked as unknown, with a name against
> it.
>
> A developer who opens it does not have to reconstruct the conversation that produced it.

**CARD 3 — Questions worth asking**

```
   29 questions  →  client answers  →  25 close as out-of-scope
                                     →  4 remain
                                     →  5 sharper ones take their place
```

> The third is the one that saves the most money, and it happens before a line of code is written.
>
> The review asks the uncomfortable questions early — the boundary nobody drew, the rule nobody
> stated, the edge case nobody considered. Then it folds the answers back in and asks the next
> layer down.
>
> An hour of questions during discovery costs less than a sprint of building the wrong thing.

---

### Scene 13 · Close · 9:40–10:00

| | |
|---|---|
| **LEFT** | Fades to black. |
| **RIGHT** | The full chain draws once, end to end, each link lighting as it is named — then holds. |

```
SRC-001 → CLR-012 → scope §3.2 → FEAT-SUP-001 → EP-SUP-03 → commit → PR
```

> Every line of code that ships can be walked back to the sentence a client said.
>
> Not through someone's memory. Through the files.
>
> That is Delivery OS.

**ON SCREEN:** `Techjays Delivery OS`

---

## Production notes

**Pacing.** Act 3 is the heaviest. If the cut runs long, Scene 7 (brownfield) and Scene 6
(greenfield) can each lose fifteen seconds by letting the animation carry more and the narration
carry less — the visuals are self-explanatory once the node pattern is established.

**The one rule for the right panel.** Never animate something the left panel is not actually
doing. The split screen only works while the audience believes the two sides are the same event.

**Numbers to keep accurate on screen.** Nine review dimensions. Fifteen QA areas. Eight plan
sections. Eleven build stages. If any of these change, the script changes.

**What this film deliberately leaves out.** Documentation generation, deck and proposal output,
and the maturity audit. They are real, and they would make the film twenty minutes long. A second
film can cover the client-facing side.

**Tone check.** If a line sounds like it belongs on a pricing page, cut it. The strongest moments
in this script are the refusals — *it never silently picks a stack*, *adjudicated, not accepted*,
*the push refuses*. Keep those.
