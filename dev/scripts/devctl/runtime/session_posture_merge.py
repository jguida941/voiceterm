"""Actor merge helpers for SessionPosture."""

from __future__ import annotations

from dataclasses import replace


def merge_actor(actors: dict[str, object], actor: object | None) -> None:
    """Merge one posture actor by actor_id/provider."""
    if actor is None:
        return
    actor_id = getattr(actor, "actor_id", "") or getattr(actor, "provider", "")
    if not actor_id:
        return
    existing = actors.get(actor_id)
    if existing is None:
        actors[actor_id] = actor
        return
    capabilities = tuple(
        dict.fromkeys(
            (
                *getattr(existing, "granted_capabilities", ()),
                *getattr(actor, "granted_capabilities", ()),
            )
        )
    )
    actors[actor_id] = replace(
        existing,
        provider=getattr(existing, "provider", "") or getattr(actor, "provider", ""),
        role=getattr(existing, "role", "") or getattr(actor, "role", ""),
        occupied_lane=getattr(existing, "occupied_lane", "")
        or getattr(actor, "occupied_lane", ""),
        presence=merged_presence(existing, actor),
        live=bool(getattr(existing, "live", False) or getattr(actor, "live", False)),
        source=getattr(existing, "source", "") or getattr(actor, "source", ""),
        activity_age_seconds=(
            int(getattr(existing, "activity_age_seconds", 0) or 0)
            or int(getattr(actor, "activity_age_seconds", 0) or 0)
        ),
        current_activity=merged_activity(existing, actor),
        current_target=(
            getattr(existing, "current_target", "")
            or getattr(actor, "current_target", "")
        ),
        granted_capabilities=capabilities,
    )


def merged_presence(existing: object, actor: object) -> str:
    """Prefer live actor presence when it upgrades a stale/configured row."""
    if (
        getattr(actor, "live", False)
        and not getattr(existing, "live", False)
        and getattr(actor, "presence", "")
    ):
        return str(getattr(actor, "presence", ""))
    return str(getattr(existing, "presence", "") or getattr(actor, "presence", ""))


def merged_activity(existing: object, actor: object) -> str:
    """Prefer specific activity over the default waiting state."""
    current = str(getattr(existing, "current_activity", "") or "")
    incoming = str(getattr(actor, "current_activity", "") or "")
    if current and current != "waiting":
        return current
    return incoming or current or "waiting"


__all__ = ["merge_actor", "merged_activity", "merged_presence"]
