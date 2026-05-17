"""Scope and promotion-plan helpers for bridge launch actions."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.current_session_projection import bridge_implementer_state_hash
from ...review_channel.handoff import extract_bridge_snapshot
from ...review_channel.plan_resolution import resolve_promotion_plan_path
from ...review_channel.promotion import (
    DEFAULT_PROMOTION_PLAN_REL,
    derive_promotion_candidate,
    resolve_scope_plan_path,
    scope_bridge_instruction,
)
from ...review_channel.reviewer_state_support import (
    current_instruction_revision_from_bridge_text,
)


def resolve_launch_promotion_plan_path(
    *,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path | None,
    action: str,
) -> Path:
    """Resolve the launch-time promotion plan, with a default fallback for non-promote actions."""
    explicit_plan_path = (
        promotion_plan_path if isinstance(promotion_plan_path, Path) else None
    )
    plan_resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        explicit_plan_path=explicit_plan_path,
    )
    resolved_path = plan_resolution.path
    if resolved_path is None and action != "promote":
        return (repo_root / DEFAULT_PROMOTION_PLAN_REL).resolve()
    if action == "promote" and resolved_path is None:
        raise ValueError(
            "scope_missing: unable to resolve promotion plan path for promote action. "
            f"{plan_resolution.detail or 'Provide --promotion-plan or set bridge/tracker scope.'}"
        )
    assert resolved_path is not None
    return resolved_path


def apply_scope_if_requested(
    *, args, repo_root: Path, bridge_path: Path
) -> object | None:
    """Rewrite the bridge instruction from ``--scope`` before launch."""
    scope_value = getattr(args, "scope", None)
    if not scope_value:
        return None
    if args.action != "launch":
        raise ValueError("--scope is only supported with --action launch.")
    scope_plan_path = resolve_scope_plan_path(
        repo_root=repo_root,
        scope_value=scope_value,
    )
    if getattr(args, "dry_run", False):
        return derive_promotion_candidate(
            repo_root=repo_root,
            promotion_plan_path=scope_plan_path,
            require_exists=True,
        )
    expected_instruction_revision = getattr(
        args,
        "expected_instruction_revision",
        None,
    )
    expected_implementer_state_hash = getattr(
        args,
        "expected_implementer_state_hash",
        None,
    )
    if (
        not expected_instruction_revision or not expected_implementer_state_hash
    ) and bridge_path.exists():
        bridge_text = bridge_path.read_text(encoding="utf-8")
        if not expected_instruction_revision:
            expected_instruction_revision = (
                current_instruction_revision_from_bridge_text(bridge_text)
            )
        if not expected_implementer_state_hash:
            expected_implementer_state_hash = bridge_implementer_state_hash(
                extract_bridge_snapshot(bridge_text)
            )
    return scope_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        scope_plan_path=scope_plan_path,
        expected_instruction_revision=expected_instruction_revision,
        expected_implementer_state_hash=expected_implementer_state_hash,
    )


__all__ = ["apply_scope_if_requested", "resolve_launch_promotion_plan_path"]
