## Stages 8 + 9 — Push branch + Raise PR

Two closely-coupled stages. Combined in one reference file because their state transitions and failure surfaces overlap.

**Runs after Stage 7 (semantic merge clean).** State: `REVIEW` (unchanged); MC: `devReview` (unchanged). On successful push + PR raise, no further state changes.

**On completion:** feature branch is on origin; PR is open; PR body is `dev/pr-summary.md`; MC status is still `devReview` (waiting on human review).

---

## Stage 8 — Push the branch

### 8a. Preconditions

- Stage 7 committed the semantic-merge changes locally
- Branch has no uncommitted changes (`git status --porcelain` empty)
- `.jetrix/project.json` has the target repo's remote name (default `origin`)

### 8b. Push

```
git push --set-upstream origin <branch-name>
```

For subsequent pushes on the same branch (re-pushing after fix loop iteration on `--resume`):

```
git push origin <branch-name>
```

Never `git push --force`, never `git push --force-with-lease` unless the developer passed `--force-push` explicitly. Feature branches usually don't need force-push. If push is rejected due to non-fast-forward (someone pushed directly to this branch), halt with:

```
✗ Push rejected — branch has been updated on remote.

git pull --rebase origin <branch-name>

Then re-run: /dev:commit --resume
```

### 8c. Push failures

Categorize:

- **Branch protection** (protected pattern) — halt with the protection rule cited; developer resolves via GitHub settings or a different base
- **RBAC / permission denied** — halt with "requires push access to <repo>"; developer resolves via GitHub org perms
- **Network / transient** — retry once; if still failing, halt with the raw error
- **Pre-push hook rejected** — surface the hook output; halt (fix underlying issue; never `--no-verify`)

Never retry silently more than once for network. Never skip hooks.

### 8d. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-8:
  status: DONE | HALTED
  started_at: <ISO>
  finished_at: <ISO>
  branch: feature/FEAT-SUP-001-supplier-onboarding-backend
  remote: origin
  commits_pushed: 9
  push_result: success | rejected | network_error
  error_message: null | "<verbatim git error>"
```

---

## Stage 9 — Raise the PR

### 9a. Preconditions

- Stage 8 pushed successfully
- `dev/pr-summary.md` exists (composed at the end of Stage 5 + augmented after Stages 6 + 7 with follow-up items + merge results)
- `gh` CLI is available; `gh auth status` clean

### 9b. Compose `dev/pr-summary.md`

This is the PR-reviewer-facing doc. NOT the developer's local runbook (`local-runbook.md`).

Structure:

```markdown
# <PR title>

## Purpose

<1-2 lines from parent's feature.md Objective, plus this sub-task's role in the parent.>

## Scope of changes

- Files: N total (+X / -Y)
- New endpoints: [POST /supplier, POST /supplier/duplicate-check]
- New entities: [supplier]
- New pages: (none — this is a backend sub-task)

## Technical approach

<3-4 sentences on the shape of the implementation. Framework-agnostic where possible; specific enough that the reviewer can navigate. Example: "Endpoint accepts a Supplier DTO, hits the ComplianceService for duplicate detection, writes via SupplierRepository, and returns 201 with the persisted entity. Duplicate rejection is enforced at both the service layer (pre-write findOneBy check) and DB layer (unique constraint on tax_id + country).">

## Test coverage summary

- Unit: 14 written, 14 passing
- Integration: 11 written, 11 passing
- E2E: 3 skeleton (deferred; last sub-task lands them)
- Coverage: 72.4% lines (≥60% required)

## Acceptance criteria

| AC | Description | Verified by | Result |
|----|-------------|-------------|--------|
| AC-1 | Tax_id validation | supplier.spec.ts::validates_tax_id | ✅ |
| AC-2 | Duplicate rejection returns 409 with DUPLICATE_TAX_ID | supplier.spec.ts::rejects_duplicate | ✅ |
| ... | | | |

## Business rules

| BR | Description | Enforcement | Result |
|----|-------------|-------------|--------|
| BR-3 | tax_id unique per country | DB unique constraint + service pre-write check | ✅ |
| ... | | | |

## Security review outcome (commit-time strict gate)

- Critical: 0
- High: 0 (2 build-deferred Highs fixed in commit iteration)
- Medium: 1 warning: PII in log output — needs redacted logger config (follow-up)
- Low: 1 informational

## Code review outcome

- Blocker: 0
- Major: 0
- Minor: 3 (surfaced below as follow-up suggestions)
- Nit: 2

## Follow-up suggestions (Minor — non-blocking, PR-time visibility only)

- CR-M-001 — extract `getSupplierWithDuplicates` into `getSupplier` + `withDuplicateChecks`. See src/supplier/service.ts:180.
- CR-M-002 — magic number 30 in retry backoff. Consider constant `DUPLICATE_CHECK_TIMEOUT_MS`. See src/supplier/service.ts:220.
- ...

## Semantic context merge

- 3 units merged clean (EP-SUP-01, EP-SUP-02, ENT-SUP-01)
- 4 baseline rows preserved (EP-ORD-14, EP-INV-03, ENT-ORD-01, ENT-INV-01)
- 0 conflicts

## Cross-sub-task E2E ownership

- TS-4 (3-tab onboarding flow) — E2E test owned by the last-landing sub-task in the split; this PR's §1 references the E2E test file location; other sub-tasks' PR summaries reference it via §6 Touch points Cross-sub-task row.

## Reviewer instructions

- Focus areas: the pre-write duplicate check (contested — see CR-B-002 discussion in dev/decisions.md)
- Not this PR's concern: rate-limiting (parent NFR doesn't require; can add later)
```

Every section is auto-populated from the actual commit-run's data. Never placeholders.

### 9c. Raise the PR

```
gh pr create \
  --base <resolved-base-branch> \
  --head <feature-branch> \
  --title "<computed title>" \
  --body-file dev/pr-summary.md
```

PR title format:

- Parent-alone: `<feature title>` (from parent's `feature.md`)
- Sub-task: `<parent title> — <repo>` (e.g. `Supplier Onboarding — backend`)

If `gh pr create` reports the PR already exists (re-run on `--resume`), fetch its URL via `gh pr view --json url --jq .url` and update its body instead:

```
gh pr edit <pr-number> --body-file dev/pr-summary.md
```

### 9d. PR-raise failures

- **Existing PR from same branch → same base** — update body (see 9c above)
- **RBAC / permission denied** — halt with "requires PR-create access to <repo>"
- **Wrong base branch (branch is behind base)** — halt with rebase instructions
- **`gh` not authenticated** — halt with `gh auth login` instructions

### 9e. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-9:
  status: DONE | HALTED
  started_at: <ISO>
  finished_at: <ISO>
  pr_number: 247
  pr_url: https://github.com/acme/acme-backend/pull/247
  pr_title: "Supplier Onboarding — backend"
  pr_body_file: dev/pr-summary.md
  action: created | updated
```

### 9f. On `--resume`

If `stage-9.status: DONE`, print the summary from the log; don't re-raise.

If `stage-9.status: HALTED` due to a transient issue, retry after human addressed it.

### 9g. Skills / agents invoked

- `gh` CLI directly
- No skill invocation (PR composition is data assembly, not stack-adaptive)
- `dev-pr-handoff` skill is INVOKED if v2.2 keeps it (see slim-down todo in the plan) — this file assumes the slim version. If `dev-pr-handoff` is still full-fat, its state/tracker code must be bypassed at commit-time.

### 9h. Never

- Never mark MC status `done` here — that's the PR-merge webhook's job (out of scope for v2.2; noted for v2.3)
- Never modify `local-runbook.md` here (that's `/dev:build` Stage 11's file)
- Never include "how to run locally" in the PR body (that's `local-runbook.md`)
- Never inline test-run outputs in the PR body — link to CI runs if the CI exposes them
- Never `--force-push` unless the developer explicitly asked
- Never `--no-verify` on push
