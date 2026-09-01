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

v2.1 additions (IMPLEMENTED):
  - Extended to also write `jetrix_task_number` (MC display number like
    `Feature-4`) alongside `jetrix_task_id` (MC numeric task_number).
  - Sub-task responses are handled via `--subtask-responses` — the plugin
    passes the `subtask_upsert_bundle` responses as a second file; the
    script patches each sub-task's tab-file frontmatter
    (`features/<parent_slug>/subtask/<subtaskRepo>/{description,implementation,status}.md`)
    with `jetrix_subtask_object_id` + `jetrix_subtask_number` and writes
    sync-state under `subtasks/<subtask_object_id>` per the shape in
    plugins/jetrix/commands/references/push/feature.md §7.
  - The existing parent-feature code path stays unchanged; sub-task work
    only runs when --subtask-responses is provided.

Usage:
    python apply-feature-responses.py \
        --responses    .jetrix/staging/push-features-responses.json \
        --project-root .jetrix \
        --sync-state   .jetrix/cache/sync-state.json

    (Legacy v1 workspaces pass `--project-root .jetrix/<slug>` instead; the
    caller auto-detects either shape.)

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


# ---------------------------------------------------------------------------
# Trust-boundary helpers — every value that flows in from the responses
# JSON (parent_slug from --responses, subtaskRepo from --subtask-responses)
# is treated as untrusted. Both files originate from task-mcp / MC, and a
# malicious record could smuggle path-traversal into `parent_slug` /
# `subtaskRepo` or YAML metacharacters into ObjectIds. Validate + refuse.
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _is_safe_slug(value) -> bool:
    if not isinstance(value, str):
        return False
    if not value or len(value) > 128:
        return False
    return bool(_SLUG_RE.match(value))


def _safe_join(root: pathlib.Path, *parts: str) -> pathlib.Path | None:
    """Join under `root` and require the resolved path to remain inside."""
    candidate = root
    for p in parts:
        candidate = candidate / p
    try:
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved_candidate.is_relative_to(resolved_root):
        return None
    return candidate


_YAML_UNSAFE_SCALAR = re.compile(r"[\r\n\x00-\x08\x0b-\x1f\x7f]")
_YAML_META_LEADING = ("#", "!", "&", "*", "|", ">", "%", "@", "`", "[", "]", "{", "}")


def _safe_yaml_scalar(value) -> str | None:
    """Return value as a safe unquoted YAML scalar, or None if unsafe."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s or len(s) > 512:
        return None
    if _YAML_UNSAFE_SCALAR.search(s):
        return None
    if s[0] in _YAML_META_LEADING:
        return None
    return s


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def _upsert_fm_key(fm_block: str, key: str, safe_value: str) -> str:
    """Insert-or-replace a single frontmatter key. `safe_value` MUST already
    be a validated single-line YAML scalar — caller runs `_safe_yaml_scalar`
    at the trust boundary and only passes through values that survived."""
    pattern = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
    if pattern.search(fm_block):
        return pattern.sub(f"{key}: {safe_value}", fm_block, count=1)
    sep = "" if fm_block.endswith("\n") else "\n"
    return f"{fm_block}{sep}{key}: {safe_value}\n"


def _patch_frontmatter_keys(md_path: pathlib.Path, keys: dict) -> bool:
    """Apply a set of {key: value} upserts to a markdown file's YAML
    frontmatter. Every value is run through `_safe_yaml_scalar` first;
    unsafe values (newlines, control chars, leading YAML metachars) are
    silently skipped so a poisoned key never corrupts the frontmatter.
    Returns True on write, False if no change or no frontmatter."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end_match = re.search(r"^---\s*$", text[3:], re.MULTILINE)
    if not end_match:
        return False
    fm_end = 3 + end_match.start()
    fm_block = text[3:fm_end]
    rest = text[fm_end:]

    new_block = fm_block
    for key, value in keys.items():
        if value is None:
            continue
        # Refuse frontmatter-key smuggling in the key itself too — writing a
        # key like "foo\nmalicious: bar" would inject an arbitrary line.
        if not isinstance(key, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        safe = _safe_yaml_scalar(value)
        if safe is None:
            continue
        new_block = _upsert_fm_key(new_block, key, safe)

    new_text = f"---{new_block}{rest}"
    if new_text != text:
        md_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def _patch_frontmatter(
    feature_md: pathlib.Path,
    task_number,
    task_object_id: str,
    task_display_number: str | None = None,
) -> bool:
    """Set jetrix_task_id + jetrix_task_object_id + (v2.1) jetrix_task_number
    in the frontmatter. Insert missing keys, replace present ones.
    Returns True on write.

    - `task_number` (int) → `jetrix_task_id` (existing convention)
    - `task_object_id` (24-hex str) → `jetrix_task_object_id` (existing)
    - `task_display_number` (str like "Feature-4") → `jetrix_task_number` (v2.1)
    """
    keys: dict = {
        "jetrix_task_id":        task_number,
        "jetrix_task_object_id": task_object_id,
    }
    if task_display_number:
        keys["jetrix_task_number"] = task_display_number
    return _patch_frontmatter_keys(feature_md, keys)


def _task_display_number(row: dict) -> str | None:
    """Some task-mcp response shapes carry a display-style number (e.g.
    'Feature-4') in a separate field; others emit only the integer
    `task_number` (4). If a display form is present under any of these
    common keys, use it verbatim; else construct `Feature-<int>` from the
    integer task_number as a v2.1-compatible fallback. Sub-task responses
    take precedence over feature responses because callers pick one path."""
    for k in ("task_number_display", "display_number", "jetrix_task_number"):
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    tn = row.get("task_number")
    if isinstance(tn, str) and tn.strip():
        return tn.strip()
    if isinstance(tn, int):
        return f"Feature-{tn}"
    return None


def _apply_features(
    responses: list,
    project_root: pathlib.Path,
    sync_state: dict,
    now: str,
) -> tuple[list, list, list]:
    """Handle parent-feature response rows. Returns (recorded, patched, failed)."""
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
        display_num   = _task_display_number(row)

        # Write-back frontmatter on create / recreate only. Also patches
        # v2.1's `jetrix_task_number` for /dev:plan Stage 0 lookup.
        if action in ("created", "recreated") and slug and task_number is not None and task_oid:
            # Trust boundary: slug came from the responses JSON (task-mcp's
            # echo of the payload slug field). Validate before joining it
            # into a path.
            if not _is_safe_slug(slug):
                failed.append((slug, "response slug is not a valid slug — refusing to patch feature.md"))
                continue
            features_root_r = (project_root / "features").resolve()
            feature_md_target = _safe_join(features_root_r, slug, "feature.md")
            if feature_md_target is None:
                failed.append((slug, f"slug {slug!r} resolves outside {features_root_r}"))
                continue
            feature_md = feature_md_target
            if feature_md.exists():
                if _patch_frontmatter(feature_md, task_number, task_oid, display_num):
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

    return recorded, patched, failed


def _apply_subtasks(
    subtask_bundle: dict,
    project_root: pathlib.Path,
    sync_state: dict,
    now: str,
) -> tuple[list, list, list]:
    """Handle sub-task response rows (v2.1).

    Bundle shape (matches subtask_upsert_bundle output, one per parent):
        {
          "parent_slug":            "supplier-onboarding",
          "parent_feature_id":      "FEAT-SUP-001",
          "parent_task_object_id":  "6a61...",
          "results": [
            {
              "subtask_number":    1,
              "external_id":       "FEAT-SUP-001-1",
              "subtask_object_id": "6b72...",
              "task_number":       "Subtask-7",
              "version":           1,
              "action":            "created",
              "ok":                true,
              "_local_content_hash": "sha256:..."
            },
            ...
          ]
        }

    Or a list of such bundles (multi-parent push).
    """
    if isinstance(subtask_bundle, list):
        bundles = subtask_bundle
    elif isinstance(subtask_bundle, dict):
        bundles = [subtask_bundle]
    else:
        return [], [], []

    patched: list[str] = []
    recorded: list[str] = []
    failed:  list[tuple[str, str]] = []

    for bundle in bundles:
        if not isinstance(bundle, dict):
            continue
        parent_slug           = str(bundle.get("parent_slug") or "").strip()
        parent_feature_id     = str(bundle.get("parent_feature_id") or "").strip()
        parent_task_object_id = str(bundle.get("parent_task_object_id") or "").strip()
        results               = bundle.get("results") or []

        if not parent_slug or not isinstance(results, list):
            continue

        # Trust boundary: parent_slug from the responses bundle is an
        # untrusted string. Reject anything that isn't a clean slug before
        # letting it near a filesystem path.
        if not _is_safe_slug(parent_slug):
            failed.append((
                f"bundle(parent_slug={parent_slug!r})",
                "not a valid slug — refusing to patch filesystem",
            ))
            continue

        # feature_id / parent_task_object_id are written into frontmatter;
        # validate their YAML-safe shape once per bundle.
        for field_name, value in (
            ("parent_feature_id",     parent_feature_id),
            ("parent_task_object_id", parent_task_object_id),
        ):
            if value and _safe_yaml_scalar(value) is None:
                failed.append((
                    f"bundle(parent_slug={parent_slug})",
                    f"{field_name} contains YAML-unsafe characters",
                ))
                # Fall through to per-row processing; downstream
                # _patch_frontmatter_keys will silently skip unsafe values.
                break

        for row in results:
            if not isinstance(row, dict):
                continue
            label_base = f"{parent_slug}/subtask/#{row.get('subtask_number')}"
            if not row.get("ok"):
                failed.append((label_base, row.get("error") or "ok:false"))
                continue

            external_id       = str(row.get("external_id") or "").strip()
            subtask_oid       = str(row.get("subtask_object_id") or "").strip()
            subtask_task_num  = row.get("task_number")  # e.g. "Subtask-7"
            subtask_number    = row.get("subtask_number")
            local_hash        = row.get("_local_content_hash") or ""

            if not subtask_oid or subtask_number is None:
                failed.append((label_base, "response missing subtask_object_id or subtask_number"))
                continue

            # Locate the sub-task's folder — subtask_repo is derived from
            # the parent's subtask/*/ walk (assemble emitted metadata.subtaskRepo
            # in the payload; the response echoes external_id but not
            # subtaskRepo). We recover subtaskRepo by inspecting the
            # response's echoed metadata OR by matching parent_feature_id +
            # subtask_number against the local `subtask/*/` folders. Prefer
            # the response's metadata when present.
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            subtask_repo = str(metadata.get("subtaskRepo") or "").strip()

            # Resolve the search root safely — parent_slug already validated
            # above; use _safe_join to be belt-and-braces against symlink /
            # encoded-traversal edge cases the slug regex might miss.
            features_root = (project_root / "features").resolve()
            parent_dir_target = _safe_join(features_root, parent_slug)
            if parent_dir_target is None:
                failed.append((label_base, f"parent_slug {parent_slug!r} resolves outside {features_root}"))
                continue
            parent_dir = parent_dir_target
            subtask_root = parent_dir / "subtask"

            if not subtask_repo and subtask_root.exists():
                # Fallback: find the folder whose description.md frontmatter's
                # subtask_number matches — one read per candidate, but usually
                # 1-3 subfolders per parent. Folder names discovered here come
                # from the local filesystem (user-controlled) so they don't
                # need the same untrusted-input validation, but we still slug-
                # check for consistency.
                try:
                    sn_int = int(subtask_number)
                except (TypeError, ValueError):
                    sn_int = None
                if sn_int is not None:
                    for cand in subtask_root.iterdir():
                        if not cand.is_dir() or not _is_safe_slug(cand.name):
                            continue
                        desc = cand / "description.md"
                        if not desc.exists():
                            continue
                        txt = desc.read_text(encoding="utf-8")
                        m = re.search(r"^subtask_number:\s*(\d+)", txt, re.MULTILINE)
                        if m and int(m.group(1)) == sn_int:
                            subtask_repo = cand.name
                            break

            if not subtask_repo:
                failed.append((
                    label_base,
                    "could not resolve subtask_repo from response metadata or local folders"
                ))
                continue

            # Trust boundary: subtask_repo came from `metadata.subtaskRepo`
            # (or a fallback filesystem walk — either way, treat it as
            # untrusted before joining into a path).
            if not _is_safe_slug(subtask_repo):
                failed.append((
                    label_base,
                    f"metadata.subtaskRepo {subtask_repo!r} is not a valid slug — "
                    "refusing to patch (potential path-traversal payload)",
                ))
                continue

            # Contain the final path under `subtask_root` — belt-and-braces
            # after the slug regex.
            try:
                subtask_root_resolved = subtask_root.resolve()
            except (OSError, RuntimeError):
                failed.append((label_base, f"could not resolve {subtask_root}"))
                continue
            subtask_dir_target = _safe_join(subtask_root_resolved, subtask_repo)
            if subtask_dir_target is None:
                failed.append((
                    label_base,
                    f"subtask_repo {subtask_repo!r} resolves outside {subtask_root_resolved}",
                ))
                continue
            subtask_dir = subtask_dir_target

            # Patch identity frontmatter on all three tab files. The values
            # here (subtask_oid, subtask_task_num) go through
            # `_patch_frontmatter_keys`, which silently drops any that fail
            # `_safe_yaml_scalar` — so an MC-injected ObjectId with an
            # embedded newline is dropped, not written.
            keys_to_upsert = {
                "jetrix_subtask_object_id": subtask_oid,
            }
            if subtask_task_num:
                keys_to_upsert["jetrix_subtask_number"] = str(subtask_task_num)

            patched_any = False
            for fname in ("description.md", "implementation.md", "status.md"):
                target = subtask_dir / fname
                if target.exists() and _patch_frontmatter_keys(target, keys_to_upsert):
                    patched_any = True
            if patched_any:
                patched.append(f"{parent_slug}/subtask/{subtask_repo}")

            # Sync-state entry per sub-task.
            state_key = f"subtasks/{subtask_oid}"
            existing_impl_hash = sync_state.get(state_key, {}).get("implementationHash")
            sync_state[state_key] = {
                "taskNumber":         subtask_task_num,
                "taskObjectId":       subtask_oid,
                "parentTaskObjectId": parent_task_object_id,
                "featureId":          parent_feature_id,
                "subtaskRepo":        subtask_repo,
                "subtaskNumber":      subtask_number,
                # contentHash covers description + implementation (matches
                # assemble-features.py's _subtask_content_hash).
                "contentHash":        f"sha256:{local_hash}" if local_hash else sync_state.get(state_key, {}).get("contentHash"),
                # implementationHash is written by apply-implementation-responses.py;
                # preserve it here so a bundle push doesn't wipe it.
                "implementationHash": existing_impl_hash,
                "version":            row.get("version"),
                "lastPushed":         now,
            }
            recorded.append(f"{parent_slug}/subtask/{subtask_repo}")

    return recorded, patched, failed


def apply(
    responses_path: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
    subtask_responses_path: pathlib.Path | None = None,
) -> int:
    responses = _load_json(responses_path, [])
    if not isinstance(responses, list):
        # Callers sometimes wrap the array in {"features":[...]} — accept both.
        responses = responses.get("features") if isinstance(responses, dict) else []

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()

    feat_recorded, feat_patched, feat_failed = _apply_features(
        responses, project_root, sync_state, now,
    )

    sub_recorded: list[str] = []
    sub_patched:  list[str] = []
    sub_failed:   list[tuple[str, str]] = []
    if subtask_responses_path is not None and subtask_responses_path.exists():
        subtask_bundle = _load_json(subtask_responses_path, {})
        sub_recorded, sub_patched, sub_failed = _apply_subtasks(
            subtask_bundle, project_root, sync_state, now,
        )

    if not responses and not sub_recorded and not sub_failed:
        print("no responses to apply")
        return 0

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    total_recorded = len(feat_recorded) + len(sub_recorded)
    total_patched  = len(feat_patched) + len(sub_patched)
    total_failed   = feat_failed + sub_failed

    print(
        f"recorded={total_recorded} "
        f"(features={len(feat_recorded)}, subtasks={len(sub_recorded)}) "
        f"patched_frontmatter={total_patched} "
        f"failed={len(total_failed)}"
    )
    for s in feat_recorded: print(f"  recorded  {s}")
    for s in feat_patched:  print(f"  patched   {s}/feature.md")
    for s in sub_recorded:  print(f"  recorded  {s}")
    for s in sub_patched:   print(f"  patched   {s}/*.md")
    for s, err in total_failed: print(f"  failed    {s}: {err}")
    return 1 if total_failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--responses",         required=True,
                    help="feature_upsert_bundle response JSON list.")
    ap.add_argument("--project-root",      required=True)
    ap.add_argument("--sync-state",        required=True)
    ap.add_argument("--subtask-responses", required=False, default=None,
                    help="v2.1: subtask_upsert_bundle response bundle JSON (per parent or list).")
    args = ap.parse_args()

    subtask_path = None
    if args.subtask_responses:
        subtask_path = pathlib.Path(args.subtask_responses).resolve()

    return apply(
        responses_path=pathlib.Path(args.responses).resolve(),
        project_root=pathlib.Path(args.project_root).resolve(),
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
        subtask_responses_path=subtask_path,
    )


if __name__ == "__main__":
    sys.exit(main())
