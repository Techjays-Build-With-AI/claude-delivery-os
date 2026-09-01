## Stage 9 — Security review (feature-diff scoped, build-time threshold)

**Purpose.** Scan the feature diff for security vulnerabilities. Build-time threshold: block on `Critical` only. High findings become warnings (they're re-checked at `/dev:commit` Stage 3 with strict blocking).

**Runs after Stage 8 acceptance-map is COMPLETE.** State: `TESTING` (unchanged). MC: `inProgress`.

**On completion:** any Critical findings resolved; Highs / Mediums / Lows recorded for `/dev:commit`'s stricter pass.

---

### 9a. Preconditions

- `dev/build-run.md` `stage-8.status: DONE` and `final_status: COMPLETE` (or `PARTIAL_DEFERRED` — deferred rows don't block security review)
- Branch has commits — `git log <base>..HEAD` returns at least one commit

If either fails → halt.

---

### 9b. Skip if `--no-security-review` flag

`/dev:build --no-security-review` skips this stage entirely. Only for prototyping / spike branches — the user takes responsibility.

`/dev:commit` will ALWAYS re-run security review at strict threshold; this flag only affects build-time. Log to `build-run.md`:

```yaml
stage-9:
  status: SKIPPED
  reason: --no-security-review flag; user opted out at build-time
```

---

### 9c. Invoke Claude Code's `security-review` skill

Invoke via the `Skill` tool with the `security-review` skill name (built-in to Claude Code — not a delivery-os plugin skill).

**Config passed:**

```
{
  "scope": "diff",
  "diff_range": "<base>...<HEAD>",         # <base> from project.json env_branches.dev
  "severity_block": ["Critical"],           # build-time threshold
  "severity_warn":  ["High"],
  "severity_note":  ["Medium", "Low"],
  "focus_areas": [
    "injection",                             # SQL, command, path traversal
    "authn_authz_new_endpoints",             # only on endpoints this feature added/modified
    "secret_leaks_new_code",                 # env vars, keys, tokens in new files
    "insecure_deserialization",
    "input_validation"                       # basic; commit-time is thorough
  ]
}
```

**Skill runs autonomously.** No further prompting.

---

### 9d. Parse findings

Skill returns a structured findings list per the `ReportFindings` tool shape:

```json
{
  "findings": [
    {
      "severity": "Critical",
      "category": "injection.sql",
      "file": "src/supplier/repo.ts",
      "line": 42,
      "summary": "Concatenated SQL from user input",
      "failure_scenario": "Attacker passes tax_id = \"' OR 1=1--\" → returns all suppliers",
      "verdict": "CONFIRMED"
    },
    {
      "severity": "High",
      "category": "authn.missing",
      "file": "src/supplier/controller.ts",
      "line": 18,
      "summary": "POST /supplier missing @UseGuards(AuthGuard)",
      "failure_scenario": "Any unauthenticated request can create a supplier"
    }
  ]
}
```

---

### 9e. Threshold application

Filter findings by severity:

| Severity | Action at build-time |
|---|---|
| Critical | Blocking → jump to §9g repair loop |
| High | Warning → record for `/dev:commit` Stage 3 to re-check; do NOT block |
| Medium | Note → record for `/dev:commit` |
| Low / Info | Log only |

If any Critical findings → §9g. Else record all findings to `dev/security-findings-build.md` and proceed to Stage 10.

---

### 9f. Record findings

Write `dev/security-findings-build.md`:

```yaml
---
doc_type: security-findings
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>
subtask_repo: <repo-slug>
scan_run_at: <ISO>
threshold: Critical-blocking-only         # build-time
build_run_id: <build-run-timestamp>
---

# Security review — build-time (Critical blocking only)

## Blocking findings (Critical) — 0 (must be zero to pass Stage 9)

*(none — all Critical findings must be resolved or Stage 9 halts)*

## Warnings (High) — 2 (will be re-checked at /dev:commit Stage 3 with High blocking)

### SR-B-001 · authn.missing · src/supplier/controller.ts:18

POST /supplier missing @UseGuards(AuthGuard)

**Failure scenario:** Any unauthenticated request can create a supplier

**Deferred to commit-time.** `/dev:commit` will block on this if not fixed before then.

## Notes (Medium / Low) — 3

- SR-B-002 · dependency.vuln · package.json — Yeah axios pinned to 1.x, latest is 1.12 (not currently exploitable)
- SR-B-003 · logging.oversharing · src/supplier/service.ts:71 — Full request body logged including tax_id (PII)
- SR-B-004 · input_validation.weak · src/supplier/dto.ts:5 — length check on name but no max
```

---

### 9g. Repair loop for Critical findings

Per `/dev:build` §14 limits (3 focused / 1 broad for security):

**Focused repair:**

1. For the Critical finding, identify: file, line, category, suggested fix (from `security-review` output)
2. Delegate to `dev-stack-adaptive-implementation` in "security-fix mode"
3. Skill applies the fix
4. Re-run `security-review` on the SAME diff — verify the specific finding is gone
5. If Critical still present → next attempt

**Broad cycle:** re-run the WHOLE security review after 3 focused attempts didn't clear one finding. Only ONE broad cycle allowed at build-time.

**Limits exceeded:**
- Write `dev/escalation-<n>.md` — sensitive-data / vulnerability / permissions escalations are per Delivery-OS never-guess policy
- Local state: `TESTING → BLOCKED`
- MC status: `blocked`
- Halt.

---

### 9h. Progress log format

Append to `dev/build-run.md`:

```yaml
stage-9:
  status: DONE                                    # DONE | SKIPPED | BLOCKED
  started_at: 2026-08-31T15:18:57Z
  scope: diff (develop...HEAD, 8 files)
  threshold: Critical-blocking
  findings:
    critical: 0                                    # became 0 after repair
    high:     2
    medium:   1
    low:      1
  repair_attempts: 1
  findings_file: dev/security-findings-build.md
  finished_at: 2026-08-31T15:21:44Z
```

---

### 9i. On `--resume`

If `--resume` finds `stage-9.status: DONE`, skip.

If `stage-9.status: BLOCKED`, re-run — the developer might have fixed the Critical by hand.

---

### Skills / agents invoked

- **Claude Code built-in `security-review` skill** — the primary work
- **`dev-stack-adaptive-implementation` skill** in security-fix mode — only during §9g repair

Never invoke `dev-stack-adaptive-code-review` from Stage 9 — that's `/dev:commit` Stage 4.
