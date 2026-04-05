"""Portable path resolution and governance helpers for session-resume."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ...repo_packs import active_path_config
from ...runtime.governance_scan import scan_repo_governance_safely

if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance

_RECEIPT_ARTIFACT_SUBPATH = Path("startup/latest/receipt.json")


def resolve_source_paths(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> dict[str, Path]:
    """Return repo-relative Paths for receipt, compact, and review_state.

    Derives all paths from ``active_path_config()`` so session-resume stays
    portable across repo-packs without hardcoding VoiceTerm literals.
    """
    config = active_path_config()
    reports_root = config.reports_root_rel
    receipt_rel = Path(reports_root) / _RECEIPT_ARTIFACT_SUBPATH
    status_dir = config.review_status_dir_rel
    review_state_rel = Path(status_dir) / "review_state.json"
    compact_rel = Path(status_dir) / "compact.json"
    return {
        "receipt": receipt_rel,
        "review_state": review_state_rel,
        "compact": compact_rel,
    }


def get_review_state_mtime(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> float:
    """Return the mtime of the active review_state.json, or 0.0 if absent."""
    paths = resolve_source_paths(repo_root, governance=governance)
    return _file_mtime(repo_root / paths["review_state"])


def resolve_governance(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> "ProjectGovernance | None":
    """Return the provided governance or scan from repo root."""
    return governance or scan_repo_governance_safely(repo_root)


def governance_interaction_mode(
    governance: "ProjectGovernance | None",
) -> str:
    """Read operator_interaction_mode from governance BridgeConfig, or empty."""
    if governance is None:
        return ""
    return str(
        governance.bridge_config.operator_interaction_mode or ""
    ).strip()


def _file_mtime(path: Path) -> float:
    """Return the mtime of a file, or 0.0 if it does not exist."""
    try:
        return path.stat().st_mtime if path.is_file() else 0.0
    except OSError:
        return 0.0
