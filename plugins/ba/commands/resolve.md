---
description: Adjudicate author answers to a scope review and close the questions. Point it at the scope-review-<timestamp>-responses.md file exported from the HTML report; the BA agent matches it to the original review, judges each answer (resolve / accept-as-assumption / ask for verification / decline), folds confirmed answers back into the scope and the BA registers, recomputes the scores and verdict, and writes a new review round.
argument-hint: "[<path-to-scope-review-<timestamp>-responses.md>  |  (blank = ask the open questions here)]"
---

# /ba:resolve

You are running a **resolution round** on a scope review: the author has answered the scope questions, and you adjudicate each answer, close the open items, and fold the answers back into the scope. Delegate the work to the **`ba-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` is **optional**. There are two ways in, and they converge on the same file.

**No argument — ask the questions here.** This is the normal path when the person who can answer is in the conversation. Load the most recent review's `.json` (or ask which, where several are open), take every question whose `status` is `Open`, and work through them **one at a time** per §1a. Write the responses file yourself, then resolve it exactly as below.

**A path — resolve what came back.** `scope-review-<reviewId>-responses.md`, exported from the interactive HTML report or hand-written in the same format. This stays the right flow when the answerer is a client who is not in the room.

- If a path is given and doesn't resolve, say so and ask for a valid one.
- If no path is given and no review has open questions, say so and stop — there is nothing to resolve.
- The `<reviewId>` (timestamp) embedded in the filename and the file's `source_review` frontmatter is the **join key** back to the original review.

### 1a. Asking the questions (no-argument path)

Everything needed to pose a question is already in the review `.json`: `id`, `clrId`, `severity`, `feature`, `dimension`, `question`, `whyItMatters`, `consequence`, `checkedIn`, `suggestedScope`, `instances`, `status`.

**Show the `clrId`, not the `SQ`.** `CLR-###` is the gap id — the same number in `clarifications.md`, in `client-questions.md` and in every round — so it is the one a person can carry between files and recognise again. `SQ-###` is the internal round key and belongs in the `.json`, not in a prompt. Where a question predates `clrId`, fall back to its `SQ` rather than inventing one.

**Show the instances when a question carries them.** A question merged from several occurrences lists where it bites, so the answerer can see that one answer settles three places rather than treating it as an isolated detail:

```
CLR-021  ·  Blocker  ·  Timesheet — allocations

When someone is removed from a project after logging hours against it,
what happens to those hours and that row — including in weeks already
submitted?

Same scenario in 3 places — one answer settles all three:
  · TIME-UC-04   removed mid-week, week not yet submitted
  · TIME-UC-07   removed after submission, before approval
  · PAY-UC-02    removed after payroll has pulled the week

  1 · Hours stay, row locks        2 · Hours move to unallocated
  3 · type your own                 d · defer
  s · these are not the same — split them
```

**Offer `s` on every question that has instances.** A merge made during extraction is a judgement, and the person answering is the one who can tell it was wrong. On `s`, split the instances back into separate ids, ask them one at a time, and say which. Without it a bad merge is permanent and invisible — the swallowed question does not exist anywhere to be found again.

**From round 2 onward, open with the ledger — before asking anything.** Print the five buckets from `resolution-loop.md` §6b: Accepted (naming the §3.x each landed in), Assumption (naming the owner), **Answered — not enough yet** (with what they said, why it fell short, and the follow-up), Declined, and Still open (with who it waits on). Then the count of new questions.

The person in front of you answered questions last time. Asking for more without first saying what those answers achieved is what makes a third round feel like the second one renumbered — and it is the reason a later round gets read as having added nothing. Round 1 has no prior round and opens straight into the questions.

**Also take the open `CLR`s** marked `answerable: here` from `ba/logs/clarifications.md`, and interleave them with the `SQ-###` by severity — to the person answering they are one list, not two passes. `/ba:scope` deliberately wrote them without asking; this is where they get asked.

**A follow-up raised by an answer is asked in the same sitting.** When an answer opens a new question — settling how history is stored raises what happens when an email changes — give it its id and **ask it now**, while the user is here and holding the context that produced it. Keep going until nothing new is raised. Ending the loop with "three new questions came up, run `/ba:resolve` again" sends someone away to answer something they could have answered in the next breath.

Only two things end the loop: every open question is answered, or the user defers. A follow-up may itself be deferred — that is a choice, not an automatic stop.

**Re-run only for what was deferred.** Close by naming exactly that, so a second run is a deliberate return rather than a chore:

```
Answered 16 · deferred 2.

Waiting on you:       SQ-020  how a manual correction reaches the portal
Waiting on Novacore:  SQ-021  filling in a week after being taken off the project

Run /ba:resolve when you have those — it will ask only these two.
```

**Run it as often as you like — it only ever asks what is still open.** A re-run reads `status: Open` afresh, so an answered question never reappears and a deferred one always does. Nothing is lost between runs.

**Offer every open question — do not pre-filter by who "should" answer.** The person running this may be the product owner, may have been told the answer in a meeting, or may simply be authorised to decide. Holding a question back because it *looks* client-bound makes them chase an answer they already have, and a 4-of-18 prompt when 18 are open reads as the tool deciding for them.

Label the ones that belong to the requirement's owner, and let the user choose:

```
CLR-009  ·  Blocker  ·  waiting on: Novacore
How strictly is a submitted week locked?

  1 · <option>      2 · <option>      3 · type your own
  d · defer — leave it for Novacore
```

**Default to defer on an owner-bound question**, so pressing through costs nothing and answering is deliberate.

**An answer given here to an owner-bound question is decided, not confirmed.** Record it as a `DEC-###` marked *decided internally, not yet confirmed by <owner>*, keep it in the sign-off list, and leave the underlying question in `ba/open-questions.md` as a confirm-this item rather than deleting it. That is the honest shape: the team can move, and the client still gets asked.

Ask **one at a time**, highest severity first (Blocker → Major → Minor → Nit):

```
CLR-021  ·  Blocker  ·  Timesheet — allocations

When someone is removed from a project after logging hours against it,
what happens to those hours and that row — including in weeks already
submitted?

For example:   Priya logs 12 hours to "Acme Portal" across Mon–Wed and submits
               the week. On Thursday she is taken off that project.
               Does her submitted week still show those 12 hours?

Why it matters: the Tracker deletes allocation rows outright, so with no rule
               the row vanishes and the hours it held become invisible. The use
               case "Remove an employee from a project" cannot be written until
               this is settled.

Already checked: the scope's allocation section and that use case, the
               contradictions log, and the use-case register — none of them say.

  1 · Keep the row, locked and read-only, with the hours intact
  2 · Keep the hours but drop the row from future weeks
  3 · Type your own answer
  d · Defer — leave it for Novacore
```

**Write the question so it can be answered without looking anything up.**

- **Never show a bare id.** `UC-07`, `CON-005`, `§3.1.4` mean nothing to the person answering. Name the thing: *the use case "Remove an employee from a project"*, not `UC-07`. Keep the id in the record, out of the prompt.
- **Give a concrete example.** One or two lines with real names, numbers and days turns an abstract rule question into something a person can picture and decide. "Priya logs 12 hours and submits, then is taken off the project" is answerable; "what happens on allocation removal" invites a shrug.
- **Say what `checkedIn` means in words.** "the scope's allocation section and the contradictions log — none of them say" tells the reader you looked and found nothing. A list of section numbers tells them nothing and reads as noise.
- **Offer the realistic options** where the answer has a small known set, with *type your own* always available. A question with no options makes the user compose prose for something that is really a choice between two behaviours.

**Show `checkedIn` every time.** The question records where it already looked for the answer. Surfacing it lets the user say "it is in the register, you missed it" instead of answering something the scope already settles — and that correction is more valuable than the answer would have been.

**Re-screen after every answer.** Drop any remaining question the answer just settled and say which: "SQ-004 and SQ-007 are answered by that — dropping them." One decision often closes three, and re-asking what is already settled is most of what makes a batch expensive.

**Deferring is one word.** A question the user defers keeps `status: Open` and simply is not written to the responses file; it carries into the next round by its stable `SQ-###`.

**Then write the responses file** at `scope-review-<reviewId>-responses.md`, in exactly the format the HTML export produces — one section per answered `SQ-###` with `**Intent:**` and `**Response:**` — with `exported_from: conversation` in the frontmatter instead of `html-report`. From here the two paths are identical.

## 2. Delegate

**Ask §1a's questions here, in this command, before delegating anything.** The user is in this conversation, not in a subagent — a delegated agent cannot run the one-at-a-time loop with them, and handing it the job is how the prompts lose their examples and turn back into bare ids. Finish the loop, write the responses file, and only then delegate.

Invoke the **ba-agent** subagent with the responses-file path — the one given as an argument, or the one §1a just wrote from the conversation. By this point the two paths are identical: the subagent only adjudicates a completed file. Pass it this instruction:

> Run a scope-review resolution round using the `ba-scope-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and load the matching `scope-review-<reviewId>.json` (the prior review state) from the same folder. For each question that received an answer, **adjudicate** it: set status to `Resolved`, `Accepted-assumption`, `Needs-verification` (with 1–3 specific follow-up questions), `Won't-fix`, or leave it `Open` — with a one-line rationale each. Be skeptical: require specifics, don't close on vague assurances. For every terminal question, **apply the scope edit** — edit `ba/scope.md` at the owning §3.x sub-heading, do not merely describe the edit — and, when a workspace exists, promote it: confirmed facts → `shared-context/decision-log.md` (`DEC-###`) and the scope; accepted assumptions → `ba/registers/assumptions.md` (`ASM-###`, RAID A-##); still-open must-close items → `ba/logs/clarifications.md` (`CLR-###`, RAID Q-##). **From round 2 onward, open the round with the ledger** — the five buckets from `resolution-loop.md` §6b (Accepted, naming the §3.x each landed in · Assumption, naming the owner · **Answered — not enough yet**, with what they said, why it fell short and the follow-up · Declined · Still open, with who it waits on), then the new questions. Write it into the round's `.md` and `.html` as a `Since the last round` section before the scorecard, and print it in chat before asking anything. **Set `clrId` on every question** so a person is shown the gap id rather than the internal round key. Carry all questions forward by their stable `SQ-###` IDs, update each feature's coverage map, and recompute the feature scores and the scope-readiness verdict (a resolved Blocker lifts the cap; note residual risk for accepted assumptions). Then write a **new review round** — fresh timestamped `.html` / `.md` / `.json`, with `round` incremented and `priorReview` set to the resolved reviewId — and return a summary of the movement.
>
> Responses file: `<path>`

## 3. Surface the result

When the agent returns, present the **round summary**: how many questions were Resolved / Accepted-as-assumption / Needs-verification (list the follow-ups the author still needs to answer) / still Open, the score and verdict movement (e.g. "3.4 → 6.2, Significant gaps → Estimate with caveats"), which scope edits were **applied** (naming each file and section actually written — and, if there is no workspace, saying plainly that the edits are pending, not applied), and any `DEC`/`ASM`/`CLR` rows logged. Link to the new round's `.html` (interactive) and `.md`. If items still need verification, tell the user to answer the follow-ups in the new report and export again.
