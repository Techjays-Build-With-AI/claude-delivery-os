---
description: Adjudicate author answers to a scope review and close the questions. Point it at the scope-review-<timestamp>-responses.md file exported from the HTML report; the BA agent matches it to the original review, judges each answer (resolve / accept-as-assumption / ask for verification / decline), folds confirmed answers back into the scope and the BA registers, recomputes the scores and verdict, and writes a new review round.
argument-hint: "<path-to-scope-review-<timestamp>-responses.md>"
---

# /ba:resolve

You are running a **resolution round** on a scope review: the author has answered the scope questions, and you adjudicate each answer, close the open items, and fold the answers back into the scope. Delegate the work to the **`ba-agent`** subagent.

## 1. Parse arguments

`$ARGUMENTS` should be the path to a **responses file** — `scope-review-<reviewId>-responses.md`, exported from the interactive HTML report (or hand-written in the same format). This is required.

- If no path is given, ask the user which responses file to resolve and stop.
- If the path doesn't resolve, say so and ask for a valid one.
- The `<reviewId>` (timestamp) embedded in the filename and the file's `source_review` frontmatter is the **join key** back to the original review.

## 2. Delegate

Invoke the **ba-agent** subagent with the responses-file path. Pass it this instruction:

> Run a scope-review resolution round using the `ba-scope-review` skill — follow `references/resolution-loop.md`. Read the responses file at `<path>`, take its `source_review` reviewId, and read the prior round back out of the report itself — `<script id="review-data">` in the matching `.html` — that block holds the prior review state. There is no `.json` sidecar. For each question that received an answer, **adjudicate** it: set status to `Resolved`, `Accepted-assumption`, `Needs-verification` (with 1–3 specific follow-up questions), `Won't-fix`, or leave it `Open` — with a one-line rationale each. Be skeptical: require specifics, don't close on vague assurances. For every terminal question, give the **exact scope edit** (which §3.x sub-heading, what text) and, when a workspace exists, promote it: confirmed facts → `shared-context/decision-log.md` (`DEC-###`) and the scope; accepted assumptions → `requirements/<slug>/ledger.md` (kind: assumption) (`ASM-###`, RAID A-##); still-open must-close items → `requirements/<slug>/ledger.md` (kind: question) (`CLR-###`, RAID Q-##). Carry all questions forward by their stable `SQ-###` IDs, update each feature's coverage map, and recompute the feature scores and the scope-readiness verdict (a resolved Blocker lifts the cap; note residual risk for accepted assumptions). Then write a **new review round** — a fresh timestamped `.html` and `.md`, with `round` incremented and `priorReview` set to the resolved reviewId — and return a summary of the movement.
>
> Responses file: `<path>`

## 3. Check the answers against the code — only if there is any

**No `.jetrix/code-map-registry.md`, or no repos mapped → skip this step entirely** and adjudicate exactly as
before. It adds a check when one is available; it is never a prerequisite for closing a round.

With mapped repos, read the graph through `tl-read-code-context` while adjudicating, **and
`.jetrix/connection-map.md` where it exists**. An answer about an existing system is checkable, and checking
it is cheap.

The two cover different ground: the graph says what one repo contains, the connection map says which apps
exist, how they talk, where auth sits and what is already integrated. An answer like *"it will sync with
payroll"* is settled by the map'"'"'s ## External integrations section, not by any single repo.

- **The answer matches the code** → `Resolved`, citing the unit. The strongest kind of close: a human said it
  and the system does it.
- **The answer contradicts the code** → **not** `Resolved`. Either it describes a change — record it as one,
  with the current state named — or someone is mistaken, which is `Needs-verification` with the conflict
  quoted. Never close a question on an answer the running system disagrees with; that is how a scope comes to
  describe a product nobody has.
- **The answer is about something unmapped** → adjudicate on the answer alone and say the code could not
  confirm it. Silence from the graph is not agreement.

**This never overrides the human.** The code is evidence of what is, not of what should be — a client is
entitled to change their system. The rule is only that a disagreement gets recorded rather than resolved away.

## 3a. Re-render the scope — it just changed

Every terminal answer edits `scope.md`. The published `scope.html` is now behind, **at the URL the client was
already sent** — so a round that resolves twelve questions leaves them reading the version that still asks
them.

**Republish without asking.** This is the flow, not a decision — the link is already out there and the only
question is whether it shows the current scope or last round’s. Stopping to ask leaves the client reading
something we know is stale, which is the worse of the two outcomes every time.

**An answer that is a BA draft rather than the client’s is not a reason to hold the publish.** It is a reason
to label it: the resolution loop already marks those `Accepted-assumption` and the scope carries *pending
client confirmation* beside each one. The client seeing our current thinking, labelled as an assumption, beats
them seeing a version that predates it.

Re-render and re-publish it exactly as `/ba:scope` §4 does, with the same flags, so the two renders cannot
drift:

```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/ba-extraction/assets/render-scope.js \
  .jetrix/requirements/<slug>/scope.md
```

Then the publish path from `/ba:scope` §4 — content-hash check first, `scope_finalize_report_push` with the
stored `attachment_id` so the link stays the same. **Replace in place, never upload a second file**: the
client bookmarked round 1 and must see round 2 at that address.

**Never call `scope_share_report` here.** It is first-publish only. Mission Control mints a new passcode on
every call and overwrites the old one, so re-sharing on a resolve round silently breaks the code the client
already has — and this command runs every round, which is exactly where that would bite. Replace keeps both
the attachment and its passcode; reprint the stored one from sync-state.

**Skip it when no scope edit landed.** A round where every answer was `Needs-verification` changes the
review, not the scope — re-rendering then produces an identical file and a pointless upload. The hash check
catches it either way, but not doing the work is better than undoing it.

## 4. Surface the result

When the agent returns, present the **round summary**: how many questions were Resolved / Accepted-as-assumption / Needs-verification (list the follow-ups the author still needs to answer) / still Open, the score and verdict movement (e.g. "3.4 → 6.2, Significant gaps → Estimate with caveats"), which scope edits were applied, and any `DEC`/`ASM`/`CLR` rows logged.

A round writes a **new timestamped report**. Link and serve it exactly as `/ba:review` §3 does — local only, never published. The round number belongs in the summary so nobody opens the wrong file.

**Reuse a server that is already up.** If one is serving `requirements/<slug>/reviews` from an earlier command in this session, the new round is already reachable — print its URL rather than starting a second one on another port, which only splits the user's attention across two tabs.

Close every round with this block. **The routing rule is `/ba:review` §3's, applied to the new counts** — a resolve round that still leaves a Blocker open routes to resolve again, not forward:

```
Round 2 — scope readiness 3.4 → 6.2   Significant gaps → Estimate with caveats
  Resolved <n> · Assumption <n> · Needs-verification <n> · Open <n>
  Logged: DEC-004, DEC-005, ASM-002, CLR-009

Review   http://127.0.0.1:<port>/scope-review-<ts>.html
         requirements/<slug>/reviews/scope-review-<ts>.html

Scope    <share url — unchanged, now showing this round's answers>
         requirements/<slug>/scope.html

Next:
  <one block, chosen by /ba:review §3's table against the NEW counts>
```

Three endings, and they are not interchangeable:

- **Follow-ups outstanding** (`Needs-verification`) → answer them in the new report, export, `/ba:resolve` again. Name the follow-ups; "some items need verification" tells the author nothing to act on.
- **No Blocker left** → `/ba:features`.
- **New material arrived instead of answers** → `/ba:scope add "…"`, then re-review. Resolve adjudicates answers to existing questions; it cannot absorb a new document.
