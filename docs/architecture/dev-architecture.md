---
title: Development — Architecture
audience: Engineers, technical leads, QA
status: current
---

# Development — Architecture

Three commands, each with a single responsibility and a hard refusal at its entry. Planning
decides *what* and *where*. Build implements and proves the tests are runnable. Commit executes,
reviews, and ships.

---

## 1. Architecture

### 1.1 The three loops

```
   feature folder (BA)                  qa/quality-gates.md (QA)
            │                                      │
            ▼                                      │ governs
   ┌─────────────────┐                             │
   │   /dev:plan     │  4 stages                   │
   │   design        │                             │
   └────────┬────────┘                             │
            │  implementation.md §1–§8             │
            │  plan-blockers.md PB-###             │
            ▼                                      │
   ┌─────────────────┐ ◄───────────────────────────┤
   │   /dev:build    │  11 stages                  │
   │   implement     │                             │
   └────────┬────────┘                             │
            │  code · tests · test-map · Acceptance table
            ▼                                      │
   ┌─────────────────┐ ◄───────────────────────────┘
   │   /dev:commit   │  12 stages — the only executor
   │   verify + ship │
   └────────┬────────┘
            │
            ▼
      pull request  →  merge  →  units flip to implemented
```

Side loops: `/dev:resolve` walks open plan blockers and resumes planning. `/dev:fix-review`
folds human reviewer feedback on an open PR back through the commit stages.

### 1.2 Separation of duties

| Command | Owns | Never does |
|---|---|---|
| `/dev:plan` | Technical design, split decision, blocker detection | Write code |
| `/dev:build` | Implementation, test authoring, test map, acceptance table | Execute the suite · commit · push |
| `/dev:commit` | Test execution, security, code review, context merge, PR | Implement new behaviour |

**Build declares; commit executes.** Build writes the tests and proves the map is runnable but
does not run the suite. This keeps exactly one executor, so a passing claim has exactly one
origin. The terminal exceptions — `--tests-only` and `--vulnerable` — execute because no commit
follows them.

### 1.3 State

Every run records to `units/<repo>/status.md`:

| Section | Carries |
|---|---|
| `## Run history` | Per-stage status, timestamps, invocation traces |
| `## Acceptance` | One row per assertion, with evidence |

Local state and tracker status move together: `readyForDev` → `agentExecuting` → `built` →
`devReview` (phase `pr-open`) → `done` on merge.

---

## 2. Planning process

| Stage | Action |
|---|---|
| 1 | Code-context readiness and QA-gate check; auto-runs forward planning if the graph is missing |
| 2 | Per-task analysis — decide the split: one unit per repository, or parent alone |
| 3 | Blocker detection — surface every decision that would otherwise interrupt the build |
| 4 | Compose the implementation plan and push it to the tracker |

**Blockers are the architectural point.** Any choice a developer would have to stop and ask about
is raised as a `PB-###` at plan time. `/dev:build` is therefore guaranteed never to prompt — it
either has everything it needs, or it was never allowed to start. Blockers are asked in
conversation as they arise; answered ones fold immediately, deferred ones leave the task
`blocked` for `/dev:resolve`.

### 2.1 The implementation plan

Eight sections, **stack-agnostic vocabulary**, plan-only:

| § | Section | Carries |
|---|---|---|
| 1 | Build sequence | Ordered steps — step, files, units, what it satisfies |
| 2 | Impacted components | Twelve-dimension impact matrix, one line each |
| 3 | Operations exposed and consumed | Per operation: contract, order-of-checks, refusals |
| 4 | Stored data changes | Fields written, with an explicit "never touched" boundary |
| 5 | User-facing surfaces | Per surface: props, state, effects, rendered states, controls |
| 6 | Touch points | Reuse / new / cross-unit |
| 7 | Risks and rollback | Risks, out of scope, cheapest lever and full rollback |
| 8 | Shared contract | Wire-level invariants inherited byte-for-byte across units |

The plan contains **implementation directives only**. The test applied to every line: *is this
something the developer types into a file, or something they read to understand?* Only the former
stays — rationale lives in the feature folder.

---

## 3. API design

API design is decided at plan time in **§8 Shared contract** and inherited byte-for-byte by every
unit in a split.

| Row | Decides |
|---|---|
| How the caller is identified | The credential on the wire and the abstract identity exposed to receiving code |
| Shape of one record | Bare object / wrapped / envelope, id encoding, null handling |
| Shape of a list | Array-under-key / bare array / envelope, empty representation, pagination placement |
| How a caller knows it failed | Success shape ≠ refusal shape / status field / discriminated union |
| Where code and message live in a refusal | Abstract path, described in prose |
| Global session-expiry behaviour | One canonical answer applied at the interface layer |
| Common identifiers | Opaque string / UUID / ULID / integer / composite, with length and case rules |
| Time and locale | Wire time format, timezone assumption, locale for user-visible text |
| Pagination convention | Cursor / offset+limit / page+size, or "none in v1 — accepted" |

**The portability test:** *could a Go, a Node and a Swift developer each build against this and
produce interoperable code?* If one of them would misread a line because it names a
runtime-specific field path, the line is rewritten to describe the wire and the condition.

**Enforcement.** Composition halts if §8 contains a framework accessor path. Those details belong
in the local context unit the developer opens at build time, not in the cross-stack contract.

**Boring decisions are recorded in context, not omitted.** "Not paginated — full result set
returned", "any authenticated caller; no role check" — stated on the operation they govern, so
their absence is never mistaken for an oversight.

**Per-operation design** lives in §3: the request contract, an order-of-checks table walking
every input state, and a refusals table with one row per distinct response message.

---

## 4. UI design and checks

A section that imports correctly and names things correctly, then renders its own fonts, spacing
and motion, reads as bolted on — because it is.

### 4.1 Mode detection

| The repo has | Mode | Action |
|---|---|---|
| Component library **and** token source | **Follow** | Detect, then apply the rules |
| Library but no tokens | **Follow + establish tokens** | Derive tokens from the library's own scales |
| Neither — fresh scaffold | **Establish** | Found the full system **before the first screen** |

Establish mode is one-time and must happen on the first UI feature. Every rule works by matching
a precedent; write the first screen without a system and the precedent becomes whatever that
screen happened to do.

### 4.2 The six scales

Every visual value comes from one of these. There is no seventh source.

| Scale | Rule |
|---|---|
| Spacing | One base unit; every margin, padding and gap is a multiple |
| Type | One ratio, few steps, each pairing size **with** line-height and weight |
| Radius | One scale, applied by component role |
| Elevation | One shadow set; depth means layer, not decoration |
| Colour | **Semantic names only** — `action`, `surface`, `danger`, never `blue-500` |
| Motion | One duration set and one easing set |

### 4.3 The hard rules

**Reuse before you create.** A second table implementation in a repo that has one is a defect.

**Never add a second UI library.** Whatever the manifest already has is the library.

**No hardcoded visual values where a token exists.** No hex colours, no pixel font sizes, no
inline transition durations.

**Match the neighbour, not your taste.** Consistency with one real neighbour beats any general
principle.

**Reusable, or it is a defect.** A visual element used on two screens is a shared component — the
second use is the trigger. Variants live inside the component, never at the call site.

### 4.4 States — what separates a product from a demo

Every interactive element ships five: `default` · `hover` · `focus-visible` · `active` ·
`disabled`. A visible focus state is never removed.

Every data surface ships four: `loading` · `empty` · `error` · `populated`. A screen that renders
only the populated case is unfinished — the other three are what users hit on a slow connection,
on day one with no data, and when the API is down.

### 4.5 Published standards the review checks against

| Requirement | Value |
|---|---|
| Text contrast | 4.5 : 1 |
| Large-text contrast | 3 : 1 |
| Non-text contrast (icons, borders, focus) | 3 : 1 |
| Target size | ≥ 24 × 24 CSS px |
| Focus appearance | 3 : 1 against unfocused, ≥ 2 px perimeter |

Motion follows published duration bands — fast 50–200 ms, base 250–400 ms, slow 450–600 ms — with
published easing curves rather than hand-tuned near-misses. Enter decelerates, exit accelerates,
and reduced-motion preferences drop transforms while keeping opacity.

Where no token file format is imposed by the framework, tokens are written in the W3C Design
Tokens format so design tooling can read them without a bespoke parser.

---

## 5. Build process — eleven stages

| Stage | Action | Gate |
|---|---|---|
| 1 | Acquire lock, mount context | |
| 2 | Pre-flight | Refuses without a completed plan |
| 3 | Branch creation | Never on a protected base |
| 4 | QA harness gate | Auto-bootstraps a greenfield harness if absent |
| 5–6 | Implement and write tests, per build-sequence step | |
| 7 | **Verify the test map** | Halts on a dangling or incomplete map |
| 8 | Validate against acceptance criteria, business rules, test scenarios, NFRs | |
| 9 | Security review — report-only | Critical blocks |
| 10 | Flip context units `designed → implemented` | Refuses if Critical findings are unaddressed |
| 11 | Summary and pull-request material | |

### 5.1 Stack-adaptive implementation

The stack is detected from the dependency manifest, then the repository's own conventions are
inferred from a bounded set of targeted reads across eight dimensions:

```
  folder structure · import style · error handling · dependency injection
  config access · logging · testing setup · naming
```

Typically four to six files: one endpoint handler, one service, the API client, one test. New
code matches what is already there rather than what the agent prefers. Where the repository's
pattern conflicts with the plan, the conflict is reported rather than silently resolved.

---

## 6. Best-practice checks

Two review engines run on the diff, each with four severity tiers.

### 6.1 Code review — eight dimensions

| # | Dimension | Looks for |
|---|---|---|
| 1 | Correctness | Does it do what the plan says, for every input state |
| 2 | Convention adherence | Does it match the repo's inferred patterns |
| 3 | Error handling | Are failures caught, surfaced and shaped per the contract |
| 4 | Testability | Can the behaviour be exercised without rewriting it |
| 5 | Business rule enforcement | Is each parent business rule actually enforced in code |
| 6 | Naming | Role-based, consistent with the repo |
| 7 | Reuse | Did it duplicate something that already exists |
| 8 | Engineering standards | Gated and advisory sections of the repo's standards |

Severity: **Blocker · Major · Minor · Nit.** At commit time Blocker and Major block; Minor and Nit
surface as follow-ups. Findings cite diff line numbers and include a concrete fix.

Review is **diff-scoped only** — never the whole repository.

### 6.2 Engineering standards — two tiers

| Tier | Sections | Effect |
|---|---|---|
| **Gated** | §1–12 (naming, folders, lint, tests, errors), §13 architecture and dependency rules, §19 reliability, §20 backward compatibility | A missing section halts the build gate |
| **Advisory** | §15 performance, §16 API design, §17 database, §21 observability, §22 accessibility | A missing section never halts |

**The tier governs whether a *missing section* stops the build — not whether a *violation* does.**
A Blocker-severity performance finding blocks like any other Blocker.

Security and dependency vulnerabilities are deliberately **not** in the standards file. They are
owned by the security review and by dependency auditing, and restating them would create a second
source that drifts from the one with teeth.

### 6.3 Security review

Runs twice, with different thresholds:

| Where | Scope | Blocks on |
|---|---|---|
| Build stage 9 | Snapshot-scoped, report-only | Critical |
| Commit stage 3 | Strict | Critical **and** High |

Every severity is recorded either way; the difference is what stops the run.

---

## 7. Test writing and the execution engine

### 7.1 Choosing the test kind

| Assertion shape | Test kind | Where |
|---|---|---|
| Endpoint returns X on valid input | Integration / contract | Backend unit |
| Endpoint returns X on error input | Integration | Backend unit |
| Business rule enforced on write | Unit on the service **and** integration on the endpoint | Backend unit |
| Database constraint such as uniqueness | Migration test or integration hitting the constraint | Backend / DB unit |
| UI form wired to an endpoint | Component test plus integration against a mocked API | Frontend unit |
| UI error display on server refusal | Component test with a mocked error response | Frontend unit |
| Full user flow | End-to-end | The last unit to land |
| Performance NFR | Benchmark / load test | Backend unit |
| Security NFR — rate limiting, authorization | Integration | Backend unit |

Tests are **behavioural, not tautological** — a test that restates the implementation proves
nothing. Test data carries no secrets and no real identifiers.

### 7.2 The test map — the machine-readable link

Build writes `<repo>/context/test-map/<feature-slug>.md`, one row per assertion, carrying the
test path, the named test, the command that runs it, what it needs to run, and its fixtures.

Stage 7 verifies the map rather than running it:

| Check | Failure |
|---|---|
| Test file exists | `test-map-dangling-test` |
| Named test exists inside that file | `test-map-dangling-test` |
| `Run it` command is populated | `test-map-incomplete` |
| `Needs` tokens are startable — `real-db`, `backend-running`, `frontend-running`, `real-auth`, or none | `test-map-unstartable` |
| Fixture exists | `test-map-dangling-fixture` |

**A missing map with tests written halts the build.** The map is the contract that lets the
executor know what to run and what each test proves.

### 7.3 Execution — commit stage 5

Commit is the only executor. Required external services are started first for integration,
contract, concurrency and end-to-end tiers. The suite runs across every test in scope — the ones
this run wrote **and** any pre-existing test the run will execute.

Failures are classified, not merely counted. An isolated re-run is **bounded to one attempt per
failing test**, so a flaky pass cannot be manufactured by repetition.

### 7.4 The fix loop

When a gate produces blocking findings, the fix loop is **mandatory and verifiable**. The
originating stage must invoke it and record the invocation — subagent id, originating findings,
attempts, exit state. Deciding privately that a finding is small enough to patch inline is a
specification violation.

The push stage **refuses** if blocking findings existed without a recorded fix-loop invocation, or
if post-loop counts are still non-zero. A fix loop that ended escalated cannot push either.

---

## 8. Evidence

### 8.1 The acceptance table

`units/<repo>/status.md § ## Acceptance` holds one row per applicable acceptance criterion,
business rule, test scenario and NFR.

| State | Meaning |
|---|---|
| `⏳ pending` | A sound test exists and is mapped, but has not been executed yet |
| `✅ pass` | Executed and passing — written only by the executor |
| `❌ fail` | Executed and failing |
| `n/a` | Not applicable to this unit |

Build can only produce `⏳ pending`, because build does not execute. Commit stage 5 converts
pending rows to pass or fail. **This is what makes a green claim attributable to a single
origin.**

### 8.2 The full evidence chain

| Artifact | Proves |
|---|---|
| `implementation.md §1–§8` | What was intended, in stack-agnostic terms |
| `plan-blockers.md` | Which decisions were escalated and how they were resolved |
| `context/test-map/<feature>.md` | Which test proves which assertion, and how to run it |
| `status.md § ## Acceptance` | Each assertion's executed result |
| `status.md § ## Run history` | Per-stage status plus fix-loop invocation traces |
| Security and code review findings | Every severity recorded, with what blocked |
| `pr-summary.md § How to verify` | The reviewer's runbook |
| Context units flipped to `implemented` | The graph now reflects reality |

### 8.3 Semantic context merge

Commit stage 7 merges the branch's context units against the base branch's baseline. It is
**graph-aware, not textual**: units merge field by field, layer indexes by row union. Two branches
touching different units of the same feature reconcile cleanly. A genuine conflict — the same unit
modified incompatibly on both sides — is recorded for human resolution and halts the commit.

This is what keeps the code context true as parallel work lands.

---

## 9. Boundaries

`/dev:build` **never** commits, pushes, or prompts. `/dev:commit` **never** implements new
behaviour, merges, or deploys. Neither weakens or deletes a test to go green. Business,
architecture, schema, security and scope decisions are escalated as blockers rather than guessed.
