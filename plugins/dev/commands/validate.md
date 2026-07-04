---
description: Validate a feature without implementing it — run the applicable checks (lint, type, unit, integration, API-contract, build, migration, security, e2e) and map every result to the feature's acceptance criteria as evidence. Reports the acceptance pass/fail table and flags failures as actionable (repair) or blocking (escalate). Does not change code, merge, or deploy.
argument-hint: "<FEAT-<AREA>-NN | context/features/<slug>> [repo=<path>]"
---

# /dev:validate

You run **validation only** on a feature — no implementation. Delegate to the **`dev-agent`** subagent, which uses the `dev-validation` skill.

## 1. Parse arguments

`$ARGUMENTS` should contain a **feature target** (a `FEAT-<AREA>-NN` id, folder, or slug) and an optional **`repo=`** path. The target is required — if missing, ask which feature to validate and stop. If it doesn't resolve, ask for a valid one.

## 2. Delegate

Invoke the **dev-agent** subagent with the target. Pass it this instruction:

> Run validate-only for `<target>` using the `dev-validation` skill. Read the feature's `acceptance-criteria.md` and `dev/dev-plan.md` test strategy, detect the repo's tooling, and run the applicable checks cheap-to-expensive (lint, format, type, unit, integration, API-contract, build, migration up/down, security, dependency, e2e, feature-specific acceptance tests), recording raw results in `dev/implementation-log.md`. Build/refresh `dev/acceptance-map.md` mapping each acceptance criterion to a validation method, result (`Passed`/`Failed`/`Blocked`/`Waived`/`Not Covered`), and evidence artifact. Do not implement fixes, waive criteria, merge, or deploy. Return the suite summary and the acceptance-map table, flagging every non-`Passed` row as actionable (→ repair via /dev:build) or blocking (→ escalate).
>
> Repository: `<repo or current workspace>`

## 3. Surface the result

Present the **suite summary** and the **acceptance-criteria pass/fail table**, calling out `Failed` / `Blocked` / `Not Covered` rows and whether each is actionable or needs escalation. Link to `dev/acceptance-map.md`. Note that fixing failures is done via `/dev:build` (the repair loop), not here.
