#!/usr/bin/env python3
"""Verify a commit run's own record against the bounds it claims to honour.

Implements /dev:commit Stage 8 §8a. Reads the `doc_type: commit-run` block in
`units/<repo>/status.md` and checks the gates that an agent writing its own
record can otherwise walk past:

  5x-executed            phase_execute.executed is true and has a finished_at
  5r-read-only           phase_review.executions is 0
  map-runs-recorded      phase_execute.full_map_runs is present
  map-run-ceiling        full map was not re-run past the §5e ceiling
  snapshot-agreement     stage-4, 5R and 5X cite the same snapshot sha
  reentry-ceiling        reentries_used is within the §6b ceiling
  nonblocking-rounds     rounds_used is within the §6e.i bound
  merge-invoked          stage-7 semantic merge has an invoked_at
  dimensions-reviewed    stage-4 lists all nine review dimensions

Usage:
    python verify-run-record.py --status <units/<repo>/status.md> [--json <out>]

Exit 0 when every check passes, 1 when any fails, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

REENTRY_CEILING = 2          # stage-6-fix-loop.md §6b
NONBLOCKING_ROUNDS = 2       # stage-6-fix-loop.md §6e.i
FULL_MAP_RUNS = 2            # stage-5-acceptance.md §5e
DIMENSIONS = 9               # dev-stack-adaptive-code-review


def blocks(md: str) -> list[str]:
    return re.findall(r"```ya?ml\n(.*?)```", md, re.S)


def flatten(block: str) -> dict:
    """Dotted path -> scalar, for the YAML subset these records use."""
    out, stack = {}, []
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = raw.split("  #")[0].rstrip()
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        listed = body.startswith("- ")
        if listed:
            body = body[2:].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+):\s*(.*)$", body)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([k for _, k in stack] + [key])
        if val.startswith("{"):
            for pair in re.findall(r"([A-Za-z0-9_.\-]+)\s*:\s*([^,{}]+)", val):
                out[f"{path}.{pair[0]}"] = pair[1].strip().strip("'\"")
        elif val and val != "|":
            out[path] = val.strip("'\"")
        if not val or val.startswith("{"):
            stack.append((indent, key))
    return out


def norm(v):
    return None if v is None else str(v).strip().strip("'\"").lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()

    try:
        md = open(a.status, encoding="utf-8").read()
    except OSError as e:
        print(f"usage error: {e}", file=sys.stderr)
        return 2

    rec = next((flatten(b) for b in blocks(md) if "doc_type: commit-run" in b), None)
    if rec is None:
        print("FAIL no-commit-run-block: status.md has no `doc_type: commit-run` YAML block")
        return 1

    def g(*names):
        for n in names:
            for k, v in rec.items():
                if k == n or k.endswith("." + n):
                    return v
        return None

    checks, fails, warns = [], [], []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fails.append(f"{name}: {detail}")

    executed = norm(g("phase_execute.executed"))
    check("5x-executed", executed == "true" and g("phase_execute.finished_at"),
          "phase_execute.executed must be true with a finished_at"
          f" (found executed={executed!r})")

    reviews = g("phase_review.executions")
    check("5r-read-only", norm(reviews) == "0",
          f"phase_review.executions must be 0 (found {reviews!r})")

    runs = g("phase_execute.full_map_runs")
    check("map-runs-recorded", runs is not None,
          f"phase_execute.full_map_runs must be recorded (found {runs!r})")
    n_runs = int(runs) if runs and runs.isdigit() else None
    check("map-run-ceiling", n_runs is None or n_runs <= FULL_MAP_RUNS,
          f"full_map_runs={n_runs} exceeds the ceiling of {FULL_MAP_RUNS}"
          " (stage-5 5e: re-run the failed rows, not the whole map)")
    if n_runs == 2:
        warns.append("full_map_runs=2: one repair landed after the execution")

    shas = {n: g(n) for n in ("stage-4.snapshot_sha",
                              "phase_review.snapshot_sha",
                              "phase_execute.snapshot_sha")}
    present = {k: v for k, v in shas.items() if v}
    check("snapshot-agreement", len(set(present.values())) <= 1,
          f"stage-4, 5R and 5X must cite one sha (found {present})")

    for name, key, ceiling in (("reentry-ceiling", "reentries_used", REENTRY_CEILING),
                               ("nonblocking-rounds", "rounds_used", NONBLOCKING_ROUNDS)):
        v = g(key)
        used = int(v) if v and v.isdigit() else None
        check(name, used is None or used <= ceiling,
              f"{key}={used} exceeds the ceiling of {ceiling}")
        if used is None:
            warns.append(f"{key} not recorded: the bound is unaudited")

    check("merge-invoked", bool(g("tl_semantic_context_merge_invocation.invoked_at")),
          "stage-7 semantic merge has no invoked_at")

    dims = g("dimensions_reviewed")
    n = len(re.findall(r"[A-Za-z_]+", dims)) if dims else 0
    check("dimensions-reviewed", n == DIMENSIONS,
          f"stage-4 must list all {DIMENSIONS} review dimensions (found {n})")

    for c in checks:
        print(f"  [{'ok  ' if c['ok'] else 'FAIL'}] {c['check']}"
              + ("" if c["ok"] else f": {c['detail']}"))
    for w in warns:
        print(f"  [warn] {w}")
    print(f"\n{len(fails)} failure(s), {len(warns)} warning(s)")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"ok": not fails, "checks": checks, "warnings": warns}, f, indent=2)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
