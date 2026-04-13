"""Contract-connectivity helpers for the governance closure guard."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_checks_dir = str(Path(__file__).resolve().parent.parent)
if _checks_dir not in sys.path:
    sys.path.insert(0, _checks_dir)

from check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_contract_connectivity = importlib.import_module(
    "dev.scripts.checks.contract_connectivity.report"
)
build_contract_connectivity_report = _contract_connectivity.build_report


def _repo_has_uncommitted_changes() -> bool:
    """Return True when the current repo checkout has worktree changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        return True
    return bool(result.stdout.strip())


def _previous_commit_ref() -> str:
    """Return ``HEAD^`` when it exists, otherwise an empty string."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _build_contract_connectivity_report_for_closure():
    """Load contract-connectivity in the strongest non-baseline mode available."""
    if _repo_has_uncommitted_changes():
        return build_contract_connectivity_report(repo_root=REPO_ROOT)
    previous_ref = _previous_commit_ref()
    if previous_ref:
        return build_contract_connectivity_report(
            repo_root=REPO_ROOT,
            since_ref=previous_ref,
            head_ref="HEAD",
        )
    return build_contract_connectivity_report(repo_root=REPO_ROOT)


def _find_contract_connectivity_orphan_gaps(
    violations: list[dict[str, str]],
) -> int:
    """Check the contract-connectivity guard for newly orphaned typed contracts."""
    report = _build_contract_connectivity_report_for_closure()
    found = 0
    for item in report.new_orphaned_contracts:
        detail = (
            f"Typed contract '{item.contract_name}' in '{item.module_path}' has no "
            f"external consumer proof (scope={item.consumer_scope}, mode={report.mode})."
        )
        violations.append(
            {
                "check": "contract_connectivity_orphan",
                "contract_name": item.contract_name,
                "module_path": item.module_path,
                "consumer_scope": item.consumer_scope,
                "mode": report.mode,
                "detail": detail,
            }
        )
        found += 1
    return found
