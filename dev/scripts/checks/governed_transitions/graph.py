"""Graph-walk orchestration for governed transition metadata."""

from __future__ import annotations

from collections.abc import Sequence

from dev.scripts.devctl.runtime.governed_transitions import TransitionContract

from .graph_build import build_transition_graph
from .models import GovernedTransitionPathCheck
from .shape import duplicate_transition_ids, shape_checks
from .walks import declared_graph_path_check, state_path_checks


def verify_transition_paths(
    transitions: Sequence[TransitionContract],
) -> tuple[GovernedTransitionPathCheck, ...]:
    """Verify transition state and metadata paths with context-graph walking."""
    nodes, edges = build_transition_graph(transitions)
    checks: list[GovernedTransitionPathCheck] = []
    duplicate_ids = duplicate_transition_ids(transitions)
    for transition in transitions:
        checks.extend(shape_checks(transition, duplicate_ids))
        if not transition.transition_id:
            continue
        checks.extend(state_path_checks(transition, nodes=nodes, edges=edges))
        if len(transition.graph_path) >= 2:
            checks.append(declared_graph_path_check(transition, nodes=nodes, edges=edges))
    return tuple(checks)
