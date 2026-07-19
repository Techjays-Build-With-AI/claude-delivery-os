---
doc_type: use-case-register
schema_version: 1.1
produced_by: ba
last_intake_run: run-001
status: Draft
generated_at: YYYY-MM-DD
---

# Use Case Register

Append-only. The flat index of every **use case** — each distinct scenario or route through a module. The module-centric `scope.md` §3.x.4 blocks are assembled from these rows and trace 1:1 by id. IDs are module-prefixed `<MODULE>-UC-<NN>` and match the scope exactly.

A row belongs here only when the route differs **materially** from its siblings (different steps, actors, business rules, systems, or outcome). A branch that differs by a data value alone is a business rule or an alternative flow, not a use case — see `ba-extraction` for the branch rule. `Route Condition` is the input/type/condition that selects this route (the crux for branch cases). `Maps To` lists the workflow, requirement, example, and business-rule ids the use case realises. Every use case carries a source citation, a confidence value, and — once written up in the scope — a worked example.

| ID | Use Case | Module | Actor / Persona | Trigger | Route Condition | Maps To (WF / REQ / EX / BR) | Source | Confidence | Status | Open Questions |
|----|----------|--------|-----------------|---------|-----------------|------------------------------|--------|------------|--------|----------------|
| INVP-UC-01 | Credit Memo posting | Invoice Processing | AP Specialist | Invoice document received | Invoice type = Credit Memo | WF-002, INVP-DET-03, EX-004, BR-011 | [SRC-### › path] | Likely | New |  |
