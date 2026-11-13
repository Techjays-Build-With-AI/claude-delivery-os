#!/usr/bin/env python3
"""Apply /dev:build Stage 10's mechanical edits to code-context unit files.

The agent decides the two things that need judgment — which source file implements
each unit, and which test asserts on it. This applies everything that follows from
those two facts, identically, to every unit:

  10c  frontmatter field writes
  10d  Source References appends (code + test), never overwriting
  10e  the unit's row in its layer index -> Status Active

Input JSON (--units):
  [{"file": "<repo-relative unit path>",
    "mapped_from": "src/routes/supplier.ts",
    "mapped_from_line": 42,                 # optional
    "test_ref": "tests/supplier.spec.ts"},  # optional
   ...]

Usage:
    python apply-context-updates.py --units u.json --repo <repo> --task FEAT-SUP-001-1
                                    [--index <repo-relative layer index> ...] [--dry-run]

Exit 0 on success, 1 if any unit could not be updated, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

SET_FIELDS = [
    ("origin", "implemented"),
    ("status", "Active"),
    ("implementation_state", "Implemented"),
    ("design_confidence", "Confirmed"),
    ("implemented_by_commit", "pending"),
    ("mapped_from_commit", "pending"),
]


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    return text[3:end].strip("\n"), text[end + 4:].lstrip("\n")


def set_field(fm: str, key: str, value: str) -> str:
    pat = re.compile(r"^%s\s*:.*$" % re.escape(key), re.M)
    line = "%s: %s" % (key, value)
    return pat.sub(line, fm, count=1) if pat.search(fm) else fm.rstrip("\n") + "\n" + line


def append_source_ref(body: str, ref: str) -> str:
    """Append one bullet under ## Source References. Never duplicates."""
    if ref in body:
        return body
    m = re.search(r"^##\s+Source References\s*$", body, re.M)
    if not m:
        return body.rstrip("\n") + "\n\n## Source References\n\n- %s\n" % ref
    start = m.end()
    nxt = re.search(r"^##\s+", body[start:], re.M)
    end = start + (nxt.start() if nxt else len(body) - start)
    block = body[start:end].rstrip("\n")
    return body[:start] + block + "\n- %s\n\n" % ref + body[end:]


def update_index_row(path: str, unit_stem: str) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return False
    hit = False
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|") or unit_stem not in line:
            continue
        cells = line.split("|")
        for j, c in enumerate(cells):
            if c.strip() in ("Proposed", "Planned", "designed"):
                cells[j] = c.replace(c.strip(), "Active")
                hit = True
        lines[i] = "|".join(cells)
    if hit:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines))
    return hit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--index", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.units, encoding="utf-8") as fh:
            units = json.load(fh)
    except (OSError, ValueError) as exc:
        print("cannot read --units: %s" % exc, file=sys.stderr)
        return 2
    if not isinstance(units, list) or not units:
        print("--units must be a non-empty list", file=sys.stderr)
        return 2

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    repo, updated, failed = os.path.abspath(args.repo), [], []

    for u in units:
        rel = u.get("file", "")
        path = os.path.join(repo, rel.replace("/", os.sep))
        src = u.get("mapped_from")
        if not rel or not src:
            failed.append((rel or "<no file>", "file and mapped_from are both required"))
            continue
        if not os.path.isfile(path):
            failed.append((rel, "no unit file on disk"))
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        fm, body = split_frontmatter(text)
        if fm is None:
            failed.append((rel, "no frontmatter"))
            continue

        for k, v in SET_FIELDS:
            fm = set_field(fm, k, v)
        fm = set_field(fm, "implemented_at", now)
        fm = set_field(fm, "implemented_by_task", args.task)
        fm = set_field(fm, "mapped_from", src)
        line_no = u.get("mapped_from_line")
        if line_no:
            fm = set_field(fm, "mapped_from_line", str(line_no))

        body = append_source_ref(body, "[code › %s%s]" % (src, ":%s" % line_no if line_no else ""))
        if u.get("test_ref"):
            body = append_source_ref(body, "[test › %s]" % u["test_ref"])

        if not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("---\n%s\n---\n\n%s" % (fm, body.lstrip("\n")))
        updated.append(rel)

    rows = 0
    for idx in args.index:
        ip = os.path.join(repo, idx.replace("/", os.sep))
        for rel in updated:
            if not args.dry_run and update_index_row(ip, os.path.splitext(os.path.basename(rel))[0]):
                rows += 1

    print("%d unit(s) updated, %d index row(s) set Active%s"
          % (len(updated), rows, " [dry-run]" if args.dry_run else ""))
    for rel, why in failed:
        print("  FAIL %-50s %s" % (rel, why))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
