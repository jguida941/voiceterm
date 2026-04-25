"""Actor-authority projection helpers for AuthoritySnapshot."""

from __future__ import annotations

from collections.abc import Mapping

from .review_state_collaboration_models import (
    actor_authorities_from_value,
    granted_capabilities_for_actor,
)


def project_actor_authorities(
    *,
    payload: Mapping[str, object],
    collaboration: Mapping[str, object],
    actor_identity: str,
) -> tuple[tuple[str, ...], tuple[object, ...]]:
    """Resolve actor-authority rows and current actor capabilities."""
    actor_authorities = actor_authorities_from_value(
        collaboration.get("actor_authorities") or payload.get("actor_authorities")
    )
    actor_key = actor_identity or str(collaboration.get("mutation_owner") or "").strip()
    return (
        granted_capabilities_for_actor(
            actor_authorities,
            actor_key,
        ),
        actor_authorities,
    )


def authority_rows_for_output(value: object) -> list[object]:
    """Render authority rows with JSON-friendly grant lists."""
    if not isinstance(value, (list, tuple)):
        return []
    rows: list[object] = []
    for row in value:
        if not isinstance(row, Mapping):
            rows.append(row)
            continue
        rendered = dict(row)
        grants = rendered.get("grants")
        if isinstance(grants, tuple):
            rendered["grants"] = list(grants)
        rows.append(rendered)
    return rows
