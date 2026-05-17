"""Reviewer-checkpoint support helpers for `devctl review-channel`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...review_channel.plan_resolution import resolve_promotion_plan_path
from ...review_channel.promotion import (
    PromotionCandidate,
    derive_promotion_candidate,
    instruction_needs_plan_promotion,
)


@dataclass(frozen=True)
class ReviewerCheckpointPayload:
    """Typed file-backed reviewer-checkpoint payload."""

    verdict: str
    open_findings: str
    instruction: str
    reviewed_scope_items: tuple[str, ...]


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


def resolve_checkpoint_payload_file(
    *,
    repo_root: Path,
    file_value: object,
) -> ReviewerCheckpointPayload:
    """Read one typed reviewer-checkpoint payload from JSON."""
    path = Path(str(file_value))
    if not path.is_absolute():
        path = repo_root / path
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(
            "review-channel reviewer-checkpoint payload file must contain a JSON object."
        )
    verdict = _require_payload_text(loaded, key="verdict")
    open_findings = _require_payload_text(loaded, key="open_findings")
    instruction = _require_payload_text(loaded, key="instruction")
    reviewed_scope_items = _require_scope_items(loaded.get("reviewed_scope_items"))
    return ReviewerCheckpointPayload(
        verdict=verdict,
        open_findings=open_findings,
        instruction=instruction,
        reviewed_scope_items=reviewed_scope_items,
    )


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


def _require_payload_text(payload: dict[str, Any], *, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "review-channel reviewer-checkpoint payload file must define a "
            f"non-empty string `{key}`."
        )
    return value


def _require_scope_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(
            "review-channel reviewer-checkpoint payload file must define a "
            "non-empty `reviewed_scope_items` list."
        )
    normalized = tuple(
        str(item).strip()
        for item in value
        if isinstance(item, str) and str(item).strip()
    )
    if not normalized:
        raise ValueError(
            "review-channel reviewer-checkpoint payload file must define at least "
            "one non-empty `reviewed_scope_items` entry."
        )
    return normalized
