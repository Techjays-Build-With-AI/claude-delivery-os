# BA regression set

Four short requirements with the answers written down in advance. Run `/ba:scope`
over one, then compare what came back against this file.

The point is to make a change to the BA **measurable**. Every rule in
`ba-extraction`, `ba-scope-review` and `ba-feature-breakdown` was added because
something was missed; without a fixed input and a fixed expected output, the
next change is judged by how the prose reads rather than by whether the miss
stopped happening.

**How to score a case.** Three counts, nothing weighted:

| | |
|---|---|
| **Caught** | expected items the run produced |
| **Missed** | expected items it did not |
| **Noise** | questions it raised that the input already answers |

**Noise is a failure, not a bonus.** A question whose answer is sitting in the
input is a reading error, and it is the specific thing the question gate exists
to stop. A run that catches everything and adds six invented questions is worse
than one that catches one fewer and adds none.

Record the three counts and the date against the case. A change that moves one
up and another down is a trade to decide deliberately, not an improvement.

---

## R-1 · Shift-based timesheet (track A — client requirement)

> "We need a timesheet tool for our site staff. Supervisors enter hours for
> their crew at the end of each shift, in half-hour steps, and nobody can be
> booked more than 12 hours a day. The week closes on Sunday and payroll pulls
> it the Monday after. If someone was on two sites in one day it has to split
> across both. Supervisors can fix their own entries until the week closes,
> after that only the site manager can. It has to work on phones — half the
> crew leads are never at a desk."

**Must appear, as stated and not generalised** — this case exists for D2:

- `12 hours a day` — the number, not "daily limits apply"
- `half-hour steps` — the increment, not "configurable granularity"
- `the Monday after the week ends` — the payroll timing, verbatim
- a split-across-two-sites route, as its own use case (different steps, not a data value)
- the edit window as a rule with its two actors: supervisor until close, site manager after

**Must appear in §4b (NFR)** — this case exists for D3:

- mobile reach ("has to work on phones"), as a stated constraint with its source

**Must be asked** (none of these is answerable from the text):

- what "the week closes" means in time terms — a clock time, a timezone, and who triggers it
- whether the 12-hour cap is per day or per shift, and what happens when a shift crosses midnight
- whether the site manager's post-close edit re-opens the payroll pull, or amends the next one
- whether a crew member can appear under two supervisors

**Must NOT be asked** — each is answered above:

- who enters the hours · what the increment is · when payroll pulls ·
  whether multi-site is supported · whether mobile matters

**Expected glossary** (M6 — settle before writing requirements): *shift*, *crew*,
*site*, *week close*, *entry*. "Shift" and "day" are used as if interchangeable in
the text and are not — that tension is a `CON`, and finding it is the case.

---

## R-2 · Asset tracker (track A — the identity-matching case)

> "We want to know which laptop is with which person. HR has the staff list.
> IT keeps a spreadsheet of machines with the person's name typed in. When
> someone leaves, the machine should come back to the pool. We also want to see
> what is unassigned and what is overdue for return. People change their names
> sometimes — after marriage — and the history should follow them."

**Must appear:**

- the return-to-pool path as a lifecycle step owned by some module, with a trigger
- unassigned and overdue as two distinct states with the rule that defines "overdue"
- the rename requirement, written as a rule about identity rather than a display concern

**Must be raised as a Blocker** — this case exists for the cross-module pass (M7):

- **the join between HR staff and IT's typed-in names.** One side has records, the
  other has free text. Nothing stated makes them matchable, and the rename
  requirement is unimplementable without a stable key. A run that writes an
  `employeeId` into the data table **without raising it** has invented the
  requirement — count that as a miss *and* a correctness failure, not a catch.

**Must be asked:**

- what identifies a person across both systems, and whether HR exposes it
- what "overdue" is measured from, and by how long
- who initiates the return when someone leaves without handing the machine back
- whether a person can hold two machines

**Must NOT be asked:** whether HR is the staff source · whether assignment is tracked.

---

## R-3 · Internal: add CSV export to the reports page (track B — no client)

> "The reports page needs a CSV export. Same filters as the screen. Finance has
> been copying out of the table by hand."

**Expected routing: track B**, and the two disqualifiers for track C both checked
and reported — if the resolved surfaces sit in one repo and the work is under
~3 features, this should hand to `/dev:plan` instead, with the reason printed.
**Either outcome is correct; failing to state which test was applied is the failure.**

**Must appear:**

- current state read from the **code** — the existing reports page, its filter
  state, and the endpoint behind it — not asked as a question to the user
- the filter parity requirement, tied to the filters that actually exist

**Must be asked, in `ba/open-questions.md` and not `client-questions.md`:**

- what happens at volume — whether the export is synchronous or queued, and the row
  ceiling at which that changes
- whether the export respects row-level permissions, if the screen does

**Must NOT appear:**

- a client packet, a client-questions file, or an example-validation finding
- `§3.x` dimensions written with "None" — omit what does not apply
- a question about why Finance wants it

**Expected question count: low.** This case exists to check that track B does not
produce client-requirement ceremony. More than four questions here is noise unless
the code genuinely raises them.

---

## R-4 · Contradictory sources (track A — the `CON` case)

Two sources on one engagement:

> **Discovery call:** "Anyone in the team can approve a request. We're small,
> we trust each other."
>
> **Process document sent afterwards:** "Approvals above AED 5,000 go to the
> finance lead. Below that, any team member."

**Must appear:**

- a `CON` row naming both statements and both sources — **not** a quiet merge into
  the threshold version because it is more specific
- the approval rule written against the contradiction, flagged, not resolved by
  the BA's own judgement

**Must be asked:**

- which of the two is current, and whether the threshold is new since the call

**Must NOT happen** — this is the whole case:

- silently adopting the document because it is later or more detailed. The BA does
  not have the standing to decide which source wins; recording that it does not
  know is the correct output.

---

## Running it

```
cd <a scratch workspace>
/ba:scope "<paste one requirement>"
```

Then score the three counts against the case above and append a row:

| Date | Case | Caught | Missed | Noise | Change under test |
|---|---|---|---|---|---|
| | | | | | |

**Nothing has been run against this set yet.** It is the expected output, written
from the rules as they now stand — it is not a record of behaviour observed.
