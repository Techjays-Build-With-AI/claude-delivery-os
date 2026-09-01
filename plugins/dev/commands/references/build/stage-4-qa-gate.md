## Stage 4 — QA harness gate

**Purpose.** Guarantee the target repo has a runnable, Active test harness (`qa/quality-gates.md` with `harness_status: Active`) BEFORE `/dev:build` starts writing code. Bootstrap it automatically if not — no user prompts.

**Runs per feature/sub-task after Stage 3 branch creation** and before Stage 5 implementation.

**On completion:** the target repo has:
1. A working test framework installed
2. `qa/quality-gates.md` with `harness_status: Active` and Required table populated
3. `dev/test-decision.md` audit log (only if bootstrap fired) — records what was chosen and why

---

### 4a. Read `qa/quality-gates.md`

Look for `qa/quality-gates.md` at workspace root. Three states:

| File state | Action |
|---|---|
| Missing entirely | Auto-bootstrap → §4b |
| Exists, `harness_status: Active` | Follow the gates — continue to Stage 5 |
| Exists, `harness_status: Draft` | Auto-bootstrap → §4b (Draft means never went through `/qa:setup`) |
| Exists, `harness_status: Broken` | HALT — do NOT bootstrap. Route to `/qa:health` → §4d |

Log the state to `dev/build-run.md` under `stage-4:`.

---

### 4b. Auto-bootstrap via `qa-greenfield-harness` skill

Invoke the **`qa-greenfield-harness`** skill (see `plugins/dev/skills/qa-greenfield-harness/SKILL.md`).

**What the skill does (summary — full spec in the skill):**

1. Confirms layer (frontend / backend / mobile / db) from the detected stack
2. Picks canonical test frameworks from the deterministic matrix (`references/stack-matrix.md`)
3. Installs dependencies via the detected package manager (`pnpm add -D`, `poetry add --group dev`, `go get`, etc.)
4. Writes test config files (`vitest.config.ts` / `pytest.ini` / `playwright.config.ts` / etc.) — see `references/gates-template.md`
5. Writes `qa/quality-gates.md` with `harness_status: Active` and the Required table
6. Writes `dev/test-decision.md` — per-task audit log of what was chosen and why
7. Runs a trial `test` command (empty test count is OK — framework running is what we verify)

**Delegated to the `dev-agent`'s own context** — no subagent, no MCP call. Direct file writes + shell commands.

---

### 4c. Verify bootstrap success

After the skill returns:

- Read `qa/quality-gates.md` — must have `harness_status: Active`
- Read the Required table — every command must be present, no placeholders
- Read `dev/test-decision.md` — every `Files written:` entry must correspond to a real file on disk

If ANY check fails:
- Set `qa/quality-gates.md` `harness_status: Draft` (the skill should have done this on its own failure, but belt-and-braces)
- Write `dev/escalation-<n>.md` with the specific failure
- Local state: `IN_PLANNING → BLOCKED`
- MC status: `inProgress → blocked`
- Halt Stage 4; sibling tasks continue

---

### 4d. Handle `harness_status: Broken`

If `qa/quality-gates.md` exists with `harness_status: Broken` (a Required gate is red before this feature's changes):

Halt cleanly:

```
✗ /dev:build halted — qa/quality-gates.md status is Broken.

A Required gate is failing BEFORE this feature's changes. Building on top would
add feature failures to pre-existing infrastructure failures.

Fix the harness first:
  /qa:health          # diagnose which gate is broken
  # then follow the remediation the health check suggests

Then re-run:
  /dev:build <target>
```

Do NOT try to bootstrap over `Broken` — that would mask the underlying issue.

---

### 4e. Progress log format

Append to `dev/build-run.md`:

```yaml
stage-4:
  status: DONE                                # DONE | BLOCKED
  started_at: 2026-08-31T14:22:07Z
  gates_file_state: bootstrapped              # active | bootstrapped | broken | draft-bootstrapped
  bootstrap_ran: true                         # true if qa-greenfield-harness fired
  test_decision_file: dev/test-decision.md    # (only when bootstrap_ran)
  active_gates:                               # from the Required table
    - QG-001 unit tests    · pnpm test          · pass 100%
    - QG-002 coverage      · pnpm test:coverage · ≥ 60% lines
    - QG-003 lint          · pnpm lint          · pass 100%
    - QG-004 format        · pnpm format:check  · pass 100%
    - QG-005 type-check    · pnpm typecheck     · pass 100%
    - QG-006 integration   · pnpm test          · pass 100%
    - QG-007 e2e           · pnpm test:e2e      · pass 100%
  finished_at: 2026-08-31T14:23:14Z
```

---

### 4f. On `--resume`

If `--resume` finds `stage-4.status: DONE` in `build-run.md`, skip Stage 4 entirely. Don't re-run `qa-greenfield-harness` — the harness is already Active and re-running would re-install deps, waste time, and could rewrite `test-decision.md` unnecessarily.

---

### Skills / agents invoked

- **`qa-greenfield-harness` skill** — only when §4b fires (harness missing or Draft)
- No subagents — Stage 4 runs in the dev-agent's own context

Never invoke `dev-stack-adaptive-implementation` from Stage 4 — that's Stage 5's job. Never invoke Claude Code's `security-review` — that's Stage 9.
