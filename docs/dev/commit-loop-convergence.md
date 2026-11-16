# Why `/dev:commit` takes an hour, and the four changes that fix it

Investigation record · v1.0 · 2026-11-13

**Status:** §4 landed in `37140ed`. Everything from §5 onward is in the working
tree, untested. §8 covers the work that followed — the rules mechanism, the
build-execution gate, and the audit that found what the earlier passes left stale.

The evidence throughout is one real run — `ui-premium-redesign` / `frontend`, a
UI restyle in the Testing-Delivery-os workspace — which took over an hour and
exited the fix loop at its bound with four findings still open. Every claim here
cites that run's `status.md` or a spec file. Nothing is inferred from how the
loop is supposed to behave.

---

## 1. What the run actually did

```
Stage 4 ──▶ CR-1..CR-12        0 blocker, 0 major, 8 minor, 4 nit
Stage 5 ──▶ TV-1..TV-6         TV-1 blocking
            │
loop-1 ─────┤ 19 findings entered, 2 of them blocking
            │ snapshot 417882b3 — 32 files, +1056/-113
            ▼
Stage 4 r2  CR-10 still open ("the no-op line still at TaskRow.css:55")
            CR2-2 (Major) — in code the round-1 repair wrote
Stage 5 r2  TV2-1 (Blocker) — "lazy-route cold import > findBy timeout"
            │ snapshot b8b4994b — 34 files, +1250/-140
            ▼
loop-2      agent records: stability_requirement: "3 sequential runs green"
            │ snapshot c424968d — 38 files, +1357/-141
            ▼
Stage 4 r3  CR3-1..CR3-4
            ▼
            BOUND REACHED — 4 open, deferred with no tracker id
```

Cost: roughly nine coverage/vitest executions, five e2e runs, four production
builds. All three reviewers fell back to `method: manual`, so they ran serially
rather than in the parallel fan-out `commit.md` §5a specifies.

---

## 2. The first review was not deficient

The obvious reading of three rounds is that the first reviewer missed things.
The run says otherwise.

Round 3's four findings, verbatim from `status.md`:

| | Finding |
|---|---|
| CR3-1 | boundary stays failed across navigation |
| CR3-2 | "check your connection" copy for any render error |
| CR3-3 | reload button reuses dismiss class |
| CR3-4 | preload list duplicates App lazy imports |

All four concern `RouteErrorBoundary` and the lazy-route preload list — code the
**round-2 repair agent wrote**. The round-1 reviewer could not have found them;
that code did not exist when it looked. CR2-2 has the same shape one round
earlier.

The snapshot grew `+1056/-113` → `+1250/-140` → `+1357/-141` across the rounds:
roughly 300 lines and six files added by repairs, each batch never reviewed
before the round that found fault with it.

**Each round reviewed genuinely new code.** The loop did not fail to converge
because the reviewer was weak. It failed because every repair enlarged the
surface the next review would read.

One case is a genuine miss of a different kind: CR-10 was in the original diff,
the repair reported it fixed, and round 2 found the no-op line still in place.
That is a repair that lied, not a reviewer that missed.

---

## 3. Root cause — the repairer and the reviewer were graded differently

`stage-6-fix-loop.md` §6b.iv claimed:

> delegated to `dev-stack-adaptive-implementation` in fix-mode — the skill that
> wrote the code in the first place and **knows the repo's conventions,
> `coding-standards.md` and the stack**

That mode did not exist. `grep -rn "fix.mode"` over the skill returned nothing.
The skill is built end to end around `/dev:build`: its Operating contract
requires `implementation.md`, Phase 3 iterates "each ordered step in
`implementation.md`", and Rules 13–14 are written against a build.

What a repair agent actually received, per §6c and §6b.ii:

```
Fix mode.
Finding: <finding>
Suggested fix: <fix_suggestion>
Constraint: minimal-surface change; do NOT expand scope; do NOT refactor
            unrelated code.
```

— delivered to "a new agent with only the finding and `allowed_files`".

No stack. No `coding-standards.md`. No sight of the nine dimensions
`dev-stack-adaptive-code-review` would grade its output against. The one
substantive instruction it did get pushed against doing the standards work.

A fresh agent handed a defect and told *smallest possible edit* makes the symptom
go away. The reviewer then reads that new code against nine dimensions it was
never shown.

**The writer and the reader were working from different contracts.** That is the
loop.

---

## 4. Landed in `37140ed`

### 4a. Fix mode, defined

`dev-stack-adaptive-implementation/SKILL.md` gains a `## Two modes` section.
Fix mode takes `{finding, allowed_files, detected_stack, repo}` and runs the
three phases scoped — stack from the caller, pattern inference from the
neighbours of `allowed_files` rather than ten repo-wide reads, one step instead
of a build sequence.

The load-bearing sentence:

> **`minimal-surface` bounds WHERE you write, never HOW WELL.**

Rules 13 and 14 hold on every repair line. The agent self-checks its diff
against the nine dimensions before reporting `fixed`.

### 4b. §6c carries the contract

The prompt now passes `allowed_files`, `detected_stack`, the path to
`coding-standards.md § <repo>`, and the nine dimensions with an explicit
self-check step. §6b.iv's claim is restated as a reference to the mode that now
exists.

### 4c. Findings are written, not just rendered

Separate from the loop, and the reason the run has no `## Code review` section
at all: `stage-4-code-review.md` permitted `ReportFindings` *instead of*
writing `units/<repo>/findings.md`. That tool renders to the UI and writes no
file. A run that only emitted left no audit trail — the next round could not
read `## Settled`, so a finding closed last round came back as new. The file is
now mandatory and Stage 8 halts on a missing section.

---

## 5. Repeated test execution

Four places in the spec re-run tests. They are not equally justified.

| | Rule | Cost | |
|---|---|---|---|
| §6c step 4 | localized re-verify per fix attempt | 1 command | keep |
| §6b.iv | after a test failure, re-run *that scenario's* `Run it` — *"costs one command rather than a suite"* | 1 command | keep |
| **§6d.i** | test verification re-runs **always**, in full, after every repair | full Stage 5 | **the problem** |
| §6e / §6e.i | one full 4→5 cascade at the end | full Stage 5 | keep — this is the gate |

§6b.iv and §6d.i contradict each other. One says re-run a single command; the
other says re-run everything, every time. In this run the second won, three
times over, and Stage 5 is fourteen rows plus a coverage run.

### 5a. Scope §6d.i the way it already scopes code review

§6d.i holds the right rule for one reviewer and the wrong one for the other:

```
code review        → only when the repair touched a file in its finding set
test verification  → always
```

The test map's columns are `| Kind | ID | Scenario | Tier | Test | Run it |
Needs | Fixtures |`. There is **no column recording which source files a row
covers**, so "re-run the rows that exercise the repair diff" is not directly
computable. It does not need to be: §6b.ii already pins the repair to
`allowed_files` — "the finding's file plus its test".

So the re-run set is an exact match on a column that already exists:

```
re-run = rows whose `Test` path ∈ allowed_files
       ∪ the regression test the repair wrote (§6b.iv already requires one)
```

No schema change, no new script, no inference.

**The risk and its cover.** A repair can break a test outside `allowed_files`.
The end-of-loop full 4→5 cascade still runs the entire map before push. The
narrow re-run is the fast signal; the cascade is the guarantee. Nothing is
skipped — it moves from *after every repair* to *once, at the end*.

### 5b. Route flakes out of the loop

This needs no new machinery. The classifier exists, and its opening line is this
run's problem stated in advance — `stage-7-test-execute.md` §7f.i:

> A failing gate is not automatically a code defect, and treating it as one
> **burns the repair budget on a test that is correct.**

Ownership is already assigned, `stage-8-validate.md:199`:

> `PARTIAL_HARNESS` — **not reachable at build.** It classifies a red run
> (`flaky`, `harness-config`) … **`/dev:commit` Stage 5 owns it**

The gap: `stage-5-acceptance.md` §5b.i applies it only to flakes *carried over
from build* through a `PARTIAL_HARNESS` handover. A failure first seen **inside**
the fix loop never reaches the classifier.

TV2-1 was a cold-import timeout — §7f.i's own words at line 307 call "a timeout
at the tool default under instrumentation" `harness-config`, not `flaky`, and
`stage-5-acceptance.md:152` routes it to the PR body with **"do not enter the
fix loop"**. Instead it became a Blocker, consumed a round, and triggered a
`stability_requirement: "3 sequential test:coverage runs green"` that appears
**nowhere in the spec** — the agent invented it, and it tripled that round by
itself.

So the change is a precondition, not new logic: classify a red row per §7f.i
*before* it can become a blocking finding.

```
defect                    → fix loop
flaky / harness-config    → PR body
```

### 5c. The three edits, as landed

| File | Change |
|---|---|
| `stage-6-fix-loop.md` §6d.i | `test verification → always` keeps its "always", but now over `rows whose Test ∈ allowed_files` rather than the whole map. States explicitly that the §6e cascade still runs the full map, and that narrowing the mid-loop re-run and skipping the cascade are different things |
| `stage-6-fix-loop.md` §6a.ii | **new.** No red row enters the loop unclassified. `defect` → loop; `flaky` / `harness-config` → PR body. Cites §7f.i's own reason and the cold-import case |
| `stage-6-fix-loop.md` §6b.iv | its *"re-run that scenario's own `Run it`"* line now reads as the mid-loop rule and points at §6d.i, instead of contradicting it |
| `stage-5-acceptance.md` §5b.i | retitled *"A red row that is not a defect — wherever it first went red"*. Two sources, one rule: carried from a `PARTIAL_HARNESS` build, or first seen here including on a fix-loop re-run |

---

## 6. The same run, replayed under the §4–§5 changes

Expected behaviour, not a measured result — the changes are specification edits
and this run has not been re-executed against them.

```
Stage 4 ──▶ CR-1..CR-12        unchanged — the reviewer is not touched
Stage 5 ──▶ TV-1..TV-6         unchanged
            │
loop-1 ─────┤ repair runs in fix mode: stack + coding-standards + the
            │ nine-dimension self-check before reporting `fixed`
            │
            │ re-run: rows whose `Test` ∈ allowed_files + the new
            │         regression test — roughly 2 commands, not 14 rows
            ▼
Stage 5 r2  the cold-import timeout hits §7f.i first → harness-config
            ──▶ PR body. Never a finding. Never enters the loop.
            ▼
            ONE full 4→5 cascade — the whole map, before push
            ▼
            CLEAN
```

Full-suite executions: roughly nine down to two or three.

### What deliberately does not change

- **Minor and Nit are still fixed**, in §6e.i's batched rounds. They were
  considered as a lever and rejected: the run's 16 non-blocking findings were a
  symptom of repair quality, not the cause of it.
- **The full 4→5 cascade still runs before push.** The narrow re-run is a signal,
  not a substitute. Nothing reaches a PR unverified.
- Stage 8's gate, the snapshot-sha agreement in §8a, and the blocking thresholds
  are untouched.

### One honest limit

Fix mode makes round-2 and round-3 findings rarer, not impossible. CR2-2 and
CR3-1…CR3-4 are all convention, naming, reuse and error-handling defects —
exactly what the self-check reads for. A repair can still introduce a genuine
logic bug, and the cascade is what catches it. The change improves the rate; it
is not a guarantee of single-round convergence.

---

## 7. Open, not addressed here

Carried forward from the same investigation and still unapplied:

- **§6e.i vs §4c/§4i contradiction.** §4c and §4i say Minor and Nit surface in
  the PR body *only*; §6e.i makes `fixed` the default at every severity. Both
  are in force; the run followed §6e.i.
- **Re-run policy stated three ways.** §6d.i (scoped), §6e (after all fixed) and
  §6h ("after each fix") disagree on when the cascade runs.
- **Build executing tests.** The run's builder executed 474 unit and 35 e2e tests
  although `/dev:build` commits nothing and runs nothing by design. Stage 7 was
  clean (`executed: false`); the execution came from Stage 2's re-checks and the
  builder subagent acting under `superpowers:test-driven-development` and
  `superpowers:verification-before-completion`, which outrank plugin reference
  files in the agent's priority ordering. A command-level invariant in
  `build.md` naming those two skills as out-ranked inside `/dev:build`, mirrored
  into `stage-2-preflight` and Stages 5–6, was drafted and not applied.
- **`stage-5-acceptance.md` Purpose paragraph** still reads "Re-verify every row
  … is still green … stale test evidence", all three phrases assuming build ran
  the suite.

---

## 8. What came after — and the audit that was the point

§1–§7 fixed instances. This section is the part that stops the next round of them.

### 8a. Restatement is a lint error (`rules`, 2.3.30)

This corpus states the same rule in several files, and nothing compared a paragraph
to its own restatement. Every drift in §7 was found by a human reading. The eleventh
lint check makes it mechanical: a rule declares its home and the exact phrases that
may only appear there; any other file carrying one must mark itself
`<!-- governed-by: <id> -->` or fail the build.

**Prose is not deleted.** A file an agent reads standalone keeps its explanation —
what changes is that the echo is now tracked, so `grep -rn "governed-by: <id>"` is
the complete update list. That list previously existed only in memory.

Five rules seeded: `build-declares-commit-executes`, `commit-stage-count`,
`non-feature-run-path`, `test-map-blocker-ids`, `fix-loop-rerun-scope`.

**The first rule declared found a live bug.** `/dev:plan` wrote a non-feature
ticket's plan to `tasks/<slug>/units/<repo>/`; `/dev:build` read
`tasks/<slug>/dev/`. Every bug, story and standalone task had an unreachable plan.
`non-feature-track.md` held both spellings — its diagram said one, its write
instructions eleven lines below said the other.

### 8b. The build-execution gate (2.3.31)

§7 listed "build executing tests" as open and said the fix was a stronger sentence.
That was wrong. Every file already forbade it in unambiguous language and the run
executed 474 tests anyway, because `superpowers:verification-before-completion` is a
loaded skill and a loaded skill outranks a reference file. **Prose cannot win that
argument.**

What works instead is a place to record and a refusal downstream:

- `stage-7.unplanned_executions` — required, `[]` written explicitly; absent HALTS
- Stage 8 §8g — `PARTIAL_UNPLANNED_RUN`; a non-empty list cannot be `COMPLETE`
- `/dev:commit` §2 — proceeds, and **discards every result it produced**
- Stage 11 — surfaces it above everything else; a gate nobody reports is half a gate

The field exists because the offending run *was honest*: it wrote `executed: false`
correctly, then parked the results in an invented `builder_run_results:` key because
the schema had nowhere for them. **Nothing was reading.**

### 8c. The audit — what the earlier passes left stale

Reviewing the above against the rest of the corpus, in order of severity:

| Found | Why it mattered |
|---|---|
| `dev-agent.md`'s own description said `/dev:build` **"execute tests locally"** | the agent's frontmatter is the first thing it loads. Every stage file said otherwise and this said yes — a strong candidate for the actual cause of the 474-test run |
| `stage-11-summary.md` did not surface `unplanned_executions` | the gate refused `COMPLETE`, but the human only ever reads the summary |
| `dev-context-templates.md` enumerated four build statuses, not five | the stale-enumeration class the `bavocab` check already exists for |
| `commit.md`'s stage table and `fix-review.md` still described Stage 5 as one phase | `/dev:fix-review` would have executed before its round's fixes settled |
| `stage-7`'s progress block declared `gates_run: 7, gates_passed: 7` | build reporting gates it cannot have run |
| `ARCHITECTURE.md` said commit *"runs the suite, reviews the code"* | the order is now the opposite, and this is the top-level document |
| the `rules` check itself matched case-sensitively | `loop-control.md` said "build executes nothing" in lower case and slipped through — the exact miss the check exists to prevent, in the check |

The last row is the useful one. The mechanism caught a restatement **I had written
four minutes earlier** in `dev-agent.md`, and then its own blind spot caught a
seventh file. That is the difference between a rule and a checked rule.

### 8d. Still open

- **Enforcement is reactive.** Five rules and one gate. Each exists because something
  bit. Coverage — every rule that matters carrying a trace and a downstream refusal —
  is the remaining work.
- **Nothing here has been run.** Lint proves the files agree. It proves nothing about
  whether the loop behaves as specified. One `/dev:commit` on a task with a blocking
  finding, then read `stage-5.phase_execute.full_map_runs`; `1` means it worked.
