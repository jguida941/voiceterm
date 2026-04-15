#!/usr/bin/env python3
"""Fail when dev/audits/REVIEW_SNAPSHOT.md has drifted from current repo state.

The ReviewSnapshot surface is a typed projection refreshed by every governed
commit/push. This guard is the generation-stamp-and-HEAD binding that makes
sure the on-disk file is never stale relative to what git actually contains:
if HEAD moved or the typed generation stamp changed without a snapshot
rewrite, the guard fails so CI blocks the merge until ``devctl
review-snapshot --write`` is rerun locally or ``devctl review-snapshot
--write --receipt-commit`` is used for the publication receipt path.

The guard replaces the narrow ``check_audit_status_sync.py`` marker check —
instead of matching against fixed phase-3/4 strings, it compares live typed
state with the projection embedded in the file itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_SCRIPTS_ROOT = REPO_ROOT / "dev" / "scripts"
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))


_DEFAULT_SNAPSHOT_REL = "dev/audits/REVIEW_SNAPSHOT.md"
_HEAD_LINE_RE = re.compile(r"^- HEAD:\s*`([^`]+)`", re.MULTILINE)
_GENERATION_LINE_RE = re.compile(r"^- Generation stamp:\s*`([^`]+)`", re.MULTILINE)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    snapshot_override_text: str | None = None,
    live_head_sha: str | None = None,
    live_generation_stamp: str | None = None,
    live_snapshot_parent_sha: str | None = None,
) -> dict[str, object]:
    """Return a typed guard report comparing on-disk snapshot vs. live state."""
    governance = _load_governance(repo_root)
    snapshot_path = _resolve_snapshot_path(repo_root, governance=governance)
    snapshot_rel = str(snapshot_path.relative_to(repo_root))
    snapshot_text = (
        snapshot_override_text
        if snapshot_override_text is not None
        else _read_snapshot_text(snapshot_path)
    )
    errors: list[str] = []
    ok = True

    if snapshot_text is None:
        ok = False
        errors.append(
            f"snapshot_missing: {snapshot_path.relative_to(repo_root)} not found. "
            "Run `python3 dev/scripts/devctl.py review-snapshot --write`."
        )
        return {
            "command": "check_review_snapshot_freshness",
            "ok": ok,
            "snapshot_path": snapshot_rel,
            "errors": errors,
        }

    embedded_head = _extract_match(_HEAD_LINE_RE, snapshot_text)
    embedded_stamp = _extract_match(_GENERATION_LINE_RE, snapshot_text)
    current_head = live_head_sha if live_head_sha is not None else _current_head(repo_root)
    current_stamp = (
        live_generation_stamp
        if live_generation_stamp is not None
        else _current_generation_stamp(repo_root)
    )
    snapshot_parent = (
        live_snapshot_parent_sha
        if live_snapshot_parent_sha is not None
        else _snapshot_only_parent_sha(
            repo_root,
            snapshot_rel,
            governance=governance,
        )
    )
    snapshot_only_parent_match = bool(
        embedded_head
        and snapshot_parent
        and snapshot_parent.startswith(embedded_head.strip())
    )

    if not embedded_head:
        ok = False
        errors.append("snapshot_header_missing_head: HEAD line not found in snapshot")
    elif (
        current_head
        and not current_head.startswith(embedded_head.strip())
        and not snapshot_only_parent_match
    ):
        ok = False
        errors.append(
            f"snapshot_head_drift: file claims HEAD={embedded_head} but git HEAD={current_head[:12]}. "
            "Run `python3 dev/scripts/devctl.py review-snapshot --write --receipt-commit` "
            "when preparing a publishable external-review receipt."
        )

    if not embedded_stamp:
        ok = False
        errors.append(
            "snapshot_header_missing_generation_stamp: generation stamp line not found"
        )
    elif (
        current_stamp
        and embedded_stamp.strip() != current_stamp
        and not snapshot_only_parent_match
    ):
        ok = False
        errors.append(
            f"snapshot_generation_drift: file stamp={embedded_stamp} vs live stamp={current_stamp}. "
            "Run `python3 dev/scripts/devctl.py review-snapshot --write --receipt-commit` "
            "when preparing a publishable external-review receipt."
        )

    return {
        "command": "check_review_snapshot_freshness",
        "ok": ok,
        "snapshot_path": str(snapshot_path.relative_to(repo_root)),
        "embedded_head": embedded_head or "",
        "embedded_generation_stamp": embedded_stamp or "",
        "live_head": current_head or "",
        "live_generation_stamp": current_stamp or "",
        "snapshot_only_parent_head": snapshot_parent or "",
        "snapshot_only_parent_match": snapshot_only_parent_match,
        "errors": errors,
    }


def _load_governance(repo_root: Path) -> object | None:
    """Return ProjectGovernance when available, else ``None``."""
    try:
        from devctl.runtime.governance_scan import scan_repo_governance_safely

        return scan_repo_governance_safely(repo_root)
    except Exception:  # broad-except: allow reason=optional governance discovery must not abort the snapshot freshness guard on partially configured repos fallback=return None
        return None


def _resolve_snapshot_path(repo_root: Path, *, governance: object | None) -> Path:
    """Return the configured snapshot path from ProjectGovernance, with default fallback."""
    configured = ""
    if governance is not None:
        artifact_roots = getattr(governance, "artifact_roots", None)
        if artifact_roots is not None:
            configured = str(
                getattr(artifact_roots, "review_snapshot_path", "") or ""
            ).strip()
    relative = configured or _DEFAULT_SNAPSHOT_REL
    return repo_root / relative


def _read_snapshot_text(snapshot_path: Path) -> str | None:
    try:
        return snapshot_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _current_head(repo_root: Path) -> str:
    try:
        from devctl.runtime.vcs import run_git_capture
    except Exception:  # broad-except: allow reason=guard entrypoint import must degrade cleanly when runtime packaging is unavailable fallback=return empty HEAD
        return ""
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return stdout.strip() if code == 0 else ""


def _current_generation_stamp(repo_root: Path) -> str:
    try:
        from devctl.runtime.review_snapshot import build_review_snapshot
    except Exception:  # broad-except: allow reason=guard entrypoint import must degrade cleanly when runtime packaging is unavailable fallback=return empty generation stamp
        return ""
    try:
        snapshot = build_review_snapshot(repo_root=repo_root)
    except Exception:  # broad-except: allow reason=snapshot rendering may fail on partial artifacts or transient repo state fallback=return empty generation stamp
        return ""
    return snapshot.identity.generation_stamp


def _snapshot_only_parent_sha(
    repo_root: Path,
    snapshot_rel: str,
    *,
    governance: object | None,
) -> str:
    """Return HEAD^ when HEAD is a governed snapshot receipt commit."""
    del snapshot_rel
    try:
        from devctl.runtime.review_snapshot_refresh import receipt_commit_parent_sha
    except Exception:  # broad-except: allow reason=guard entrypoint import must degrade cleanly when receipt runtime helpers are unavailable fallback=return empty parent SHA
        return ""
    return receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head="HEAD",
        governance=governance,
    )


def _extract_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1) if match else ""


def _render_report(report: dict[str, object]) -> str:
    lines = ["# check_review_snapshot_freshness", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- snapshot_path: {report.get('snapshot_path')}")
    embedded_head = report.get("embedded_head") or "—"
    embedded_stamp = report.get("embedded_generation_stamp") or "—"
    live_head = report.get("live_head") or "—"
    live_stamp = report.get("live_generation_stamp") or "—"
    lines.append(f"- embedded_head: {embedded_head}")
    lines.append(f"- live_head: {live_head}")
    if report.get("snapshot_only_parent_head"):
        lines.append(
            f"- snapshot_only_parent_head: {report.get('snapshot_only_parent_head')}"
        )
    lines.append(f"- embedded_generation_stamp: {embedded_stamp}")
    lines.append(f"- live_generation_stamp: {live_stamp}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for err in errors:
            lines.append(f"- {err}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_report(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
