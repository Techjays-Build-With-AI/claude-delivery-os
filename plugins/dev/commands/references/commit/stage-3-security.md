## Stage 3 — Strict security review (commit-time gate)

**Purpose.** Re-run the Claude Code `security-review` skill on the feature diff, but at the STRICT commit-time threshold. `/dev:build`'s Stage 9 was Critical-only. Here we block on `Critical` AND `High`. Same skill, different threshold config.

**Runs after Stage 2 (base branch selected).** State: `IN_PROGRESS → REVIEW` (local); MC: `devReview`. On any Critical/High finding the fix loop kicks in — never push a branch with unresolved commit-time-severity security findings.

**On completion:** `units/<repo>/findings.md § ## Security — commit` written; zero Critical + zero High; the deferred build-time High findings from `/dev:build`'s Stage 9 are now addressed OR the fix loop will address them.

---

### 3a. Preconditions

- Stage 2 confirmed base branch (`develop` from `.jetrix/project.json` `env_branches.dev`, unless overridden)
- Branch is up to date locally with base (verified via `git fetch <remote>` + `git log HEAD..<remote>/<base>` = empty; if not, halt with "rebase against <base> and re-run")
- **`snapshot_sha` is recorded** in `status.md` § `## Run history` by Stage 0, and `git diff <base>..$SNAP` returns a non-empty file list. An empty scope here is `blocker: empty-scope` at Stage 0, never a clean pass here

---

### 3b. Skill invocation

**The scope is the review snapshot, not a branch diff.** `/dev:build` commits
nothing, so `<base>...HEAD` is empty on a freshly-built task and this stage would
review zero bytes while reporting a clean result. `$SNAP` is built at Stage 0 from
the working tree — see `references/common/review-snapshot.md`.

Invoke Claude Code's built-in `security-review` skill with:

- **Scope:** `git diff <base>..$SNAP` in the target repo — the review snapshot Stage 0 built. **Under `tests_only`** it is the same snapshot; the product-code review is skipped only where no product file appears in it (`commit.md` §2). The secrets scan always covers every file in the snapshot.
- **If the skill refuses to run** (it requires a git repository, and halts when the session's working directory is the folder above the repo): do not halt this stage. Follow `commit.md` → *When a required tool cannot run* — record the refusal verbatim, apply the criteria below by hand at the same threshold, and carry that into the PR body.
- **Severity threshold at commit-time:** `Critical + High` block; `Medium` warns; `Low + Info` logged only
- **Full focus areas (not the build-time subset):**
  - Injection (SQL, command, path, LDAP, XPath, NoSQL, prompt injection)
  - Auth / authz on every new + modified endpoint
  - Secret leaks in new code AND in `.env.example` / config files touched
  - Insecure deserialization
  - Input validation completeness (server-side, not just client)
  - CSRF / CORS on new endpoints
  - Rate-limiting on new endpoints (parent NFR-declared thresholds)
  - Sensitive-data logging (PII, tokens, credentials)
  - Newly-added dependency vulnerabilities (`pnpm audit`, `pip-audit`, `go list -m -u`, etc.)
  - Hardcoded credentials or tokens
  - Timing-attack surfaces in auth/comparison paths

Do NOT re-run against the whole repo. `/dev:commit` is diff-scoped.

If the `security-review` skill's invocation config supports a severity-threshold param, pass `min_severity=High`. If not, invoke at default and post-filter findings.

---

### 3c. Findings file

Write findings to `units/<repo>/findings.md § ## Security — commit`:

```yaml
---
doc_type: security-findings-commit
schema_version: 1.0
produced_by: security-review
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: 2026-08-31T15:35:00Z
diff_base: develop
snapshot_sha: <sha>              # the exact bytes these findings cite
severity_threshold: High
---

# Commit-time security findings

**Findings follow `references/common/findings-contract.md`**: a stable id derived
from repo + path + enclosing symbol (never a line number), a `disposition` on every
row, and `## Settled` carried in so a decision made last run is not re-raised.


## Blocking (Critical + High)

- SR-C-001 (High) — POST /supplier endpoint missing @UseGuards(AuthGuard). Endpoint accepts requests without auth token. src/routes/supplier.ts:42.
  Fix: add `@UseGuards(AuthGuard)` decorator matching other endpoints in the file.
  Failure scenario: attacker POSTs to /supplier without a token; DB gets an unowned row; tax_id uniqueness is bypassed for a different tenant.

## Warnings (Medium — surface in PR body, non-blocking)

- SR-W-001 (Medium) — `console.log` in service.ts:55 logs the full request body including PII (name, tax_id).
  Fix: use structured logger with redaction, or remove the log.

## Informational (Low / Info — logged only, not in PR)

- SR-I-001 (Low) — package.json added `axios@1.6.2`; latest with known CVE fix is `1.7.4`.
```

The findings file is the ONLY source of truth for what blocks vs warns. `/dev:commit` Stage 6 reads it directly.

---

### 3d. Deferred High-severity from `/dev:build`

Read `units/<repo>/findings.md § ## Security — build` (from `/dev:build` Stage 9, which is report-only). **Every** finding it recorded arrives here unrepaired — Critical and High now block, Medium and below must be dispositioned.

Cross-reference with commit-time findings:
- If a build-deferred High is STILL present in the commit-time findings → block on it (routed via Stage 6 fix loop).
- If a build-deferred High was fixed in dev iteration between `/dev:build` and `/dev:commit` → no longer appears in commit-time scan; log to `status.md` § `## Run history` as `build_deferred_high_resolved: [SR-B-001]`.

---

### 3e. Route to fix loop or advance

**Zero Critical + Zero High** → mark Stage 3 done. Log warnings for reviewer visibility. Advance to Stage 4.

**One or more Critical/High** → invoke the fix loop per `stage-6-fix-loop.md` §6a.i (v2.3.27). The fix loop is **MANDATORY and VERIFIABLE** — this stage MUST invoke `dev-stack-adaptive-implementation` in fix-mode via the Skill / Agent tool and record a `stage-3.fix_loop_invocation:` block in `status.md` § `## Run history` with `invoked_at`, `subagent_id`, `origin_findings`, `fix_attempts[]`, `broad_reruns_used`, `exit_state`. Applying the fix inline "because it's a small change" without recording the invocation trace is a spec violation and Stage 8 §8a will refuse to push. After fix loop, Stage 3 re-runs from the top (order matters — a security fix may break a test).

---

### 3f. Skips

- `--no-security-review` flag is NOT accepted at commit-time. Rejected with: "Security review at commit-time is mandatory. Use /dev:commit --skip-security only with `SECURITY_REVIEW_OVERRIDE` env var + a documented reason (audit)."
- If the override is used, the reason is recorded in `status.md` § `## Run history` `stage-3.override_reason:` and surfaced in the PR body under "⚠ Security review overridden".

Overriding requires operator-level intent — not a normal dev-loop escape hatch.

---

### 3g. Progress log

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-3:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  snapshot_sha: 0f50921291d9
  scope: "snapshot vs develop (18 files, +624/-12)"
  severity_threshold: High
  findings:
    critical: 0
    high: 0
    medium: 1
    low: 1
    info: 0
  fix_loop_invocation:                  # REQUIRED when the pre-loop blocking count was > 0
    invoked_at: <ISO>                   # absent + blocking findings => Stage 8 halts
    invocation: <subagent id | "inline">
    origin_findings: [SEC-authn.missing-4f2a91c8]
    fix_attempts: [{finding: SEC-authn.missing-4f2a91c8, attempts_used: 1, resolved: true}]
    broad_reruns_used: 0
    exit_state: CLEAN                   # CLEAN | ESCALATED
  build_deferred_high_resolved: [SEC-authn.missing-4f2a91c8]
  findings_file: units/<repo>/findings.md § ## Security — commit
```

---

### 3h. Skills / agents invoked

- `security-review` — Claude Code built-in skill
- No subagents in the fix loop for this stage; the fix loop delegates to `dev-stack-adaptive-implementation` in fix-mode

---

### 3i. On `--resume`

If `--resume` finds `stage-3.status: DONE`, **recompute the review snapshot and compare its sha** with the recorded `stage-3.snapshot_sha`. Same sha → the tree has not moved, skip. Different → re-run Stage 3 from the top.

**Do not key this off commit history.** `git log --since=<finished_at> HEAD` was the old test and it sees nothing: the fix loop writes to the working tree, and nothing is committed until Stage 7.5. A resume would skip a stage whose input had changed under it.
