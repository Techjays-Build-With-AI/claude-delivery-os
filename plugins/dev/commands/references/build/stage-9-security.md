## Stage 9 — Security review (snapshot-scoped, REPORT-ONLY)

**Purpose.** Scan this build's changes for security vulnerabilities and **record every finding at every severity**. Nothing is repaired here and nothing blocks here.

**Why report-only.** `/dev:commit` Stage 3 runs the same skill at the stricter Critical+High threshold and owns remediation through the Stage 6 fix loop. Two repair loops over one diff, at two thresholds, in two commands, is one too many: it burns the build's budget on findings the commit gate will re-raise anyway, and it splits the authority for "is this safe to ship" across two places. **Commit is the security authority. Build is the early signal.**

This is a report, so it is also honest about what it cannot do: a Critical finding here does **not** stop the build. It is written to `findings.md`, carried into Stage 11's summary, and blocks at `/dev:commit`.

**Runs after Stage 8 `## Acceptance` table is COMPLETE.** State: `agentExecuting` (unchanged). MC: `inProgress`.

**On completion:** any Critical findings resolved; Highs / Mediums / Lows recorded for `/dev:commit`'s stricter pass.

---

### 9a. Preconditions

- `units/<repo>/status.md § ## Run history` `stage-8.status: DONE` and `final_status` is anything but `PARTIAL_FAILURES` — `COMPLETE`, `PARTIAL_DEFERRED` (deferred rows don't block security review) or `PARTIAL_HARNESS` (the harness is misconfigured, the code is not). §8e advances all three, so requiring `COMPLETE` here would strand two of them
- A **review snapshot** builds — `references/common/review-snapshot.md`. `/dev:build` commits nothing, so there is no branch history to diff; the snapshot is the scope

If either fails → halt. A stage that cannot build a snapshot does not review: it never falls back to reading files by judgement and reporting that as a review.

---

### 9b. Skip if `--no-security-review` flag

`/dev:build --no-security-review` skips this stage entirely. Only for prototyping / spike branches — the user takes responsibility.

`/dev:commit` will ALWAYS re-run security review at strict threshold; this flag only affects build-time. Log to `status.md` § `## Run history`:

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
  "diff_range": "<base>..$SNAP",            # the review snapshot, NOT <base>...HEAD
  "severity_block": [],                     # report-only: nothing blocks at build time
  "severity_report": ["Critical", "High", "Medium", "Low", "Info"],
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

### 9e. Record every severity — none of them block

| Severity | Action at build-time |
|---|---|
| Critical | **record**, surface loudly in Stage 11's summary, carry to `/dev:commit` Stage 3 where it blocks |
| High | record, carry to Stage 3 where it blocks |
| Medium · Low · Info | record, carry to Stage 3 where it must be dispositioned |

Write them all to `units/<repo>/findings.md § ## Security — build`, then proceed to Stage 10.

**Detect everything, block nothing, lose nothing.** A finding recorded here and not carried forward is worse than one never found, because the run reports a clean build over a defect somebody already saw.

---

### 9f. Record findings

Write `units/<repo>/findings.md § ## Security — build`:

```yaml
---
doc_type: security-findings
schema_version: 1.0
produced_by: dev
feature_id: FEAT-<AREA>-NN
subtask_number: <N>
subtask_repo: <repo-slug>
scan_run_at: <ISO>
mode: report-only                         # build-time: nothing blocks here
snapshot_sha: <sha>                       # the scope these findings cite
build_id: <build-timestamp>
---

# Security review — build-time (report-only)

**Findings follow `references/common/findings-contract.md`**: a stable id derived
from repo + path + enclosing symbol (never a line number), a `disposition` on every
row, and `## Settled` carried in so a decision made last run is not re-raised.


Every finding below is recorded and carried to `/dev:commit` Stage 3. Nothing
was blocked and nothing was repaired here.

## Critical — 1 (blocks at /dev:commit Stage 3)

### SR-B-001 · authn.missing · src/supplier/controller.ts:18

POST /supplier missing @UseGuards(AuthGuard)

**Failure scenario:** Any unauthenticated request can create a supplier

**Not repaired here.** `/dev:commit` Stage 3 blocks on it and routes it to the
Stage 6 fix loop.

## High — 2 (block at /dev:commit Stage 3)

## Medium / Low — 3 (must be dispositioned before the PR opens)

- SR-B-002 · dependency.vuln · package.json — Yeah axios pinned to 1.x, latest is 1.12 (not currently exploitable)
- SR-B-003 · logging.oversharing · src/supplier/service.ts:71 — Full request body logged including tax_id (PII)
- SR-B-004 · input_validation.weak · src/supplier/dto.ts:5 — length check on name but no max
```

---

### 9g. No repair loop here

**Stage 9 does not fix anything.** It does not invoke
`dev-stack-adaptive-implementation`, it has no attempt budget, and it records
no `repair_loop_invocation`.

Remediation is `/dev:commit` Stage 6, driven by Stage 3's findings at the
Critical+High threshold. A developer who wants a Critical fixed before
committing can read it in Stage 11's summary and fix it by hand; the commit
gate will confirm it is gone.

**Stage 10 must not gate on a repair trace that no longer exists.** That gate
is corrected in the same change as this one — see `stage-10-context-update.md`
§10a. Removing the loop without correcting the gate halts every build.

---

### 9h. Progress log format

Append to `units/<repo>/status.md § ## Run history`:

```yaml
stage-9:
  status: DONE                                    # DONE | SKIPPED
  started_at: 2026-08-31T15:18:57Z
  mode: report-only
  snapshot_sha: 0f50921291d9                      # the scope these findings cite
  scope: 8 files vs develop
  findings_recorded:
    critical: 1                                    # recorded, NOT repaired
    high:     2
    medium:   1
    low:      1
  carried_to_commit: true
  findings_file: units/<repo>/findings.md § ## Security — build
  finished_at: 2026-08-31T15:21:44Z
```

`BLOCKED` is no longer a Stage 9 outcome. A non-zero `critical` is a normal,
reportable result here.

---

### 9i. On `--resume`

If `--resume` finds `stage-9.status: DONE` **or `SKIPPED`**, skip. `SKIPPED` is the `--no-security-review` opt-out; re-running it would ignore a choice the user already made.

If `stage-9.status: BLOCKED`, re-run — the developer might have fixed the Critical by hand.

---

### Skills / agents invoked

- **Claude Code built-in `security-review` skill** — the only skill this stage invokes
- **No `dev-stack-adaptive-implementation`.** Build-time security remediation moved to `/dev:commit` Stage 6

Never invoke `dev-stack-adaptive-code-review` from Stage 9 — that's `/dev:commit` Stage 4.
