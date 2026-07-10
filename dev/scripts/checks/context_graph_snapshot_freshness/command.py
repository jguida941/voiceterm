#!/usr/bin/env python3
"""Validate the latest ContextGraphSnapshot matches current HEAD.

P181 guard (R124 fleet finding): ContextGraphSnapshot can drift from HEAD when
source/contract/plan/guard/probe changes land but no snapshot refresh fires.
The post-commit hook refreshes ReviewSnapshot but NOT ContextGraphSnapshot.

This guard mirrors the `review_snapshot_freshness` package pattern. Reports
when the most-recent snapshot's commit_hash != current HEAD. Report-only mode
initially per P188 discipline (would_fail tracks but does not block).

Composes with:
- check_review_snapshot_freshness (sibling pattern)
- ContextGraphSnapshot contract (dev/scripts/devctl/context_graph/snapshot_payload.py)
- Snapshots live at dev/reports/graph_snapshots/{commit_sha}_{timestamp}.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_context_graph_snapshot_freshness"
CONTEXT_GRAPH_SNAPSHOT_FRESHNESS_GUARD_ID = "ContextGraphSnapshotFreshness"
CONTEXT_GRAPH_SNAPSHOT_FRESHNESS_CONTRACT_ID = "ContextGraphSnapshotFreshnessGuard"
DEFAULT_SNAPSHOT_DIR_REL = "dev/reports/graph_snapshots"


@dataclass(frozen=True, slots=True)
class ContextGraphSnapshotFreshnessGuard:
    """Registry-facing contract for the ContextGraph snapshot freshness report."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    head_sha: str
    latest_snapshot_path: str = ""
    latest_snapshot_commit_hash: str = ""
    snapshot_count: int = 0
    drift: bool = False
    detail: str = ""
    schema_version: int = 1
    contract_id: str = "ContextGraphSnapshotFreshnessGuard"
    command: str = "check_context_graph_snapshot_freshness"


def _resolve_head_sha(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, OSError):
        pass
    return ""


def _latest_snapshot_path(snapshot_dir: Path) -> Path | None:
    if not snapshot_dir.exists():
        return None
    candidates = sorted(snapshot_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    return candidates[0]


def _read_snapshot_commit_hash(snapshot_path: Path) -> str:
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    if isinstance(payload, dict):
        commit_hash = payload.get("commit_hash") or payload.get("head_sha")
        if isinstance(commit_hash, str):
            return commit_hash
    name = snapshot_path.name
    if "_" in name:
        return name.split("_", 1)[0]
    return ""


def evaluate_context_graph_snapshot_freshness(
    *,
    repo_root: Path = REPO_ROOT,
    snapshot_dir_rel: str = DEFAULT_SNAPSHOT_DIR_REL,
) -> ContextGraphSnapshotFreshnessGuard:
    snapshot_dir = repo_root / snapshot_dir_rel
    head_sha = _resolve_head_sha(repo_root)
    snapshots = sorted(snapshot_dir.glob("*.json")) if snapshot_dir.exists() else []
    snapshot_count = len(snapshots)
    latest = _latest_snapshot_path(snapshot_dir)

    if latest is None:
        return ContextGraphSnapshotFreshnessGuard(
            guard_id=CONTEXT_GRAPH_SNAPSHOT_FRESHNESS_GUARD_ID,
            ok=True,
            report_only=True,
            would_fail=True,
            head_sha=head_sha,
            snapshot_count=0,
            drift=True,
            detail="no ContextGraphSnapshot found in dev/reports/graph_snapshots/",
        )

    latest_commit_hash = _read_snapshot_commit_hash(latest)
    drift = bool(head_sha and latest_commit_hash and head_sha != latest_commit_hash)
    detail = (
        f"latest snapshot commit_hash={latest_commit_hash!r} matches HEAD"
        if not drift
        else f"drift: latest snapshot commit_hash={latest_commit_hash!r} but HEAD={head_sha!r}"
    )

    return ContextGraphSnapshotFreshnessGuard(
        guard_id=CONTEXT_GRAPH_SNAPSHOT_FRESHNESS_GUARD_ID,
        ok=True,
        report_only=True,
        would_fail=drift,
        head_sha=head_sha,
        latest_snapshot_path=str(latest.relative_to(repo_root)),
        latest_snapshot_commit_hash=latest_commit_hash,
        snapshot_count=snapshot_count,
        drift=drift,
        detail=detail,
    )


def _render_md(report: ContextGraphSnapshotFreshnessGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- head_sha: {report.head_sha}")
    lines.append(f"- snapshot_count: {report.snapshot_count}")
    lines.append(f"- latest_snapshot_path: {report.latest_snapshot_path}")
    lines.append(f"- latest_snapshot_commit_hash: {report.latest_snapshot_commit_hash}")
    lines.append(f"- drift: {report.drift}")
    lines.append(f"- detail: {report.detail}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_context_graph_snapshot_freshness()
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
