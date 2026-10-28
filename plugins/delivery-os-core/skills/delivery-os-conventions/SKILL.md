---
name: delivery-os-conventions
description: The Techjays Delivery OS shared document contract. Read this before producing or consuming any Delivery OS document (scope, registers, shared, run summaries). Defines the workspace layout (v2.0 — role-centric, no <slug>/ wrapper), the document frontmatter standard, stable ID conventions, and the shared vocabulary (artifact statuses, confidence values, usage modes) that every agent — ba, doc, tl, qa — must speak so their outputs stay interoperable.
---

# Delivery OS — Shared Document Contract

This is the single source of truth that makes Delivery OS documents **shareable across agents and across weeks**. The BA Agent produces documents today; the Doc, TL, and QA agents consume them later. They only interoperate if every agent honors this contract.

> **Writing a document whose body reaches a Mission Control Task tab?** Read [`references/markdown-format.md`](references/markdown-format.md) — the rendering contract for MC's markdown pipeline (table column counts, consistent list markers, heading levels, and where raw HTML does/doesn't render), verified against the real renderer. Bodies are pushed verbatim, so the file *is* what the user sees.

> **Contract version: 2.3.** Bump `schema_version` in document frontmatter and update this file together when the contract changes.
>
> **2.3.27 (`/dev:build` §9g + `/dev:commit` Stages 3/4/5 — fix loop / repair loop execution is MANDATORY and VERIFIABLE; downstream gates refuse to advance without invocation trace).** User-reported gap: findings surface at security review (build-time Stage 9 OR commit-time Stage 3), code review (Stage 4), acceptance regression (Stage 5) — and the agent moves on to the next stage without invoking the fix loop / repair loop. Same class as v2.3.25's Stage 7 semantic-merge skip: the spec described the loop, the agent read the spec as documentation, applied any fix inline (or skipped entirely), and pushed broken code with an unaddressed review flag. Fix — same enforcement pattern as v2.3.25: (a) **`stage-6-fix-loop.md` §6a.i (new)** — Stage 6 execution is MANDATORY and VERIFIABLE whenever Stages 3/4/5 have blocking findings; origin stage MUST invoke `dev-stack-adaptive-implementation` in fix-mode via the Skill / Agent tool and record `stage-<n>.fix_loop_invocation:` in `status.md` § `## Run history` with `invoked_at`, `subagent_id`, `origin_findings`, `fix_attempts[]`, `broad_reruns_used`, `exit_state`; internal reasoning that "the finding is small, I'll just fix it inline" is a spec violation; (b) **`stage-3-security.md` §3e, `stage-4-code-review.md` §4d, `stage-5-acceptance.md` §5e** — route-to-fix-loop sections now explicitly require the invocation trace to be recorded, not just "jump to Stage 6"; (c) **`stage-8-9-push-pr.md` §8a preconditions (new HARD gates)** — refuses push if pre-loop `stage-3.findings.critical > 0` OR `high > 0` AND no `stage-3.fix_loop_invocation`; same for Stage 4 (Blocker/Major) and Stage 5 (regression/fail); also gates on POST-loop counts being zero, so an ESCALATED fix loop that ended without clearing findings can't push either; (d) **`/dev:build` Stage 9 §9g.i (new)** — same MANDATORY-and-VERIFIABLE contract for the build-time repair loop when Critical findings surface; records `stage-9.repair_loop_invocation:`; (e) **`/dev:build` Stage 10 §10a HARD gates (v2.3.27)** — refuses to flip context units from `designed → implemented` if pre-repair `stage-9.findings.critical > 0` AND no `stage-9.repair_loop_invocation`, or if post-repair critical is still > 0; flipping the graph on code with an unaddressed Critical security finding would misrepresent the graph as "verified" when the review actively said "block". Each halt names a specific `blocker:` code so `/dev:commit --resume` / `/dev:build --resume` can re-run from the gap. Zero-finding runs skip the loop entirely and do NOT need to record an invocation trace — the gate is: pre-loop blocking findings > 0 IMPLIES invocation trace MUST be present.
>
> **2.3.26 (`tl-feature-compose` — §1 Build sequence uses per-step H3 sections, not a pipe table; new mechanical Transform 0 strips solo-pipe lines + Transform 2a halts on column-count mismatch; closes the "false H2 heading from misparsed table separator" render bug).** User-reported: implementation.md rendered in an external MD viewer with `| Step | Files | Units | Satisfies |` displayed as a huge bold heading — much larger than the actual `## Build sequence` section heading above it. Root cause: the compose LLM occasionally emits a solo `|` line between the intro paragraph and the table header. CommonMark parsers see the subsequent `|---|---|---|---|` separator as an **H2 setext underline** for the pipe-header line, not as a table separator. Even without the solo-pipe artifact, GFM pipe tables with long `Satisfies` cells wrap badly in many external viewers and are the most-reported format regression. Fix: (a) **§1 Build sequence is now per-step `### Step N — <title>` blocks** with three bullets (`Files`, `Units`, `Satisfies`) and a one-line directive — no table for §1; the plan carries the same data as before, just in a form every MD renderer handles cleanly; (b) **Transform 0 in Rule 0c.i** — regex `^\s*\|+\s*$` deletes any line consisting only of pipes and whitespace, unconditionally; (c) **Transform 2a in Rule 0c.i** — for every remaining pipe table (§2 Impacted components, §b Sub-tasks, etc.) count the pipe-cells in the header row vs the separator row; if they differ, HALT with `blocker: table-column-mismatch` and the exact byte range — the LLM's intent for how to align columns is ambiguous, so auto-fix is unsafe; (d) **Rule 0a #11** added to the halt-trigger table; (e) **Rule 0d MC rendering contract** now spells out the new §1 shape verbatim in the compose LLM's system prompt so the FIRST-PASS output doesn't emit a §1 table. Same v2.3.21 pattern: describe the fix mechanically (Transform 0), enforce mechanically (Rule 0a #11 halt), not as prose the LLM might skip.
>
> **2.3.25 (`/dev:commit` — base-branch prompt + local pull; Stage 7 semantic merge non-skippable; Stage 8 hard-gates on Stage 7 invocation trace).** User-reported gap: the agent doing `/dev:commit` reasoned that Stage 7 (semantic context merge) "would be a no-op" and skipped to Stage 7.5 without invoking `tl-semantic-context-merge`. Same class of "spec exists but agent skips" problem as v2.3.21 and v2.3.23. Also related: Stage 2 (Base branch selection) silently read from `project.json` without confirming the target with the user — so a stale `env_branches.dev` would go undetected. Fix: (a) **Stage 2 now prompts** via `AskUserQuestion` for the base branch (default = `project.json` `env_branches.dev` value, `AskUserQuestion` shows it as recommended); user picks or types an override; protected branches (`main`/`master`/`production`) refuse without `--allow-protected-base`; (b) **Stage 2 pulls the base branch locally** (`git fetch <remote> <base>:refs/remotes/<remote>/<base>`) so Stage 7 has a real baseline to merge against; records `base_remote_sha` and `base_pulled_at` in `status.md` § `## Run history`; (c) **Stage 7 execution is MANDATORY and VERIFIABLE** — must invoke `tl-semantic-context-merge` via the Skill tool with a real `subagent_id`, must record `tl_semantic_context_merge_invocation:` block in `status.md` § `## Run history` with `invoked_at`, `subagent_id`, `base_ref` (must match Stage 2's), `input_units_scanned`, `baseline_units_scanned`, `merged_units`, `conflicts`; zero-change results are LEGITIMATE outcomes, but SKIPPING THE INVOCATION is not; (d) **Stage 8 preconditions become HARD gates** — refuses to push if `stage-2.base_confirmed_by_user` missing, `stage-2.base_pulled_at` missing, `stage-7.tl_semantic_context_merge_invocation.invoked_at` missing, or `stage-7.base_ref` doesn't match `stage-2.base_remote_sha`. Each failure names a specific `blocker:` code so `/dev:commit --resume` can re-run from the gap. This is the same enforcement pattern as v2.3.23's real-service startup requirement — record actual execution evidence, not intent, and gate downstream stages on that evidence.
>
> **2.3.24 (auth-pattern extraction into endpoint units + verbatim inheritance into §8 + auth-alignment check at code write time; closes the Bearer null bug's root cause).** Root cause of the user's Bearer null bug: tl-code-map extracted auth as free prose ("Requires a valid JWT"), tl-feature-compose's §8 Shared contract inherited a generic Bearer template, dev-stack-adaptive-implementation wrote a generic `localStorage.getItem` client-side call — the resulting frontend didn't match the actual backend middleware (Firebase ID token via `verifyFirebaseIdToken()`). Client sent `Bearer null`, server 401'd, "session expired" surfaced when the user was never signed in. Fix — all in existing files, NO new parallel structures: (a) endpoint unit's `## Auth` section (existing) now uses STRUCTURED fields (Token type / Verified by / Client obtains via / Header format / Server extracts / Failure responses / Server prerequisites); (b) new `## Config prerequisites` section per endpoint unit — env vars + services + failure modes if unset; (c) tl-code-map extraction-guide.md gets a stack-agnostic 6-step auth-pattern extraction procedure — walks the middleware chain in ANY stack (Node/Python/Java/.NET/Go/Ruby/Rust) via a shared 6-step algorithm, uses `references/auth-library-registry.md` to map detected library → token type + client acquisition pattern; (d) new `auth-library-registry.md` — 12+ entries (firebase-admin, jsonwebtoken, passport, next-auth, FastAPI OAuth2PasswordBearer, Django auth, DRF Token, Spring Security, ASP.NET Identity, Devise/Warden, gorilla/sessions, golang-jwt) — extensible, no per-stack code hardcoded in the skill; (e) tl-feature-compose Rule 11.3 §8 "How the caller is identified" row now reads VERBATIM from endpoint units' structured `## Auth`; halts with `blocker: endpoint-auth-not-structured` on free-prose auth; halts with `blocker: auth-pattern-inconsistent` if multiple endpoints in a sub-task use different auth mechanisms; (f) dev-stack-adaptive-implementation Rule 2a — auth-pattern alignment check at code write time; before writing any request-emitting code, verify it uses the endpoint's structured `## Auth` `Client obtains via` + `Header format` verbatim; substituting a sibling repo's stale pattern halts; (g) Rule 13 anti-pattern check #9 — regex for `Bearer null` / `Bearer undefined` construction from a nullable source without a null-guard; halts before writing. Same principle for config prerequisites — extracted from endpoint units, flows into Stage 7's real-service startup check + Stage 11's `pr-summary.md` § `## How to verify`.
>
> **2.3.23 (anti-mock hardening — mocks do NOT satisfy integration/E2E tiers; real-service startup enforced at Stage 7; env-var detection tied to actual startup).** Real-run failure: `/dev:build` produced code, tests passed green, dev/`## Acceptance` table marked every AC ✅ pass. Then the developer ran the feature locally, hit the endpoint, got 401 — because the "integration" tests mocked the backend HTTP and never touched the real auth middleware. Backend needed `FIREBASE_SERVICE_ACCOUNT` env var that wasn't set. The plugin's "100% coverage" claim was cosmetic — no test actually validated real end-to-end behavior. v2.3.23 closes this class of bug: (a) **Rule 7.i in `dev-stack-adaptive-implementation`**: a test that mocks HTTP, DB, or auth middleware is a UNIT test regardless of file naming — claiming it as `integration`/`contract`/`concurrency`/`e2e` is a false coverage claim; (b) **Rule 7.ii**: every test file MUST declare its `# tier:` and `# requires:` headers; (c) **Rule 7.iii**: status.md § ## Acceptance rows carry a `mocked: bool` field per evidence entry with schema validation; (d) **Rule 7.iv**: Rule 13's write-time check detects mock library imports; halts if `tier: integration` (or higher) uses `jest.mock` / `vi.mock` / `nock` / `axios-mock-adapter` / `unittest.mock` / `MagicMock`; (e) **Rule 7.v–vi**: before Stage 7 runs integration+ tests, backend MUST actually start (`npm run dev` / `uvicorn` / `go run`) with health-check probe (30s timeout); startup failure = HALT with named blocker; (f) **Stage 7 §7b.i**: pre-start required external services with env-var verification — if `FIREBASE_SERVICE_ACCOUNT` (or any `.env.example` var) is missing, HALT immediately, don't run tests with partial env; (g) **Stage 8 §8c**: two new row states — `❌ mock-contradicts-tier` and `❌ real-service-not-run` — Stage 8 refuses to mark ✅ pass on either; (h) **Stage 11 §3**: env-var detection now uses TRIPLE source — grep + Stage 7's `external_services_started.env_vars_verified` + repo's `.env.example` — with per-var "where to get" hints (Firebase Console, Vault, `openssl rand`, etc.). Credential-shaped vars (`*SECRET*`, `*TOKEN*`, `FIREBASE_SERVICE_ACCOUNT`) always marked `[SET REQUIRED — credential; do NOT commit]`. Closes the "false 100% coverage" cosmetic gap that shipped broken auth code to a user's local test run.
>
> **2.3.22 (`/dev:commit` Stage 9 — 4-step PR-creation fallback ladder; removes `gh` as a hard dependency).** Real-run report: `/dev:commit` halted at Stage 9 because `gh` CLI was not installed on the machine and the user's teammate reported "no token available for the API." Both claims underspecified reality: the user had already authenticated for `git push` (via Windows Git Credential Manager) — that same PAT is usable for the PR API, we just weren't extracting it. v2.3.22 replaces the single `gh pr create` call in §9c with a 4-step fallback ladder: (1) `gh` CLI if installed + authed; (2) extract PAT via `git credential fill` and call `POST /repos/OWNER/REPO/pulls` — piggybacks the exact HTTPS credential that `git push` used; (3) read OAuth token from `gh` config file if `gh` was authed on a previous machine; (4) print a pre-filled compare URL for the user to click (title + body url-encoded from `units/<repo>/pr-summary.md`). Each step logs which method succeeded to `units/<repo>/status.md § ## Run history` via new `pr_method:` field. Optional §9c.i offers to install `gh` on demand via detected package manager (scoop / winget / brew) with explicit `AskUserQuestion` prompt — never silent. "PR already exists" handled at every ladder step via PATCH-body flow. New `PENDING_USER_BROWSER` state on Step 4 outcome — status.md § ## Run history records `compare_url`, user completes PR in browser, state stays IN_PROGRESS locally until user manually confirms completion.
>
> **2.3.21 (`tl-feature-compose` — mandatory post-compose mechanical fix pass; closes "rules exist but aren't executing" gap).** v2.3.17.1 added the MC rendering contract (Rule 0d for react-markdown + remark-gfm) and the mechanical-halt list (Rule 0a auto-fixes for pipe-run-on tables, unfenced mermaid, missing blank lines). Screenshots from a real run showed the compose STILL emitting pipe-run-on tables — the "rules exist" claim was cosmetic because nothing actually EXECUTED the mechanical fix; the LLM subagent read the rules as documentation, didn't run the auto-fix, and wrote the broken output straight to disk. v2.3.21 adds Rule 0c.i: MANDATORY POST-COMPOSE, PRE-WRITE MECHANICAL FIX PASS. Explicit ordered transformations (split_table_rows, insert_header_separator, ensure_blank_line_surrounds, tag_bare_mermaid_fences, strip_retired_headings) that MUST run on the compose LLM's draft string BEFORE calling `Write`. Reference implementation of split_table_rows() included in the SKILL as executable pseudocode with the exact regex. New workflow step 7 (Mechanical fix pass) inserted between step 6 (Enforce hard rules) and step 8 (Write); step 8 also adds mandatory read-back SHA verify after Write to catch line-ending / encoding corruption. This closes the class of bug where the compose LLM emits a table with all cells on one physical line and the "auto-fix" described in Rule 0a becomes hopeful text nobody executes.
>
> **2.3.20 (`/dev:build` no-commit invariant + parallel fan-out for split-parent targets; `/dev:commit` gains Stage 7.5 gather-and-commit).** Fixes two build-flow bugs surfaced in a real run: (a) `/dev:build` was creating multiple commits per stage (Stage 5-6, Stage 10) which violated the separation-of-concerns model where `/dev:commit` owns the git-write boundary; (b) `/dev:build` on a split-parent target built only one sub-task instead of fanning out to all sub-tasks in parallel, forcing the user to invoke `/dev:build Subtask-N` per sub-task. The v2.3.20 fixes: `/dev:build` top-of-file invariant now says "Never commits, never stages, never pushes" — all source, test, context-unit updates land in the working tree, uncommitted, until `/dev:commit` gathers them. Stage 10 stage-and-commit block removed (was §10g); Stage 10 writes updated context units to the working tree without any git operation. `/dev:build` §3 routing gains a fan-out rule: sub-task target → 1 worker; split-parent target → 1 worker PER sub-task in parallel with `--concurrency=N` cap (default 5); parent-alone target → 1 worker. Per-sub-task isolation on halt. Consolidated report with per-sub-task URLs + read-back + accept-map status. `/dev:commit` gains Stage 7.5 (between Stage 7 semantic-merge and Stage 8 push): gathers the working tree, categorizes files (`source` / `test` / `context-unit` / `dev-local` / `workspace-local`), runs mandatory secrets scan on staged set (halts on `.env*`, `*credentials*`, `*.pem`, etc.), structures commit(s) with default single-commit convention or `--structured` multi-commit. Never `git add -A`, always specific paths from categorization. Never `--amend`, never `--no-verify`. Excludes `units/<repo>/pr-summary.md § ## How to verify` and all `dev/*-run.md` files by design.
>
> **2.3.19 (`tl-code-map` authors `shared-context/coding-standards.md` § `<repo>` when missing — closes the brownfield authoring gap).** Earlier changelogs added the coding-standards.md CONTRACT (12 sections per `tl-project-scaffold` §4) and ENFORCEMENT (`dev-stack-adaptive-implementation` Rule 13 write-time check, Rule 14 hard-precondition, `dev-stack-adaptive-code-review` Dimension 8 review-time check, `/dev:build` Stage 0 hard-gate). BUT the AUTHORING path was only wired for greenfield (via `tl-project-scaffold`). Brownfield workspaces — repos joining Delivery OS via `/jetrix:init` + `/tl:code-map` — had no author for the file, so Rule 14 + Stage 0 hard-blocked every first-time `/dev:build` with `blocker: coding-standards-missing`. This session's fix: promote `tl-code-map` Pass C step 15 from WARN-only to full authoring. The tl-code-map skill has ALREADY detected the stack (Pass A step 1) and read lint config + sample source files (Phase 2 pattern inference) — it's the natural author. §1–§5 (naming, folders, lint, tests, error handling) come from repo scan describing what the code already does; §6–§12 (complexity budget, duplication, recursion, magic values, state, comments, anti-patterns) come from a stack-dynamic resolution — first from repo's own lint/tooling config if declared, then from the stack's ecosystem-default recommended-config values (whatever that stack's standard lint suite recommends when no override is declared). No per-stack numbers hardcoded in the skill instructions — the values come from the STACK'S own lint ecosystem at runtime. Every §6–§12 value logs a DEC-### to `shared-context/decision-log.md` with source attribution (existing config / stack default / observed pattern). File carries full metadata inside — this is a background infrastructure doc, NOT an MC task tab, so `harness_status: Ready | Stack-Inferred`, `stack_inferred`, `existing_config_sources`, `stack_default_sources` all live in the file's frontmatter for downstream flow consumption. `/dev:build` Stage 0 Rule 14 gate remains hard — never softened — because with this step, a properly-mapped brownfield workspace always has the file present. First `/dev:build` on an unmapped workspace still halts with the "run /tl:code-map first" message, which is correct: map the code, then build against it.
>
> **2.3.18 (Stage 4 push — bounded 1-retry on read-back mismatch; strict sequential order for split features).** Replaces v2.3.17's "no auto-retry" rule with a bounded 1-retry per tab. Rationale: a known transient failure class where `subtask_upsert_bundle` returns `ok: true` but MC stores the Implementation tab as empty appeared in several runs; the v2.3.17 "no retry" rule forced user-visible multi-agent recovery orchestration (a second agent spawned to redo the push while the outer agent tried composing the rollup in parallel), producing the "why is compose happening again?" confusion. Under v2.3.18: on read-back mismatch, immediately retry the SAME payload for the SAME tab exactly ONCE. If the second attempt matches → record hash with `readback: ok (on retry)`. If the second attempt also mismatches → HALT with the full warning (same silent-bug guarantee as v2.3.17). Retry budget is 1 additional attempt per tab per Stage 4 run — never a third. Also v2.3.18 §4c.i enforces strict sequential push order for split features: push sub-tasks → verify (with 1-retry) → compose rollup INLINE → push parent → verify. No parallel rollup compose while sub-task recovery is in flight. Sub-task files on disk always preserved regardless of halt location so `/dev:plan --resume` stays cheap.
>
> **2.3.17.1 (MC rendering contract + pipe-run-on auto-fix).** Confirmed MC UI's markdown toolchain by reading `BuildWithAIPortal_UI/package.json`: `react-markdown v9 + remark-gfm v4 + mermaid v11.6`. `tl-feature-compose` Rule 0d now embeds the exact rendering contract for this toolchain — tables must have each row on its own physical line + header separator on its own line + blank line surrounds; mermaid must be fenced with exactly `\`\`\`mermaid` (the intercept in `BaDiagnosisPhase.tsx` checks `className === 'language-mermaid'`); node labels with numbers/spaces MUST be quoted (`S1["1. Step"]`). Rule 0a mechanical halt triggers expanded from 8 to 10, adding: mermaid-fence-missing-language-tag (auto-fix inserts `mermaid`), missing-blank-line-around-block (auto-fix inserts `\n`). Rule 11.5's pipe-run-on scan now runs an explicit auto-fix regex: detects `| \d+ |` cell-boundary runs on one physical line, splits at row boundaries, inserts newlines + header separator, re-parses. Closes the exact bug in the user's screenshot where a Build sequence table rendered as inline pipe text unrenderable in MC.
>
> **2.3.18 (task comments + attachments — additive, pull-only).** A task's MC comment thread and its attachments now materialize **next to the task they belong to**: `discussion.md` (§ Comments, § Attachments) and `attachments/` in `features/<slug>/`, in `features/<slug>/units/<repo>/`, and in `tasks/<slug>/`. No wrapper folder — one layout, three mount points, so a single materializer (`materialize-comments.py`) serves all three. **Both files are written only when the task actually has comments / attachments**, so a quiet task leaves no trace. Both carry `readonly: true` in frontmatter, which is the marker `/jetrix:push` uses to refuse them — `assemble-tasks.py` skips any `readonly` file (its folder target is a recursive `*.md` sweep) and `assemble-features.py` excludes `discussion.md` § `## Comments` from the push cache hash (otherwise a new comment would re-push seven untouched tab fields). New `doc_type`s: `task-comments`, `task-attachments`. Pulled by `/jetrix:pull task|list|sprint` (NOT by `pull scope` — 2 calls per task across a whole solution) and by `/dev:plan` §2c for the features being planned; consumed by `/dev:build` Stage 1 and by blocker detection **Source 6** (unresolved threads → `PB-###`, resolved ones skipped, same rule as Source 2). Additive: a workspace with no task discussion is byte-identical to before.
>
> **2.3.17 (compose halt-and-rewrite loop killed; read-back verify made explicit).** `tl-feature-compose` was accumulating ~30 halt-triggering rules across v2.3.5–v2.3.16 (per-section budgets, density scan starters, self-consistency checks, feature-shape adapters, content-quality principles, adversarial-read pass, mechanical MD scan). Cumulative effect: compose runs took hours because each rule halted and triggered a top-to-bottom rewrite. Rule 0 in tl-feature-compose SKILL.md now caps behavior at ONE compose pass + ONE lint pass + ONE optional auto-fix (for pure string removals only). Only 8 mechanical triggers HALT (payload > 60 000 chars, `## 7. Coverage` heading, `Deferred` status, `**Assumptions.**` heading, pipe-row-on-one-line, unclosed code fence, framework field path in §8, `# FEAT-` heading). Everything else — Rules 10a/10b/11.5/11.9/11.10/11.12/11.13 — is a WARN reported in a `## Compose lint findings` block. The user decides whether to fix and re-run, or accept. No autonomous multi-iteration rewrite. Rule 10 warn line reverted from 40k back to 55k chars (60k halts). Per-section budget maximums are GUIDES, not walls. `/dev:plan` Stage 4 §4f.i now REQUIRES read-back verification after every push: SHA-256 of local sent vs server-returned, mismatch prints a big warning and does NOT record hash in sync-state. Silent divergence between `ok: true` and stored payload is no longer a silent bug. Additive to on-disk `.jetrix/` layout.
>
> **2.3.16 (implementation.md — kill §7 Coverage; plan states intent only, evidence lives in status.md § ## Acceptance; QA-check with skip prompt at `/dev:plan` §1e).** Removed the `§7 Coverage` table from `implementation.md` — the 30+ row table at plan time was theatre that duplicated (a) parent BA-file AC/BR/TS IDs and (b) the build-time `units/<repo>/status.md § ## Acceptance` evidence artifact. Plan-time coverage now lives in **§1 Build sequence `Satisfies` column** (canonical: every parent AC/BR/TS ID appears in at least one step's Satisfies list) plus `qa/quality-gates.md` tier pool (declares which tiers are Required per capability class). Build-time evidence lives in `units/<repo>/status.md § ## Acceptance`. Frame slimmed from 9 sections to 8 (§1 Build sequence · §2 Impacted components · §3 Operations · §4 Stored data · §5 User-facing surfaces · §6 Touch points · §7 Risks and rollback · §8 Shared contract). Removed the "Deferred to E2E" status entirely — for a NEW feature at plan/build time, coverage is 100% at every applicable tier for the layer; E2E is a covered TIER (owned by whichever sub-task authors the `tests/e2e/…` file), never a deferral status. Added `/dev:plan` Stage 1 §1e QA-check with skip prompt: when `qa/quality-gates.md` is missing at plan time, the user is asked whether to audit+set-up gates for the EXISTING codebase (Yes → `/qa:audit → /qa:plan → /qa:setup` inline) OR skip that and just plan the new feature (Skip → writes a `harness_status: Stack-Inferred` marker file with tier pools derived from stack detection). The NEW feature still gets 100% coverage at every applicable tier regardless of Yes/Skip; the Skip path only defers the existing-code audit. Rule 7 in `dev-stack-adaptive-implementation` sharpened to require every applicable tier per step. `/dev:build` Stage 0 QA gate has soft mode when `Stack-Inferred` (proceeds with a warning about un-audited existing coverage). Cascading rename in downstream files: `§7 Risks and rollback` → `§7 Risks and rollback`, `§9 Shared contract` → `§8 Shared contract`. Additive to on-disk `.jetrix/` layout — file names + folder structure unchanged.
>
> **2.3.11 (implementation.md — stack-agnostic 9-section frame, Shared contract at tail).** `implementation.md` section vocabulary made stack-agnostic so the frame serves REST + GraphQL + gRPC + queues; SQL + NoSQL + KV + object stores; web + mobile + CLI + service. Renames: `§3 API endpoints → §3 Operations exposed and consumed`, `§4 Database changes → §4 Stored data changes`, `§5 Frontend UI → §5 User-facing surfaces`. Structural moves: `§0 Shared contracts` → `§9 Shared contract` (moved to tail — plan opens with buildable work, closes with reference contract). Dropped in v2.3.10: `§1 Business flow` (duplicates Description tab), `§10 How to verify locally` (runbook belongs in a separate file, not the plan — `units/<repo>/pr-summary.md § ## How to verify` is restored as its own file with `doc_type: `pr-summary.md` § `## How to verify`, written by `/dev:build` Stage 11). Additions: `capabilities:` frontmatter field (controlled vocab: `exposes-contract`, `consumes-contract`, `owns-state`, `reads-state`, `renders-surface`, `bridges-integration`, `schedules-work`, `observes`) — Rule 11.15 uses it for cross-sub-task check; `§1` Build sequence table gains a `Files` column (drops free-form `Notes`); `§8` Risks and rollback closes with TWO explicit rollback levers (cheapest + full) per Rule 11.14. Mechanical pre-write markdown scan (Rule 11.5 upgraded) — halts on pipe-run-on tables, unfenced mermaid, unbalanced code fences, mixed bullets, missing blank lines. `§9` wire-only enforcement (Rule 11.3a) — halts on `req.`/`res.`/`result.response`/`ctx.`/`.headers[`/runtime-accessor paths anywhere in `## 9. Shared contract`. Additive to on-disk `.jetrix/` layout — file names + folder structure unchanged.
>
> **2.3.1 (/dev:plan stage reorder — analysis before compose).** The `/dev:plan` stage order was reordered so `implementation.md` is written ONCE with all sections filled in, instead of being half-baked at Stage 2 and appended to at Stage 3. New order: Stage 1 (code-context readiness — unchanged) → Stage 2 (PER-TASK ANALYSIS — was Stage 3 — writes intermediate scratchpad `units/<repo>/analysis.md`, not `implementation.md`) → Stage 3 (BLOCKER DETECTION — was Stage 3.5 — reads scratchpad, halts on OPEN blockers) → Stage 4 (COMPOSE + MC PUSH — was Stage 2 — `tl-feature-compose` reads scratchpad + TL context graph, writes ALL 10 sections of `implementation.md` in ONE pass, pushes to MC). Stage 4 REFUSES to run if the scratchpad is missing or blockers OPEN — no half-baked implementation.md, no partial MC push. Blocker fold on `--resume` now updates the SCRATCHPAD (not implementation.md) so Stage 4 composes with resolutions baked in. `tl-feature-compose` mode names updated: `narrative → description` (professional 6-section format for MC Description tab), `detailed → implementation` (10-section single source of truth). Every stage logs skill invocations to `status.md` § `## Run history` for verification. Additive-safe: parent-alone tasks use bare filenames (`units/<repo>/analysis.md`, `units/<repo>/plan-blockers.md`); split tasks use repo-slug prefix (`units/backend/analysis.md`, etc.).
>
> **2.3 (flat sub-task tabs + flat dev/ + single implementation source of truth — breaking).** File structure simplified per user's design intent. Under each `<feature-slug>/` (parent-alone) or each `<feature-slug>/units/<repo>/` (sub-task), MC-facing content is now **3 flat files**: `description.md` (→ MC Description tab), `implementation.md` (→ MC Implementation tab — SINGLE SOURCE OF TRUTH with 10 sections: business flow, build sequence, impacted components, API endpoints, database, frontend UI, touch points, test strategy, risks + rollback, how to verify locally), and `status.md` (MC-mirrored + local loop state — absorbs the retired `delivery-status.md`). **All local audit lives under ONE FLAT `dev/` folder at feature root** — `features/<slug>/dev/`. **NO nested `units/` folder inside `dev/`** — per-sub-task audit files use repo-slug PREFIX in the filename (e.g. `units/backend/plan-blockers.md`, `dev/frontend-analysis.md`). Two folders with the same name (`units/` at feature root AND `units/` inside `dev/`) is a mistake, not a design. **No nested `dev/` inside sub-task roots** either — sub-task folders hold only the 3 MC-facing files. New per-feature file `units/<repo>/analysis.md` (parent-alone) or `dev/<repo>-analysis.md` (per sub-task) — the ID cross-reference map (AC ↔ BR ↔ EP ↔ implementation-step ↔ test ↔ PB ↔ DEC), local-only. **Retired doc_types:** `dev-plan`, `impacted-components`, `delivery-status`, `subtask-description` (folded into `description`), `subtask-implementation` (folded into `implementation`), `subtask-status` (folded into `status`), `pr-summary.md` § `## How to verify` (folded into `implementation.md § 10`). **Retired files/paths:** `dev/dev-plan.md`, `dev/impacted-components.md`, `dev/delivery-status.md`, `units/<repo>/pr-summary.md § ## How to verify`, `units/<repo>/dev/*` (nested dev/ inside sub-task), `dev/units/<repo>/*` (nested subtask/ inside dev/ — replaced by flat repo-prefix filenames), `units/task-decision.md` (moved to `status.md § ## Run history`), `tl-plan.md` for parent-alone (split rollup still uses `tl-plan.md`). Backward compatibility: migration handled by `/jetrix:init` when it detects v2.2 layout on disk.
>
> **2.2 (plan-time blocker resolution — additive).** Added the plan-time blocker resolution loop so `/dev:build` never has to make build-time decisions. New per-task file `units/<repo>/plan-blockers.md` (`doc_type: plan-blockers`) captures decisions the user must make BEFORE build starts — missing integration contracts, undecided auth models, ambiguous schemas, unknown config, unclear business rule edge cases. `/dev:plan` Stage 3 detects them from 5 sources (`tl-plan.md` `[HELD]` markers, BA `dependencies.md` § `## Open questions` "Blocks build" rows, `integrations.md` unresolved entries, `system-landscape.md` gaps, `implementation.md § 3 Impacted components` `unknown` entries). User fills `Resolution:` per blocker → `/dev:plan --resume` deterministically folds resolutions into `implementation.md` and logs each as a `DEC-###`. New state `BLOCKED_ON_PLAN` (distinct from execution-time `BLOCKED`) — both map to MC `blocked`. New ID prefix `PB-###` (Plan Blocker, sequential per task). `/dev:build` Stage 0 refuses to run if `plan-blockers.md` `status:` is `OPEN` or `RESOLVING`. Additive: features whose plan is already fully-decidable never get a `plan-blockers.md` file.
>
> **2.1 (sub-task delivery layer — additive).** Added the sub-task tree under each feature: `features/<slug>/units/<repo>/` holds one sub-task per involved repo when `/dev:plan` decides to split a multi-repo feature. Each sub-task's tab files (`description.md`, `implementation.md`, `status.md`) map 1:1 to MC's 4-tab sub-task schema (`taskType: subtask`; the `acceptanceCriteria` and `testScenarios` tabs stay empty on MC — validation reads parent). Dev artifacts for each sub-task live under `units/<repo>/dev/`. New `doc_type`s: `subtask-description`, `subtask-implementation`, `subtask-status`, `## Run history`, `task-decision`. `/dev:plan` batch runs write summaries under `.jetrix/plan-runs/<ts>.md`. Reverse mapping (MC metadata → local layout) uses `metadata.subtaskNumber` + `metadata.subtaskRepo` on each sub-task so `/jetrix:pull scope` can reconstruct the tree cold. Additive — single-repo and bug/story features never get a `units/` folder and are unaffected.
>
> **2.4 (one dev layout, repo-keyed QA).** Dev had three shapes on disk — feature-one-repo, feature-many-repos,
> direct — and that difference forced a branch into every command. **`units/<repo>/` now exists always, including
> at N=1**, because N=1 is a fan-out of one rather than a special case; the word is *unit* and not *subtask*
> because at N=1 Mission Control has only the parent, so no sub-task exists and the folder name would be a lie.
> That lie is what carried two layouts. The `dev/` folder goes — its only job was separating pushed files from
> local audit, but the push maps each tab to a named file and never globbed the folder, so it organised without
> ever enforcing. The `<repo>-` filename prefix goes with it: 22 prefixed names on a two-repo feature become one
> name each, inside the unit that owns them. Sixteen audit files become six: the run journals and
> `acceptance-map` fold into `status.md` (which the contract already declared holds *run history* and an
> *acceptance status table*), the four findings files into `findings.md`, and `local-runbook.md` into
> `pr-summary.md` § `## How to verify`, which sends it to the reviewer who needs it. **`findings.md` stays a
> file because it is the fix loop's input** — Stage 6 reads each finding, re-runs the originating stage and
> rewrites it, and Stage 8 refuses to push without the resulting trace. `traceability.md` is removed outright:
> a full schema with no writer and no reader. 19 files → 8 on one repo, 38 → 17 on two, 17 → 9 direct.
>
> **QA's `quality-gates.md` is one file with a `## <repo>` section each.** It was one workspace file written once
> per repo, so a second `/qa:setup` destroyed the first and `/dev:build` then ran `npm test` in a Python repo —
> while Stage 4's own purpose line said *"the target repo"*. Frontmatter is now a map keyed by repo. Nine QA paths
> become three: `test-setup-plan` + `setup-log` + `escalations/` → `<repo>-setup.md` (§ Plan, § Run history);
> `testing-conventions.md` → `quality-gates.md § <repo> → ## Conventions`, where it finally gets a consumer;
> `health/` → `§ ## History`; `decisions.md` → `shared-context/decision-log.md`; the audit trio → one
> `qa/reviews/<repo>-audit-<ts>.html` with a third **Evidence** tab recording every command run and its exit
> code — because an audit once scored a runner 8/10 without running it while seven tests were failing. A
> dimension with no recorded command now reports `not-measured`, never a number.

> **2.1 (requirement-centric workspace layout).** `ba/` becomes `requirements/<slug>/`, so a workspace holds
> many requirements instead of one that had to be overwritten to start the next. Anything project-wide moves up to
> `shared-context/`: `data.md` and `integrations.md` (entities and integrations belong to the system, and
> `tl-feature-planning` cites `DATA-###` when minting `ENT-` units). `features/` moves under its requirement and
> `initiative=` retires — the requirement slug is the folder that label stood in for. Four files merge into two:
> `sources.md` + `sources.md` (Status: Needs User Guidance) → `sources.md`, and `logs/clarifications` +
> `logs/contradictions` + `registers/assumptions` → `ledger.md`, keyed by `kind`. `client-questions.md` and
> `dependencies.md` § `## Open questions` become rendered tabs of the review report; `logs/changes.md` becomes its “Since the last
> round” section; `intake-runs/` becomes the Source coverage block in `scope.html`. The `tl/` folder goes and
> `code-map-registry.md` sits at the `.jetrix/` root with the rest of the wiring. `/jetrix:clear <path>` removes a
> finished requirement, and its `cache/sync-state.json` rows with it.

> **2.0 (role-centric workspace layout).** Major rework of the workspace tree — the `<slug>/` folder wrapper inside `.jetrix/` is retired (a workspace binds one Solution; the slug lives in `project.json`). Every path drops two segments. Role folders drop the `-output` suffix (`ba/`, `tl/`, `qa/`, `doc/`); `shared-context/` keeps its name and simply moves up out of `<slug>/`. `context/features/` is promoted to `features/` at the top level (features are a deliverable, not code context). Workspace-level `context/frontend|backend|database|project/` folders are deleted — that graph lives per-repo at `<repo>/context/code-context/` (Model B, unchanged from 1.3). BA registers are grouped under `requirements/<slug>/registers/`; BA logs under `ba/logs/`; QA under `qa/{audits,health,escalations}/`; DOC under `doc/{decks,walkthroughs,workflows,boards}/`. `/jetrix:init §3` performs a soft, idempotent migration from v1 to v2 layouts on first run.
>
> **1.3 (in-repo code context).** Added the brownfield **code-context** layer: a committed `<repo>/context/code-context/` tree written by the TL's `tl-code-map` **inside the mapped repository** — a `context/` folder at the repo root with `code-context/` inside it (not in the workspace, and not inside `.jetrix/`, which is gitignored), holding one markdown unit per page, endpoint and database object, grouped by business domain — with database objects grouped on disk by **kind** (`tables/ collections/ views/ procedures/ functions/ triggers/`) — plus **semantic layer indexes** (a `## Domain Map` in prose alongside the unit table) that exist so a consumer can pick the right file without opening any other. New doc_types: `code-context-readme`, `code-context-index`, `code-map-registry`, `map-coverage`; the layer indexes keep the existing `page-index` / `endpoint-index` / `entity-index` doc_types so current consumers keep working by doc_type rather than filename. Workspace-level pointer file: `code-map-registry.md` (v2.0 path; was `context/code-map-registry.md` in v1.3). IDs are unchanged. Additive: greenfield projects that never run `/tl:code-map` are unaffected.
>
> **1.2 (eval layer).** Added the applied-AI **eval** layer: the `EVAL-<AREA>-NN` id (§3) and the *applied-AI / LLM feature* classification (§5) that gates it. Eval units live per-feature under `features/<slug>/evals/` (v2.0 path; was `context/evals/<feature-slug>/` in v1.2). The TL's `tl-feature-planning` **designs** eval units for AI-bearing features, the dev `feature-delivery-loop` **runs and inspects** them, and QA's harness hosts them — see the core **`eval-engineering`** skill. Additive — deterministic features are unaffected.
>
> **1.1 (use-case model).** Made **use cases** first-class: added the `<MODULE>-UC-NN` id and `use-case-register.md`; the scope §3.x now carries a **§3.x.3 Master Flow** and a **§3.x.4 Use Cases** layer (renumbered through §3.x.11); added the **Mermaid diagram convention** (§8) where Mermaid is the living source and the Doc Agent's branded SVG swimlane is its projection. The change is **additive** — a `schema_version: 1.1` document remains readable; new documents are written at `1.1`.

---

## 1. Workspace layout (v2.1 — requirement-centric)

A workspace is bound to **one** project on **one** tracker — a Jetrix Solution, a Jira project, a ClickUp
Folder, whatever `/jetrix:init` bound. It holds **as many requirements as you like**. Everything lives at the
`.jetrix/` root with no `<slug>/` wrapper; the whole folder is gitignored and is a local working copy of
tracker state. Agents read and write **only** at these paths.

**Two tiers, and the line between them is load-bearing.** `shared-context/` is the project — terms, people,
systems, entities, integrations, decisions. It outlives every requirement. `requirements/<slug>/` is one
requirement: its scope, its sources, its questions, its features. A second requirement costs a folder.

Before this, a workspace held one requirement and the only way to start a second was
`/ba:scope mode=full-refresh`, which backs up the previous `ba/` and overwrites — a backup, not a second
requirement. Anything project-wide that lived under `ba/` moved up, because a second requirement touching the
same customer table is discovering more of the same entity, not a new one.

```text
<workspace>/
└── .jetrix/                              # gitignored (whole folder)
    ├── project.json                      # tracker binding — /jetrix:init writes it
    ├── connection-map.md                 # cross-repo wiring: transport per pair, auth boundary,
    │                                     # external integrations. From the Jetrix portal's Build map,
    │                                     # or asked directly at /jetrix:init §13 on any other tracker.
    │                                     # Read before any cross-repo integration is planned.
    ├── code-map-registry.md              # one row per mapped repo — /tl:code-map writes it.
    │                                     # At the root with the rest of the wiring; there is no tl/ folder.
    ├── cache/
    │   ├── repolocation.json             # per-app local repo paths
    │   └── sync-state.json               # drift hashes for /jetrix:push and /jetrix:pull
    │
    ├── shared-context/                   # PROJECT LEVEL — outlives every requirement
    │   ├── decision-log.md               # append-only DEC-### from every role
    │   ├── glossary.md                   # terms are project-wide
    │   ├── stakeholder-map.md            # PEOPLE — who can answer a ledger row.
    │   │                                 # Name · Role · Team · Involvement · Source.
    │   │                                 # Not scope §5, which is SYSTEM roles and permissions.
    │   ├── system-landscape.md           # systems and their integration touchpoints
    │   ├── data.md                       # DATA-### — entities belong to the system, not one requirement.
    │   │                                 # tl-feature-planning cites these when minting ENT- units, so a
    │   │                                 # per-requirement DATA-001 meaning two things would break that link.
    │   ├── integrations.md               # INT-### — same reasoning; /dev:plan blocker-detection reads it
    │   └── coding-standards.md           # /tl:code-map writes it; /dev:build Stage 0 gates on it
    │
    ├── requirements/                     # STAGE 01 — one folder per requirement, n per workspace
    │   └── <requirement-slug>/           # lowercase-kebab, e.g. shift-timesheet
    │       ├── scope.md                  # THE source — the living scope document
    │       ├── scope.html                # rendered by render-scope.js; published where the
    │       │                             # tracker supports it, local otherwise (capabilities.documents)
    │       ├── sources.md                # SRC-### registry — was sources.md +
    │       │                             # indexing-assistance-needed.md. Source · Category · Mode ·
    │       │                             # Why · Summary · Status · contentHash. "Needs User Guidance"
    │       │                             # is a Status value, so the assistance list is a filter.
    │       ├── ledger.md                 # CLR · CON · ASM in one table — was logs/clarifications.md +
    │       │                             # logs/contradictions.md + registers/assumptions.md.
    │       │                             # ID · Kind · Status · Topic · Statement · Already checked ·
    │       │                             # Answer · Owner. RAID renders as a filter on Kind.
    │       ├── artifacts/                # generated summaries — categories created on demand
    │       │   └── <category>/<name>.summary.md
    │       ├── registers/                # derived: true — PROJECTIONS of scope.md, rebuilt every run,
    │       │   │                         # never hand-edited. They exist because six consumers cannot
    │       │   │                         # read a narrative scope.
    │       │   ├── requirements.md       # from scope §3.x.5
    │       │   ├── use-cases.md          # from §3.x.4 — ba-feature-breakdown decomposes from these
    │       │   ├── workflows.md          # from §3.x.3 — forward planning reads it
    │       │   ├── business-rules.md     # from §3.x
    │       │   └── examples.md           # from §3.x.4 — ba-scope-review validates against these
    │       ├── reviews/                  # /ba:review — LOCAL ONLY, never published
    │       │   ├── review-<ts>.html      # carries its own data at <script id="review-data">
    │       │   └── review-<ts>-responses.md   # written by the page's Save, read by /ba:resolve
    │       └── features/                 # BA authors, TL enriches, Dev delivers
    │           └── <feature-slug>/
                ├── feature.md            # BA — Description tab source (workflow folded in)
                ├── acceptance-criteria.md
                ├── business-rules.md
                ├── nfrs.md
                ├── test-scenarios.md
                ├── dependencies.md       # BA — open questions folded in
                ├── status.md             # BA seeds it; dev drives it
                │
                │                         # ── dev adds, on the same feature folder ──
                ├── implementation.md     # parent Implementation tab — ONLY when N > 1.
                │                         # tl-feature-compose ROLLUP mode: names each unit, its
                │                         # sequence, cross-unit dependencies and touch points.
                │                         # It never repeats a unit's own plan.
                ├── status.md             # DERIVED, never written directly: all units done → done;
                │                         # any blocked → blocked; any agentExecuting or
                │                         # else PLANNED. Carries a per-unit table (repo · state ·
                │                         # branch · MC number) — which is what lets the LAST unit to
                │                         # land close the cross-unit `deferred-to-e2e` rows.
                │                         # ## Run history — the plan journal + the split decision.
                ├── discussion.md         # PULL-ONLY. ## Comments (nested by parentCommentId,
                │                         # soft-deleted filtered, carries unresolved_count) +
                │                         # ## Attachments (the manifest). Unresolved → PB-### via
                │                         # blocker detection Source 6.
                ├── attachments/          # PULL-ONLY — the files themselves
                ├── evals/                # TL — applied-AI features only (EVAL-<AREA>-NN)
                └── units/                # ONE FOLDER PER REPO — always, including when there is
                    │                     # one. "unit" rather than "subtask" because at N=1 MC has
                    │                     # only the parent, so no sub-task exists and the folder
                    │                     # name would be a lie. That lie is what forced two layouts.
                    └── <repo>/           # matches a key in cache/repolocation.json
                        │                 # ONE REPO = ONE UNIT = ONE BRANCH = ONE PR. That is why
                        │                 # the axis is the repo and not the use case: a use case
                        │                 # spans repos, and a sub-task cannot have two branches.
                        │
                        │                 # ── pushed to the tracker ──
                        ├── implementation.md   # → Implementation tab. Eight stack-agnostic
                        │                     # sections; §1 Build sequence carries real file
                        │                     # paths, unit ids (EP-/PAGE-/ENT-) and the parent
                        │                     # AC/BR/TS each step Satisfies. The only tab that
                        │                     # keeps paths and ids — it is what the build follows.
                        ├── description.md      # → Description tab. ONLY when N > 1.
                        │                     # One to two paragraphs of continuous prose: no
                        │                     # headings, bullets, tables, code fences, HTTP codes
                        │                     # or field lists. Business vocabulary from the
                        │                     # parent's BA files.
                        ├── status.md           # state · history · proof. Frontmatter: status · phase ·
                        │                     # branch · owner_lock ·
                        │                     # ready_for_dev_build · ready_for_dev_commit ·
                        │                     # blocker_ids · status_pushed · tests_only.
                        │                     # ## Run history — one entry per stage, the build
                        │                     # verdict, base branch + SHA, the semantic-merge
                        │                     # trace Stage 8 hard-gates on, the PR url, and any
                        │                     # BLOCKED entry with its reason.
                        │                     # ## Acceptance — Kind | ID | Assertion | Evidence |
                        │                     # Result | Notes, one row per parent AC/BR/NFR/TS.
                        │
                        │                 # ── local ──
                        ├── analysis.md         # /dev:plan Stage 2. Stage 4 compose REFUSES to run
                        │                     # without it. Blocks: build_sequence · impact_matrix
                        │                     # (N/A written explicitly, never omitted) ·
                        │                     # risks_and_rollback. Blocker resolutions fold back
                        │                     # into this file, not into the plan.
                        ├── findings.md         # FIX-LOOP STATE — read, not archived.
                        │                     # ## Security — build (Critical-blocking) ·
                        │                     # ## Security — commit (Critical + High) ·
                        │                     # ## Code review (7 dimensions × 4 severities) ·
                        │                     # ## Context merge.
                        │                     # Every finding: id · severity · origin stage ·
                        │                     # status (open → fixed → escalated) · attempts_used,
                        │                     # bounded at 3 focused fixes and 2 broad re-runs.
                        │                     # Each unit runs its OWN loop with its own bounds,
                        │                     # which is why this is per-unit and not per-task.
                        ├── pr-summary.md       # = the PR body, passed verbatim to gh pr create.
                        │                     # What shipped · findings that did NOT block, as
                        │                     # follow-ups · ## How to verify (env, services,
                        │                     # commands, expected output) · anything checked
                        │                     # manually rather than by tool.
                        ├── discussion.md       # PULL-ONLY — this unit's OWN MC thread. A
                        │                     # clarification left on the backend sub-task is
                        │                     # missed when only the parent is fetched.
                        ├── attachments/        # PULL-ONLY
                        ├── plan-blockers.md    # CONDITIONAL · a human fills Resolution:
                        └── merge-conflicts.md  # CONDITIONAL · a human settles a Stage 7 halt


    ├── tl-reviews/                       # /dev:review + /tl:maturity output pages.
    │   ├── spec-review-<ts>.html   # No tl/ folder: /tl:code-map is the only TL command a
    │   └── maturity-<ts>.html      # user types, and its registry is wiring, so it sits at root.
    │
    ├── qa/                               # STAGE 03 — Quality Assurance
    │   ├── quality-gates.md              # THE test contract — ONE file whatever the repo count.
    │   │                                 # Frontmatter is a MAP KEYED BY REPO, not singular keys:
    │   │                                 #   repos:
    │   │                                 #     backend:  { harness_status: Active, baseline_status: Met,
    │   │                                 #                 coverage_floor: 70, source_audit: <ts> }
    │   │                                 #     frontend: { harness_status: Stack-Inferred, coverage_floor: 60 }
    │   │                                 # One `## <repo>` section each, holding:
    │   │                                 #   ## Gates        id · Required/Required*/Optional · the
    │   │                                 #                   EXACT command · threshold · Status
    │   │                                 #   ## Green smoke  the sequence proving the harness runs
    │   │                                 #   ## Conventions  how THIS repo writes tests — read by
    │   │                                 #                   dev-stack-adaptive-implementation
    │   │                                 #   ## History      dated /qa:health results and drift
    │   │                                 # /qa:setup repo=frontend rewrites ONLY `## frontend` and
    │   │                                 # cannot touch `## backend`. A single-repo workspace has one
    │   │                                 # section, so there is no special case.
    │   ├── <repo>-setup.md               # the build record, one per repo.
    │   │                                 #   ## Plan         written by /qa:plan from the APPROVED
    │   │                                 #                   findings only, cheapest-first
    │   │                                 #   ## Run history  written by /qa:setup: per-step attempt,
    │   │                                 #                   verification, failure, next action; the
    │   │                                 #                   green-smoke result; any escalation with
    │   │                                 #                   its trade-off named.
    │   │                                 # Bounds: 3 focused fixes per failing step, 2 broad smoke
    │   │                                 # re-runs, 0 strategy guesses.
    │   └── reviews/
    │       ├── <repo>-audit-<ts>.md      # the durable artifact. TWO files per audit, not three —
    │       │                             # the old .json sidecar is gone; see the .html below.
    │       └── <repo>-audit-<ts>.html    # the decision surface — three tabs.
    │                                     # Scorecard · Findings (you set Adopt/Skip/Defer) ·
    │                                     # EVIDENCE — every command the audit ran and its exit code.
    │                                     # Carries its own JSON at <script id="audit-data">, so
    │                                     # /qa:plan reads the round from the page. Rounds accumulate.
    │
    ├── doc/                              # STAGE 05 — Documentation deliverables, grouped by artifact kind
    │   ├── decks/                        # /doc:deck, /doc:proposal — pptx
    │   │   └── deck-<name>-<ts>.pptx
    │   ├── walkthroughs/                 # /doc:walkthrough — html
    │   │   └── walkthrough-<topic>-<ts>.html
    │   ├── workflows/                    # /doc:workflow — html
    │   │   └── workflow-<topic>-<ts>.html
    │   └── boards/                       # /doc:magic-board — html
    │       └── board-<topic>-<ts>.html
    │
    ├── tasks/                            # work that is not a requirement — a bug, a one-off ticket
    │   └── <slug>/                       # THE SAME SHAPE as a feature. That is the point of
    │       │                             # units/: direct execution stopped being a third layout.
    │       ├── <slug>.md                 # the ticket itself (round-trips to the tracker)
    │       ├── status.md                 # derived from the units, as on a feature
    │       ├── discussion.md             # PULL-ONLY — § Comments + § Attachments
    │       ├── attachments/              # PULL-ONLY
    │       └── units/<repo>/             # identical to a feature's unit — implementation.md,
    │                                     # status.md, analysis.md, findings.md, pr-summary.md,
    │                                     # discussion.md. One implementation.md, composed once:
    │                                     # pushed from here and built from here.
    │
    └── plan-runs/                        # /dev:plan batch summaries (multi-target runs)
        └── <ts>.md                       # targets, decisions, outcomes. At the root rather than
                                          # under a dev/ folder — there is no dev/ folder.
```

### 1.b The per-repo code-context tree (Model B — TL owns the graph, but it lives with the code)

The **as-built code graph** (pages, endpoints, entities) does NOT live under `.jetrix/`. Each linked app repo carries its own `<repo>/context/code-context/` tree, committed with the code. Written by `/tl:code-map` (brownfield reverse-map) and extended by `tl-feature-planning` (internal) (forward planning of new units), read by `/dev:plan` (v2.3 Stage 2 analysis + Stage 4 compose), `/dev:build` (Stage 10 `designed → implemented` flip), `/dev:commit` (Stage 7 semantic-context-merge via `tl-semantic-context-merge`), and doc/qa consumers. Structure:

```text
<repo>/context/code-context/
├── README.md
├── code-context-index.md
├── map-coverage.md
├── backend/
│   ├── backend-index.md                  # endpoint-index doc_type
│   ├── _overview.md
│   └── domains/<domain>/endpoints/<slug>.md      # EP-<AREA>-NN
├── frontend/
│   ├── frontend-index.md                 # page-index doc_type
│   ├── _overview.md
│   └── pages/<area>/<slug>.md            # PAGE-<AREA>-NN
└── database/
    ├── database-index.md                 # entity-index doc_type
    ├── _overview.md
    └── {tables,collections,views,procedures,functions,triggers}/<slug>.md    # ENT-<AREA>-NN
```

**An index's header count is derived, never carried forward.** Recompute it from the rows the index
now holds, every time you write one. Four things write these files — `tl-code-map`,
`tl-feature-planning`, `/dev:build` Stage 10 and `tl-semantic-context-merge` — and a count that only
the first of them sets is wrong from the second write onward. One real backend index opened with
*"15 endpoints across 4 domains"* while listing 82, because the map wrote 15 and planning added 67
without touching the line. That header is the first thing a reader uses to judge whether the map is
worth opening.

The workspace `.jetrix/code-map-registry.md` is the one workspace-level TL file — it lists each mapped repo, its context root, its indexes and its area tokens, so `tl-feature-planning` (internal) can find as-built units to reuse and cross-repo links resolve. Unit IDs and match keys are identical to forward-planned ones; reverse-mapped units add `origin: reverse-mapped`, `mapped_from`, `mapped_from_commit`, and `map_confidence`. Nothing sensitive is written into this tree — it is committed and shared.

### 1.c Jetrix binding — `.jetrix/` (owned by the **jetrix** plugin)

Jetrix is the **single source of truth** for all project context (glossary, scope, registers, feature breakdown). The local `.jetrix/` folder is a disposable **working copy** — the ENTIRE folder is gitignored, including `project.json`, the cache, and every role subfolder. Binding a workspace and syncing it are owned by the separate **`jetrix`** plugin — read its **`jetrix-sync`** skill for the full contract: `.jetrix/project.json` (regenerable identity + app/environment→branch wiring — no secrets), the cache, and the pull/push model. Commands: `/jetrix:init` (bind + run the v1→v2 migration on old workspaces), `/jetrix:pull` (refresh the cache from Jetrix, incremental), `/jetrix:push` (publish local work back as structured records — upsert by stable id, transactional, pull-before-push). The canonical form in Jetrix is **structured records** (the IDs in §3); `scope.md` and the branded `.docx` are projections rendered from them.

#### The tracker block — which tool holds the tasks

`project.json` carries a `tracker` block. **Every consumer branches on its `capabilities`, never on `provider`.** Jetrix is the default; any tool whose MCP the user has registered works the same way.

```yaml
tracker:
  provider:     jetrix            # jetrix | jira | clickup | azure | <any name>
  mcp:          project-mcp       # the registered server name — recorded, never assumed
  project_ref:  <id or key>       # the LOCKED project/folder. We select it, never create it.
  project_path: <Acme / Delivery / Supplier Platform>   # what summaries print
  container_ref:  <id or key>     # WHERE ISSUES ARE CREATED, under project_ref.
  container_path: <… / Delivery OS>                     # what summaries print
  container_kind: list            # list | epic | none  (none → == project_ref)
  capabilities:
    apps:       true              # false → repos + dev branch asked at bind
    tabs:       7                 # 1 → the six BA files + Implementation as ## sections in one body
    documents:  scope-mcp         # none → scope.html stays local
  mapping:      null              # ten keys, null where unsupported, confirmed once:
                                  # browse[] is ORDERED — "project" is not one level in
                                  # every tool. ClickUp: Workspace → Space → Folder → List.
                                  # A flat tracker is a one-element list.
                                  # resolve_project · resolve_container · create_container
                                  # create_issue · update_issue · read_issue
                                  # child_issues · comments · attachments · set_status · put_document
  status_map:   null              # every local state in §5 except MERGE_CONFLICT → that tool's states

```

**Two levels, not one — the project is locked, the container is where issues land.** `browse[]` ends at the thing that already exists and we never create: a Jetrix Solution, a Jira project, a ClickUp Folder. Issues are not created there. They are created in a **container** under it, and `container_ref` is the only ref any push or pull targets — `project_ref` is for display and for resolving the container, nothing else.

| | project_ref | container_ref | `container_kind` |
|---|---|---|---|
| Jetrix | Solution | an MC List named after `solutionSlug` | `list` |
| ClickUp | Folder (or Space) | a **List** — mandatory, a task cannot exist outside one | `list` |
| Jira | project `SUP` | an epic, **or the project itself** | `epic` / `none` |
| Azure | project | an Area Path, or a parent work item | `list` / `none` |

`container_kind: none` means that tracker creates issues directly in the project; `container_ref` is then set equal to `project_ref` rather than left null, so consumers never branch. **A null `container_ref` is a broken bind** — halt and point at `/jetrix:init refresh`, never fall back to `project_ref` silently. That fallback is exactly how a workspace quietly files thirty features into the wrong place.

One container per workspace, named after the workspace, is the default on every tracker — it is what Jetrix already does and it keeps the mapping back from issue to workspace obvious. Grouping *within* it is the tracker's own job (an initiative label, a sprint), not a second container.

**The one-body projection — `capabilities.tabs: 1`.** Mission Control has seven tab fields; nothing else does. Where a tracker has one description field, push concatenates the local files under fixed headings and pull splits them back out. **Push and pull are inverses, so the heading set is the contract — and it is the one already shipped**, written by `references/pull/list.md` and parsed by `references/push/task.md` §2:

```markdown
<!-- delivery-os:v1 FEAT-SUP-001 -->

## Description
## Business Rules
## Acceptance Criteria
## NFRs
## Test Scenarios
## Assumptions / Dependencies
## Implementation
```

**Emit this order and this spelling; accept more.** `push/task.md` §2 holds the alias table (`Dependencies`, `Test Cases`, `Non-Functional Requirements`, …) and is the only parser — a tracker body is written by hand as often as not. A section whose field is empty is **omitted**, heading and all, rather than left blank.

Three rules keep the round-trip safe:

- **The marker is the gate.** No `<!-- delivery-os:v1 … -->` and pull does not split at all — the body was written by hand in the tracker, so it becomes Description verbatim and the run says so. Never guess at splitting someone's prose.
- **An unrecognised `##` heading halts the pull.** It is not dropped. A heading someone added in the tracker is content, and silently discarding it is the worst outcome available.
- **A child issue carries only `## Description` and `## Implementation`.** Acceptance and Test Scenarios live on the parent, exactly as they do on Mission Control sub-tasks.

`## Implementation` runs long — 32k characters is normal. Where a tracker refuses a body that size, attach `implementation.md` and leave a pointer line under the heading rather than truncating a build spec.

**Addressing a ticket.** Accept whatever that tracker calls it, **including a pasted URL** — a URL is what someone actually has in hand. Jetrix takes `Task-11` / `Feature-4` / `FEAT-SUP-001` / the Mongo id; Jira takes `SUP-123` or its browse URL; ClickUp takes the task id or its URL. Resolve through `mapping.read_issue`.

**Matching a ticket back to a local folder** needs its own mechanism, because only Mission Control has `metadata.externalId`. Jira custom-field ids vary per instance and labels are neither universal nor long enough, so identity travels in the one field every tracker has — the body:

```
<!-- delivery-os:v1 FEAT-SUP-001 -->

## Description
…
```

Paired with `tracker_issue_ref` in the local `status.md`, the link is two-way: local → tracker by the ref, tracker → local by the marker. **An issue with no marker was filed by hand in the tracker** — treat it as the non-feature track, never as a feature whose folder went missing.

Reports follow `capabilities.documents`: `scope-mcp` publishes `scope.html` to Dashboard → Reports and returns a stable share link; `none` keeps it local. There is no separate reports binding.

`mapping` and `status_map` are `null` on Jetrix (its tools are fixed) and filled on any other tracker by the discovery step at `/jetrix:init` §4. A refresh preserves both — they are confirmed by a human once and never re-derived.

### Source handling — reference, never copy or move
Original source files (local folders/files, Google Drive, etc.) **stay where they are**. The workspace never copies, moves, or deletes a user's originals. Intake only:
1. **records** each source in `sources.md` (its real location + classification + status), and
2. **generates** a normalized markdown summary under `artifacts/<category>/` for eligible sources.
So the workspace holds only the **index + generated summaries** — it is a knowledge layer *over* the user's files, not a copy of them.

### `requirements/<slug>/sources.md` is the single source registry
It is **agent-maintained** (the user can still hand-edit it) and folds together what were previously separate artifact-map / artifact-ledger / source-classification files: each source's description, original location, detected category, usage mode (the classification + reason), summary path, content hash, and status all live in one registry. Add sources conversationally via `/ba:scope add "..."` — the agent classifies, summarizes, and registers them.

**Handoff rule:** an agent reads another agent's **published** files (`ba/`, `shared-context/`, `features/`); it never reaches into another agent's working notes. `shared-context/` and `requirements/<slug>/scope.md` are the primary handoff surfaces.

---

## 1.e Every HTML report is served, and both links are printed

A command that writes an HTML report **starts the server and prints a URL**. It does not print a path and tell
the user to open it.

```bash
node ${CLAUDE_PLUGIN_ROOT}/../delivery-os-core/scripts/serve-review.js <the report's folder>
```

Run it in the background as the last action. It picks a free port from 4100 and prints one
machine-readable line — `DELIVERY_OS_SERVE_READY http://127.0.0.1:<port>/`. **Read the port from that line**;
never assume 4100, because a second workspace already serving will have taken it.

**It does not open a browser, and must not be made to.** The run is usually still printing when the server
binds, and launching a browser there steals focus mid-summary — the report lands on top of the sentence
explaining it. Print the URL and let the reader choose the moment. (`--open` exists for anyone who wants
the opposite; no command passes it.)

Then close with both, in this order and this shape:

```
Report   http://127.0.0.1:<port>/<file>.html      ← open in your browser
         <workspace-relative path>/<file>.html    ← the file itself
```

**Both lines, every time.** The URL is for the person who wants to look at it now; the path is for the person
who wants to attach it, diff it, or find it again tomorrow. Printing only the path makes the reader do work the
command could have done; printing only the URL loses the report the moment the server stops.

**The server is plumbing. Start it and say nothing about it.** Print the two link lines and move on. It is
not running, it died, a previous one was killed, the port moved — none of that is the user’s business. They
ran a command about their scope; a paragraph about memory pressure and a raw `node` path is noise they did
not ask for and cannot act on usefully.

| | |
|---|---|
| It is not running | start it. Silently |
| An earlier one died | start another. Silently |
| It genuinely will not start | **one line**: what failed, and the local file path. Nothing else |

**Never hand the user a command to run that the run could have run itself**, and never one carrying an
absolute path with `..` in it. If a restart is needed, restart it.

**Only this script, ever.** Not `python -m http.server`, not `npx serve`, not any other static server. They
look like success — the page opens, the URL works — and they silently break Save, because a static server has
no `POST /save` and no `/__whoami` for the page to recognise it by. A real run did exactly this: a Python
server on :8765 served the report perfectly while every save fell through to a file dialog, and the page told
the user no review server was running, which was true and looked like a bug.

**If `serve-review.js` will not start, say so and print the local path.** A named failure the user can act on
beats a substitute that appears to work. Never improvise a different server to fill the gap.

**Why serve rather than double-click.** A `file://` page cannot fetch a sibling — an exported asset, the next
round's data, a POST back to save answers. One line removes a whole class of "it looks broken locally", and the
same script serves every report in the system.

**Where the report accepts input** — the scope review and the QA audit — serving is not optional: Save POSTs
back to this server, which writes the responses file into the folder and returns the path it wrote. Without it
Save degrades to a download and the user has to move the file by hand, which is the step people skip.

**Reuse a server that is already up.** If one is serving that folder from an earlier command in this session,
print its URL rather than starting a second on another port — two tabs on two ports is worse than one.

**If Node is missing or the server will not start**, say so in one line and print the path alone. A report
nobody can serve is still worth reading.

### 1.e.1 Placeholders in a line the user is meant to run

A next-step line is there to be copied. Two kinds of placeholder end up in one, and only one of them is
allowed to survive:

| Kind | Example | What to do |
|---|---|---|
| **The run knows it** | `<ts>` `<slug>` `<repo>` `<port>` `<task-ref>` after a target is resolved | **Fill it in.** The timestamp, the slug, the port are all in hand by the time the block prints |
| **The user would supply it** | `<ref>` `<target>` `<project-id>` before anything is bound | **Never print it bare.** Give a worked example, in the form that reader's tooling actually uses |

`/jetrix:pull task <ref>` is the second kind, and it reached a real user's screen exactly as written. "Ref"
is an argument name; it is not a thing anyone can type. The line should read `/jetrix:pull task PAY-412`,
with the tracker named — see `/jetrix:pull` § *Never print the word `<ref>` to a user*.

**An example is worth more than a syntax.** `/ba:scope add "requirements in ./client-docs"` teaches the shape
in one read; `[add "<sources>"]` teaches nothing and has to be decoded. Prefer a value from the run in
progress — a real task number the reader just saw beats any invented one.

**This rule is about printed blocks only.** A usage line in a readme, an `argument-hint`, or a syntax summary
is *describing* an argument, and placeholders are exactly right there. The test is whether the reader is
meant to run that line as it stands.

### 1.f Which commands a user is told to run

Some commands exist for an agent to invoke, not for a person to type. Suggesting one as a next step sends the
user to do a job the system was about to do itself.

| | |
|---|---|
| **The dev loop is three commands** | `/dev:plan` → `/dev:build` → `/dev:commit` |
| **Feature planning is a skill, not a command** | `/dev:plan` verifies the technical context graph and **auto-runs `tl-feature-planning` when it is missing**. There is no slash command for it. |

**A next-step block may only name a command that exists.** Never a skill (`tl-feature-planning`,
`tl-feature-compose`, `dev-stack-adaptive-implementation`), and never a retired one — `/tl:plan`,
`/tl:review`, `/tl:resolve`, `/tl:compose`, `/dev:validate`, `/dev:pr` and `/tl:map` were all real once and
all still appear in older prose. If a feature needs a graph, the step is `/dev:plan`; it builds the graph
itself.

The one TL command a user does type is **`/tl:code-map`**, and even that is usually raised by `/dev:plan` as a
`PB-###` blocker rather than suggested — it writes a committed tree into the product repo, which no summary
line should trigger by itself.

Naming a skill in prose is fine where the subject is what it does — *"`tl-feature-planning` reuses these
units"* — because that is an explanation, not an instruction. The rule is about next-step blocks.

## 2. Document frontmatter standard

**Every generated Markdown document** starts with YAML frontmatter so any consumer can validate compatibility before reading the body:

```yaml
---
doc_type: scope            # scope | requirement-register | use-case-register | glossary | run-summary | source-summary | intake-index | description | implementation | status | plan-run | analysis-scratchpad | task-decision | plan-blockers | traceability | `## Acceptance` table | build-run | commit-run | implementation-log | security-findings | code-review-findings | context-merge-log | merge-conflicts | escalation | task-comments | task-attachments | ...
schema_version: 1.3        # the contract version this file conforms to
produced_by: ba            # ba | doc | tl | qa | delivery-os
last_intake_run: run-003   # the run that last touched this file (omit if N/A)
status: Emerging           # see §5 maturity values
requirement: shift-timesheet  # REQUIRED on feature files — the requirement folder this feature belongs to.
                           # Replaces the retired `initiative:`; see §3.
generated_at: 2026-06-18   # ISO date of last write
---
```

A **normalized source summary** (`artifacts/<category>/<name>.summary.md`) carries extra provenance so a fact extracted from it traces all the way back to the untouched original:

```yaml
---
doc_type: source-summary
schema_version: 1.1
produced_by: ba
source_id: SRC-002              # matches the sources.md registry row
summary_of: "D:/acme/meetings/2026-06-12-kickoff.docx"   # the ORIGINAL location (path or Drive link), referenced not copied
source_hash: "sha256:…"         # so re-runs detect change
usage_mode: Deep Analysis
status: Processed
generated_at: 2026-06-18
---
```

A consuming agent that finds `schema_version` newer than it understands must **stop and warn** rather than guess — with one standing exception, because the contract has so far only ever grown: where a minor bump is declared **additive** in the version note above (1.1, 1.2 and 1.3 all are), a consumer written for an earlier minor may read the document, use the fields it knows, and ignore the rest. It must still warn if a *major* version is newer, or if a minor bump is not marked additive. Concretely: a `tl-feature-planning` (internal) written against 1.1 may read, reuse and extend a 1.3 `code-context/` unit — the sections it knows are present under their original headings — and should not refuse it.

### Sub-task frontmatter (written by `/dev:plan` when a feature is split)

Every file inside `features/<slug>/units/<repo>/` carries this frontmatter. The three tab files (`description.md`, `implementation.md`, `status.md`) share the identity fields; `doc_type` distinguishes each file. **Folder name = repo slug** (matches key in `.jetrix/cache/repolocation.json`); **execution sequence lives in frontmatter** (`subtask_number`), not the folder name.

```yaml
---
doc_type:                 description   # description | implementation | status   (v2.3 — subtask-* prefixes retired; distinguished by folder location)
schema_version:           1.0
produced_by:              dev
feature_id:               FEAT-SUP-001          # parent feature (matches parent feature.md)
parent_task_object_id:    6a61…                 # parent Task's Mongo _id in MC
parent_task_number:       Feature-4             # parent's MC display number
subtask_number:           1                     # 1..N execution sequence within parent
subtask_repo:             backend               # matches folder name + repolocation.json key
jetrix_subtask_object_id: 6b72…                 # this sub-task's Mongo _id (set after /jetrix:push)
jetrix_subtask_number:    Subtask-7             # MC display number (set after push)
composed_at:              2026-08-29T14:24:11Z
inputs_hash:              sha256:…              # hash of the compose inputs; used by idempotency check
---
```

`status.md` adds `status`, `phase`, `owner_lock`, and `branch` for the loop-state model (§5) — same fields the parent's `status.md` uses.

**MC-side reverse mapping** — the plugin sends this shape to `task-mcp.subtask_upsert_bundle`:

```json
{
  "metadata": {
    "externalId":       "FEAT-SUP-001-1",
    "parentExternalId": "FEAT-SUP-001",
    "subtaskNumber":    1,
    "subtaskRepo":      "backend",
    "source":           "ai",
    "aiGenerated":      true
  }
}
```

task-mcp **translates** this to MC's whitelisted metadata schema on the write path (MC only accepts `externalId` / `externalSlug` / `externalInitiative` / `externalUrl` / `source` / `aiGenerated` / `aiGeneratedAt`), then **reverses** the mapping in `subtask_list` so consumers read the same shape. Concretely:

| Plugin field | Write path | Read path (`subtask_list`) |
|---|---|---|
| `externalId` | → `metadata.externalId` (whitelisted) | ← `metadata.externalId` |
| `unitRepo` | → `metadata.externalSlug` (whitelisted) | ← derived from `metadata.externalSlug` |
| `subtaskNumber` | dropped (not stored) | ← derived from sort position (`taskNumber` ascending, index+1) |
| `parentExternalId` | dropped (parent link is URL path `:taskId`) | ← derived from parent's `metadata.externalId` (single MC lookup per listing) |

This metadata is what `/jetrix:pull scope` reads to reconstruct the local `units/<repo>/` tree from MC on a cold clone — task-mcp's read-side derivation preserves the round-trip.

---

### 1.d Resolving which requirement

Every BA command, and `/jetrix:push`/`/jetrix:pull`, operates **inside one requirement**. They resolve it the
same way, in this order, and the order is what keeps the single-requirement case free of ceremony:

1. **`requirement=<slug>` was passed** — use it. An unknown slug stops with the list of real ones; never
   create a requirement to satisfy a typo.
2. **Exactly one `requirements/*/` exists** — use it, silently. The common case must not cost a question.
3. **The path argument names one** — `requirements/shift-timesheet/scope.md`, or a bare `shift-timesheet`.
4. **Several exist and nothing picked one** — ask, listing each slug with its scope title, status and feature
   count so the choice is made on recognisable things rather than on slugs.
5. **None exist** — only `/ba:scope` may create one. It derives the slug from the material it was given and
   **says which slug it chose**, because every later command takes that slug. Every other command stops and
   points at `/ba:scope`.

**Never guess by recency.** "The most recently modified requirement" is the rule that silently files a payroll
question under the timesheet requirement, and nothing downstream can detect it.

**A requirement slug is lowercase-kebab and permanent.** It is the folder name, it appears in every
`feature.md` frontmatter as `requirement:`, and renaming it orphans the sync-state rows keyed to it.

## 3. Stable ID conventions

IDs are the threads that let one agent cite what another produced. They are **append-only** — never renumber, never reuse a retired ID.

| Entity            | Prefix | Example  | Lives in                     |
|-------------------|--------|----------|------------------------------|
| Requirement       | `<MODULE>-<FR\|AI\|DET\|HUM>` | INTK-AI-02 | requirements/<slug>/registers/requirements.md / scope §3 |
| Use case          | `<MODULE>-UC` | INVP-UC-01 | requirements/<slug>/registers/use-cases.md / scope §3.x.4 |
| Workflow          | `WF`   | WF-001   | requirements/<slug>/registers/workflows.md    |
| Business rule     | `BR`   | BR-001   | requirements/<slug>/registers/business-rules.md |
| Data entity       | `DATA` | DATA-001 | shared-context/data.md         |
| Integration       | `INT`  | INT-001  | shared-context/integrations.md |
| Example/scenario  | `EX`   | EX-001   | requirements/<slug>/registers/examples.md     |
| Assumption        | `ASM`  | ASM-001  | `requirements/<slug>/ledger.md` — kind: assumption  |
| Clarification     | `CLR`  | CLR-001  | `requirements/<slug>/ledger.md` — kind: question    |
| Contradiction     | `CON`  | CON-001  | `requirements/<slug>/ledger.md` — kind: contradiction    |
| Decision          | `DEC`  | DEC-001  | shared-context/decision-log.md       |
| Artifact source   | `SRC`  | SRC-001  | requirements/<slug>/sources.md (registry) |
| Feature           | `FEAT-<AREA>` | FEAT-SUP-001 | requirements/<slug>/features/ (ba) |
| Page              | `PAGE-<AREA>` | PAGE-SUP-01 | <repo>/context/code-context/frontend/ (tl) |
| Endpoint          | `EP-<AREA>`   | EP-SUP-02   | <repo>/context/code-context/backend/ (tl) |
| Entity            | `ENT-<AREA>`  | ENT-SUP-01  | <repo>/context/code-context/database/ (tl) — realises a `DATA-###` |
| Eval              | `EVAL-<AREA>` | EVAL-SUP-01 | features/<slug>/evals/ (tl) — verifies an AC, exercises EP-/ENT- (applied-AI features) |
| QA finding        | `QAF`  | QAF-001  | qa/reviews/<repo>-audit-*.md (qa)    |
| Quality gate      | `QG`   | QG-001   | qa/quality-gates.md (qa)           |
| Requirement       | *(kebab slug)* | shift-timesheet | the folder name + `requirement:` in feature frontmatter (ba) |
| Plan blocker      | `PB` (or `PB-<N>` for sub-task N) | PB-001 · PB-1-002 | units/<repo>/plan-blockers.md (dev) — v2.2 |

### Requirement — the folder that replaced the initiative label

**`initiative` is retired.** It was a human-named slug grouping the features produced by one scoping effort, so a
developer could act on their batch while many developers' features shared one flat `features/`. That is a label
standing in for a folder — and `requirements/<slug>/features/` is now that folder.

Every command that took `initiative=<name>` takes `requirement=<slug>` instead, and it is no longer a filter over a
shared directory but a path: `/dev:plan requirement=shift-timesheet`, `/dev:build requirement=shift-timesheet`.
Grouping is structural, so it cannot drift from the thing it groups — a feature cannot carry the wrong requirement
while sitting in the right folder.

**Reading an older workspace.** A `feature.md` carrying `initiative:` predates this; treat it as the requirement
slug if a folder of that name exists, and otherwise report it rather than guessing. Never rewrite the field
silently — a developer filtering on a batch name needs to know the name changed meaning.

The `context/` graph IDs (`FEAT-`/`PAGE-`/`EP-`/`ENT-`) carry a short uppercase **area** token and a sequence within that area/layer (`PAGE-SUP-01`, `EP-SUP-02`). A database entity **cites the BA `DATA-###`** it realises rather than inventing a parallel data ID; likewise endpoints cite `INT-###` for integrations. Never mint a `context/` ID that shadows a BA register ID.

IDs are zero-padded to 3 digits (functional-requirement `NN` is 2 digits within its module, per the scope template). Cross-references are written inline as the bare ID (e.g. "validated by EX-014" or "see WF-002").

**Requirement IDs** follow the Techjays Scope Document convention: `<MODULE>-<FR|AI|DET|HUM>-<NN>` where the module prefix is a short uppercase abbreviation (Intake → `INTK`, Validation → `VALD`), the middle token is `FR` or the responsibility code, and `NN` is sequential within that module. The same ID is used in `requirements/<slug>/registers/requirements.md` and in `scope.md` §3.x.5 so they trace 1:1.

**Use-case IDs** follow the same module-prefix convention: `<MODULE>-UC-<NN>` (e.g. `INVP-UC-01`), `NN` sequential within the module. A use case is a **distinct scenario or route** through a module — one that differs from its siblings in a *material* way (different steps, actors, business rules, systems, or outcome), not merely in a data value. The canonical use case lives in `scope.md` §3.x.4 (nested under its module) and in `requirements/<slug>/registers/use-cases.md`; the two trace 1:1. Functional requirements, workflows, examples, and business rules cite the use case(s) they serve by ID, and a use case cites the requirements/workflows/examples/rules that realise it — so a route is traceable in both directions. See `ba-extraction` for the rule that decides when a branch becomes its own use case versus an alternative flow.

---

## 4. Source traceability

Every extracted fact must trace back to where it came from. Use this citation form everywhere:

```text
[SRC-002 › meeting-transcripts/2026-06-10-kickoff.md]
```

A requirement, rule, or workflow with no source citation is **not allowed** — if its origin is unknown, raise a clarification (CLR) instead.

---

## 5. Shared vocabulary (controlled values)

All agents use these exact values — no synonyms.

**Artifact status** (per source/file):
`New` · `Processed` · `Changed` · `Unchanged` · `Missing` · `Inaccessible` · `Superseded` · `Archived` · `Access Required` · `Needs User Guidance`

**Confidence** (per extracted fact):
`Confirmed` · `Likely` · `Assumed` · `Conflicting` · `Needs Clarification`

**Usage mode** (per source, how deeply to process it):
`Deep Analysis` · `Reference Only` · `Sample and Summarize` · `Index Only` · `Future Agent Input` · `Needs User Guidance`

**Scope maturity** (document-level status, in frontmatter):
`Draft` · `Emerging` · `Reviewed` · `Frozen` — surfaced on the scope cover block as `Draft` / `In Review` / `Approved`.

**Responsibility** (`Resp.` on every functional requirement, per the Techjays Scope Document):
`AI` (AI capability) · `DET` (deterministic logic) · `HUM` (human action)

**Priority** (`Pri.`, MoSCoW):
`M` (Must) · `S` (Should) · `C` (Could) · `W` (Won't-this-phase)

**Dev delivery state** (per task — parent Task or sub-task)

**One vocabulary.** `status:` holds the same seven values in the local `status.md`, in Mission Control, and
on every other tracker. It is Mission Control's enum, used verbatim — never a local variant, never a
translation:

`todo` · `readyForDev` · `agentExecuting` · `inProgress` · `devReview` · `blocked` · `done`

A second field, **`phase:`**, carries what the loop is doing. It is **local only — never pushed to any
tracker**, and it is not a status: it is only meaningful alongside one. It exists because five gates need a
distinction the seven values deliberately do not carry.

```yaml
status: blocked          # the shared value — identical locally, on Jetrix, on Jira
phase: plan-blockers     # local detail — tells /dev:build WHY, so it can route correctly
```

| `status` | `phase` | Set by | Means |
|---|---|---|---|
| `todo` | — | `/jetrix:pull`, MC | not started |
| `readyForDev` | `planned` | `/dev:plan`, `/jetrix:push implementation` | plan on disk, ready to build |
| `agentExecuting` | `planning` | `/dev:plan` while it runs | an agent holds it |
| `agentExecuting` | `implementing` | `/dev:build` Stages 3–6 | |
| `agentExecuting` | `testing` | `/dev:build` Stages 7–10 | |
| `inProgress` | `built` | `/dev:build` Stage 11 | build complete, awaiting `/dev:commit` |
| `devReview` | `pr-open` | `/dev:commit` Stage 3 onward | in the review pipeline |
| `devReview` | `pr-pending` | `/dev:commit` Stage 9 Step 4 | pushed, but the PR was never opened — the user has a compare link to click |
| `devReview` | `merge-conflict` | `/dev:commit` Stage 7 halt | resolvable, not a full block |
| `blocked` | `plan-blockers` | `/dev:plan`, `plan-blockers.md` has OPEN rows | the human must decide |
| `blocked` | `escalated` | any stage, execution-time | |
| `done` | — | the PR-merge webhook | |

**The five gates read both fields**, and this is the whole reason `phase` exists:

| Command | Runs only when |
|---|---|
| `/dev:plan` | `status: todo` — unplanned work. With `--resume`, `status: blocked` **and** `phase: plan-blockers`. **Never `readyForDev`:** that is this command's own output, so selecting it means re-planning finished work and skipping everything that actually needs a plan. |
| `/dev:build` | `status: readyForDev`. On `blocked` + `plan-blockers` it refuses and routes to `/dev:plan --resume` — a different message from `blocked` + `escalated`. |
| `/dev:commit` | `status: inProgress` **and** `phase: built`. `agentExecuting` means a build is still running. |
| `/dev:fix-review` | `status: devReview` **and** `phase: pr-open` **and** a non-empty `pr_url:`. On `merge-conflict` there is no PR yet; on `pr-pending` the PR was never opened, so route to the compare link, not here. |
| `/dev:resolve` | `status: blocked` **and** `phase: plan-blockers`. |

### What a question may be about

Every command composes its own prompts, so every prompt is a place to invent an option nobody asked
for. One line separates the two kinds:

**A question asks the user to choose a VALUE the run cannot determine. It never asks them to reduce
the WORK they already asked for.**

| Legitimate — a value is genuinely open | Illegitimate — scope is already settled |
|---|---|
| which base branch this merges into | "plan the 4 release-1 features instead of all 18" |
| how to resolve `PB-003` — option 1, 2 or 3 | "build the backend ones first and the rest later" |
| which test framework to stand up | "skip the features whose repo isn't mapped yet" |
| which stack, where the architecture is silent | "this is 36 sub-tasks — start smaller?" |

Scope is set by the invocation and nothing downstream reopens it. A target named is that target; no
target named is the whole set. **Cost is not a reason to offer less** — not sub-task count, not agent
count, not how long the conversation will be. If the batch is big, say how big and carry on.

Where a command does offer a subset form (`/dev:plan` §4's `pick=`), it belongs to the user: never
the default, never marked recommended, never listed first, never framed so the full set reads as the
reckless choice. And never quote a figure to justify shrinking — a count produced before the stage
that computes it is invented, and settled rows (`Closed`, `Accepted (assumed)`) are not open
questions.

**A blank target means the whole batch, never "the next one".** `/dev:plan`, `/dev:build` and
`/dev:commit` all resolve a blank argument to *every* task their gate admits — `todo`, `readyForDev`,
and `inProgress` + `built` respectively — and fan out bounded by `--concurrency` (default 5). This
matches `/ba:features`, which decomposes a whole scope rather than one feature. A user who wants one
thing names it; a user who names nothing wants the set. Three consequences, and none of them are
optional: never present a picker of candidate tasks, never narrow the set yourself ("start with the
release-1 four" is the user's call, not yours), and never let one task's failed gate halt the rest —
skip it, keep the reason, and report every skip together at the end.

**Never print two status lines.** A summary reports `status` once. The old `Local state: … / MC status: …`
pair described one thing twice and let the two drift — which they did.

**Syncing — the map runs both ways.** On Jetrix `tracker.status_map` is `null`, because the values already
match: push sends `status` unchanged and pull copies it back unchanged. On every other tracker the map has
**exactly these seven keys** and nothing else — `phase` is never sent, and no tracker needs a key for it.

| | |
|---|---|
| **Push** | `status` → `status_map[status]` → the tracker |
| **Pull** | the tracker’s value → **the inverse of `status_map`** → `status` |

A tracker whose statuses are coarser maps several of the seven onto one of its own, so **the inverse is
ambiguous** — Jira’s *"In Progress"* could be `agentExecuting` or `inProgress`. Resolve it by taking the
**least advanced** candidate, in the order listed at the top of this section (`todo` < `readyForDev` <
`agentExecuting` < `inProgress` < `devReview` < `blocked` < `done`).

**Under-claim, never over-claim.** Reading more progress than really happened lets `/dev:commit` start on a
task that was never built; reading less costs at worst a re-plan. So *"In Progress"* comes back as
`inProgress`, not `agentExecuting` — no agent is running here — and *"To Do"* comes back as `todo`, not
`readyForDev`, because `readyForDev` claims a local plan exists and a pull cannot know that.

**Pull never sets `phase` from a tracker.** No tracker has the field. Pull writes it only where the status
determines it (`readyForDev` → `planned`, `devReview` → `pr-open`) and otherwise leaves it out, so the gates
fall back to `plan-blockers.md` and `## Run history`, which do know.

A tracker status that is in **no** map value — someone added a column in Jira — is not guessed at: write the
task with `status: todo`, and say in the run output which issue carried which unmapped status, so the human
can add the key at `/jetrix:init refresh`.

For a split feature the parent's `status` is **derived** from its sub-tasks (all `done` → parent `done`; any
`blocked` → parent `blocked`; any `agentExecuting` or `inProgress` → parent `inProgress`; else
`readyForDev`) — parent status is never written directly.

**Applied-AI / LLM feature** (does a feature need eval-engineering?):
A feature is **AI-bearing** when its behaviour depends on a model's output — generation, classification/extraction, ranking or semantic search, RAG, or agentic tool use — or it declares `ai_component: true` / cites an `INT-###` to an LLM/AI provider. AI-bearing features get an **eval layer** (`features/<slug>/evals/`, `EVAL-<AREA>-NN`, see the `eval-engineering` skill); every other feature is **deterministic** and is proven by the dev `## Acceptance` table alone. When it's genuinely unclear, record an **open question** rather than assuming — don't skip evals on a feature that turns out to be AI-bearing, or invent them for one that isn't.

---

## 6. Producer / consumer map

| Surface                              | Produced by | Consumed by        |
|--------------------------------------|-------------|--------------------|
| `requirements/<slug>/sources.md` (source registry) | ba (human-editable) | ba         |
| `requirements/<slug>/artifacts/**/*.summary.md`       | ba          | ba (extraction)    |
| `shared-context/*`                           | ba          | doc, tl, qa        |
| `requirements/<slug>/scope.md`                        | ba          | doc, tl, qa        |
| `requirements/<slug>/registers/requirements.md`       | ba          | doc, tl, qa        |
| `requirements/<slug>/registers/use-cases.md`          | ba          | doc, tl, qa        |
| `shared-context/integrations.md`       | ba          | tl                 |
| `shared-context/data.md`               | ba          | tl                 |
| `features/*` (BA files)              | ba          | tl, doc, qa        |
| `features/<slug>/tl-plan.md`         | tl (feature-compose) | dev, doc, qa · pushed verbatim to `MC.Task.implementationDetails` by `/jetrix:push implementation` |
| `<repo>/context/code-context/*` (committed with the code — Model B) | tl (code-map reverse, feature-planning forward) | tl (spec-review, feature-compose), dev, doc, qa, coding agents |
| `code-map-registry.md`            | tl (code-map) | tl (feature-planning), dev |
| `features/<slug>/evals/*` (applied-AI) | tl (feature-planning designs) | dev (feature-delivery-loop runs + inspects), qa (harness hosts) |
| each feature’s own `status.md`                | dev         | dev, tl (roll-up)  |
| `doc/**/*`                           | doc         | human, final       |
| `tl-reviews/*`       | tl          | human, delivery    |
| `qa/quality-gates.md`                | qa          | dev (`/dev:plan` harness gate; `/dev:build` Stages 4/7/8; `/dev:commit` Stage 5) |
| `qa/reviews/*` `qa/<repo>-setup.md` § `## Plan` | qa         | human, qa          |

When a downstream agent (doc/tl/qa) runs, it should prefer `requirements/<slug>/scope.md` as its primary input and **not re-run BA analysis** unless explicitly asked.

---

## 6a. Navigating an existing codebase — graph first, source last

Two artefacts describe a mapped system, at two different scales. **Between** repos and **inside** one:

| Question | Read | Scale |
|---|---|---|
| Which app calls which? What transport, what auth boundary, which external services? | `.jetrix/connection-map.md` | **between repos** — solution-wide |
| What does this endpoint do? Which page calls it? What does it touch in the database? Where is X defined? | `<repo>/context/code-context/` via the **`tl-read-code-context`** skill | **inside one repo** |
| Line-level detail the graph doesn't carry, or code you are about to change | the source file the unit cites | last resort |

**The rule: when `<repo>/context/code-context/` exists, a question about what the code does is answered from the graph, not by reading source.** Invoke `tl-read-code-context`. Grepping the repository to answer a general codebase question — "how does X work", "where is Y", "what calls Z" — is a contract violation when the graph covers that area, and it is slower and less reliable besides: the graph carries validation rules, business logic, data-access tables and cross-references that no single source file states.

The two artefacts chain. A cross-repo trace starts in `connection-map.md` to establish *which* repos are involved and how they talk, then continues in each repo's `code-context/` for the units at either end. Starting in the source loses both halves.

Source is read when the graph is **silent** (the area isn't mapped — say so and point at `/tl:code-map`), when you need a line-level detail the unit cites but doesn't reproduce, or when you are **implementing** a change rather than answering a question.

This applies to every agent — `dev`, `tl`, `qa`, `doc`, `ba` — and to direct questions with no agent involved. The skill auto-triggers on question shape, but do not rely on that: invoke it explicitly as the first step whenever the graph exists.

---

## 6b. Mission Control tab content — reader-facing, always

**Tabs have two audiences, and the rule differs by which.**

| Tab | Audience | File paths, unit ids |
|---|---|---|
| Description, Acceptance Criteria, Business Rules, Test Scenarios, NFRs, Assumptions, Scope, Steps to Reproduce, Actual / Expected Result | designers, QA, PMs, the client &mdash; people without the repo open | **stripped** |
| **Implementation** | the developer or agent building it | **required** &mdash; see below |

**The Implementation tab is a build spec, not a summary.** `tl-feature-compose` Rule 1 requires concrete paths in §1's Files column (`Modified: src/components/Home.jsx`), in §4's fields-written source, §5's component paths, and §6's Reuse rows. Only §8 Shared contract stays path-free. A plan that says "give the sign-in page a flag" without naming the file is not a plan &mdash; the developer cannot act on it and the reviewer cannot check it. An earlier draft of this contract forbade paths everywhere; that was wrong for exactly this reason and was reverted in v2.3.11. Do not re-introduce it.

For the reader-facing tabs, the rule below applies across every producer — `/ba:features`, `/jetrix:push feature`, `/jetrix:push task`, `/dev:plan`, `/jetrix:task-update` — and every task type, plugin-authored or hand-filed:

| Never on a tab | Where it belongs |
|---|---|
| file paths, line numbers (`src/components/Home.css:1-7`) | `units/<repo>/analysis.md`, `units/<repo>/implementation.md` |
| unit ids (`PAGE-AUTH-01`, `EP-…`, `ENT-…`) | `units/<repo>/analysis.md`, the code-context graph |
| blocker and decision ids (`PB-###`, `DEC-###`) | `units/<repo>/plan-blockers.md`, `shared-context/decision-log.md` |
| finding ids (`FND-##`), framework names, method names, HTTP status codes | `units/<repo>/analysis.md` |
| feature-id headings, provenance callouts, source-reference blocks | the local author-side files |

Say what a person sees and what will change. "The sign-in page's only action is the **Google** button; its background is a four-stop gradient today and becomes solid black" is a tab. "`.btn1` at `Home.css:1-7`, per DEC-109" is not.

**Local files are richer than the reader-facing tabs, and that is the design.** The push performs a one-way transformation for those: author-side files keep every co-ordinate; the tab keeps the decision. The Implementation tab is the exception — it carries the co-ordinates too, because it is what the build follows. Never write a different plan for the tab.

**Pull writes tabs back verbatim.** Once content is tab-shape it stays that way; `/jetrix:pull` does no re-transformation, so anything that leaks onto a tab persists into the local copy on the next pull and compounds.

**An unrelated defect found while investigating is not an edit to this ticket.** Report it in the run summary so it can be filed separately. Appending it to a Description hides it from triage and confuses whoever reads the ticket.

---

## 7. Canonical deliverable formats (Techjays D&D pack)

Client-facing deliverables conform to the Techjays **Design & Discovery** templates. These are the authority for structure and style; the markdown an agent maintains is the living source that the Doc Agent renders into the branded `.docx` at freeze time. The **Scope Document** template is bundled with this core plugin at `${CLAUDE_PLUGIN_ROOT}/templates/d&d/scope-document/` (versioned via its `manifest.json` + `CHANGELOG.md`); the rest still live in the repo `docs/D&D Documentation/` and will be bundled as their agents are built.

| Deliverable | D&D template | Maintained as | Owner |
|-------------|--------------|---------------|-------|
| Scope Document | **bundled** → `templates/d&d/scope-document/scope-document-template.docx` | `requirements/<slug>/scope.md` (module-centric) | ba |
| RAID Register | `docs/…/04 - RAID Register Template.docx` | `requirements/<slug>/ledger.md` — A/D/R/Q rows are a filter on `kind`, so the register renders rather than being maintained | ba |
| Executive Summary | `docs/…/01 - Executive Summary Template.docx` | `doc/decks/` | doc (Phase 2) |
| Technical Architecture | `docs/…/03 - Technical Architecture Template.docx` | `tl-reviews/` or handoff to doc | tl (Phase 3) |
| Implementation Plan | `docs/…/05 - Implementation Plan Template.docx` | `doc/decks/` | doc (Phase 2) |

**RAID alignment** — the BA registers map onto the RAID Register's four registers:
`requirements/<slug>/ledger.md` (kind: assumption) → Assumptions `A-##` · dependencies → Dependencies `D-##` · `requirements/<slug>/ledger.md` (kind: contradiction) / risk notes → Risks `R-##` · `requirements/<slug>/ledger.md` (kind: question) → Open Questions `Q-##` (classified: *Must close before estimate · Proceed with assumption · Minor implementation detail · Too uncertain (exclude/T&M) · Future phase*). Scope §7 only references RAID — it never duplicates these.

---

## 8. Diagram convention (Mermaid is the living source; branded SVG is the projection)

Flows are authored as **Mermaid** fenced code blocks directly in the markdown the BA maintains — a module master flow in `scope.md` §3.x.3, and a per-use-case flow in each §3.x.4 use case (and, downstream, in each feature's `## Workflow` section). Mermaid is chosen because it is diffable, reviewable in a pull request, and renders in most markdown viewers, so the diagram evolves with the words around it instead of drifting out of date in a separate file. The **Doc Agent** renders these same flows into the branded **SVG swimlanes** of the Techjays deliverables at doc/freeze time (`doc-workflow`) — so Mermaid is the *source*, SVG is the *client-facing projection* of the same journey, never a second hand-authored diagram to keep in sync.

Authoring rules so the diagrams stay uniform and machine-mappable:

- Use `flowchart TD` (top-down) for a use-case route and `flowchart TD` or `LR` for a module master flow — pick one orientation per module and keep it.
- **Decision/branch points are diamond nodes** (`{...}`), and **every branch edge is labelled with the condition** that selects it (`-->|credit memo| ...`). In a module master flow, each terminal branch names the use case it leads to by ID and name, so the master flow and the nested use cases line up 1:1.
- Terminal/outcome nodes use rounded ends (`([...])`); systems of record or integrations referenced in a step name the `INT-###` they map to in the node text where it helps.
- Keep the master flow to the decision skeleton (trigger → branch points → which use case) and push step-level detail into each use case's own flow — the master answers *which route*, the use-case flow answers *how that route runs*.
- Fence every diagram as ` ``mermaid ` … ` `` ` and keep the label text short; long prose belongs in the surrounding narrative, not inside a node.
