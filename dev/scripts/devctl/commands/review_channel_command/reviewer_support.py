"""Reviewer-checkpoint support helpers for `devctl review-channel`."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.plan_resolution import resolve_promotion_plan_path
from ...review_channel.promotion import (
    PromotionCandidate,
    derive_promotion_candidate,
    instruction_needs_plan_promotion,
)


def resolve_checkpoint_body(
    *,
    repo_root: Path,
    inline_value: object,
    file_value: object,
    inline_flag: str,
    file_flag: str,
) -> str:
    """Return one reviewer-checkpoint body from inline text or a file."""
    has_inline = bool(inline_value)
    has_file = bool(file_value)
    if has_inline == has_file:
        raise ValueError(
            "review-channel reviewer-checkpoint requires exactly one of "
            f"{inline_flag} or {file_flag}."
        )
    if has_inline:
        return str(inline_value)
    path = Path(str(file_value))
    if not path.is_absolute():
        path = repo_root / path
    return path.read_text(encoding="utf-8")


def resolve_checkpoint_instruction(
    *,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path | None,
    instruction: str,
) -> tuple[str, PromotionCandidate | None]:
    """Auto-resolve generic reviewer instructions to a concrete plan item."""
    checkpoint_instruction = instruction
    if not instruction_needs_plan_promotion(checkpoint_instruction):
        return checkpoint_instruction, None
    resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        explicit_plan_path=promotion_plan_path,
    )
    if resolution.path is None:
        raise ValueError(
            "Cannot auto-promote generic reviewer instruction: scope_missing. "
            f"{resolution.detail or 'No scoped plan was resolved from bridge/tracker state.'}"
        )
    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=resolution.path,
        require_exists=True,
    )
    if candidate is None:
        return checkpoint_instruction, None
    return candidate.instruction, candidate
