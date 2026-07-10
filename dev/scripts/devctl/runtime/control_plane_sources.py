"""Artifact-loading helpers for the control-plane read model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .control_plane_daemons import load_conductor_sources

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


def read_json_artifact(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def artifact_paths(
    repo_root: Path,
    *,
    review_status_dir: Path | None = None,
) -> dict[str, Path]:
    """Resolve all artifact paths needed for the read model."""
    if review_status_dir is not None:
        status_root = (
            review_status_dir
            if review_status_dir.is_absolute()
            else (repo_root / review_status_dir)
        )
        return _artifact_path_mapping(
            repo_root=repo_root,
            status_root=status_root,
            review_state_path=_projection_root_for_status_root(status_root)
            / "review_state.json",
            push_report_path=_push_report_path(repo_root),
        )
    try:
        from ..repo_packs import active_path_config

        cfg = active_path_config()
        return _artifact_path_mapping(
            repo_root=repo_root,
            status_root=repo_root / cfg.review_status_dir_rel,
            review_state_path=repo_root / cfg.review_state_json_rel,
            push_report_path=repo_root / cfg.push_report_rel,
        )
    except Exception:  # broad-except: allow reason=repo-pack bootstrap can fail before path config is activated fallback=legacy review-status layout
        return _artifact_path_mapping(
            repo_root=repo_root,
            status_root=repo_root / "dev/review_status",
            review_state_path=repo_root / "dev/review_status/review_state.json",
            push_report_path=repo_root / "dev/reports/push/latest/push_report.json",
        )


def load_sources(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
    review_status_dir: Path | None = None,
    review_state_override: "ReviewState | None" = None,
) -> dict[str, Any]:
    """Load every artifact the read model needs, exactly once.

    When ``review_state_override`` is supplied, the typed projection is
    consumed directly via ``review_state_override.to_dict()`` and the
    bridge-refreshing ``load_current_review_state_payload`` call is skipped
    entirely. This is the F1 / MP-384 parity contract: if a caller already
    resolved one frozen ``ReviewState`` for a proof tick, every governance
    surface (startup-context, dashboard, session-resume) must observe that
    exact snapshot instead of triggering an independent
    ``refresh_bridge_backed_review_state_payload`` reproject that could
    rewrite ``review_state.json`` mid-tick and desync the three surfaces.

    Without an override, review-state is still loaded through
    ``load_current_review_state_payload`` so every governance surface that
    has not pre-resolved its own typed snapshot still observes one
    bridge-refreshed projection per call.
    """
    paths = artifact_paths(repo_root, review_status_dir=review_status_dir)
    conductor_sources = load_conductor_sources(paths)
    if review_state_override is not None:
        review_state_payload: dict[str, Any] | None = review_state_override.to_dict()
    else:
        # Imported lazily to avoid a control_plane_sources <-> review_state_locator
        # initialization cycle at module load time.
        from .review_state_locator import (
            live_review_state_freshness_paths,
            load_current_review_state_payload,
        )

        review_state_payload = load_current_review_state_payload(
            repo_root,
            governance=governance,
            review_status_dir=review_status_dir,
        )
        # Legacy fallback: environments without an overridden repo-pack config
        # and without a governance-backed review_root cannot produce a payload
        # through the typed locator. Drop back to ``paths["review_state"]`` so
        # older fixtures and bare repos keep working. Do NOT fall back when live
        # bridge-backed freshness paths exist; that would silently reintroduce a
        # stale typed projection after the freshness-aware loader already refused
        # it.
        if review_state_payload is None and not live_review_state_freshness_paths(
            repo_root,
            governance=governance,
        ):
            review_state_payload = read_json_artifact(paths["review_state"])
    push_report_payload = read_json_artifact(paths["push_report"])
    if push_report_payload is None and not paths["push_report"].exists():
        push_report_payload = _read_legacy_push_report_artifact(repo_root)
    sources: dict[str, Any] = {
        "receipt": read_json_artifact(paths["receipt"]),
        "review_state": review_state_payload,
        "push_report": push_report_payload,
        "publisher_hb": read_json_artifact(paths["publisher_hb"]),
        "supervisor_hb": read_json_artifact(paths["supervisor_hb"]),
        "session_output_root": paths["publisher_hb"].parent,
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
    status_root: Path,
    review_state_path: Path,
    push_report_path: Path,
) -> dict[str, Path]:
    projection_root = _projection_root_for_status_root(status_root)
    paths: dict[str, Path] = {
        "receipt": repo_root / "dev/reports/startup/latest/receipt.json",
        "review_state": review_state_path,
        "push_report": push_report_path,
        "publisher_hb": status_root / "publisher_heartbeat.json",
        "supervisor_hb": status_root / "reviewer_supervisor_heartbeat.json",
    }
    paths["codex_conductor"] = status_root / "sessions" / "codex-conductor.json"
    paths["claude_conductor"] = status_root / "sessions" / "claude-conductor.json"
    paths["full_json"] = projection_root / "full.json"
    paths["compact_json"] = projection_root / "compact.json"
    return paths


def _projection_root_for_status_root(status_root: Path) -> Path:
    if status_root.name == "latest" and status_root.parent.name != "projections":
        return status_root.parent / "projections" / status_root.name
    return status_root


def _push_report_path(repo_root: Path) -> Path:
    try:
        from ..repo_packs import active_path_config

        return repo_root / active_path_config().push_report_rel
    except Exception:  # broad-except: allow reason=repo-pack bootstrap can fail before path config is activated fallback=legacy push-report layout
        return repo_root / "dev/reports/push/latest/push_report.json"


def _read_legacy_push_report_artifact(repo_root: Path) -> dict[str, Any] | None:
    try:
        from ..repo_packs import active_path_config

        rels = getattr(active_path_config(), "legacy_push_report_rels", ())
    except Exception:  # broad-except: allow reason=repo-pack path config fallback must not break read-only control-state projection fallback=skip legacy report scan
        rels = ()
    for rel in rels:
        relpath = str(rel).strip()
        if not relpath:
            continue
        payload = read_json_artifact(repo_root / relpath)
        if payload is not None:
            return payload
    return None
