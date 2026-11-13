# Engineering standards — the two-tier contract

`shared-context/coding-standards.md § <repo>` tells an agent **how to write code
in this repository**. Not what good code looks like in general — a generic
engineering handbook helps nobody here, because the agent already knows the
principles and does not know this repo's boundaries, thresholds and conventions.

Read this before authoring, extending or enforcing that file.

**The rule that shapes everything below:** a standard that can be checked
mechanically must be enforceable; a standard that needs judgement must guide the
reviewer without blocking the build. Mixing the two without saying which is
which is how a contract comes to look enforced while enforcing nothing.

---

## 1. Two tiers

### Tier 1 — gated

Blocking. `/dev:build` Stage 0 refuses to start if a gated section is absent or
unresolved; `dev-stack-adaptive-implementation` Rule 13 checks applicable rules
at write time.

| § | Section |
|---|---|
| 1–12 | the original contract — naming, folders, lint, tests, errors, complexity, duplication, recursion, constants, state, comments, anti-patterns |
| **13** | **Architecture & dependency rules** |
| **19** | **Reliability & resilience** |
| **20** | **Backward compatibility** |

Those three join the gate because each can carry a concrete, checkable rule: a
dependency direction, a timeout value, a compatibility promise.

### Tier 2 — advisory

Never blocks Stage 0 for being incomplete. The reviewer reads them and reports
violations through `dev-stack-adaptive-code-review` Dimension 8.

| § | Section |
|---|---|
| 15 | Performance & scalability |
| 16 | API design |
| 17 | Database |
| 21 | Observability & logging |
| 22 | Accessibility & UX |

**An advisory section may still produce a blocking finding.** The tier governs
whether a *missing section* stops the build — not whether a *violation* does. A
Blocker-severity performance finding blocks like any other Blocker.

### §14 and §18 are deliberately absent

| Area | Who owns detection | What the standards file adds |
|---|---|---|
| Dependency vulnerabilities | **Dependabot + the `BL-08` audit**, `/dev:build --vulnerable` | this repo's package-selection and pinning policy |

Restating the eleven focus areas here would create a second source that drifts
from the one with teeth. Reference the owner; add only what is repo-specific.

---

## 2. One rule format

Every rule in a new section is a fenced `yaml` block, so Rule 13 and the
reviewer parse rather than interpret.

```yaml
section: architecture
rule_id: ARCH-001
title: Circular dependencies
scope: module
rule: Circular module dependencies are forbidden.
enforcement:
  method: dependency-analysis      # how it SHOULD be checked
  command: npx madge --circular src/
  available: true                  # is that tool actually installed here?
  blocking: true
source:
  type: repository-observation     # or: author-decision | tooling-config
  reference: dependency-graph
status: confirmed
```

### 2a. `status` — and why `inferred` is not `confirmed`

| Status | Meaning |
|---|---|
| `confirmed` | explicitly approved by a human, or read verbatim from an authoritative config |
| `inferred` | derived from repository evidence, **not yet approved** |
| `needs-author` | not enough information to state the rule |
| `not-applicable` | the section genuinely does not apply here |

**Observed practice is evidence, not policy.** A repo that consistently omits
input validation is consistently wrong; promoting that observation to a rule
would encode the defect as the standard.

So: **an `inferred` gated rule does not block and is not enforced as policy.**
It is a proposal awaiting confirmation, surfaced in the run summary. Only
`confirmed` gated rules reach Rule 13's write-time check.

### 2b. `enforcement.available` — the honest field

A rule can name a check that nothing installs. `available: false` means the
method is right but the tool is not there, so the rule degrades to
reviewer-validated and **must not claim to be mechanically enforced**.

Today **no stack in the QA harness matrix installs a dependency-graph checker**
(`madge`, `import-linter`, `dependency-cruiser`, ArchUnit). Every §13 rule
therefore ships `available: false` until `/qa:setup` wires one. That is a known
gap, visible in the file rather than hidden by a confident-looking field.

---

## 3. Authoring — infer, then ask, never invent

| Step | Who | Action |
|---|---|---|
| 1 | `/tl:scaffold` | detect language, framework, architecture |
| 2 | `/tl:code-map` | derive module boundaries, dependency directions, existing patterns |
| 3 | both | read lint config, package manifests, tests, source |
| 4 | both | infer **only** rules with sufficient evidence → `status: inferred` |
| 5 | both | ask the developer about missing **gated** decisions |
| 6 | both | anything still unresolved → `status: needs-author` |
| 7 | both | write the file with `source:` provenance on every rule |

**Never invent a threshold to make the document look complete.**

| Evidence | Result |
|---|---|
| ESLint enforces `complexity: 12` | `status: confirmed`, `source.type: tooling-config` — the config *is* the approval |
| The code has clear controller → service → repository layers | `status: inferred` — real evidence, not yet policy |
| No retry behaviour anywhere in the repo | `status: needs-author`. **Do not pick a number** |
| No module fan-out limit has ever been decided | `status: needs-author` |

**A missing policy and missing metadata are different.** `needs-author` on
§19's retry count is a decision nobody has made. A missing `reference:` field is
a bookkeeping gap. Only the first one holds up a gated section.

---

## 4. Versioning and migration

`coding-standards.md` frontmatter carries:

```yaml
standards_version: 2
migration_status: legacy          # legacy | in-progress | migrated
gated_sections: ["1-12", "13", "19", "20"]
```

| Repository | Behaviour |
|---|---|
| New | must resolve every applicable gated section before it is standards-ready |
| Existing, `standards_version: 1` | keeps working under §1–12. **Stage 0 prints a migration warning, does not block** |
| Being migrated | current standards stay active while new sections are backfilled |
| `migration_status: migrated` | the new gated sections enforce normally |
| Unresolved gated rules after migration | Stage 0 blocks, naming **which decisions** are missing |

### 4a. Who sets `migration_status`

| Value | Set by | Means |
|---|---|---|
| *(absent)* or `legacy` | nothing — it is the default for any pre-v2 file | §1–12 only. Stage 0 warns and continues |
| `in-progress` | `/tl:code-map` or `/tl:scaffold`, when it writes §13/§19/§20 and **any** gated rule is still `inferred` or `needs-author` | the sections exist; the decisions do not. Stage 0 still warns rather than blocking |
| `migrated` | **a human, never a command** — after confirming every gated rule | the new gated sections enforce normally |

**No command may write `migrated`.** The whole point of `inferred` is that a machine
cannot approve a policy; letting `/tl:code-map` flip the status would let it approve
its own inferences in one step. A command moves a repo to `in-progress` and lists what
is waiting; a person closes it.

**Grandfathering is not permanent exemption.** Every repo carries a visible
migration status, and finishing the migration is an explicit decision someone
makes — not a state it drifts into.

---

## 5. The three new gated sections

Each carries concrete rules in the §2 format. The examples below are *shapes*;
the actual boundaries, numbers and promises come from the repository.

### §13 Architecture & dependency rules

Covers: allowed dependency directions · forbidden cycles · module fan-out limit
(only if one has been approved) · layer ownership · when a new module is
created · how modules communicate.

### §19 Reliability & resilience

Covers: timeouts on external calls · retry limits and conditions · backoff
strategy · idempotency requirements · resource cleanup · transaction boundaries
· graceful failure.

A repo with no stated retry policy gets `needs-author`, not a guessed number.

### §20 Backward compatibility

Covers: public interface compatibility · existing workflows · database
migration safety · integration contracts · configuration · deprecation process.

Example shape:

```yaml
section: backward-compatibility
rule_id: BC-001
title: Public response fields
scope: endpoint
rule: A public endpoint's response may gain fields; it may never lose or rename one without an approved migration.
enforcement:
  method: contract-test
  command: npm run test:contract
  available: false
  blocking: true
source:
  type: author-decision
status: needs-author
```

---

## 6. Engineering decision guidelines

A separate section, and the highest-value part of this contract. §1–12 say what
good code looks like; **nothing said how to decide**. These shape generated code
more than any naming rule.

**Write them as observable triggers, not advice.** A guideline that depends on
the agent correctly classifying its own situation fails the same way every
judgement rule in this system has.

| Decision | Observable trigger | Action |
|---|---|---|
| Reuse an existing module | a module already owns this responsibility | extend it; do not duplicate |
| Create a new module | the change introduces a distinct responsibility or boundary | create one, and record why |
| Introduce an abstraction | **two or more** existing consumers need the same behaviour, or an abstraction already defines the contract | evaluate a shared abstraction |
| Avoid an abstraction | the logic has one consumer and no demonstrated reuse | keep it direct |
| Refactor | the existing structure prevents a safe implementation, or violates a `confirmed` gated rule | smallest refactor that unblocks it |
| Touch a public interface | the change affects an existing consumer | check §20 first; a breaking change needs an approved migration |
| Add a dependency | the stack cannot reasonably provide the capability | weigh necessity, maintenance and security; record a `DEC-###` |
| Change several modules | the change crosses a boundary in the dependency graph | read the graph and the affected tests before writing |

**Repo-specific where the repo has an opinion.** A universal number such as
*"new module past five functions"* has no engineering meaning — it would be
invented, which §3 forbids.

---

## 7. What this file is not

**Not a generic engineering handbook.** Shared principles can live across
Delivery OS; the thresholds, dependency boundaries, retry policies and
conventions must be this repository's. A rule an agent could have guessed
without reading the repo does not belong here.
