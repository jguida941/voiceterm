"""Bridge-liveness authority overlays from typed collaboration sessions."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import asdict, is_dataclass

from ..runtime.review_state_collaboration_models import CollaborationSessionState


def apply_collaboration_authority_liveness(
    bridge_liveness: MutableMapping[str, object],
    collaboration: CollaborationSessionState | None,
) -> None:
    """Expose role/capability authority to liveness classifiers."""
    if collaboration is None:
        return
    bridge_liveness["mutation_owner"] = _field(collaboration, "mutation_owner")
    bridge_liveness["verification_owner"] = _field(
        collaboration,
        "verification_owner",
    )
    bridge_liveness["verification_status"] = (
        _field(collaboration, "verification_status") or "inactive"
    )
    bridge_liveness["watcher_owner"] = _field(collaboration, "watcher_owner")
    bridge_liveness["watcher_status"] = _field(collaboration, "watcher_status")
    bridge_liveness["actor_authorities"] = [
        _actor_authority_dict(row)
        for row in tuple(getattr(collaboration, "actor_authorities", ()) or ())
    ]


def _actor_authority_dict(row: object) -> dict[str, object]:
    if isinstance(row, Mapping):
        return dict(row)
    if not is_dataclass(row):
        return {}
    payload = asdict(row)
    grants = payload.get("grants")
    if isinstance(grants, tuple):
        payload["grants"] = list(grants)
    return payload


def _field(source: object, field: str) -> str:
    return str(getattr(source, field, "") or "").strip()


__all__ = ["apply_collaboration_authority_liveness"]
