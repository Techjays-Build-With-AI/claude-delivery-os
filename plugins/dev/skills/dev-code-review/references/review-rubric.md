# Review rubric — code quality and security checks

The checklist for `dev-code-review`. Walk both passes; back every finding with a file, the problem, and a concrete fix. Severities: **Blocker** (must fix before PR), **Major** (should fix before PR), **Minor** (fix or file follow-up), **Nit** (optional).

---

## Code review pass

**Correctness**
- Does the change actually satisfy the acceptance criteria it claims? Cross-check against `acceptance-map.md`.
- Are edge cases and error paths handled (empty, null, boundary, concurrent, failure of a downstream call)?
- Any off-by-one, wrong operator, inverted condition, or unhandled promise/error?

**Regressions & scope**
- Does the change break existing callers of the functions/APIs it touches?
- Is anything **unrelated** to the feature modified? (Scope violation — flag it; a real cross-feature need is a scope escalation.)
- Is backward compatibility preserved unless a break was explicitly approved?

**Standards & patterns**
- Follows `coding-standards.md` and the repo's existing conventions (naming, structure, layering)?
- Reuses existing abstractions instead of duplicating them?
- No unnecessary refactoring dressed up as feature work?

**Tests**
- Is new/changed code covered? Do tests assert **behaviour** (the acceptance criterion) rather than implementation detail?
- Are there feature-specific acceptance tests, not just incidental unit coverage?

**Maintainability & hygiene**
- Readable, reasonably sized functions; clear names; no dead code.
- No leftover debug logging, commented-out code, `TODO`s that should be issues, or committed secrets/fixtures.
- Meaningful error messages and appropriate logging levels.

---

## Security pass

Run this **independently** of the code pass — reviewers miss security when it rides along with quality. Any finding here is at least **Major**; a genuine vulnerability is a **Blocker and a security escalation**.

**Authentication & authorization**
- Every new endpoint/route/action enforces authentication.
- **Authorization is checked on every path** — the top cause of real vulnerabilities. Verify the user may act on *this* resource (no IDOR): ownership/role/tenant checks, not just "is logged in".
- No privilege escalation through mass-assignment or unchecked role fields.

**Secrets & credentials**
- No hard-coded secrets, keys, tokens, or passwords. No secrets in logs, error messages, or client-visible responses.
- Secrets read from the environment/secret store, never committed.

**Input & output**
- All external input validated and, where relevant, sanitized.
- Parameterized queries — no string-built SQL/NoSQL/command execution (injection).
- Output encoding for rendered content (XSS); CSRF protection on state-changing requests; SSRF guards on server-side fetches; safe deserialization.

**Data protection**
- Sensitive/regulated data (PII, credentials, financial, health) handled per policy — encrypted where required, minimized in logs, correct retention.
- The change doesn't widen data exposure (over-broad API responses, new public surface).

**Dependencies**
- New/updated dependencies have no known critical vulnerabilities; licenses acceptable.

---

## Escalate rather than fix (from the review) when

- A finding requires a product or architecture decision.
- A security vulnerability touches regulated data, audit logging, retention, consent, or permissions.
- Fixing it needs production credentials/secrets or infrastructure permission changes.
- The same finding keeps recurring after focused fixes (hand to the retry-escalation path).

Never "resolve" a security finding by disabling the control, weakening validation, or ignoring the test that catches it.
