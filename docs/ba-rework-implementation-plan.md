# BA rework — implementation plan

Three entry modes, review folded into scope, and questions answered in the
conversation instead of a file round-trip.

Every claim about current behaviour below was read from the source or from a
real run artifact in `plugin-test` before it was written down. Where this plan
contradicts something that already exists, that contradiction is named.

---

## 1. What we are building

`/ba:scope` reads its input, then asks which of three jobs this is:

| Mode | For | Code context | Produces |
|---|---|---|---|
| **Client requirement** | work a client must sign off and someone must estimate | no | scope · registers · client packet · HTML — as today |
| **Task needing a BA plan** *(new)* | a module-sized internal piece: too big for one plan, no client to question | **yes — this is what grounds it** | scope-shaped document + feature split |
| **Simple task** | one repo, well enough understood to build | resolved at plan time | nothing — hands to `/dev:plan` |

**The middle mode is the gap this plan exists to close.** Today a module-sized
internal piece has nowhere to go: too large for `/dev:plan`, which plans one
flat sequence, and too internal for full BA, which has no client to question.

**Routing is confirmed, not self-declared.** Read the file or ticket first, then
propose the mode with a reason. A user should not have to classify work nobody
has looked at yet.

---

## 2. The changes

### BA-1 · Three-way fork at `/ba:scope`

**Files:** `plugins/ba/commands/scope.md`, `plugins/ba/skills/ba-extraction/SKILL.md`

Ask once, after reading the input, before any extraction. On **simple task**,
print the reason and the handoff (`/dev:plan <ref>`) and stop — `/dev:plan` now
accepts a plain description or an adopted `.md`, so the handoff is real rather
than advice.

**Two hard ineligibility rules for "simple", both checkable, not judgement:**

- resolved surfaces span **more than one repo**
- the work needs **more than ~3 features**

Either one means the task is not simple, whatever it looks like.

### BA-2 · The middle mode

**Files:** new reference under `plugins/ba/skills/ba-extraction/references/`,
wired from `scope.md`

Starts from the code, which is the whole point:

1. Read repo paths from `.jetrix/cache/repolocation.json` — `/jetrix:init`
   already collects them, so the user is asked for a path only when the
   workspace is unbound.
2. Resolve the surfaces the work touches from `context/code-context/`, falling
   back to a question — never a silent grep — when the repo is unmapped. Same
   rule and reason as `/dev:plan` §2a.1.
3. Build the scope document **against what exists**: what is already there, what
   is new, what changes.
4. Split into features, then hand each to `/dev:plan`.

**Writes the scope document and the feature breakdown. Not the seven registers**
— on internal work nothing reads them. Add one back the moment something cites
it.

**Bounding the research step.** This is the part most likely to bloat back into
the ceremony we are removing. Stop when every §3.x dimension is either filled or
recorded as a question. Not when it feels complete.

### BA-3 · Review folded into `/ba:scope`

**Files:** `plugins/ba/commands/scope.md`, `plugins/ba/commands/review.md`

Review runs inside every scope run, because it already does in practice: the
cycle is scope → review → resolve, and `/ba:resolve` itself *"recomputes the
scores and verdict, and writes a new review round"*. There is no useful state
where you have run scope and not reviewed — you would have no score, no verdict
and no questions.

**The HTML becomes conditional.** The score lives in the `.json`
(`overallScore`, `verdict`), so the summary can print it without a dashboard
existing. Generate the 62 KB HTML only when questions are client-bound — that is
the packet you send. The `.md` and `.json` are written every run; `/ba:resolve`
matches rounds against the `.json`.

**`/ba:review` stays as a command** for a deliberate re-score without a scope
pass.

### BA-4 · `/ba:resolve` asks, instead of being handed a file

**Files:** `plugins/ba/commands/resolve.md`,
`plugins/ba/skills/ba-scope-review/references/resolution-loop.md`

This is the smallest change with the largest effect, because it reuses the
existing machinery exactly.

**It can already ask.** The review `.json` carries, per question: `id`,
`severity`, `feature`, `dimension`, `question`, `whyItMatters`, `consequence`,
`checkedIn`, `suggestedScope`, `status`. Everything needed to pose it.

**Run with no file:** read the open `SQ-###` from the matched review and ask one
at a time —

```
SQ-001  ·  Blocker  ·  ASSIGN
Can an asset record exist without being assigned to anyone?
Why it matters: <whyItMatters>
Already checked: scope.md §3.1.2, ba/registers/assumptions.md

Intent:    resolve · accept-assumption · need-info · wont-fix
Response:  ____
```

Then write the responses file in the format the HTML export already produces —
`**Intent:**` plus `**Response:**` per `SQ-###`, with
`exported_from: conversation` — and run the existing adjudication unchanged.

**Show `checkedIn` when asking.** The question already records where it looked
for the answer. Surfacing it lets the user say *"it is in the register, you
missed it"* instead of answering something already settled. That value is in the
data today and shown nowhere.

**Re-screen after every answer** and drop questions the answer just settled,
saying which. One decision often closes three — this is most of the token cost
the field feedback measured.

**The file path stays.** Point `/ba:resolve` at an exported responses file and
it behaves exactly as it does today. That is still the right flow when the
answerer is a client who is not in the room.

### BA-5 · Multi-repo on the non-feature track

**Files:** `plugins/dev/commands/references/plan/non-feature-track.md`

**This is a contradiction to fix, not a feature to add.** The split table in
`implementation-preparation.md` already says:

> `taskType == feature / epic / task` AND `repos ≥ 2` → **Split — one sub-task per repo**

but the non-feature track says *"Never split a non-feature into sub-tasks"*,
justifying it with *"bug, story and subtask are in `PLANNING_NOT_REQUIRED_TYPES`"*
— true for those three, then over-applied to `task` and `epic`, which are not in
that list and which the table explicitly says to split.

The signal was the real blocker: `repos ≥ 2` is computed from a feature's owned
units, and a non-feature has none. `/dev:plan` §2a.1 now resolves surfaces to
file paths, and file paths resolve against `repolocation.json` — which is the
repo set.

| Type | Repos | Result |
|---|---|---|
| `bug` · `story` | any | parent alone — a point fix by definition |
| `task` · `epic` | 1 | parent alone |
| `task` · `epic` | ≥ 2 | **split, one sub-task per repo** |

A small change that happens to touch two repos is common, and today it has no
path. This gives it the one that already exists for features.

---

## 3. What this removes

| Removed | Why |
|---|---|
| The task **weight classifier** (P0-1 in the earlier usability plan) | The three-way fork replaces it and is better — it asks rather than guesses, and it has a mode for the middle case a classifier would have misrouted into a path that cannot split |
| **`/ba:review` as a required second step** | Folded into scope, which is the sequence everyone already follows |
| **HTML on every review** | Only when questions are client-bound |
| **The export round-trip in `/ba:resolve`** | The conversation writes the responses file |
| **"Never split a non-feature"** | Becomes conditional on the resolved repo set |
| **The seven registers on internal work** | Nothing reads them there |

---

## 4. What this does not touch

Deliberately, because it is where the real rigour lives:

- **The adjudication engine.** `/ba:resolve` judging each answer
  (`resolve · accept-assumption · need-info · wont-fix`), folding into scope and
  registers, recomputing scores, writing the next round. Only its *input method*
  changes. This is what keeps the change safe.
- **The four screening rules** — screen out-of-scope first, probe every step of a
  multi-step flow, probe the existing setup when extending a live platform, cover
  per-module corner cases. `33c0184` sharpened these recently; this plan builds
  on them.
- **Example validation** — `Pass / Partial / Conflict / No-examples` citing `EX`
  ids. Nothing a conversation produces replaces checking a feature against what
  the client actually sent.
- **Derived, capped scoring** and the `SQ-###` round carry-forward.
- **`client-questions.md`** — correct for its real audience. The bug was using it
  where the developer was the answerer.
- **Every gate downstream.** Acceptance mapping, security review, the
  quality-gate contract, the test harness. This plan reduces *documents and
  round-trips*, never verification.

---

## 5. Risks

| | Risk | Mitigation |
|---|---|---|
| R-1 | The middle mode bloats into full BA — it is the least specified step | Stop condition in BA-2: every §3.x dimension filled or recorded as a question. Writes no registers. |
| R-2 | Conversational resolve loses the audit trail | It writes the same responses file, and `SQ-###` ids stay stable and append-only, so rounds still diff |
| R-3 | Mode routing guesses wrong | Confirmed with the user before anything is written, with the reason stated |
| R-4 | Splitting a `task` conflicts with Mission Control's model | `task` and `epic` are not in `PLANNING_NOT_REQUIRED_TYPES`; the split table already sanctions it. Verify against a real MC push before shipping. |
| R-5 | Code-context staleness feeds a wrong scope | Same rule as `/dev:plan` §2a.1 — verify one cited file, say "stale" out loud, never plan against a unit that no longer matches |

---

## 6. Sequence

Smallest and most certain first.

1. **BA-5** — the split contradiction. One rule, already sanctioned elsewhere, unblocks a common case.
2. **BA-4** — conversational `/ba:resolve`. Reuses the existing file format and engine; highest relief per line changed.
3. **BA-3** — fold review into scope, make HTML conditional.
4. **BA-1** — the three-way fork.
5. **BA-2** — the middle mode. Largest, and it depends on 1–4 being settled.

---

## 7. Open questions

1. **Where exactly is the "~3 features" line for simple?** Worth testing against
   ten real recent tickets rather than deciding in the abstract.
2. **Should the middle mode push its features to Mission Control automatically,
   or stay local until asked?** Same question `/dev:plan` adoption answered with
   "stay local"; consistency argues for the same answer.
3. **Does a `task` split into sub-tasks round-trip cleanly through MC?** R-4 —
   needs one real push to confirm, not a reading of the config.

---

*Nothing here is implemented. The current behaviour described above was verified;
the proposed behaviour has not been built or run.*
