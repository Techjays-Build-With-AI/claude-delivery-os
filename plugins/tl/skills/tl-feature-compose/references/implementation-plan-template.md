# `tl-plan.md` — Implementation-tab content

The output of `/tl:compose`. Populates **only** the Implementation tab on the Jetrix Task via `/jetrix:push implementation`. Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, and Dependencies are populated by BA push from other files — they never appear in this document.

A reader of the composed file gets a solid, buildable spec — enough behavioural / contractual detail to implement — with no framework, library, version, or file-path noise. Components are named by their **role**.

## Frontmatter (required)

```yaml
---
doc_type: tl-plan
schema_version: 1.2
produced_by: tl
feature_id: FEAT-<AREA>-NN
composed_at: <ISO date>
inputs_hash: <sha256 of feature.md + owned unit bodies>
---
```

Feature identity lives in this frontmatter (and in the MC task metadata). It **never** appears in the visible content — no `# FEAT-…` heading, no reference to the id inline.

## Section skeleton

```markdown
## Build sequence

<one paragraph naming the phases and their dependency order>

```mermaid
flowchart LR
    S1[1. <phase>] --> S2[2. <phase>]
    S2 --> S3[3. <phase>]
    …
```

| Step | Build | Done when |
|---|---|---|
| **1** | <what to build in this phase, by role> | <verifiable condition> |
| **2** | <what to build in this phase, by role> | <verifiable condition> |
| … | … | … |

## API endpoints

### Create — <endpoint role, plain-language>

<one line naming HTTP method + path, auth requirement>

**Path parameter**  (only when the endpoint has one)

| Name | Type | Constraint |
|---|---|---|
| `<name>` | <type> | <role — e.g. "Identifier of the leave request"> |

**Request body**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `<field>` | <type> | <Yes/No> | <constraint> |

```json
{
  "<field>": "<example value>",
  …
}
```

<one line naming what OTHER body fields are silently discarded, if any>

**Execution order — normative**

| Step | Check | Failure |
|---|---|---|
| 1 | <check> | <code + reason> |
| 2 | <check> | <code + reason> |
| … | … | … |

<one paragraph explaining any invariant the order guarantees — e.g. concurrency via a single conditional write>

**Success — `<code>`**

```json
{
  "<field>": "<example value>",
  …
}
```

<one line on what is returned and why the client uses it>

**Refusals** — every body is `{ "message": "..." }` and nothing else.

| Code | Condition | `message` |
|---|---|---|
| `<code>` | <condition> | `<exact message text>` |
| … | … | … |

<one paragraph naming the invariants: idempotency, partial-write behaviour, side-effects>

### Update — <endpoint role>  (if the feature updates one)

<same shape>

## Database modifications

<one line naming the affected data object by role — collection or table — and confirming what does or does not change: new fields, new indexes, migrations>

**Fields written by this feature:**

| Field | Type | Written value |
|---|---|---|
| `<field>` | <type> | <what is set, in prose> |

**Never touched** — <one line listing existing fields the feature does not write, so reviewers see the boundary>: `<field-a>`, `<field-b>`, `<field-c>`.

<one paragraph on any state semantics the write depends on — for example, "Pending is the only decidable state; Approved, Rejected and Cancelled are terminal">

## Frontend UI

**API wiring** — which surface calls what.

| Surface | Trigger | Calls |
|---|---|---|
| <surface role> | <user action> | <endpoint role + reference to the API section, OR "no call — opens the <dialog role>"> |
| <surface role> | <after a specific response> | <existing call — no new endpoint> OR <endpoint role> |

<one line naming what is the ONLY new call this feature adds and what everything else reuses>

### <surface role> — row / list / summary action

<one paragraph on placement — where in the existing surface this action lives, and what it opens>

- <bullet on action visibility rule — e.g. "renders only when the row is Pending">
- <bullet on the read-only representation after action, if applicable>
- <bullet on graceful degradation — e.g. "unmatched directory record shows the raw identifier">

### <dialog role> — the interactive form

Submits to <endpoint role>. Only <fields> are sent; identity or context is server-resolved.

| Control | Behaviour |
|---|---|
| <control name> | <shape + required + validation> |
| <control name> | <shape + required + validation> |
| Submit | Disabled until <condition>. Re-enables only on <condition> |
| Cancel | Closes without a request |

**On success** — <what the dialog does + what the surrounding surface does>.

**On refusal** — <keep dialog open? preserve values? render inline? banner?>

| Code | Placement | Additional action |
|---|---|---|
| `<code>` | <where the message renders> | <optional follow-up, e.g. "refresh the list behind the dialog"> |
| … | … | … |

<one line naming what the client mirrors from server validation for enablement, and confirming the server's `message` is always what is displayed>

### API service

One call wrapping <endpoint role>, returning a value the caller can distinguish across every response code above plus transport failure. The server's `message` is carried through unmodified.

## Touch points

> Reuse entries are verified against the target codebase at authoring time; re-verify if this ticket sits idle. New entries carry no path — naming and placement are the developer's call. Strip this sub-section if the ticket goes to a client.

| | Component |
|---|---|
| **Reuse** | <existing component described by role — one line naming why it is the right host> |
| **Reuse** | <existing component described by role> |
| **New** | <new component described by role> |
```

---

## What this file MUST NOT contain

Enforced by the composer. If any of these appear, the composition is wrong and must be redone.

### 1. File paths — anywhere

No `controllers/Leave.js`, `src/components/**/*.jsx`, `models/LeaveRequest.js`, `routes/router.js`, or any other path. Components are named by role: **the leave controller**, **the decision dialog**, **the API service layer**, **the leave list**, **the row action**. Reuse entries in the Touch points section name the existing component by role too, never by path.

### 2. Framework, library, or version names — anywhere

No `React`, `React 18`, `Vite`, `Express`, `Mongoose`, `TipTap`, `Redux`, `Playwright`, `Jest`, `axios`, `@uiw/react-md-editor`, `Prisma`, `SQLAlchemy`, or any version number. Describe what a component does, not what technology it uses. `new mongoose.Schema({...})` fences are forbidden — describe the data object by role and by the fields written.

### 3. Duplication of other tabs

Never re-print content that belongs in Description, Business Rules, Acceptance Criteria, NFRs, Test Scenarios, or Dependencies. **This document is Implementation-tab content only.**

- No Business Goal / feature summary / user-value section.
- No user-flow narrative (that lives in Description).
- No mermaid workflow diagram (that lives in Description).
- No AC list (that lives in Acceptance Criteria).
- No NFR list (that lives in NFRs).
- No Business Rule list (that lives in Business Rules).
- No Test Scenarios (they live in Test Scenarios).
- No Dependencies / Assumptions / Open Questions (they live in Dependencies).

The visible content of this document is: **Build sequence · API endpoints · Database modifications · Frontend UI · Touch points**. That is the entire allowance.

### 4. Feature identity in visible headings or prose

Feature id, initiative, slug, provenance, and file-source annotations live in the frontmatter and the MC task metadata. Never in headings, never in prose. No `# FEAT-…` H1. No "Provenance: …" line. No mention of `feature.md`, `workflow.md`, `acceptance-criteria.md`, any `ba-output/…` file, any `context/…` file, or any scope-review filename. Ever.

### 5. Existing schema fields the feature does not write

If the feature modifies four fields on an existing model, print those four — and only those four — in the "Fields written by this feature" table. The other fields on the model are named in one line ("Never touched: `<field-a>`, `<field-b>`, `<field-c>`") for reviewer boundary awareness, and that is the whole allowance.

### 6. Redundant response text or duplicated status meanings

If the endpoint returns three distinct `409` messages, list three rows in the Refusals table. Never collapse "Approved" and "Rejected" into a single `409` row, and never leave the discrimination ambiguous. Similarly for `400` variants — list each `message` explicitly.

### 7. Client-narrative, provenance blocks, or author-side commentary

- No "the client chose transparency knowingly", "the plan is not consent", "note the tension worth raising with the client".
- No `⚠ PROVENANCE — PLANNED, NOT BUILD-READY` blockquote callouts.
- No "the register marks this …", "acceptance criteria are authored as bullets without ids".
- No "SIMULATED response round" preambles.

The task's Description and Dependencies tabs carry any workflow provenance the client needs to see.

### 8. Aspirational text

No "consider", "might", "could", "we should think about". A phase is either buildable or it is `[HELD · waiting on <OQ-id>]` and named as such.

---

## What this file MUST contain

- **Build sequence** at the top — a paragraph, a mermaid step-graph, and a step table with a verifiable "Done when" for each step.
- **API endpoints** — one section per endpoint (Create / Update / Delete / Read), with Request body table, normative Execution-order table, Success JSON, and Refusals table. Every distinct response code and every distinct `message` gets its own row.
- **Database modifications** — the "Fields written" table for this feature, a one-line boundary listing "Never touched" fields on the same object, and a paragraph on any state semantics the write depends on.
- **Frontend UI** — an API-wiring table (which surface calls what), a section per user-facing surface (row action / dialog / etc.) describing behaviour by role, a Refusal-placement table, and a one-paragraph API service description.
- **Touch points** — a Reuse / New table naming existing and new components by role, with the internal review caveat.

## Size budget

- **Target:** 10–15 KB per feature (≈2500–4000 words).
- **Warn at:** 55 KB.
- **Hard fail at:** 60 KB — MC's `implementationDetails` field caps at 60 000 characters.

If a feature would compose above 60 KB, the feature is too wide — refuse to write, ask the user to split.

---

## Worked example

The full worked example lives at `<repo-root>/docs/dharma-feedback-plan-example.md` and demonstrates the exact shape, tone, and density this template requires. Read it once before composing your first feature. **Every rule above is honoured in that example** — no paths, no framework names, no cross-tab duplication, no feature id in visible content.

Two properties to lift from that example:

1. **Behaviourally detailed, repo-abstract** — execution order is normative and named as such; every response code carries its exact `message`; the dialog table names every control and its enablement rule. None of it names a file, a framework, or a version.
2. **Boundary-aware** — the "Never touched" line on the data object, the "only new call this feature adds" line in API wiring, and the Touch points table's "Reuse / New" split all give a reviewer the change boundary at a glance.
