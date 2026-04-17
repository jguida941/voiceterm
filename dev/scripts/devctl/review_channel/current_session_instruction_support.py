"""Instruction revision helpers for current-session projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_semantics import (
    is_missing_instruction,
    normalize_instruction_markdown,
)
from .handoff import BridgeSnapshot
from .reviewer_state_normalize import (
    instruction_revision as _normalized_instruction_revision,
    normalize_instruction_body as _normalize_instruction_body,
)
from .status_projection_helpers import clean_section


def resolve_instruction_revision(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    current_instruction: str,
    prior_review_state: Mapping[str, object] | None,
) -> str:
    """Return the current instruction revision for bridge-backed status."""
    revision = str(bridge_liveness.get("current_instruction_revision") or "").strip()
    if revision and _instruction_revision_reused_for_changed_instruction(
        revision=revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return _derived_instruction_revision(current_instruction)
    if revision:
        return revision

    revision = str(snapshot.metadata.get("current_instruction_revision") or "").strip()
    if revision and _instruction_revision_reused_for_changed_instruction(
        revision=revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return _derived_instruction_revision(current_instruction)
    if revision:
        return revision
    return _derived_instruction_revision(current_instruction)


def instruction_revision_reuse_warning(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None,
) -> str:
    """Return a warning when reviewer instruction text changed under one revision."""
    current_instruction = clean_section(snapshot.sections.get("Current Instruction For Claude", ""))
    explicit_revision = str(
        snapshot.metadata.get("current_instruction_revision")
        or bridge_liveness.get("current_instruction_revision")
        or ""
    ).strip()
    if not explicit_revision:
        return ""
    if not _instruction_revision_reused_for_changed_instruction(
        revision=explicit_revision,
        current_instruction=current_instruction,
        prior_review_state=prior_review_state,
    ):
        return ""
    derived_revision = _derived_instruction_revision(current_instruction)
    if not derived_revision:
        return ""
    return (
        "Current reviewer instruction text changed while `Current instruction "
        f"revision` stayed at `{explicit_revision}`. Typed state re-derived the "
        f"live revision as `{derived_revision}`; refresh reviewer-owned bridge "
        "metadata so the markdown header matches the current instruction body."
    )


def canonicalize_instruction_state(
    current_instruction: str,
    current_instruction_revision: str,
) -> tuple[str, str]:
    canonical_instruction = canonical_instruction_markdown(current_instruction)
    if is_missing_instruction(canonical_instruction):
        return canonical_instruction, ""
    revision = str(current_instruction_revision or "").strip()
    if canonical_instruction != current_instruction:
        raw_revision = _derived_instruction_revision(current_instruction)
        if not revision or revision == raw_revision:
            revision = _derived_instruction_revision(canonical_instruction)
    elif not revision and canonical_instruction:
        revision = _derived_instruction_revision(canonical_instruction)
    return canonical_instruction, revision


def canonical_instruction_markdown(current_instruction: str) -> str:
    return normalize_instruction_markdown(clean_section(current_instruction))


def _instruction_revision_reused_for_changed_instruction(
    *,
    revision: str,
    current_instruction: str,
    prior_review_state: Mapping[str, object] | None,
) -> bool:
    if not revision:
        return False
    prior_session = _mapping(_mapping(prior_review_state).get("current_session"))
    prior_revision = str(prior_session.get("current_instruction_revision") or "").strip()
    if prior_revision != revision:
        return False
    prior_instruction = _normalize_instruction_body(
        str(prior_session.get("current_instruction") or "")
    )
    current_normalized = _normalize_instruction_body(current_instruction)
    if not prior_instruction or not current_normalized:
        return False
    return prior_instruction != current_normalized


def _derived_instruction_revision(current_instruction: str) -> str:
    normalized_instruction = _normalize_instruction_body(current_instruction)
    if is_missing_instruction(normalized_instruction):
        return ""
    return _normalized_instruction_revision(normalized_instruction)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
