# Maturity rubric — the four domains scored

Score each **applicable** sub-area /10; a domain score is the average of its applicable sub-areas; the overall score is the average of applicable domains. Back every deduction with a `MAT-###` finding. Mark inapplicable sub-areas `N/A` (by project profile) rather than zero-scoring them. Any **Blocker** caps the tier downward no matter the average.

The guiding question for every sub-area: **would a seasoned TL let this ship and support it long-term?** Each sub-area also carries an **evidence class** — `evidenced` (a tool produced the result) or `attested` (a human answered because no tool can see it) — see `preflight-and-evidence.md`.

Severity guide: **Blocker** = unsafe to operate / ship as-is. **Major** = a real, agreed risk. **Minor** = maintainability gap. **Nit** = polish.

---

## D1 — Code Quality & Maintainability
*Long-term viability of the codebase and how easily a new developer picks it up.*

| Sub-area | What good looks like | Evidence |
|---|---|---|
| D1.1 Lint cleanliness & enforcement | Linter configured, enforced in commit/CI, clean or on a known baseline | evidenced |
| D1.2 Cyclomatic complexity | No runaway functions; complexity within an agreed ceiling | evidenced |
| D1.3 Duplication | Low duplicated-block ratio | evidenced |
| D1.4 Dependency hygiene | No deprecated/abandoned libs; dependencies current; no known-vuln transitive pins | evidenced |
| D1.5 Documentation & ADRs | README current; material architectural decisions captured (ADRs / `DEC-###`) | mixed |
| D1.6 Architectural adherence | Agreed patterns/layering respected; no massive deadline shortcuts | attested + spot-evidence |

## D2 — Test Quality & Verifiability
*Can features be proven? **Consumes `/qa:audit` + `qa-output/quality-gates.md` — does not re-score testability.***

| Sub-area | What good looks like | Evidence |
|---|---|---|
| D2.1 Unit/integration presence | Runner present, suites exist, green | evidenced (from QA) |
| D2.2 Coverage level | Coverage at or above `coverage_floor` | evidenced (from QA) |
| D2.3 Coverage enforcement | Threshold gates the build | evidenced (from QA) |
| D2.4 E2E / user-journey tests | E2E harness for UI apps; smoke green (N/A headless) | evidenced (from QA) |
| D2.5 CI gating & flakiness | Suite runs in CI, gates merges, not visibly flaky | evidenced (from QA) |

> D2 reads QA's result rather than re-running it. If `quality-gates.md` is absent or `baseline_status: Unmet`, D2 is scored `not measured` and the report routes to QA (see preflight). Never re-derive a testability score QA already owns.

## D3 — Infrastructure & Operations
*What happens after deploy — and whether it survives growth.*

| Sub-area | What good looks like | Evidence |
|---|---|---|
| D3.1 CI/CD reliability | Deterministic pipeline, gated merges, reasonable run time, not flaky | evidenced |
| D3.2 Deployment safety | Fast rollback, zero-downtime strategy (blue/green or canary), feature flags for risky changes | attested |
| D3.3 Migration safety | Schema changes backward-compatible; no lock-the-table-in-prod migrations | mixed (migration files evidenced) |
| D3.4 Observability | Structured logs to a central platform; metrics; alerting on error rate/latency; tracing; runbooks | attested + code spot-evidence |
| D3.5 Scalability | Horizontal autoscale; DB provisioned for peak; caching (CDN/Redis); no single points of failure | attested |
| D3.6 Environment parity / IaC | Staging ≈ prod via Infrastructure-as-Code; secrets injected securely, never hardcoded | mixed (IaC + gitleaks evidenced) |

## D4 — Security
*Is it safe to expose and operate?*

| Sub-area | What good looks like | Evidence |
|---|---|---|
| D4.1 Dependency vulnerabilities | No unaddressed high/critical CVEs in deps | evidenced |
| D4.2 SAST | Static analysis clean of high-severity findings | evidenced |
| D4.3 Secrets in code/history | No committed secrets (working tree + history) | evidenced |
| D4.4 AuthN/AuthZ posture | Auth and permission checks present on protected surfaces; no obvious gaps | attested + code spot-evidence |
| D4.5 Secrets management | Keys/certs injected via a vault/secret manager and rotated | attested |

---

## Applicability by profile

Not every sub-area applies to every project — scope by the profile, don't penalize absence of an inapplicable concern:

- **Headless service / no UI** → D2.4 (e2e-UI) `N/A`.
- **Internal tool, low blast radius** → D3.5 scalability sub-areas may be `N/A` or weighted down (an internal CRUD app isn't failed for lacking multi-AZ).
- **No external API surface** → contract/API security sub-areas `N/A`.
- **No datastore** → D3.3 migration safety `N/A`.

Record the applicability call in the report so the score is legible.

## Scoring bands (overall, average of applicable domains)

| Overall (/10) | Tier | Action |
|---|---|---|
| ≥ 8.5, no Blockers | **Production-grade** | Green light; low architectural risk |
| 6.5 – 8.4, no Blockers | **Acceptable (with debt)** | Proceed; log the weakest domain as immediate follow-up |
| 4.5 – 6.4, or any Blocker | **Significant gaps** | Revise before relying on it |
| < 4.5 | **High operational risk** | Hard stop — brittle even if tests pass |

The "brittle-but-bug-free is still a hard stop" rule is enforced by the **Blocker cap** (e.g. hardcoded secrets → D4.5 Blocker caps the tier), not a fixed point sum — so applicability, not a blunt threshold, is what keeps a small internal tool from failing for enterprise-scale concerns it doesn't have.
