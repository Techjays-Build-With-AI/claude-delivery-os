"""Apply `feature_update_implementation` responses — sync-state update only.

Invoked by `/jetrix:push implementation` (see plugins/jetrix/commands/references/push/implementation.md)
after the MCP call. Only touches sync-state — no frontmatter write-back (the
task_object_id in feature.md is already set by `/jetrix:push feature`, not
this stage).

Contract preserved:
  - Only rows with `ok:true` recorded
  - Sets `implementation_hash` on the `tasks/<feature_id>` entry
  - Merge-safe (existing keys under `tasks/<feature_id>` — taskNumber /
    taskObjectId / etc. — preserved)

Usage:
    python apply-implementation-responses.py \
        --responses  /tmp/impl-responses.json \
        --sync-state .jetrix/cache/sync-state.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
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


def apply(responses_path: pathlib.Path, sync_state_path: pathlib.Path) -> int:
    responses = _load_json(responses_path, [])
    if isinstance(responses, dict):
        responses = responses.get("features") or []
    if not responses:
        print("no responses to apply")
        return 0

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()

    recorded: list[str] = []
    failed:   list[tuple[str, str]] = []

    for row in responses:
        if not isinstance(row, dict) or not row.get("ok"):
            failed.append((row.get("slug") or row.get("feature_id") or "?", row.get("error") or "ok:false"))
            continue

        feature_id = row.get("feature_id")
        if not feature_id:
            continue
        state_key = f"tasks/{feature_id}"
        existing = sync_state.get(state_key, {}) if isinstance(sync_state.get(state_key), dict) else {}

        impl_hash = row.get("_local_impl_hash") or ""
        merged = dict(existing)
        if impl_hash:
            merged["implementation_hash"] = f"sha256:{impl_hash}"
        # Task version + object id are set by feature push; this stage's
        # response also carries version (from update). Overwrite only if provided.
        if row.get("task_object_id"):
            merged["taskObjectId"] = row["task_object_id"]
        if row.get("task_number") is not None:
            merged["taskNumber"] = row["task_number"]
        if row.get("version") is not None:
            merged["version"] = row["version"]
        merged["implementation_pushed_at"] = now

        sync_state[state_key] = merged
        recorded.append(row.get("slug") or feature_id)

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"recorded={len(recorded)} failed={len(failed)}")
    for s in recorded: print(f"  recorded {s}")
    for s, err in failed: print(f"  failed   {s}: {err}")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--responses",  required=True)
    ap.add_argument("--sync-state", required=True)
    args = ap.parse_args()

    return apply(
        responses_path=pathlib.Path(args.responses).resolve(),
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
    )


if __name__ == "__main__":
    sys.exit(main())
