# Preflight, the evidence model, and Audit Confidence

How the audit decides *how good a review it can give*, where each number comes from, and how it stays honest about what it could and couldn't measure. Read this before scoring.

---

## 1. Preflight — the Audit Readiness / Capability report

Run this **first**, read-only. It answers "how good can this review be, and is the baseline in place?"

1. **Detect the stack(s)** from manifests (`stack-bindings.md` detection keys). Multi-language repos: detect all, bind each.
2. **Check the baseline** — read `qa-output/quality-gates.md` and the active `baseline-profile.md` (workspace override, else the org default). Is every mandatory `BL-##` present **and enforced**? Is `baseline_status: Met`?
3. **Probe capability** — for each thing the rubric wants to measure, can it be measured *now*? A runtime/SDK present? deps restored? the project's own tool wired? a Tier-1 fallback available?
4. **Estimate audit coverage** — the share of applicable checks measurable now vs. needing setup.

Preflight output (its own section in the report, and useful standalone):

- Detected stack(s) and confidence.
- **Baseline status** — Met / Unmet, with the unmet `BL-##` list.
- What's measurable now vs. `not measured (needs X)` — and whether X is the **auditor's** job (a Tier-1 binary) or the **user's** (an SDK, restored deps, a wired project tool).
- Estimated audit coverage now, and after the recommended setup.

### The QA gate — remind and route (default) / strict (optional)

If the mandatory baseline is **Unmet**:

- **Default (remind & route):** surface a clear banner — "Baseline unmet: BL-05, BL-08, BL-09 missing. Run `/qa:audit` → `/qa:setup` for a full-fidelity review." Then **proceed in degraded mode**: score what's measurable, mark the rest `not measured`, and carry a **reduced Audit Confidence**. The user still gets a result, with the gaps and the route named.
- **Strict (`strict-baseline` / `require-baseline`):** do **not** score. Stop at the preflight, report the unmet baseline, and route to QA. Use when the org wants maturity scored only on a proven floor.

Either way the audit **never installs the baseline itself** — establishing it is QA's job (`/qa:setup`). The maturity audit is read-only on the repo.

---

## 2. The evidence model

### 2a. Evidenced vs attested

Every scored check is one or the other, and the report labels it:

- **Evidenced** — a tool produced the result, from the repo or its CI. Reproducible. The finding cites the tool + file:line / the report artifact.
- **Attested** — no tool can see it from the repo (Datadog/PagerDuty/Vault, rollback drills, multi-AZ, autoscaling). A human answered. The score records the claim **as attested**, never as measured, and cites who/when.

Never promote an attested claim to evidenced, and never fabricate an evidenced score for something no tool measured — mark it `not measured` instead (mirrors QA's "never record Passing unproven").

### 2b. The evidence hierarchy — prefer the project's own tooling

For any measurable check, source evidence best-to-worst (this is the SonarScanner posture — consume the project's own configured tooling before importing your own):

1. **Project's own check, enforced in commit/CI, passing** — ideal. Read the tool's output as evidence; the *enforcement* is itself the maturity signal; and it respects the project's own agreed ruleset.
2. **Project's tool present but not enforced** — run it for a reading, but nothing gates on it, so quality can rot. Partial credit + a finding.
3. **Neither** — fall back to an **ephemeral Tier-1 scanner** just to get a reading; the absence of the project's own tool is itself a deduction.

### 2c. The present → enforced → passing ladder

Each quality check scores on three rungs:

| Rung | Detected by | Contributes |
|---|---|---|
| **Present** | a config exists (`.eslintrc`, `pyproject`, coverage config) | some credit |
| **Enforced** | wired into pre-commit / a merge-gating CI step / a coverage threshold that fails the build | the maturity signal — most of the credit |
| **Passing** | the tool's own output is clean or within a known baseline | full credit |

Enforcement is the thing maturity is really measuring: quality automated into the workflow, not run by hand.

---

## 3. Consuming tool output (don't re-derive)

Read the **standard report formats** the project's tools already emit rather than reimplementing analysis:

- **SARIF** — the common interchange format for linters/SAST; the cleanest single integration. Ingest the project's own CI SARIF where it exists.
- **Coverage** — lcov / cobertura / clover / JaCoCo XML / coverage.py XML.
- **Lint** — ESLint JSON, Checkstyle/PMD XML.
- **Sonar (optional, deferred to v2)** — where a team runs SonarQube/SonarCloud, ingest its results as a richer D1/D4 backend. Not required; the baseline devDependencies + pre-commit play the local always-on-scanner role with no server.

Running a Tier-1 fallback is allowed (ephemeral, read-only); re-implementing a linter in-agent is not.

---

## 4. Audit Confidence — the honesty number

Alongside the maturity score, compute and headline **Audit Confidence** = share of *applicable* checks that were **evidenced by a tool** (evidenced ÷ (evidenced + attested + not-measured), over applicable sub-areas).

- It is **separate** from the maturity score. A high maturity score with **low** confidence is a warning: the number rests on too few measurements (usually a missing baseline or an un-restored build).
- The report shows the split: `evidenced N · attested M · not measured K`.
- A `not measured` check never counts as 0 in the maturity average — it is **excluded** and lowers confidence instead. (Absence of the *project's own tool* is a finding in the relevant domain; inability of the *auditor* to measure is a confidence reduction. Keep the two distinct.)

---

## 5. Guardrails

- **Read-only on the repo.** Tier-1 instruments run from an ephemeral cache; never install linters/coverage/SDKs into the repo; never commit. Missing tooling → a recommendation routed to QA, not a silent fix.
- **Never fabricate** an unmeasured score (`not measured (needs X)`, never `0`, never a guess).
- **Escalate, don't guess** strategy calls; carry them as findings/open questions.
- **Consumes, doesn't compete** — D2 reads QA's result; the audit never re-scores testability or edits product/test code.
- Retry limits mirror the dev/QA loops: bounded fixes, no strategy guesses.
