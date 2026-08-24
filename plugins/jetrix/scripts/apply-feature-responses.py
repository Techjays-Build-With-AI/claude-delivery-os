"""Apply `feature_upsert_bundle` response(s) — patch feature.md frontmatter + sync-state.

Invoked by `/jetrix:push feature` (see plugins/jetrix/commands/references/push/feature.md)
after all MCP calls return. Replaces the "for each response, sed-patch feature.md
+ Read/Write sync-state" iteration in the plugin markdown.

Contract preserved:
  - Only rows with `ok:true` are recorded
  - `action == "created"` or `"recreated"` → patch feature.md frontmatter with
    jetrix_task_id + jetrix_task_object_id
  - sync-state entries land under `tasks/<feature_id>` (feature-scoped, not
    file-scoped — matches pull side)
  - Merge-safe: existing keys for other stages preserved

Usage:
    python apply-feature-responses.py \
        --responses    /tmp/feature-responses.json \
        --project-root .jetrix/<slug> \
        --sync-state   .jetrix/cache/sync-state.json

The --responses file is a JSON list of items with shape:
    [{"slug": ..., "feature_id": ..., "task_object_id": ..., "task_number": ...,
      "version": ..., "action": "created"|"updated"|"recreated", "ok": true,
      "_local_content_hash": "<sha256 from assemble step>"}, ...]

Where `_local_content_hash` comes verbatim from the payload assemble-features.py
produced (echoed through the MCP round-trip by the caller).
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


def _patch_frontmatter(feature_md: pathlib.Path, task_number: int, task_object_id: str) -> bool:
    """Set jetrix_task_id + jetrix_task_object_id in the frontmatter. Insert
    the keys if absent, replace them if present. Returns True on write."""
    text = feature_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end_match = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if not end_match:
        return False
    fm_end = 3 + end_match.start()
    fm_block = text[3:fm_end]
    rest = text[fm_end:]

    def upsert(block: str, key: str, value) -> str:
        pattern = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
        if pattern.search(block):
            return pattern.sub(f"{key}: {value}", block, count=1)
        # Insert before the closing fence — append at end of the FM block.
        sep = "" if block.endswith("\n") else "\n"
        return f"{block}{sep}{key}: {value}\n"

    new_block = upsert(fm_block, "jetrix_task_id", task_number)
    new_block = upsert(new_block, "jetrix_task_object_id", task_object_id)

    new_text = f"---{new_block}{rest}"
    if new_text != text:
        feature_md.write_text(new_text, encoding="utf-8")
        return True
    return False


def apply(
    responses_path: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
) -> int:
    responses = _load_json(responses_path, [])
    if not isinstance(responses, list):
        # Callers sometimes wrap the array in {"features":[...]} — accept both.
        responses = responses.get("features") if isinstance(responses, dict) else []
    if not responses:
        print("no responses to apply")
        return 0

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()

    patched: list[str] = []
    recorded: list[str] = []
    failed:  list[tuple[str, str]] = []

    for row in responses:
        if not isinstance(row, dict) or not row.get("ok"):
            failed.append((row.get("slug") or "?", row.get("error") or "ok:false"))
            continue
        slug          = row.get("slug") or ""
        feature_id    = row.get("feature_id") or slug
        task_number   = row.get("task_number")
        task_oid      = row.get("task_object_id")
        action        = (row.get("action") or "updated").lower()
        local_hash    = row.get("_local_content_hash") or ""

        # Write-back frontmatter on create / recreate only.
        if action in ("created", "recreated") and slug and task_number is not None and task_oid:
            feature_md = project_root / "features" / slug / "feature.md"
            if feature_md.exists():
                if _patch_frontmatter(feature_md, task_number, task_oid):
                    patched.append(slug)

        # Sync-state entry per feature (idempotent update).
        key = f"tasks/{feature_id}"
        sync_state[key] = {
            "taskNumber":   task_number,
            "taskObjectId": task_oid,
            "slug":         slug,
            "contentHash":  f"sha256:{local_hash}" if local_hash else sync_state.get(key, {}).get("contentHash"),
            "version":      row.get("version"),
            "lastPushed":   now,
        }
        recorded.append(slug)

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"recorded={len(recorded)} patched_frontmatter={len(patched)} failed={len(failed)}")
    for s in recorded: print(f"  recorded  {s}")
    for s in patched:  print(f"  patched   {s}/feature.md")
    for s, err in failed: print(f"  failed    {s}: {err}")
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
