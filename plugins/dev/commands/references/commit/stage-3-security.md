## Stage 3 — Strict security review (commit-time gate)

**Purpose.** Re-run the Claude Code `security-review` skill on the feature diff, but at the STRICT commit-time threshold. `/dev:build`'s Stage 9 was Critical-only. Here we block on `Critical` AND `High`. Same skill, different threshold config.

**Runs after Stage 2 (base branch selected).** State: `IN_PROGRESS → REVIEW` (local); MC: `devReview`. On any Critical/High finding the fix loop kicks in — never push a branch with unresolved commit-time-severity security findings.

**On completion:** `dev/security-findings-commit.md` written; zero Critical + zero High; the deferred build-time High findings from `/dev:build`'s Stage 9 are now addressed OR the fix loop will address them.

---

### 3a. Preconditions

- Stage 2 confirmed base branch (`develop` from `.jetrix/project.json` `env_branches.dev`, unless overridden)
- Branch is up to date locally with base (verified via `git fetch <remote>` + `git log HEAD..<remote>/<base>` = empty; if not, halt with "rebase against <base> and re-run")
- Feature diff is deterministic: `git diff <base>...HEAD` returns the expected file list from `build-run.md` Stage 10's `context_units_updated:` + source-file commits

---

### 3b. Skill invocation

Invoke Claude Code's built-in `security-review` skill with:

- **Scope:** `git diff <base>...HEAD` in the target repo
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

Write findings to `dev/security-findings-commit.md`:

```yaml
---
doc_type: security-findings-commit
schema_version: 1.0
produced_by: security-review
feature_id: FEAT-SUP-001
subtask_number: 1
generated_at: 2026-08-31T15:35:00Z
diff_base: develop
diff_head: <sha>
severity_threshold: High
---

# Commit-time security findings

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

Read `dev/security-findings-build.md` (from `/dev:build` Stage 9). Any `Severity: High` items in there were deferred at build time (Critical-only gate). At commit time they now block.

Cross-reference with commit-time findings:
- If a build-deferred High is STILL present in the commit-time findings → block on it (routed via Stage 6 fix loop).
- If a build-deferred High was fixed in dev iteration between `/dev:build` and `/dev:commit` → no longer appears in commit-time scan; log to `commit-run.md` as `build_deferred_high_resolved: [SR-B-001]`.

---

### 3e. Route to fix loop or advance

**Zero Critical + Zero High** → mark Stage 3 done. Log warnings for reviewer visibility. Advance to Stage 4.

**One or more Critical/High** → jump to `stage-6-fix-loop.md`. After fix loop, Stage 3 re-runs from the top (order matters — a security fix may break a test).

---

### 3f. Skips

- `--no-security-review` flag is NOT accepted at commit-time. Rejected with: "Security review at commit-time is mandatory. Use /dev:commit --skip-security only with `SECURITY_REVIEW_OVERRIDE` env var + a documented reason (audit)."
- If the override is used, the reason is recorded in `commit-run.md` `stage-3.override_reason:` and surfaced in the PR body under "⚠ Security review overridden".

Overriding requires operator-level intent — not a normal dev-loop escape hatch.

---

### 3g. Progress log

Append to `dev/commit-run.md`:

```yaml
stage-3:
  status: DONE
  started_at: <ISO>
  finished_at: <ISO>
  scope: "git diff develop...HEAD (18 files, +624/-12)"
  severity_threshold: High
  findings:
    critical: 0
    high: 0
    medium: 1
    low: 1
    info: 0
  build_deferred_high_resolved: [SR-B-001, SR-B-002]
  findings_file: dev/security-findings-commit.md
```

---

### 3h. Skills / agents invoked

- `security-review` — Claude Code built-in skill
- No subagents in the fix loop for this stage; the fix loop delegates to `dev-stack-adaptive-implementation` in fix-mode

---

### 3i. On `--resume`

If `--resume` finds `stage-3.status: DONE`, skip re-running unless the branch has new commits since Stage 3's `finished_at` (compare via `git log --since=<finished_at> HEAD`). If new commits exist, re-run Stage 3 from the top — the fix loop guarantees this.
