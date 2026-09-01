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
import re
import sys


# ---------------------------------------------------------------------------
# Trust-boundary helpers — every value that flows in from the bundle JSON
# (which is populated from MC via task-mcp.subtask_list) is treated as
# untrusted. A rogue teammate with MC write access, a compromised task-mcp
# instance, or a stale local cache could inject:
#   · path-traversal fragments (`..`, absolute paths, `/`) into
#     `subtaskRepo` or `parent_slug` → writes outside `features/<slug>/subtask/`
#   · YAML metacharacters or line breaks into ObjectIds / task_numbers →
#     breaks the frontmatter and mis-tags subsequent scalar keys
# We validate at the boundary and refuse rather than sanitize-and-hope.
# ---------------------------------------------------------------------------

# Strict slug: lowercase alnum + underscore + hyphen, must start alnum. Used
# for `parent_slug` (matches the on-disk feature folder name) and
# `subtaskRepo` (matches a key in .jetrix/cache/repolocation.json). Any value
# not matching is a design error or an attack — reject either way.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _is_safe_slug(value) -> bool:
    if not isinstance(value, str):
        return False
    if not value or len(value) > 128:
        return False
    return bool(_SLUG_RE.match(value))


def _safe_join(root: pathlib.Path, *parts: str) -> pathlib.Path | None:
    """Join a path under `root`, then verify the resolved path is still
    inside `root`. Returns None if the check fails.

    Belt-and-braces defence: even if the slug-regex misses a novel attack
    vector (encoded traversal, symlink shenanigans), the resolve+
    is_relative_to pair catches escape from the intended prefix.
    """
    candidate = root
    for p in parts:
        candidate = candidate / p
    try:
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    # Path.is_relative_to is 3.9+; the plugin's targeted runtime is 3.11+.
    if not resolved_candidate.is_relative_to(resolved_root):
        return None
    return candidate


# YAML frontmatter scalar sanitizer — reject values with control characters
# or leading YAML metacharacters, rather than try to escape them. All the
# real-world sources for these values (MC ObjectId, integer task_number,
# ISO timestamps, repo slugs) are single-line ASCII; anything else is
# either broken metadata or a payload smuggle attempt.
_YAML_UNSAFE_SCALAR = re.compile(r"[\r\n\x00-\x08\x0b-\x1f\x7f]")
_YAML_META_LEADING = ("#", "!", "&", "*", "|", ">", "%", "@", "`", "[", "]", "{", "}")


def _safe_yaml_scalar(value) -> str | None:
    """Return `value` verbatim if it is safe to inline as an unquoted YAML
    scalar. Returns None if the value would break the frontmatter shape.

    Accepts int / bool (str-formatted). Rejects strings containing newlines,
    carriage returns, NULs / other control chars, or leading YAML
    metacharacters. Callers should treat None as "reject this row".
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if len(s) > 512:
        return None
    if _YAML_UNSAFE_SCALAR.search(s):
        return None
    if s[0] in _YAML_META_LEADING:
        return None
    return s


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
    subtask_number,
    subtask_repo: str,
    subtask_object_id: str,
    subtask_task_number: str,
    generated_at: str,
    doc_type: str,
) -> list[str] | None:
    """Shared identity block for all three tab files (§v2.1 frontmatter).

    Every scalar goes through `_safe_yaml_scalar` — if any value fails
    validation (newlines, control chars, leading YAML metachar, overlong),
    the whole frontmatter is rejected by returning None. Caller treats None
    as a per-row skip so a single bad response can't poison every file.
    """
    values: list[tuple[str, object]] = [
        ("doc_type",                doc_type),
        ("schema_version",          "1.0"),
        ("produced_by",             "dev"),
        ("feature_id",              parent_feature_id),
        ("parent_task_object_id",   parent_task_object_id),
        ("parent_task_number",      parent_task_number),
        ("subtask_number",          subtask_number),
        ("subtask_repo",            subtask_repo),
        ("jetrix_subtask_object_id", subtask_object_id),
        ("jetrix_subtask_number",   subtask_task_number),
        ("composed_at",             generated_at),
    ]
    lines = ["---"]
    for key, raw in values:
        safe = _safe_yaml_scalar(raw)
        if safe is None:
            return None
        lines.append(f"{key}: {safe}")
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

    # Trust boundary: bundle originates from MC (via task-mcp.subtask_list).
    # A malicious or corrupted MC record could carry a `parent_slug` like
    # "../../etc" — refuse anything not matching the strict slug shape
    # before letting it near a filesystem operation.
    if not _is_safe_slug(parent_slug):
        print(json.dumps({
            "error": f"parent_slug {parent_slug!r} is not a valid slug "
                     "([a-z0-9][a-z0-9_-]*) — refusing to touch the filesystem"
        }))
        return 2

    # feature_id is also written into every frontmatter block — validate its
    # YAML-scalar shape now so a bad value halts once, not per-row.
    if _safe_yaml_scalar(parent_feature_id) is None:
        print(json.dumps({
            "error": f"parent_feature_id {parent_feature_id!r} contains "
                     "YAML-unsafe characters — refusing to write frontmatter"
        }))
        return 2

    if not isinstance(subtasks, list):
        print(json.dumps({"error": "bundle.subtasks is not a list"}))
        return 2

    features_root = (project_root / "features").resolve()
    parent_dir_target = _safe_join(features_root, parent_slug)
    if parent_dir_target is None:
        print(json.dumps({
            "error": f"parent_slug {parent_slug!r} resolves outside {features_root}"
        }))
        return 2
    parent_dir = parent_dir_target

    if not parent_dir.exists():
        # Parent feature folder must exist first — materialize-features.py
        # runs before this script in the pull flow.
        print(json.dumps({"error": f"parent feature folder not found: {parent_dir}"}))
        return 2

    subtask_root = parent_dir / "subtask"
    subtask_root_resolved = subtask_root.resolve() if subtask_root.exists() else (parent_dir / "subtask").resolve()

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

        # Trust boundary again: subtaskRepo is a JSON string from MC.
        # Refuse anything not matching a strict slug shape before joining
        # it into a path.
        if not _is_safe_slug(subtask_repo):
            warned.append(
                f"{subtask_task_num or subtask_object_id[:8]}: metadata.subtaskRepo "
                f"{subtask_repo!r} is not a valid slug — skipped (potential path-traversal payload)"
            )
            continue

        # Belt-and-braces containment check even after the slug regex.
        subtask_dir_target = _safe_join(subtask_root_resolved, subtask_repo)
        if subtask_dir_target is None:
            warned.append(
                f"{subtask_task_num or subtask_object_id[:8]}: subtask_repo "
                f"{subtask_repo!r} resolves outside {subtask_root_resolved} — skipped"
            )
            continue
        subtask_dir = subtask_dir_target
        subtask_dir.mkdir(parents=True, exist_ok=True)

        description    = st.get("description") or ""
        implementation = st.get("implementation_details") or ""
        ac             = st.get("acceptance_criteria") or ""
        ts             = st.get("test_scenarios") or ""
        mc_status      = st.get("status") or "todo"
        local_state    = _local_state(mc_status)

        # Description tab
        desc_fm_lines = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-description",
        )
        if desc_fm_lines is None:
            warned.append(
                f"{subtask_task_num or subtask_object_id[:8]}: identity field "
                "failed YAML sanitiser (control chars, newlines, or leading "
                "YAML metachar) — skipped"
            )
            continue
        desc_fm = desc_fm_lines + ["---"]
        desc_content = "\n".join(desc_fm) + "\n\n" + description.rstrip() + "\n"

        # Implementation tab
        impl_fm_lines = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-implementation",
        )
        # Guaranteed non-None since same values passed desc_fm; assert for safety.
        assert impl_fm_lines is not None
        impl_fm = impl_fm_lines + ["---"]
        impl_content = "\n".join(impl_fm) + "\n\n" + implementation.rstrip() + "\n"

        # Status tab — includes the current_state body block for /dev:build
        # + /dev:plan resume to read.
        status_fm_lines = _identity_frontmatter(
            parent_feature_id, parent_task_object_id, parent_task_number,
            subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
            now_iso, "subtask-status",
        )
        assert status_fm_lines is not None
        status_fm = status_fm_lines + ["---"]
        # local_state comes from our own _MC_STATUS_TO_LOCAL enum mapping
        # (bounded set) so it's guaranteed YAML-safe; sanity-check anyway.
        safe_state = _safe_yaml_scalar(local_state) or "PLANNED"
        status_content = (
            "\n".join(status_fm)
            + f"\n\ncurrent_state: {safe_state}\n"
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
            ac_fm_lines = _identity_frontmatter(
                parent_feature_id, parent_task_object_id, parent_task_number,
                subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
                now_iso, "subtask-acceptance-criteria",
            )
            assert ac_fm_lines is not None  # same values passed desc_fm
            ac_content = "\n".join(ac_fm_lines + ["---"]) + "\n\n" + ac.rstrip() + "\n"
            target = subtask_dir / "acceptance-criteria.md"
            if not target.exists() or target.read_text(encoding="utf-8") != ac_content:
                target.write_text(ac_content, encoding="utf-8")
                changed_any = True

        if ts.strip():
            ts_fm_lines = _identity_frontmatter(
                parent_feature_id, parent_task_object_id, parent_task_number,
                subtask_number, subtask_repo, subtask_object_id, subtask_task_num,
                now_iso, "subtask-test-scenarios",
            )
            assert ts_fm_lines is not None
            ts_content = "\n".join(ts_fm_lines + ["---"]) + "\n\n" + ts.rstrip() + "\n"
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
