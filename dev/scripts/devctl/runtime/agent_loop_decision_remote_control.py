"""Remote-control capability projection for agent-loop decisions."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_decision_rows import (
    actor_row_matches,
    normalize_role,
    participant_rows,
)
from .agent_loop_decision_values import truthy
from .value_coercion import coerce_text as _text


def remote_control_checkpoint_capabilities(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    role: str = "",
) -> tuple[str, ...]:
    """Return VCS checkpoint grants from a live typed remote-control participant."""
    if normalize_role(role) != "implementer":
        return ()
    actor_id = _text(actor).lower()
    if not actor_id:
        return ()
    for row in participant_rows(review_state, dashboard):
        if not actor_row_matches(row, actor_id):
            continue
        if _text(row.get("capture_mode")) != "remote-control":
            continue
        if not truthy(row.get("live")):
            continue
        participant_role = normalize_role(row.get("role"))
        if participant_role not in {"operator", "implementer", "dashboard"}:
            continue
        return ("repo.stage", "repo.commit")
    return ()


__all__ = ["remote_control_checkpoint_capabilities"]
