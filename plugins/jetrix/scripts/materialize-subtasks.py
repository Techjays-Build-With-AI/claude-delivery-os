"""Materialize `features/<slug>/subtask/<repo>/*.md` from a subtask_list JSON.

Invoked by `/jetrix:pull scope` (see plugins/jetrix/commands/references/pull/scope.md §7)
after each parent feature's sub-tasks are fetched via `task-mcp.subtask_list`.
Replaces the "for each sub-task, write three files" iteration in the plugin
markdown — the plugin does one task-mcp call per parent and one script call
per parent, not O(sub-tasks * 3) tool round-trips.

Usage:
    python materialize-subtasks.py \
        --bundle       .jetrix/cache/.pull-subtasks-<parent-slug>.json \
        --project-root .jetrix \
        --sync-state   .jetrix/cache/sync-state.json

The bundle file's shape (one per parent):
    {
      "parent_slug":            "supplier-onboarding",
      "parent_feature_id":      "FEAT-SUP-001",
      "parent_task_object_id":  "6a61...",
      "parent_task_number":     "Feature-4",
      "subtasks": [                           # verbatim from subtask_list.subtasks
        {
          "subtask_object_id":      "6b72...",
          "task_number":            "Subtask-7",
          "task_type":              "subtask",
          "title":                  "...",
          "status":                 "todo",
          "description":            "...",
          "implementation_details": "...",
          "acceptance_criteria":    "",       # usually empty; parent owns AC
          "test_scenarios":         "",       # usually empty; parent owns TS
          "metadata": {
            "externalId":       "FEAT-SUP-001-1",
            "parentExternalId": "FEAT-SUP-001",
            "subtaskNumber":    1,
            "subtaskRepo":      "backend",
            ...
          }
        },
        ...
      ]
    }

Writes three files per sub-task (only those with non-empty content — AC / TS
files are only written when the tab has content, matching push-side
convention: empty tab = no local file):

    features/<parent_slug>/subtask/<subtaskRepo>/
      description.md          # always written (Description tab)
      implementation.md       # always written (Implementation tab)
      status.md               # always written (mirrors MC status → PLANNED/etc.)

Sync-state entries land under `subtasks/<subtask_object_id>` with
`contentHash = sha256(description.md + implementation.md)` — matches
push-side skip-unchanged key so a re-push after a pull is a no-op.

Detached-subtask handling: local `subtask/<repo>/` folders whose IDs are NOT
in the incoming bundle are LEFT UNTOUCHED (do NOT delete), with a warning
printed. This avoids accidental data loss if MC's list is stale or a
sub-task was created locally but never pushed.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import sys


# Map MC status enum → local 5-state loop-control vocabulary
# (delivery-os-conventions §5 dev delivery state). Anything unrecognised
# defaults to PLANNED so we never write a state that isn't in the enum.
_MC_STATUS_TO_LOCAL = {
    "todo":           "PLANNED",
    "readyForDev":    "PLANNED",
    "inProgress":     "IN_PROGRESS",
    "agentExecuting": "IN_PROGRESS",
    "devReview":      "REVIEW",
    "inQaReview":     "REVIEW",
    "reopen":         "IN_PROGRESS",
    "blocked":        "BLOCKED",
    "done":           "DONE",
}


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _local_state(mc_status: str) -> str:
    return _MC_STATUS_TO_LOCAL.get((mc_status or "").strip(), "PLANNED")


def _identity_frontmatter(
    parent_feature_id: str,
    parent_task_object_id: str,
    parent_task_number: str,
    subtask_number: int,
    subtask_repo: str,
    subtask_object_id: str,
    subtask_task_number: str,
    generated_at: str,
    doc_type: str,
) -> list[str]:
    """Shared identity block for all three tab files (§v2.1 frontmatter)."""
    lines = ["---"]
    lines.append(f"doc_type: {doc_type}")
    lines.append("schema_version: 1.0")
    lines.append("produced_by: dev")
    lines.append(f"feature_id: {parent_feature_id}")
    lines.append(f"parent_task_object_id: {parent_task_object_id}")
    lines.append(f"parent_task_number: {parent_task_number}")
    lines.append(f"subtask_number: {subtask_number}")
    lines.append(f"subtask_repo: {subtask_repo}")
    lines.append(f"jetrix_subtask_object_id: {subtask_object_id}")
    lines.append(f"jetrix_subtask_number: {subtask_task_number}")
    lines.append(f"composed_at: {generated_at}")
    return lines


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def materialize(
    bundle_path: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
) -> int:
    bundle = _load_json(bundle_path, {})
    parent_slug           = str(bundle.get("parent_slug") or "").strip()
    parent_feature_id     = str(bundle.get("parent_feature_id") or "").strip()
    parent_task_object_id = str(bundle.get("parent_task_object_id") or "").strip()
    parent_task_number    = str(bundle.get("parent_task_number") or "").strip()
    subtasks              = bundle.get("subtasks") or []

    if not parent_slug or not parent_feature_id:
        print(json.dumps({"error": "bundle missing parent_slug or parent_feature_id"}))
        return 2

    if not isinstance(subtasks, list):
        print(json.dumps({"error": "bundle.subtasks is not a list"}))
        return 2

    parent_dir = project_root / "features" / parent_slug
    if not parent_dir.exists():
        # Parent feature folder must exist first — materialize-features.py
        # runs before this script in the pull flow.
        print(json.dumps({"error": f"parent feature folder not found: {parent_dir}"}))
        return 2

    subtask_root = parent_dir / "subtask"

    now = _iso_now()
    now_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    sync_state = _load_json(sync_state_path, {})

    updated:   list[str] = []
    unchanged: list[str] = []
    warned:    list[str] = []

    incoming_ids: set[str] = set()

    for st in subtasks:
        if not isinstance(st, dict):
            continue

        subtask_object_id = str(st.get("subtask_object_id") or "").strip()
        subtask_task_num  = str(st.get("task_number") or "").strip()
        if not subtask_object_id:
            continue
        incoming_ids.add(subtask_object_id)

        metadata = st.get("metadata") if isinstance(st.get("metadata"), dict) else {}
        subtask_repo   = str(metadata.get("subtaskRepo") or "").strip()
        subtask_number = metadata.get("subtaskNumber")

        # Metadata must include enough to route into the right local folder.
        # If MC ever loses the metadata (edge case: a sub-task created via UI
        # without the plugin's payload) we skip with a warning so it doesn't
        # land in a mystery location.
        if not subtask_repo or subtask_number is None:
            warned.append(
                f"{subtask_task_num or subtask_object_id[:8]}: missing "
                "metadata.subtaskRepo or subtaskNumber — skipped"
            )
            continue

        subtask_dir = subtask_root / subtask_repo
        subtask_dir.mkdir(parents=True, exist_ok=True)

        description    = st.get("description") or ""
        implementation = st.get("implementation_details") or ""
        ac             = st.get("acceptance_criteria") or ""
        ts             = st.get("test_scenarios") or ""
        mc_status      = st.get("status") or "todo"
        local_state    = _local_state(mc_status)

        # Description tab
        desc_fm = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-description",
        ) + ["---"]
        desc_content = "\n".join(desc_fm) + "\n\n" + description.rstrip() + "\n"

        # Implementation tab
        impl_fm = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-implementation",
        ) + ["---"]
        impl_content = "\n".join(impl_fm) + "\n\n" + implementation.rstrip() + "\n"

        # Status tab — includes the current_state body block for /dev:build
        # + /dev:plan resume to read.
        status_fm = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-status",
        ) + ["---"]
        status_content = (
            "\n".join(status_fm)
            + f"\n\ncurrent_state: {local_state}\n"
            + "owner_lock: null\n"
            + "branch: null\n"
        )

        changed_any = False

        for fname, content in (
            ("description.md",    desc_content),
            ("implementation.md", impl_content),
            ("status.md",         status_content),
        ):
            target = subtask_dir / fname
            old = target.read_text(encoding="utf-8") if target.exists() else None
            if old != content:
                target.write_text(content, encoding="utf-8")
                changed_any = True

        # Optional AC / TS tabs — only write local files when MC has content
        # for them. Empty tabs → no local file (matches push-side asymmetry:
        # empty string is never sent up, empty content is never written down).
        if ac.strip():
            ac_fm = _identity_frontmatter(
                parent_feature_id, parent_task_object_id, parent_task_number,
                subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
                now_iso, "subtask-acceptance-criteria",
            ) + ["---"]
            ac_content = "\n".join(ac_fm) + "\n\n" + ac.rstrip() + "\n"
            target = subtask_dir / "acceptance-criteria.md"
            if not target.exists() or target.read_text(encoding="utf-8") != ac_content:
                target.write_text(ac_content, encoding="utf-8")
                changed_any = True

        if ts.strip():
            ts_fm = _identity_frontmatter(
                parent_feature_id, parent_task_object_id, parent_task_number,
                subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
                now_iso, "subtask-test-scenarios",
            ) + ["---"]
            ts_content = "\n".join(ts_fm) + "\n\n" + ts.rstrip() + "\n"
            target = subtask_dir / "test-scenarios.md"
            if not target.exists() or target.read_text(encoding="utf-8") != ts_content:
                target.write_text(ts_content, encoding="utf-8")
                changed_any = True

        # Content hash — matches push-side (description + implementation only).
        content_hash = hashlib.sha256(
            (desc_content + impl_content).encode("utf-8")
        ).hexdigest()
        impl_hash = hashlib.sha256(impl_content.encode("utf-8")).hexdigest()

        state_key = f"subtasks/{subtask_object_id}"
        sync_state[state_key] = {
            "taskNumber":         subtask_task_num,
            "taskObjectId":       subtask_object_id,
            "parentTaskObjectId": parent_task_object_id,
            "featureId":          parent_feature_id,
            "subtaskRepo":        subtask_repo,
            "subtaskNumber":      subtask_number,
            "contentHash":        f"sha256:{content_hash}",
            "implementationHash": f"sha256:{impl_hash}",
            "lastPulled":         now,
        }

        label = f"{parent_slug}/subtask/{subtask_repo}"
        (updated if changed_any else unchanged).append(label)

    # Detached-subtask warning: any local subtask/<repo>/ folder whose
    # sync-state entry's object_id is NOT in incoming_ids has no MC
    # counterpart in this pull. Never delete — MC's list might be stale, or
    # the sub-task might have been intentionally created locally and not
    # pushed. Just warn.
    if subtask_root.exists():
        for local_sub in subtask_root.iterdir():
            if not local_sub.is_dir():
                continue
            # Find sync-state entry for this local subtask via subtaskRepo
            # match (there should be one per repo per parent).
            matched = False
            for key, entry in sync_state.items():
                if not key.startswith("subtasks/") or not isinstance(entry, dict):
                    continue
                if (
                    entry.get("featureId") == parent_feature_id
                    and entry.get("subtaskRepo") == local_sub.name
                    and key[len("subtasks/"):] in incoming_ids
                ):
                    matched = True
                    break
            if not matched and (local_sub / "description.md").exists():
                warned.append(
                    f"{parent_slug}/subtask/{local_sub.name}: no MC counterpart "
                    "in this pull (may have been deleted server-side — delete "
                    "manually if intentional)"
                )

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(
        f"updated={len(updated)} unchanged={len(unchanged)} "
        f"warned={len(warned)} parent={parent_slug}"
    )
    for s in updated:
        print(f"  updated   {s}")
    for s in unchanged:
        print(f"  unchanged {s}")
    for w in warned:
        print(f"  warn      {w}")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Materialize a parent feature's sub-task folders from a subtask_list JSON."
    )
    ap.add_argument("--bundle",       required=True,
                    help="Path to the per-parent subtask_list bundle JSON.")
    ap.add_argument("--project-root", required=True,
                    help="Absolute path to <workspace>/.jetrix/.")
    ap.add_argument("--sync-state",   required=True,
                    help="Absolute path to <workspace>/.jetrix/cache/sync-state.json.")
    args = ap.parse_args()

    return materialize(
        bundle_path=pathlib.Path(args.bundle),
        project_root=pathlib.Path(args.project_root),
        sync_state_path=pathlib.Path(args.sync_state),
    )


if __name__ == "__main__":
    sys.exit(main())
