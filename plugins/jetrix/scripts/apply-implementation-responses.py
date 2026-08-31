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
        --sync-state .jetrix/cache/sync-state.json \
        [--subtask-responses /tmp/subtask-impl-responses.json]

v2.1 additions (IMPLEMENTED):
  - Sub-task Implementation responses are handled via
    `--subtask-responses` — the plugin passes
    `subtask_update_implementation`'s bundle output as a second file. Each
    row's `implementationHash` lands under `subtasks/<subtask_object_id>`
    on sync-state, merge-safe with the parent's `subtask_upsert_bundle`
    fields (taskNumber / taskObjectId / parentTaskObjectId / etc.).
  - Existing feature code path stays unchanged.
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


def _apply_features(
    responses: list,
    sync_state: dict,
    now: str,
) -> tuple[list, list]:
    """Handle parent-feature response rows."""
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

    return recorded, failed


def _apply_subtasks(
    subtask_bundle,
    sync_state: dict,
    now: str,
) -> tuple[list, list]:
    """Handle sub-task Implementation-tab responses (v2.1).

    Bundle shape matches `subtask_update_implementation`'s response —
    a dict with `results: [...]`, or a list of such dicts for multi-parent
    pushes.

        {
          "parent_task_id": "6a61...",
          "results": [
            {
              "subtask_object_id": "6b72...",
              "external_id":       "FEAT-SUP-001-1",
              "task_number":       "Subtask-7",
              "version":           2,
              "ok":                true,
              "_local_impl_hash":  "sha256:..."
            },
            ...
          ]
        }
    """
    if isinstance(subtask_bundle, list):
        bundles = subtask_bundle
    elif isinstance(subtask_bundle, dict):
        # A single bundle OR a wrapped list under 'bundles' — accept both.
        maybe_list = subtask_bundle.get("bundles")
        if isinstance(maybe_list, list):
            bundles = maybe_list
        else:
            bundles = [subtask_bundle]
    else:
        return [], []

    recorded: list[str] = []
    failed:   list[tuple[str, str]] = []

    for bundle in bundles:
        if not isinstance(bundle, dict):
            continue
        results = bundle.get("results") or []
        if not isinstance(results, list):
            continue

        for row in results:
            if not isinstance(row, dict) or not row.get("ok"):
                label = row.get("subtask_object_id") or row.get("external_id") or "?"
                failed.append((label, row.get("error") or "ok:false"))
                continue

            subtask_oid = str(row.get("subtask_object_id") or "").strip()
            if not subtask_oid:
                continue

            state_key = f"subtasks/{subtask_oid}"
            existing = sync_state.get(state_key, {}) if isinstance(sync_state.get(state_key), dict) else {}
            merged = dict(existing)

            impl_hash = row.get("_local_impl_hash") or ""
            if impl_hash:
                merged["implementationHash"] = f"sha256:{impl_hash}" if not impl_hash.startswith("sha256:") else impl_hash
            if row.get("task_number"):
                merged["taskNumber"] = row["task_number"]
            if row.get("version") is not None:
                merged["version"] = row["version"]
            merged["taskObjectId"] = subtask_oid
            merged["implementation_pushed_at"] = now

            sync_state[state_key] = merged
            recorded.append(f"subtask:{row.get('external_id') or subtask_oid[:8]}")

    return recorded, failed


def apply(
    responses_path: pathlib.Path,
    sync_state_path: pathlib.Path,
    subtask_responses_path: pathlib.Path | None = None,
) -> int:
    responses = _load_json(responses_path, [])
    if isinstance(responses, dict):
        responses = responses.get("features") or []

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()

    feat_recorded, feat_failed = _apply_features(responses, sync_state, now)

    sub_recorded: list[str] = []
    sub_failed:   list[tuple[str, str]] = []
    if subtask_responses_path is not None and subtask_responses_path.exists():
        subtask_bundle = _load_json(subtask_responses_path, {})
        sub_recorded, sub_failed = _apply_subtasks(subtask_bundle, sync_state, now)

    if not responses and not sub_recorded and not sub_failed:
        print("no responses to apply")
        return 0

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    total_recorded = len(feat_recorded) + len(sub_recorded)
    total_failed   = feat_failed + sub_failed

    print(
        f"recorded={total_recorded} "
        f"(features={len(feat_recorded)}, subtasks={len(sub_recorded)}) "
        f"failed={len(total_failed)}"
    )
    for s in feat_recorded: print(f"  recorded {s}")
    for s in sub_recorded:  print(f"  recorded {s}")
    for s, err in total_failed: print(f"  failed   {s}: {err}")
    return 1 if total_failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--responses",         required=True,
                    help="feature_update_implementation response JSON list.")
    ap.add_argument("--sync-state",        required=True)
    ap.add_argument("--subtask-responses", required=False, default=None,
                    help="v2.1: subtask_update_implementation response bundle JSON.")
    args = ap.parse_args()

    subtask_path = None
    if args.subtask_responses:
        subtask_path = pathlib.Path(args.subtask_responses).resolve()

    return apply(
        responses_path=pathlib.Path(args.responses).resolve(),
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
        subtask_responses_path=subtask_path,
    )


if __name__ == "__main__":
    sys.exit(main())
