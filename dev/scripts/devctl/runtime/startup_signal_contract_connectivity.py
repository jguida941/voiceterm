"""Startup summary for contract-connectivity guard debt."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dev.scripts.checks.contract_connectivity.models import (
    ContractConnectivityReport,
    LayerContractCount,
    OrphanedContractFinding,
)
from dev.scripts.checks.contract_connectivity.report import build_report
from .startup_signal_io import load_json_file

_SUMMARY_REL_PATH = Path("dev/reports/contract_connectivity/latest/summary.json")
_CACHE_SCHEMA_VERSION = 1


def load_contract_connectivity_summary(repo_root: Path) -> dict[str, object] | None:
    """Return a bounded live summary of contract-connectivity debt."""
    head_sha = _head_sha(repo_root)
    worktree_dirty = _worktree_dirty(repo_root)
    cached = _load_cached_summary(repo_root, head_sha=head_sha)
    if cached:
        return _with_cache_state(cached, worktree_dirty=worktree_dirty)

    try:
        report = build_report(repo_root=repo_root)
    except (ImportError, OSError, RuntimeError, SyntaxError, TypeError, ValueError):
        return None

    summary = _summary_from_report(
        report,
        head_sha=head_sha,
        worktree_dirty=worktree_dirty,
    )
    _write_cached_summary(repo_root, summary)
    return summary


def _summary_from_report(
    report: ContractConnectivityReport,
    *,
    head_sha: str,
    worktree_dirty: bool,
) -> dict[str, object] | None:
    current_counts = {
        "orphaned": len(report.orphaned_contracts),
        "duplicates": len(report.duplicate_contracts),
        "stranded": len(report.stranded_consumers),
        "bidirectional": len(report.bidirectional_reference_findings),
    }
    baseline_counts = {
        "orphaned": report.baseline_orphaned_count,
        "duplicates": report.baseline_duplicate_count,
        "stranded": report.baseline_stranded_count,
        "bidirectional": report.baseline_bidirectional_reference_count,
    }
    new_counts = {
        "orphaned": len(report.new_orphaned_contracts),
        "duplicates": len(report.new_duplicate_contracts),
        "stranded": len(report.new_stranded_consumers),
        "bidirectional": len(report.new_bidirectional_reference_findings),
    }
    current_total = sum(current_counts.values())
    baseline_total = sum(baseline_counts.values())
    new_total = sum(new_counts.values())
    if not current_total and not baseline_total and not new_total:
        return None

    summary: dict[str, object] = {
        "schema_version": _CACHE_SCHEMA_VERSION,
        "cache_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cache_state": "live_scan",
    }
    summary.update({
        "head_sha": head_sha,
        "worktree_dirty": worktree_dirty,
        "mode": report.mode,
        "ok": report.ok,
        "severity": _severity(current_total=current_total, new_total=new_total),
    })
    summary.update({
        "contracts_scanned": report.contracts_scanned,
        "importer_modules_scanned": report.importer_modules_scanned,
        "current_counts": current_counts,
        "baseline_counts": baseline_counts,
        "new_counts": new_counts,
    })
    summary.update({
        "current_debt_count": current_total,
        "baseline_debt_count": baseline_total,
        "new_debt_count": new_total,
        "orphan_scope_counts": _orphan_scope_counts(report.orphaned_contracts),
        "top_layers": _top_layers(report.layer_counts),
    })
    summary["sample_findings"] = _sample_findings(report)
    summary["ai_instruction"] = _ai_instruction(
        current_total=current_total,
        baseline_total=baseline_total,
        new_total=new_total,
    )
    return summary


def _load_cached_summary(
    repo_root: Path,
    *,
    head_sha: str,
) -> dict[str, object] | None:
    payload = load_json_file(repo_root / _SUMMARY_REL_PATH)
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != _CACHE_SCHEMA_VERSION:
        return None
    if head_sha and payload.get("head_sha") != head_sha:
        return None
    return dict(payload)


def _write_cached_summary(repo_root: Path, summary: dict[str, object] | None) -> None:
    if not summary:
        return
    path = repo_root / _SUMMARY_REL_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return


def _with_cache_state(
    summary: dict[str, object],
    *,
    worktree_dirty: bool,
) -> dict[str, object]:
    cached = dict(summary)
    cached["cache_state"] = "stale_dirty_worktree" if worktree_dirty else "fresh"
    cached["worktree_dirty"] = worktree_dirty
    if worktree_dirty:
        instruction = str(cached.get("ai_instruction") or "").strip()
        suffix = (
            " Cached summary is HEAD-scoped; run check_contract_connectivity "
            "before closing dirty worktree connectivity debt."
        )
        cached["ai_instruction"] = (instruction + suffix).strip()
    return cached


def _head_sha(repo_root: Path) -> str:
    return _git_stdout(repo_root, "rev-parse", "HEAD")


def _worktree_dirty(repo_root: Path) -> bool:
    return bool(_git_stdout(repo_root, "status", "--porcelain"))


def _git_stdout(repo_root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _severity(*, current_total: int, new_total: int) -> str:
    if new_total:
        return "critical"
    if current_total >= 100:
        return "high"
    if current_total:
        return "medium"
    return "none"


def _orphan_scope_counts(items: tuple[OrphanedContractFinding, ...]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        counter[str(item.consumer_scope or "unknown")] += 1
    return dict(sorted(counter.items()))


def _top_layers(items: tuple[LayerContractCount, ...]) -> list[dict[str, object]]:
    rows = list(items)
    rows.sort(key=lambda row: row.contract_count, reverse=True)
    return [
        {
            "layer": row.layer,
            "contract_count": row.contract_count,
        }
        for row in rows[:4]
    ]


def _sample_findings(
    report: ContractConnectivityReport,
) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for item in report.new_orphaned_contracts[:2]:
        samples.append(
            {
                "kind": "new_orphaned",
                "contract": item.contract_name,
                "path": item.module_path,
                "scope": item.consumer_scope,
            }
        )
    for item in report.orphaned_contracts[:2]:
        if len(samples) >= 4:
            break
        samples.append(
            {
                "kind": "orphaned",
                "contract": item.contract_name,
                "path": item.module_path,
                "scope": item.consumer_scope,
            }
        )
    for item in report.duplicate_contracts[:1]:
        if len(samples) >= 4:
            break
        samples.append(
            {
                "kind": "duplicate",
                "contract": item.left_contract_name,
                "path": item.left_module_path,
                "paired_contract": item.right_contract_name,
                "paired_path": item.right_module_path,
            }
        )
    for item in report.stranded_consumers[:1]:
        if len(samples) >= 4:
            break
        samples.append(
            {
                "kind": "stranded",
                "contract": item.contract_name,
                "path": item.consumer_path,
                "contract_path": item.contract_module_path,
            }
        )
    return samples


def _ai_instruction(
    *,
    current_total: int,
    baseline_total: int,
    new_total: int,
) -> str:
    if new_total:
        return (
            "Do not add more contract surfaces until the new connectivity findings "
            "are wired, merged, or justified with typed closure evidence."
        )
    if baseline_total or current_total:
        return (
            "Prioritize contract connectivity closure: classify internal-only "
            "contracts, remove duplicate contract shapes, replace raw dict rebuilds "
            "with typed imports, and add closure receipts for accepted exceptions."
        )
    return ""
