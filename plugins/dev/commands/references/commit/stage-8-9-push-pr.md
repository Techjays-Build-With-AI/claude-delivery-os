## Stages 8 + 9 — Push branch + Raise PR

Two closely-coupled stages. Combined in one reference file because their state transitions and failure surfaces overlap.

**Runs after Stage 7 (semantic merge clean).** State: `REVIEW` (unchanged); MC: `devReview` (unchanged). On successful push + PR raise, no further state changes.

**On completion:** feature branch is on origin; PR is open; PR body is `dev/pr-summary.md`; MC status is still `devReview` (waiting on human review).

---

## Stage 8 — Push the branch

### 8a. Preconditions (v2.3.25 — HARD gates that refuse push if any is missing)

- **Stage 2 base-branch confirmed by user** — check `commit-run.md` `stage-2.base_confirmed_by_user: true`; missing → HALT with `blocker: stage-2-base-not-confirmed` (user must re-run so the branch prompt fires)
- **Stage 2 base pulled locally** — check `commit-run.md` `stage-2.base_pulled_at` timestamp exists; missing → HALT with `blocker: base-branch-not-pulled` (Stage 7 can't merge against a base that isn't on disk)
- **Stage 7 semantic-merge INVOKED** — check `commit-run.md` `stage-7.tl_semantic_context_merge_invocation.invoked_at` is set with a real subagent_id; MISSING or NULL → HALT with `blocker: stage-7-not-executed` (this is the user-reported gap: agent skipped Stage 7 by "reasoning it was a no-op"; the skill invocation is the ONLY evidence of execution)
- **Stage 7 merged base matches Stage 2 base** — check `stage-7.tl_semantic_context_merge_invocation.base_ref` sha matches `stage-2.base_remote_sha`; mismatch → HALT with `blocker: stage-7-merged-against-wrong-base` (means Stage 7 pulled its own base separately from Stage 2's; not allowed)
- **Stage 7.5 commits landed** — check `stage-7-5.commits_made` list is non-empty (or `stage-7-5.status: SKIPPED` with reason `working tree has no source/test/context uncommitted changes`)
- **Working tree clean** — `git status --porcelain` shows only allowed `dev-local` / `workspace-local` files (see Stage 7.5 §7.5b categorization)
- **`.jetrix/project.json`** has the target repo's remote name (default `origin`)

Any halt at 8a means the developer needs to re-run `/dev:commit --resume <task-ref>` — the missing stage will re-run from where the trace shows the gap.

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
- A working PR-creation mechanism per §9c's ladder (v2.3.22 — no longer requires `gh`)

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

### 9c. Raise the PR — 4-step fallback ladder (v2.3.22)

PR title format (used by all three ladder steps):

- Parent-alone: `<feature title>` (from parent's `feature.md`)
- Sub-task: `<parent title> — <repo>` (e.g. `Supplier Onboarding — backend`)

Resolve `<owner>/<repo>` from the target repo's `origin` remote:

```bash
ORIGIN=$(git -C <target-repo> config --get remote.origin.url)
# Extract owner/repo from git@github.com:<owner>/<repo>.git OR https://github.com/<owner>/<repo>.git
OWNER_REPO=$(echo "$ORIGIN" | sed -E 's#(git@github.com:|https://github.com/)([^/]+/[^/.]+)(\.git)?#\2#')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

**Try each step in order. On success, log which step ran to `dev/commit-run.md` and proceed.**

**Step 1 — `gh` CLI (if installed + authed):**

```bash
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh pr create \
    --base <resolved-base-branch> \
    --head <feature-branch> \
    --title "<computed title>" \
    --body-file dev/pr-summary.md
  # Log: pr_method: gh_cli
fi
```

**Step 2 — Extract token from git credential store (works because you already authenticated for `git push`):**

Windows Git Credential Manager, macOS Keychain, and Linux libsecret all cache the HTTPS token you used when you first pushed. If the remote is HTTPS AND the cached credential is a PAT with `repo` scope (GCM's default), we can piggyback:

```bash
if [ -z "$PR_METHOD" ]; then
  CREDS=$(echo -e "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null)
  TOKEN=$(echo "$CREDS" | grep '^password=' | cut -d= -f2)
  if [ -n "$TOKEN" ]; then
    BODY=$(jq -Rs . < dev/pr-summary.md)
    RESPONSE=$(curl -s -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/$OWNER/$REPO/pulls" \
      -d "{\"title\":\"<computed title>\",\"body\":$BODY,\"head\":\"<feature-branch>\",\"base\":\"<resolved-base-branch>\"}")
    PR_URL=$(echo "$RESPONSE" | jq -r '.html_url // empty')
    if [ -n "$PR_URL" ]; then
      # Log: pr_method: git_credential_fill
      echo "PR opened: $PR_URL"
    fi
  fi
fi
```

**Step 3 — Read token from `gh` config file (if `gh` was authed even though `gh` binary is missing):**

Sometimes `gh` was installed on a previous machine or the binary was removed but the config remains. `~/.config/gh/hosts.yml` (`%APPDATA%\GitHub CLI\hosts.yml` on Windows) contains the OAuth token from `gh auth login`. Extract and use it:

```bash
if [ -z "$PR_METHOD" ]; then
  GH_HOSTS="${XDG_CONFIG_HOME:-$HOME/.config}/gh/hosts.yml"
  [ ! -f "$GH_HOSTS" ] && [ -f "$APPDATA/GitHub CLI/hosts.yml" ] && GH_HOSTS="$APPDATA/GitHub CLI/hosts.yml"
  if [ -f "$GH_HOSTS" ]; then
    TOKEN=$(grep -A5 'github.com:' "$GH_HOSTS" | grep 'oauth_token:' | head -1 | awk '{print $2}')
    if [ -n "$TOKEN" ]; then
      # Same curl call as Step 2
      # Log: pr_method: gh_config_read
    fi
  fi
fi
```

**Step 4 — Web UI URL fallback (nothing available; user completes in browser):**

```bash
if [ -z "$PR_METHOD" ]; then
  TITLE_ENC=$(printf '%s' "<computed title>" | jq -sRr @uri)
  BODY_ENC=$(cat dev/pr-summary.md | jq -sRr @uri)
  COMPARE_URL="https://github.com/$OWNER/$REPO/compare/<base>...<head>?expand=1&title=$TITLE_ENC&body=$BODY_ENC"
  echo "PR-creation auth not available. Open this URL in your browser — the form will be pre-filled with title + body:"
  echo ""
  echo "  $COMPARE_URL"
  echo ""
  echo "After you click Create pull request, paste the PR URL back if you want /dev:commit --resume to record it."
  # Log: pr_method: web_url_fallback + compare_url in commit-run.md
  # State: /dev:commit exits successfully; user manually completes the PR in browser
fi
```

**"PR already exists" handling** — if Step 1 or Steps 2/3 return a "PR already exists" error (`422 Unprocessable Entity` with `A pull request already exists for <head>`):

```bash
# Step 1: gh pr edit <pr-number> --body-file dev/pr-summary.md
# Steps 2/3 curl: PATCH /repos/$OWNER/$REPO/pulls/<pr-number> with body update
```

Fetch existing PR: `GET /repos/$OWNER/$REPO/pulls?head=$OWNER:<feature-branch>&base=<base>&state=open` → take `.[0].number` → PATCH its body.

### 9c.i. Optional: install `gh` on demand (prompt-gated, v2.3.22)

If Steps 1–3 all fail AND the machine has no cached HTTPS token at all (only SSH auth for git), OFFER — do NOT silently install — to install `gh`:

```
Nothing to auth PR creation against (no gh, no cached HTTPS token, no gh config).
Install gh via <detected package manager>? [y]es / [n]o (fall back to web URL)

Detected package managers on this machine:
  · scoop (available)
  · winget (available)

If you say yes, I'll run:
  scoop install gh
  gh auth login   (opens browser for device code — you enter it once)
Then re-attempt PR create in this run.
```

Use `AskUserQuestion` for the yes/no. On `y`: run the install, run `gh auth login` (user provides device code), retry Step 1. On `n`: proceed to Step 4 (web URL).

**Never install without explicit user confirmation.** This is a persistent system change.

### 9d. PR-raise failures per ladder step

| Failure | Step | Behavior |
|---|---|---|
| `gh` missing | Step 1 | Continue to Step 2 (no error surfaced) |
| `gh auth status` fails | Step 1 | Continue to Step 2 |
| `git credential fill` returns no password | Step 2 | Continue to Step 3 |
| Token from credential fill lacks `repo` scope (401 from API) | Step 2 | Continue to Step 3 |
| `gh` config file missing | Step 3 | Continue to Step 4 |
| Web URL computed | Step 4 | Success (manual completion) |
| API returns `422` "PR already exists" | Any step | Fetch existing PR + update body via PATCH; do NOT create new |
| API returns `403 RBAC forbidden` | Any step | HALT with "requires PR-create access to <owner>/<repo>" — token lacks permission |
| API returns `422 head branch not found` | Any step | HALT — Step 8 push didn't land or was force-cleaned. User verifies branch on remote. |
| Network error | Any step | HALT with the error; user re-runs `/dev:commit --resume` when connectivity returns |

### 9e. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-9:
  status: DONE | HALTED | PENDING_USER_BROWSER
  started_at: <ISO>
  finished_at: <ISO>
  pr_method: gh_cli | git_credential_fill | gh_config_read | gh_installed_on_demand | web_url_fallback
  pr_number: 247                                       # empty when pr_method == web_url_fallback
  pr_url: https://github.com/acme/acme-backend/pull/247   # empty when pr_method == web_url_fallback (compare_url instead)
  compare_url: https://github.com/.../compare/...      # only when pr_method == web_url_fallback
  pr_title: "Supplier Onboarding — backend"
  pr_body_file: dev/pr-summary.md
  action: created | updated | pending_user_completion
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
