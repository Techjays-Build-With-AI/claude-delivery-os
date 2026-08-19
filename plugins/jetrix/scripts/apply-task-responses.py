"""Apply `task_upsert_bundle` response — patch task .md frontmatter + sync-state.

Invoked by `/jetrix:push task` (see plugins/jetrix/commands/references/push/task.md)
after the MCP call returns. Replaces the "for each response, sed-patch the file
+ Read/Write sync-state" iteration.

Contract preserved:
  - Only `ok:true` rows are recorded
  - `action == "created"` or `"recreated"` → set jetrix_task_id + jetrix_task_object_id
    in the file's frontmatter (upsert keys)
  - sync-state key = `tasks/<rel-path>` (file-scoped, not feature-scoped —
    keeps task-stage entries distinct from feature-stage entries)

Usage:
    python apply-task-responses.py \
        --responses    /tmp/task-responses.json \
        --project-root .jetrix/<slug> \
        --sync-state   .jetrix/cache/sync-state.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def _patch_frontmatter(md: pathlib.Path, task_number: int, task_object_id: str) -> bool:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end_match = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if not end_match:
        return False
    fm_end = 3 + end_match.start()
    fm_block = text[3:fm_end]
    rest = text[fm_end:]

    def upsert(block: str, key: str, value) -> str:
        pat = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
        if pat.search(block):
            return pat.sub(f"{key}: {value}", block, count=1)
        sep = "" if block.endswith("\n") else "\n"
        return f"{block}{sep}{key}: {value}\n"

    new_block = upsert(fm_block, "jetrix_task_id", task_number)
    new_block = upsert(new_block, "jetrix_task_object_id", task_object_id)

    new_text = f"---{new_block}{rest}"
    if new_text != text:
        md.write_text(new_text, encoding="utf-8")
        return True
    return False


def apply(
    responses_path: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
) -> int:
    responses = _load_json(responses_path, [])
    if isinstance(responses, dict):
        responses = responses.get("tasks") or responses.get("features") or []
    if not responses:
        print("no responses to apply")
        return 0

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()

    recorded: list[str] = []
    patched:  list[str] = []
    failed:   list[tuple[str, str]] = []

    for row in responses:
        if not isinstance(row, dict) or not row.get("ok"):
            failed.append((row.get("_local_rel_path") or row.get("slug") or "?",
                          row.get("error") or "ok:false"))
            continue

        rel = row.get("_local_rel_path") or ""
        task_number = row.get("task_number")
        task_oid    = row.get("task_object_id")
        action      = (row.get("action") or "updated").lower()
        local_hash  = row.get("_local_content_hash") or ""

        if action in ("created", "recreated") and rel and task_number is not None and task_oid:
            md = project_root / rel
            if md.exists() and _patch_frontmatter(md, task_number, task_oid):
                patched.append(rel)

        state_key = f"tasks/{rel}" if rel else f"tasks/{row.get('slug') or row.get('feature_id')}"
        sync_state[state_key] = {
            "taskNumber":   task_number,
            "taskObjectId": task_oid,
            "featureId":    row.get("feature_id"),
            "slug":         row.get("slug"),
            "contentHash":  f"sha256:{local_hash}" if local_hash else sync_state.get(state_key, {}).get("contentHash"),
            "version":      row.get("version"),
            "lastPushed":   now,
        }
        recorded.append(rel or row.get("slug") or "")

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"recorded={len(recorded)} patched_frontmatter={len(patched)} failed={len(failed)}")
    for s in recorded: print(f"  recorded {s}")
    for s in patched:  print(f"  patched  {s}")
    for s, err in failed: print(f"  failed   {s}: {err}")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--responses",    required=True)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--sync-state",   required=True)
    args = ap.parse_args()

    return apply(
        responses_path=pathlib.Path(args.responses).resolve(),
        project_root=pathlib.Path(args.project_root).resolve(),
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
    )


if __name__ == "__main__":
    sys.exit(main())
