"""Metadata-shape checks for governed transition contracts."""

from __future__ import annotations

from collections.abc import Sequence

from dev.scripts.devctl.runtime.governed_transitions import TransitionContract

from .models import GovernedTransitionPathCheck


def duplicate_transition_ids(transitions: Sequence[TransitionContract]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for transition in transitions:
        if transition.transition_id in seen:
            duplicates.add(transition.transition_id)
        seen.add(transition.transition_id)
    return duplicates


def shape_checks(
    transition: TransitionContract,
    duplicate_transition_ids: set[str],
) -> tuple[GovernedTransitionPathCheck, ...]:
    checks: list[GovernedTransitionPathCheck] = []
    transition_id = transition.transition_id or "<missing>"
    if not transition.transition_id:
        checks.append(_shape_failure(transition_id, "transition_id is required"))
    if transition.transition_id in duplicate_transition_ids:
        checks.append(_shape_failure(transition_id, "transition_id must be unique"))
    if not transition.owner_module:
        checks.append(_shape_failure(transition_id, "owner_module is required"))
    if not transition.function_name:
        checks.append(_shape_failure(transition_id, "function_name is required"))
    if not transition.requires:
        checks.append(_shape_failure(transition_id, "requires must not be empty"))
    if not transition.produces:
        checks.append(_shape_failure(transition_id, "produces must not be empty"))
    if not transition.emits:
        checks.append(_shape_failure(transition_id, "emits must not be empty"))
    if len(transition.graph_path) < 2:
        checks.append(
            _shape_failure(transition_id, "graph_path must contain at least two nodes")
        )
    return tuple(checks)


def _shape_failure(
    transition_id: str,
    reason: str,
) -> GovernedTransitionPathCheck:
    return GovernedTransitionPathCheck(
        transition_id=transition_id,
        check_kind="metadata_shape",
        from_ref="",
        to_ref="",
        ok=False,
        confidence="no_match",
        path_length=0,
        edge_kinds=(),
        reason=reason,
    )
