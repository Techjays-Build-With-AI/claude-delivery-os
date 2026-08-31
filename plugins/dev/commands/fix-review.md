---
description: Fold human reviewer feedback on an open PR back through the /dev:commit loop — re-run the affected commit stages (Stages 3–5 code fixes + Stage 7 semantic-context-merge if code-context units touched), refresh dev/pr-summary.md, keep local state REVIEW / MC status devReview. Escalates comments requiring product / architecture / security decisions instead of guessing. Never merges or deploys.
argument-hint: "<Task-N | Feature-N | Subtask-N | slug | features/<slug> | features/<slug>/subtask/<repo> | FEAT-<AREA>-NN> [feedback=<path-to-review-comments> | pr=<link>]"
---

# /dev:fix-review

You respond to **reviewer feedback** on a task already at local `REVIEW` (MC `devReview`) — the PR is open and the human left comments. You NEVER merge or deploy.

## 1. Parse arguments

`$ARGUMENTS` must contain:

- A **task target** (same 4-way resolution as `/dev:plan` Stage 0 / `/dev:build` Stage 0 / `/dev:commit` Stage 0)
- The **reviewer feedback** source — one of:
  - `feedback=<path>` — a local file with the reviewer comments (markdown, plain text, or exported from GitHub)
  - `pr=<link>` — a GitHub PR URL; use `gh pr view <n> --json comments,reviews` to fetch
  - Inline — a list of comments in the argument text itself

If target present but feedback source missing → ask where the review comments are and stop.

## 2. Verify state

Read `status.md`:
- `current_state: REVIEW` — expected
- MC status: `devReview` — expected
- `pr_url:` non-empty in `dev/commit-run.md`

If state is anything other than `REVIEW`, halt with the actual state and route to the appropriate command (`/dev:build` if `PLANNED`; `/dev:commit` if `IN_PROGRESS`).

## 3. Categorize each comment

For each comment in the feedback:

- **Actionable code fix** — clear defect, missing test, style deviation from repo conventions, security concern. Route to Stage 6 fix-loop mechanics (see `plugins/dev/commands/references/commit/stage-6-fix-loop.md`) — invoke `dev-stack-adaptive-implementation` in fix-mode, capped at 3 focused attempts per comment.
- **Product / architecture / security decision needed** — comment asks "should we do X instead" where X is a design change beyond scope. Do NOT guess. Write `dev/escalation-<n>.md` with the comment + decision needed + recommended options + rationale. Local state `REVIEW → BLOCKED`; MC status `devReview → blocked`. Halt for that comment; siblings continue.
- **Clarification** — comment asks a question about the code. Answer inline via `gh pr comment` (if available) OR record the answer in `dev/pr-comment-replies.md` for the developer to post. No code change.
- **Nit / opinion** — non-blocking suggestion. Note in `dev/pr-comment-replies.md`; can defer to a follow-up PR.

## 4. Re-run affected commit stages

After all actionable code fixes are applied for THIS round:

1. **Re-run Stage 3 (security review)** — `plugins/dev/commands/references/commit/stage-3-security.md`. Any new Critical/High from the fixes → Stage 6 fix-loop within THIS command.
2. **Re-run Stage 4 (code review)** — `plugins/dev/commands/references/commit/stage-4-code-review.md`. Any new Blocker/Major → Stage 6 fix-loop.
3. **Re-run Stage 5 (acceptance re-verify)** — `plugins/dev/commands/references/commit/stage-5-acceptance.md`. Regression → Stage 6 fix-loop.
4. **If any code-context units were touched** by fixes (rare — reviewers usually don't request context-graph changes, but possible for endpoint contract adjustments) → re-run Stage 7 (semantic-context-merge) — `plugins/dev/commands/references/commit/stage-7-semantic-merge.md`. If clean, otherwise halt with `dev/context-merge-conflicts.md`.
5. **Skip Stage 8 (push)** if there are no new commits from this round. Otherwise `git push origin <branch>` — the existing PR picks up the new commits automatically.

Bounds: same as `/dev:commit` — 3 focused fix attempts per comment, 2 broad re-runs per stage. Exceed → escalate.

## 5. Refresh `dev/pr-summary.md`

Delegate to `dev-pr-handoff` skill (v2.2 slimmed — content compose only). Regenerate `dev/pr-summary.md` with:

- Purpose (unchanged)
- Scope of changes (updated file count, +X/-Y)
- New section: **Review round N — comments addressed** — one row per comment: comment text, disposition (fixed / clarified / escalated / deferred-as-followup), commit SHA if code changed
- Updated security + code review outcome tables (from re-runs above)
- Updated acceptance table
- Updated follow-up suggestions (add any Minor from re-runs)

Update the PR body via `gh pr edit <pr-number> --body-file dev/pr-summary.md`.

## 6. Progress log

Append to `dev/commit-run.md`:

```yaml
fix-review-round-<n>:
  status: DONE | HALTED | ESCALATED
  started_at: <ISO>
  finished_at: <ISO>
  feedback_source: pr=https://github.com/acme/acme-backend/pull/247
  comments_processed: 7
  comments:
    - id: RC-01
      text: "Missing test for edge case X"
      disposition: fixed
      commit_sha: <sha>
    - id: RC-02
      text: "Should we use pattern Y instead"
      disposition: escalated
      escalation_file: dev/escalation-2.md
    - id: RC-03
      text: "Nit: rename var"
      disposition: deferred_followup
  stages_rerun: [stage-3, stage-4, stage-5]
  new_commits_pushed: 2
  pr_body_updated: true
```

## 7. Surface the result

Print in-terminal:

```
✓ /dev:fix-review FEAT-SUP-001-1 round 2 complete

Comments processed: 7
  · Fixed:      4  (commits <sha1>, <sha2>)
  · Clarified:  2  (replies drafted in dev/pr-comment-replies.md)
  · Escalated:  1  (see dev/escalation-2.md — decision needed)
  · Deferred:   1  (Nit — follow-up PR)

Re-run: Stage 3 (security) ✓ · Stage 4 (code review) ✓ · Stage 5 (acceptance) ✓
Pushed: 2 new commits
PR body: refreshed via gh pr edit

Local state: REVIEW  (unchanged)
MC status:   devReview  (unchanged)

Next:
  1. Post the 2 clarification replies from dev/pr-comment-replies.md to the PR
  2. Resolve the 1 escalation (see dev/escalation-2.md)
  3. Reviewer re-reviews PR
```

If ANY comment escalated:
- Local state: `REVIEW → BLOCKED`
- MC status: `devReview → blocked`
- Lead the terminal output with the escalation

## 8. Guardrails

- Never mark comments "resolved on GitHub" from this command — reviewer does that
- Never merge the PR (that's the reviewer's job)
- Never rebase automatically — if the PR is behind base, halt with rebase instructions
- Never `--no-verify` on push
- Never expand scope while addressing a comment — a scope-expanding fix escalates
- Every meaningful design fix → `DEC-###` in `dev/decisions.md`
