"""Artifact-loading helpers for the control-plane read model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .control_plane_daemons import load_conductor_sources

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def read_json_artifact(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def artifact_paths(repo_root: Path) -> dict[str, Path]:
    """Resolve all artifact paths needed for the read model."""
    try:
        from ..repo_packs import active_path_config

        cfg = active_path_config()
        return _artifact_path_mapping(
            repo_root=repo_root,
            status_dir=cfg.review_status_dir_rel,
            review_state_rel=cfg.review_state_json_rel,
            push_report_rel=cfg.push_report_rel,
        )
    except Exception:  # broad-except: allow reason=repo-pack bootstrap can fail before path config is activated fallback=legacy review-status layout
        return _artifact_path_mapping(
            repo_root=repo_root,
            status_dir="dev/review_status",
            review_state_rel="dev/review_status/review_state.json",
            push_report_rel="dev/reports/push/latest/push_report.json",
        )


def load_sources(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
) -> dict[str, Any]:
    """Load every artifact the read model needs, exactly once.

    Review-state is loaded through ``load_current_review_state_payload`` so
    every governance surface (dashboard, session-resume, startup-context)
    observes the same bridge-refreshed projection instead of diverging
    across multiple persisted review-state files on disk.
    """
    paths = artifact_paths(repo_root)
    conductor_sources = load_conductor_sources(paths)
    # Imported lazily to avoid a control_plane_sources <-> review_state_locator
    # initialization cycle at module load time.
    from .review_state_locator import load_current_review_state_payload

    review_state_payload = load_current_review_state_payload(
        repo_root, governance=governance,
    )
    # Legacy fallback: environments without an overridden repo-pack config
    # and without a governance-backed review_root cannot produce a payload
    # through the typed locator. Drop back to ``paths["review_state"]`` so
    # older fixtures and bare repos keep working; the primary fresh-read
    # path above still satisfies the F1 parity contract in production.
    if review_state_payload is None:
        review_state_payload = read_json_artifact(paths["review_state"])
    sources: dict[str, Any] = {
        "receipt": read_json_artifact(paths["receipt"]),
        "review_state": review_state_payload,
        "push_report": read_json_artifact(paths["push_report"]),
        "publisher_hb": read_json_artifact(paths["publisher_hb"]),
        "supervisor_hb": read_json_artifact(paths["supervisor_hb"]),
    }
    sources["codex_conductor"] = conductor_sources.get("codex") or read_json_artifact(
        paths["codex_conductor"]
    )
    sources["claude_conductor"] = conductor_sources.get(
        "claude"
    ) or read_json_artifact(paths["claude_conductor"])
    sources["full_json"] = read_json_artifact(paths["full_json"])
    sources["compact_json"] = read_json_artifact(paths["compact_json"])
    return sources


def _artifact_path_mapping(
    *,
    repo_root: Path,
    status_dir: str,
    review_state_rel: str,
    push_report_rel: str,
) -> dict[str, Path]:
    paths: dict[str, Path] = {
        "receipt": repo_root / "dev/reports/startup/latest/receipt.json",
        "review_state": repo_root / review_state_rel,
        "push_report": repo_root / push_report_rel,
        "publisher_hb": repo_root / f"{status_dir}/publisher_heartbeat.json",
        "supervisor_hb": repo_root
        / f"{status_dir}/reviewer_supervisor_heartbeat.json",
    }
    paths["codex_conductor"] = repo_root / f"{status_dir}/sessions/codex-conductor.json"
    paths["claude_conductor"] = repo_root / f"{status_dir}/sessions/claude-conductor.json"
    paths["full_json"] = repo_root / f"{status_dir}/full.json"
    paths["compact_json"] = repo_root / f"{status_dir}/compact.json"
    return paths
