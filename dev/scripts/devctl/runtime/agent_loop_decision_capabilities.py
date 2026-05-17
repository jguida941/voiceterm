"""Capability/action reconciliation for agent-loop decisions."""

from __future__ import annotations

_MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit"})
_MUTATION_ACTIONS = frozenset({"implementation.edit", "vcs.stage", "vcs.commit"})
_CAPABILITY_ACTIONS = {
    "repo.stage": ("vcs.stage",),
    "repo.commit": ("vcs.commit",),
}


def reconcile_actions_with_capability_grants(
    *,
    allowed_actions: tuple[str, ...],
    blocked_actions: tuple[str, ...],
    granted_capabilities: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Make action allow/block sets a thin adapter over actor capabilities."""
    granted_actions = capability_actions(granted_capabilities)
    if not granted_actions:
        return allowed_actions, blocked_actions
    allowed = list(allowed_actions)
    for action in granted_actions:
        if action not in allowed:
            allowed.append(action)
    blocked = tuple(action for action in blocked_actions if action not in granted_actions)
    return tuple(allowed), blocked


def capability_actions(granted_capabilities: tuple[str, ...]) -> frozenset[str]:
    actions: set[str] = set()
    for capability in granted_capabilities:
        actions.update(_CAPABILITY_ACTIONS.get(capability, ()))
    return frozenset(actions)


def may_actor_mutate(
    *,
    granted_capabilities: tuple[str, ...],
    allowed_actions: tuple[str, ...],
    blocked_actions: tuple[str, ...],
    edit_allowed: bool,
) -> bool:
    if not (_MUTATION_CAPABILITIES & set(granted_capabilities)):
        return False
    viable_actions = set(capability_actions(granted_capabilities))
    if edit_allowed and "implementation.edit" in allowed_actions:
        viable_actions.add("implementation.edit")
    if allowed_actions:
        viable_actions &= set(allowed_actions)
    viable_actions -= set(blocked_actions)
    if not viable_actions:
        return False
    return bool(_MUTATION_ACTIONS & viable_actions)


__all__ = [
    "capability_actions",
    "may_actor_mutate",
    "reconcile_actions_with_capability_grants",
]
