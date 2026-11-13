#!/usr/bin/env python3
"""Verify every row of a test map against the disk. Runs nothing.

Implements /dev:build Stage 7 §7b. Five checks per row:

  test-file-exists      the Test column names a path on disk
  named-test-resolves   the runner's own filter selects exactly one test
  run-it-populated      the Run it cell is neither empty nor an em dash
  needs-startable       every Needs token is a known service token
  fixture-exists        every Fixtures entry is defined somewhere in the repo

Usage:
    python verify-test-map.py --map <test-map.md> --repo <repo-root> [--json <out>]

Exit 0 when every row passes, 1 when any row fails, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DASH = "—"
NEEDS_TOKENS = {"real-db", "backend-running", "frontend-running", "real-auth", DASH, "-", ""}

# How each language declares a test name. Group 1 is always the name.
NAME_PATTERNS = [
    re.compile(r"""\b(?:it|test)(?:\.\w+)*\s*\(\s*(['"`])(.+?)\1""", re.S),   # js/ts
    re.compile(r"""^\s*def\s+(test_\w+)""", re.M),                             # python
    re.compile(r"""^\s*func\s+(Test\w+)""", re.M),                             # go
    re.compile(r"""^\s*(?:public\s+)?void\s+(test\w+)\s*\(""", re.M),          # java
]
SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".java", ".rb", ".kt", ".rs")
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".venv", "venv", "__pycache__", ".next", "coverage"}


def cell(text: str) -> str:
    return text.strip().strip("`").strip()


def parse_rows(md: str) -> list[dict]:
    """Rows of the map's table, keyed by its declared headers."""
    rows, headers = [], None
    for line in md.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if headers is None:
            if "Test" in parts and "Run it" in parts:
                headers = parts
            continue
        if all(set(p) <= set("-: ") for p in parts):   # the --- separator
            continue
        if len(parts) == len(headers):
            rows.append(dict(zip(headers, parts)))
    return rows


def test_names(path: str) -> list[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
    except OSError:
        return []
    found = []
    for pat in NAME_PATTERNS:
        for m in pat.finditer(src):
            found.append(m.group(2) if pat.groups >= 2 else m.group(1))
    return found


def fixture_defined(repo: str, name: str) -> bool:
    """A fixture is defined if a file is named for it, or something declares it."""
    decl = re.compile(
        r"(?:const|let|var|function|class|def|func|export\s+(?:const|function|class))\s+"
        + re.escape(name) + r"\b"
    )
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            stem = os.path.splitext(fn)[0]
            if stem == name or stem == name.replace("Factory", "").lower():
                return True
            if not fn.endswith(SOURCE_EXT):
                continue
            try:
                with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as fh:
                    if decl.search(fh.read()):
                        return True
            except OSError:
                continue
    return False


def check_row(row: dict, repo: str) -> dict:
    ref = cell(row.get("Test", ""))
    out = {"id": cell(row.get("ID", "")), "test": ref, "failures": []}

    def fail(blocker, detail):
        out["failures"].append({"blocker": blocker, "detail": detail})

    # 1 + 2 — the test file, and the named test inside it
    rel, _, name = ref.partition("::")
    path = os.path.join(repo, rel.replace("/", os.sep))
    if not rel:
        fail("test-map-incomplete", "Test column is empty")
    elif not os.path.isfile(path):
        fail("test-map-dangling-test", "no file at %s" % rel)
    elif name:
        names = test_names(path)
        # The runner's -t filter is a substring match. One match is the row's
        # claim; several means the row runs more than it names.
        hits = [n for n in names if name in n]
        if not hits:
            fail("test-map-dangling-test", "no test in %s matches %r" % (rel, name))
        elif len(hits) > 1:
            fail("test-map-dangling-test",
                 "%r is ambiguous in %s; the runner would also select %s"
                 % (name, rel, ", ".join(repr(h) for h in hits if h != name)[:160]))

    # 3 — Run it
    run_it = cell(row.get("Run it", ""))
    if run_it in ("", DASH, "-"):
        fail("test-map-incomplete", "Run it is empty")

    # 4 — Needs
    for tok in [t.strip().strip("`") for t in cell(row.get("Needs", "")).split(",")]:
        if tok not in NEEDS_TOKENS:
            fail("test-map-unstartable", "unknown Needs token %r" % tok)

    # 5 — Fixtures
    for fx in [f.strip().strip("`") for f in cell(row.get("Fixtures", "")).split(",")]:
        if fx in ("", DASH, "-"):
            continue
        if not fixture_defined(repo, fx):
            fail("test-map-dangling-fixture", "fixture %r is not defined anywhere in the repo" % fx)

    out["ok"] = not out["failures"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--json", help="write the full result here")
    args = ap.parse_args()

    if not os.path.isfile(args.map):
        print("test-map-missing: %s" % args.map, file=sys.stderr)
        return 2
    repo = os.path.abspath(args.repo)

    with open(args.map, encoding="utf-8") as fh:
        rows = parse_rows(fh.read())
    if not rows:
        print("test-map-missing: no table rows in %s" % args.map, file=sys.stderr)
        return 2

    results = [check_row(r, repo) for r in rows]
    failed = [r for r in results if not r["ok"]]
    report = {
        "rows_total": len(results),
        "rows_verified": len(results) - len(failed),
        "rows_failed": len(failed),
        "blockers": sorted({f["blocker"] for r in failed for f in r["failures"]}),
        "rows": results,
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)

    print("%d/%d rows verified" % (report["rows_verified"], report["rows_total"]))
    for r in failed:
        for f in r["failures"]:
            print("  FAIL %-28s %s  (%s)" % (r["id"] or r["test"], f["detail"], f["blocker"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
