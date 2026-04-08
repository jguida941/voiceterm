"""Shared governed coordination-snapshot loader for every read surface.

Every read model (``startup-context``, dashboard / ``ControlPlaneReadModel``,
``session-resume`` cache packet) must observe the same coordination snapshot
— same ``declared/observed/recommended_topology``, ``ownership_status``,
``resync_reasons``, and ``current_slice`` — or the MP-384/MP-387 parity
proof is vacuous. Before this module existed, each surface had its own
``_extract_coordination`` helper that first tried to deserialize a persisted
``coordination`` mapping out of the on-disk review-state payload, then only
fell back to a fresh ``build_coordination_snapshot_for_review_state`` build
(without forwarding the ``reviewer_gate``). Startup-context, meanwhile,
always built a fresh snapshot via ``build_coordination_snapshot`` with the
gate-aware ``WorkIntakeCoordinationState``. The result: dashboard and
session-resume saw raw review-state topology while startup-context saw the
gate-corrected topology, and the three surfaces diverged on live parity.

This helper unifies the path: given the already-loaded ``sources`` dict,
``governance``, and optional typed ``review_state`` / ``reviewer_gate``, it
always builds fresh via the same reducer as startup-context. The only
fallback to persisted ``coordination`` mappings is for bare-repo / legacy
test fixtures where no governance + typed review-state combination is
available.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..platform.coordination_snapshot_models import (
    CoordinationSnapshot,
    coordination_snapshot_from_mapping,
)

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState
    from .startup_context import ReviewerGateState


def load_coordination_snapshot(
    *,
    repo_root: Path,
    sources: dict[str, Any],
    governance: "ProjectGovernance | None",
    review_state: "ReviewState | None" = None,
    reviewer_gate: "ReviewerGateState | None" = None,
) -> CoordinationSnapshot | None:
    """Return the single governed coordination snapshot for a read surface.

    Resolution order:

    1. When ``governance`` and a typed ``review_state`` are available (either
       passed explicitly or parsed from ``sources``), build fresh via the
       canonical ``build_coordination_snapshot_for_review_state`` reducer.
       When ``reviewer_gate`` is not supplied, derive it from the typed
       review state the same way ``build_startup_context`` does so every
       surface sees the gate-corrected observed topology.
    2. Fall back to deserializing a persisted ``coordination`` mapping that
       may be embedded in the governed sources. This is the bare-repo /
       legacy-fixture path: callers without governance cannot take the
       typed reducer route, so the best we can do is echo whatever the
       source payload already carried.
    3. Return ``None`` when neither path yields a snapshot. Callers are
       responsible for their own graceful degradation; the read model
       surfaces it as ``coordination=None``.
    """
    typed_review_state = _resolve_typed_review_state(review_state, sources)

    if governance is not None and typed_review_state is not None:
        gate = reviewer_gate or _derive_reviewer_gate(
            typed_review_state, governance,
        )
        fresh = _build_fresh_snapshot(
            repo_root=repo_root,
            governance=governance,
            review_state=typed_review_state,
            reviewer_gate=gate,
        )
        if fresh is not None:
            return fresh

    return _load_persisted_fallback(sources)


def _resolve_typed_review_state(
    review_state: "ReviewState | None",
    sources: dict[str, Any],
) -> "ReviewState | None":
    """Parse a typed review-state from sources when the caller didn't supply one."""
    if review_state is not None:
        return review_state
    # Lazy import avoids a review_state_parser <-> coordination_loader cycle.
    from .review_state_parser import review_state_from_payload

    for key in ("review_state", "full_json"):
        payload = sources.get(key)
        if not isinstance(payload, dict):
            continue
        parsed = review_state_from_payload(payload)
        if parsed is not None:
            return parsed
    return None


def _derive_reviewer_gate(
    review_state: "ReviewState",
    governance: "ProjectGovernance",
) -> "ReviewerGateState | None":
    """Re-derive the reviewer gate the same way ``build_startup_context`` does.

    Dashboard and session-resume do not compute a ``ReviewerGateState`` today
    — they only derive a reviewer_dict from the read model. To keep the
    coordination reducer gate-aware for every surface, this helper builds a
    typed gate from the already-typed review state using the same private
    helper the startup-context builder relies on.
    """
    # Lazy import because startup_context imports this loader indirectly
    # through platform.coordination_snapshot at runtime.
    from .startup_context import _detect_reviewer_gate_from_review_state

    governance_mode = str(
        governance.bridge_config.operator_interaction_mode or ""
    ).strip()
    return _detect_reviewer_gate_from_review_state(
        review_state, governance_mode=governance_mode,
    )


def _build_fresh_snapshot(
    *,
    repo_root: Path,
    governance: "ProjectGovernance",
    review_state: "ReviewState",
    reviewer_gate: "ReviewerGateState | None",
) -> CoordinationSnapshot | None:
    """Call the typed reducer. Kept separate so the main function stays flat."""
    from ..platform.coordination_snapshot import (
        build_coordination_snapshot_for_review_state,
    )

    return build_coordination_snapshot_for_review_state(
        repo_root=repo_root,
        governance=governance,
        review_state=review_state,
        reviewer_gate=reviewer_gate,
    )


def _load_persisted_fallback(
    sources: dict[str, Any],
) -> CoordinationSnapshot | None:
    """Deserialize a persisted ``coordination`` mapping out of the sources dict.

    This only matters for bare-repo / legacy paths that cannot supply
    governance; the typed path in ``load_coordination_snapshot`` is always
    preferred when both governance and a typed review state are available.
    """
    for key in ("review_state", "full_json", "compact_json"):
        payload = sources.get(key)
        if not isinstance(payload, dict):
            continue
        direct = coordination_snapshot_from_mapping(payload.get("coordination"))
        if direct is not None:
            return direct
        nested = payload.get("review_state")
        if isinstance(nested, dict):
            direct = coordination_snapshot_from_mapping(nested.get("coordination"))
            if direct is not None:
                return direct
    return None


__all__ = ["load_coordination_snapshot"]
