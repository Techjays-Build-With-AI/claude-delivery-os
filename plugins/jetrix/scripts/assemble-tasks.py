"""Assemble `task_upsert_bundle` payloads from local `.md` task files.

Invoked by `/jetrix:push task` (see plugins/jetrix/commands/references/push/task.md).
Walks the target set (a single file, a directory, or the default `tasks/`),
parses frontmatter + body from each, applies skip-unchanged via sync-state,
and emits ONE JSON blob Claude passes to `task_upsert_bundle`.

Contract preserved:
  - Reject any file missing `feature_id` in frontmatter (surfaced as halt)
  - `title` fallback: frontmatter.title → body H1 → slug
  - `description` = body verbatim (frontmatter stripped, H1 stripped if leading)
  - Skip file when sync-state[<rel-path>].contentHash matches current hash

Usage:
    python assemble-tasks.py \
        --project-root .jetrix \
        --sync-state   .jetrix/cache/sync-state.json \
        --output       /tmp/tasks-assembled.json \
        [--target tasks/foo.md | tasks/subdir | tasks]

    (Legacy v1 workspaces pass `--project-root .jetrix/<slug>` instead; the
    caller auto-detects either shape.)

The output JSON shape:
{
  "tasks":              [<payload>, ...],
  "skipped_unchanged":  [<rel-path>, ...],
  "halts":              [{"path": "tasks/x.md", "reason": "..."}, ...]
}

Each `<payload>` matches task_upsert_bundle's schema; carries a `_local_content_hash`
+ `_local_rel_path` echoed by apply-task-responses.py for sync-state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


def _parse_scalar(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    m = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if not m:
        return {}, text
    end = 3 + m.start()
    fm_block = text[3:end]
    body = text[end + len("---"):].lstrip("\r\n")

    fm: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in fm_block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and current_list_key is not None:
            fm[current_list_key].append(_parse_scalar(line.lstrip()[2:]))
            continue
        mm = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not mm:
            current_list_key = None
            continue
        key, val = mm.group(1), mm.group(2).strip()
        if val == "":
            current_list_key = key
            fm[key] = []
        else:
            current_list_key = None
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = [] if not inner else [_parse_scalar(s.strip()) for s in inner.split(",")]
            else:
                fm[key] = _parse_scalar(val)
    return fm, body


def strip_h1(body: str) -> tuple[str | None, str]:
    lines = body.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or not lines[i].startswith("# "):
        return None, body
    return lines[i][2:].strip(), "\n".join(lines[i + 1:]).lstrip("\n")


def _collect_files(project_root: pathlib.Path, target: str) -> list[pathlib.Path]:
    tgt = project_root / target
    if tgt.is_file() and tgt.suffix == ".md":
        return [tgt]
    if tgt.is_dir():
        return sorted(tgt.rglob("*.md"))
    # Missing target — return empty; caller decides how to report.
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--sync-state",   required=True)
    ap.add_argument("--output",       required=True)
    ap.add_argument("--target",       default="tasks",
                    help="File or directory (default 'tasks/'). Relative to project-root.")
    args = ap.parse_args()

    project_root = pathlib.Path(args.project_root).resolve()
    sync_state_path = pathlib.Path(args.sync_state).resolve()

    files = _collect_files(project_root, args.target)
    if not files:
        pathlib.Path(args.output).write_text(json.dumps({
            "tasks": [], "skipped_unchanged": [],
            "halts": [{"path": args.target, "reason": "no .md files found at target"}],
        }, indent=2), encoding="utf-8")
        print(f"no files at {args.target}")
        return 0

    sync_state: dict[str, Any] = {}
    if sync_state_path.exists():
        try:
            sync_state = json.loads(sync_state_path.read_text(encoding="utf-8") or "null") or {}
        except json.JSONDecodeError:
            sync_state = {}

    payloads: list[dict] = []
    skipped: list[str] = []
    halts: list[dict] = []

    for fpath in files:
        rel = str(fpath.relative_to(project_root)).replace("\\", "/")
        try:
            text = fpath.read_text(encoding="utf-8")
        except OSError as exc:
            halts.append({"path": rel, "reason": f"read failed: {exc}"})
            continue

        fm, body = split_frontmatter(text)
        if not fm.get("feature_id"):
            halts.append({"path": rel, "reason": "missing feature_id in frontmatter"})
            continue

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        prev = sync_state.get(f"tasks/{rel}", {})
        prev_hash = (prev.get("contentHash") or "").replace("sha256:", "")
        if prev_hash == content_hash:
            skipped.append(rel)
            continue

        h1, body_no_h1 = strip_h1(body)
        title = fm.get("title") or h1 or fm.get("slug") or ""

        payloads.append({
            "feature_id":   fm.get("feature_id"),
            "slug":         fm.get("slug") or "",
            "title":        title,
            "description":  body_no_h1.strip(),
            "status":       fm.get("status") or "",
            "priority":     fm.get("priority") or "",
            "initiative":   fm.get("initiative") or "",
            "task_object_id":   fm.get("jetrix_task_object_id") or None,
            "expected_version": prev.get("version") if isinstance(prev, dict) else None,
            "_local_content_hash": content_hash,
            "_local_rel_path":     rel,
        })

    output = {
        "tasks":             payloads,
        "skipped_unchanged": skipped,
        "halts":             halts,
    }
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"to_push={len(payloads)} skipped_unchanged={len(skipped)} halts={len(halts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
