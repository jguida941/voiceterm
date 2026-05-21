"""Neutral primitive for executor/subject proxy-execution detection.

Phase 0.6.C v4.41 (rev_pkt_4713 / plan row
``MP-GUARDIR-V4-PHASE-0-6-C-COORDINATION-LANE-IMPORT-ISOLATION-S1``):
``_proxy_execution`` previously lived inside ``control_decision_obedience``
alongside the larger ``ControlDecisionObedienceGuard`` substrate. Downstream
modules (``command_envelope_classification``, review-channel attempted-action
helpers) needed JUST this primitive, but importing it forced them to pull
in the whole control-decision-obedience graph — which in turn pulled
``control_decision_action_matching``, which in v4.40 pulled
``command_envelope_classification`` itself, creating a circular dependency
that broke the coordination lane (``agent-mind`` / ``review-channel``).

This module owns the neutral primitive. It has no dependencies beyond
the tiny ``value_coercion`` helpers, so it can be imported safely from
any layer (classifier, review-channel adapter, control-decision-obedience,
etc.) without creating cycles.

The semantics of ``_proxy_execution`` are unchanged: True when executor !=
subject (across actor/role/session), False when they are aligned. The
public surface for downstream callers is also unchanged — ``proxy_execution``
without the underscore is the canonical name; the underscore-prefixed name
is preserved as an alias for legacy imports.
"""

from __future__ import annotations


def proxy_execution(
    *,
    executor_actor: str,
    executor_role: str,
    executor_session_id: str,
    subject_actor: str,
    subject_role: str,
    subject_session_id: str,
) -> bool:
    """Return True when the executor identity differs from the subject identity.

    The semantics match the historical ``control_decision_obedience._proxy_execution``:
    executor == subject (same actor + role + session) → False (not proxied)
    executor != subject (any of the three dimensions differs) → True (proxied).

    Used by:
    - ``command_envelope_classification`` for actor/proxy classification
    - ``control_decision_obedience`` for attempted-action proxy-violation checks
    - ``review_channel/event_attempted_action_scope`` for proxy authority refs
    """
    if not executor_actor or not subject_actor:
        return False
    if executor_actor != subject_actor:
        return True
    if executor_role and subject_role and executor_role != subject_role:
        return True
    if (
        executor_session_id
        and subject_session_id
        and executor_session_id != subject_session_id
    ):
        return True
    return False


#: Backwards-compatible alias for the historical underscore-prefixed name.
#: Callers should migrate to ``proxy_execution`` (no underscore), but the
#: underscore form is retained so existing imports do not break.
_proxy_execution = proxy_execution


__all__ = ["_proxy_execution", "proxy_execution"]
