"""Repair and rebuild the transitional markdown bridge projection."""

from __future__ import annotations

import json
from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_projection import (
    bridge_hygiene_errors,
    bridge_render_result_to_dict,
    render_bridge_projection,
)
from ...review_channel.core import filter_provider_lanes
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.state import (
    build_attach_auth_policy,
    build_service_identity,
    refresh_status_snapshot,
)
from ..review_channel_bridge_render import build_bridge_success_report


def run_render_bridge_action(
    *,
    args,
    repo_root: Path,
    paths,
) -> tuple[dict[str, object], int]:
    """Rebuild `bridge.md` from the tracked live sections and fixed template."""
    runtime_paths = paths if hasattr(paths, "bridge_path") else None
    review_channel_path = (
        runtime_paths.review_channel_path
        if runtime_paths is not None
        else paths["review_channel_path"]
    )
    bridge_path = (
        runtime_paths.bridge_path if runtime_paths is not None else paths["bridge_path"]
    )
    status_dir = (
        runtime_paths.status_dir if runtime_paths is not None else paths["status_dir"]
    )
    promotion_plan_path = (
        runtime_paths.promotion_plan_path
        if runtime_paths is not None
        else paths["promotion_plan_path"]
    )
    assert isinstance(review_channel_path, Path)
    assert isinstance(bridge_path, Path)
    assert isinstance(status_dir, Path)

    bridge_rel = str(bridge_path.relative_to(repo_root))
    worktree_hash = compute_non_audit_worktree_hash(
        repo_root=repo_root,
        excluded_rel_paths=(bridge_rel,),
    )
    typed_review_state = _load_typed_review_state(status_dir)
    render_result = None

    def transform(_bridge_text: str) -> str:
        nonlocal render_result
        rendered, render_result = render_bridge_projection(
            review_state=typed_review_state,
            last_worktree_hash=worktree_hash,
        )
        hygiene_errors = bridge_hygiene_errors(rendered)
        if hygiene_errors:
            raise ValueError("; ".join(hygiene_errors))
        return rendered

    rewrite_bridge_markdown(bridge_path, transform=transform)
    assert render_result is not None

    snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        promotion_plan_path=promotion_plan_path,
        execution_mode=args.execution_mode,
        warnings=[
            "Re-rendered `bridge.md` from typed review-state compatibility projection data."
        ],
        errors=[],
    )
    report, exit_code = build_bridge_success_report(
        args=args,
        bridge_liveness=snapshot.bridge_liveness,
        attention=snapshot.attention,
        reviewer_worker=snapshot.reviewer_worker,
        codex_lanes=filter_provider_lanes(snapshot.lanes, provider="codex"),
        claude_lanes=filter_provider_lanes(snapshot.lanes, provider="claude"),
        terminal_profile_applied=None,
        warnings=snapshot.warnings,
        sessions=[],
        handoff_bundle=None,
        projection_paths=snapshot.projection_paths,
        launched=False,
        handoff_ack_required=False,
        handoff_ack_observed=None,
        promotion=None,
        bridge_heartbeat_refresh=None,
        reviewer_state_write=None,
        execution_mode_override="markdown-bridge",
    )
    report["bridge_render"] = bridge_render_result_to_dict(render_result)
    service_identity = build_service_identity(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
    )
    report["service_identity"] = service_identity
    report["attach_auth_policy"] = build_attach_auth_policy(
        service_identity=service_identity,
    )
    return report, exit_code


def _load_typed_review_state(status_dir: Path) -> dict[str, object]:
    review_state_path = status_dir / "review_state.json"
    try:
        payload = json.loads(review_state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            "Missing typed review-state projection for `render-bridge`: "
            f"`{review_state_path}`. Refresh repo-owned review status before "
            "rebuilding `bridge.md`."
        ) from exc
    except (OSError, ValueError) as exc:
        raise ValueError(
            "Unable to load typed review-state projection for `render-bridge`: "
            f"`{review_state_path}`."
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "Typed review-state projection must be a JSON object before "
            "rebuilding `bridge.md`."
        )
    return payload
