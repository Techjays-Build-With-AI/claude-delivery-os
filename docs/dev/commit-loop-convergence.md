# Why `/dev:commit` takes an hour, and the four changes that fix it

Investigation record · v1.0 · 2026-11-13

**Status:** three changes landed in `37140ed`. Three more are specified below in
§5 and not yet applied.

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

## 5. Not yet applied — repeated test execution

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

### 5c. The three edits

| File | Change |
|---|---|
| `stage-6-fix-loop.md` §6d.i | `test verification → always` becomes the `allowed_files ∩ Test` rule; add the §7f.i classification precondition |
| `stage-6-fix-loop.md` §6b.iv | its *"re-run that scenario's own `Run it`"* line becomes the rule rather than the exception it currently contradicts |
| `stage-5-acceptance.md` §5b.i | widen from "carried from build" to "any red row, wherever first seen" |

---

## 6. The same run, replayed under all six changes

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
