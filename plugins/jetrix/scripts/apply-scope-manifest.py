"""Post-download apply step for `/jetrix:pull scope`.

Reads the curl parallel-download log, atomically moves successful transfers
from a staging dir into their final on-disk location, and updates
`sync-state.json` with per-file `documentId`, `version`, `contentHash`,
`lastPulled` sourced from the manifest sidecar.

Invoked by `/jetrix:pull scope` (see plugins/jetrix/commands/references/pull/scope.md)
after `curl --parallel` finishes. Replaces the "curl -o <final_path>" data-loss
pattern — on any non-200 the staging file is discarded and the local original
(if any) stays untouched.

Two write roots — decided from the relative path shape:
  * `.jetrix/…` paths are Solution-scoped singletons (e.g. `connection-map.md`)
    and land at `<workspace_root>/<rel>`.
  * every other path lands at `<project_root>/<rel>` (BA docs, registers,
    shared-context, feature-index).
See scope-mcp/app/tools/scope/pull_manifest.py — the manifest emits the
`.jetrix/…` prefix for docs tagged `connection-map`, so the plugin never
has to interpret tags here.

Usage:
    python apply-scope-manifest.py \
        --staging        /tmp/jetrix-pull-XXXX \
        --workspace-root <workspace> \
        --project-root   <workspace>/.jetrix/<solution-slug> \
        --sync-state     <workspace>/.jetrix/cache/sync-state.json \
        --curl-log       /tmp/curl-log-XXXX \
        --manifest       /tmp/manifest-XXXX.json

Backwards compatibility: `--workspace-root` is optional; if omitted, it
defaults to the parent of `.jetrix/` inferred from `--project-root` (so
callers that pass the pre-2026-08-20 arg set still work — every path lands
under `project_root` unless it explicitly starts with `.jetrix/`).

The curl log is a series of `<staged_absolute_path>|<http_code>` lines
(produced by `-w "%{filename_effective}|%{http_code}\n" --parallel`).
The manifest file is a JSON object keyed by relative path:
    { "ba-output/scope.md": { "documentId": "...", "version": 3, "contentHash": "..." }, ... }
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import shutil
import sys


# Prefix that flags a workspace-root-relative path (vs project-root-relative).
# Kept in sync with scope-mcp/app/tools/scope/pull_manifest.py::_WORKSPACE_ROOT_PATHS.
_WORKSPACE_ROOT_PREFIX = ".jetrix/"


def _iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        return default


def _resolve_target(rel_path: str, workspace_root: pathlib.Path, project_root: pathlib.Path) -> pathlib.Path:
    """Map a manifest-relative path to its final on-disk location.

    Paths under `.jetrix/…` are Solution-scoped singletons and resolve
    against workspace_root. Everything else is under `<project_root>/…`.
    """
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith(_WORKSPACE_ROOT_PREFIX):
        return workspace_root / normalized
    return project_root / normalized


def _infer_workspace_root(project_root: pathlib.Path) -> pathlib.Path:
    """Given `<workspace>/.jetrix/<slug>`, return `<workspace>`.

    Callers that don't pass --workspace-root fall back here. If the shape
    doesn't match (e.g. someone re-purposed --project-root), we return
    project_root itself — the workspace-root branch simply won't be used
    for any doc since no rel path will resolve inside it.
    """
    if project_root.parent.name == ".jetrix":
        return project_root.parent.parent
    return project_root


def apply(
    staging: pathlib.Path,
    workspace_root: pathlib.Path,
    project_root: pathlib.Path,
    sync_state_path: pathlib.Path,
    curl_log_path: pathlib.Path,
    manifest_path: pathlib.Path,
) -> int:
    manifest = _load_json(manifest_path, {})
    ok: list[str] = []
    fail: list[tuple[str, str]] = []

    for raw in curl_log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if "|" not in line:
            continue
        staged, code = line.rsplit("|", 1)
        staged = staged.strip()
        code = code.strip()
        if not staged.startswith(str(staging)):
            continue  # unrelated curl stderr line
        try:
            rel = str(pathlib.Path(staged).relative_to(staging)).replace("\\", "/")
        except ValueError:
            continue
        if code == "200":
            target = _resolve_target(rel, workspace_root, project_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(staged, target)
            ok.append(rel)
        else:
            fail.append((rel, code))

    sync_state = _load_json(sync_state_path, {})
    now = _iso_now()
    for rel in ok:
        meta = manifest.get(rel, {})
        ch = meta.get("contentHash") or ""
        entry = {
            "documentId":  meta.get("documentId"),
            "version":     meta.get("version"),
            "contentHash": f"sha256:{ch}" if ch and not ch.startswith("sha256:") else (ch or None),
            "lastPulled":  now,
        }
        sync_state[rel] = {k: v for k, v in entry.items() if v is not None}

    sync_state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_state_path.write_text(json.dumps(sync_state, indent=2), encoding="utf-8")

    print(f"downloaded={len(ok)} failed={len(fail)}")
    for rel in ok:
        print(f"  OK   {rel}")
    for rel, code in fail:
        print(f"  FAIL {rel} (HTTP {code})")
    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--staging",        required=True)
    ap.add_argument("--project-root",   required=True)
    ap.add_argument("--workspace-root", required=False,
                    help="Absolute workspace root (parent of .jetrix). "
                         "Defaults to inferring from --project-root.")
    ap.add_argument("--sync-state",     required=True)
    ap.add_argument("--curl-log",       required=True)
    ap.add_argument("--manifest",       required=True)
    args = ap.parse_args()

    project_root = pathlib.Path(args.project_root).resolve()
    workspace_root = (
        pathlib.Path(args.workspace_root).resolve()
        if args.workspace_root
        else _infer_workspace_root(project_root)
    )

    return apply(
        staging=pathlib.Path(args.staging).resolve(),
        workspace_root=workspace_root,
        project_root=project_root,
        sync_state_path=pathlib.Path(args.sync_state).resolve(),
        curl_log_path=pathlib.Path(args.curl_log).resolve(),
        manifest_path=pathlib.Path(args.manifest).resolve(),
    )


if __name__ == "__main__":
    sys.exit(main())
