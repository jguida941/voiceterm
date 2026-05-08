"""Publication-deferral predicates for startup action routing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .action_routing_support import push_safe_to_continue

DEFER_SAFE_CHECKPOINT_REASONS = frozenset(
    {
        "dirty_path_budget_exceeded",
        "staged_and_unstaged_worktree_present",
    }
)
DIRTY_EDIT_DEFER_TOPOLOGIES = frozenset(
    {
        "no_live_agents",
        "implementer_without_reviewer",
    }
)
DIRTY_EDIT_DEFER_REASONS = frozenset({"worktree_dirty"})


@dataclass(frozen=True, slots=True)
class PublicationDeferDecision:
    """Bounded development-only deferral of final publication gates."""

    active: bool = False
    reason: str = ""
    deferred_command: str = ""
    blocked_actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PublicationDeferInput:
    """Inputs needed to decide whether publication can be deferred for edits."""

    ctx_payload: Mapping[str, object]
    next_command: str
    lane_edit_allowed: bool
    lane_permissions: tuple[str, ...]
    push: Mapping[str, object]
    permission: str
    defer_publication: bool
    caller_role: object = ""


def publication_defer_decision(
    spec: PublicationDeferInput,
) -> PublicationDeferDecision:
    """Return whether implementation edits may continue while push is deferred."""
    if not _allows_implementation_edit(spec):
        return PublicationDeferDecision()
    return PublicationDeferDecision(
        active=True,
        reason="publication_deferred_for_development",
        deferred_command=_deferred_publication_command(
            spec.ctx_payload,
            next_command=spec.next_command,
        ),
        blocked_actions=("vcs.stage", "vcs.commit", "vcs.push"),
    )


def _allows_implementation_edit(spec: PublicationDeferInput) -> bool:
    if not spec.defer_publication:
        return False
    if not spec.lane_edit_allowed:
        return False
    if "implementation.edit" not in spec.lane_permissions:
        return False
    if not _permission_allows_development_edit(spec):
        return False
    if not _checkpoint_deferable_for_editing(spec.push):
        return False
    return _publication_or_checkpoint_pending(
        spec.ctx_payload,
        push=spec.push,
    )


def _permission_allows_development_edit(spec: PublicationDeferInput) -> bool:
    if spec.permission == "active":
        return True
    if spec.permission not in {"blocked", "suspended"}:
        return False
    return _inactive_tools_only_loop_allows_edit_deferral(
        spec.ctx_payload,
        push=spec.push,
        caller_role=spec.caller_role,
    )


def _inactive_tools_only_loop_allows_edit_deferral(
    ctx_payload: Mapping[str, object],
    *,
    push: Mapping[str, object],
    caller_role: object,
) -> bool:
    """Allow edit-only build continuation when publication owns the stall.

    This is deliberately narrower than a takeover policy: it only applies to a
    bounded implementer lane while startup is in the transitional tools-only
    loop and the blocker is publication/checkpoint cleanliness. Stage, commit,
    and push remain blocked by the deferral decision.
    """
    if bool(push.get("checkpoint_required", False)):
        return False
    dirty = _worktree_has_edit_debt(push)
    if not push_safe_to_continue(push) and not (
        dirty and _dirty_edit_defer_context(ctx_payload, push=push)
    ):
        return False

    topology = _observed_topology(ctx_payload)
    if topology not in DIRTY_EDIT_DEFER_TOPOLOGIES:
        return False
    if topology == "implementer_without_reviewer" and _role(caller_role) != "implementer":
        return False
    if dirty and not _dirty_edit_defer_context(ctx_payload, push=push):
        return False

    mode = _effective_reviewer_mode(ctx_payload)
    if mode not in {"tools_only", "single_agent"}:
        return False

    return True


def _dirty_edit_defer_context(
    ctx_payload: Mapping[str, object],
    *,
    push: Mapping[str, object],
) -> bool:
    if _safe_int(push.get("staged_path_count")) > 0:
        return False
    if _safe_int(push.get("untracked_path_count")) > 0:
        return False
    push_decision = _mapping(ctx_payload.get("push_decision"))
    action = str(push_decision.get("action") or "").strip()
    reason = str(
        push_decision.get("reason") or push.get("checkpoint_reason") or ""
    ).strip()
    return action == "await_checkpoint" and reason in DIRTY_EDIT_DEFER_REASONS


def _worktree_has_edit_debt(push: Mapping[str, object]) -> bool:
    return (
        bool(push.get("worktree_dirty", False))
        or _safe_int(push.get("dirty_path_count")) > 0
        or _safe_int(push.get("unstaged_path_count")) > 0
        or _safe_int(push.get("untracked_path_count")) > 0
        or _safe_int(push.get("staged_path_count")) > 0
    )


def _checkpoint_deferable_for_editing(push: Mapping[str, object]) -> bool:
    """Return whether checkpoint pressure is safe to defer for edits.

    This is a positive list. New checkpoint reasons must be explicitly reviewed
    before they can reopen implementation edits while publication stays blocked.
    """
    if push_safe_to_continue(push):
        return True
    reason = str(push.get("checkpoint_reason") or "").strip()
    return reason in DEFER_SAFE_CHECKPOINT_REASONS


def _publication_or_checkpoint_pending(
    ctx_payload: Mapping[str, object],
    *,
    push: Mapping[str, object],
) -> bool:
    push_decision = _mapping(ctx_payload.get("push_decision"))
    push_action = str(push_decision.get("action") or ctx_payload.get("push_action") or "")
    advisory_action = str(ctx_payload.get("advisory_action") or "")
    recommended = str(push.get("recommended_action") or "")
    return (
        push_action.strip() == "run_devctl_push"
        or push_action.strip() == "await_checkpoint"
        or advisory_action.strip() == "push_allowed"
        or advisory_action.strip() in {"checkpoint_before_continue", "checkpoint_allowed"}
        or recommended.strip() in {"run_devctl_push", "use_devctl_push"}
        or recommended.strip() in {"checkpoint_before_continue", "commit_before_push"}
        or bool(ctx_payload.get("push_eligible_now", False))
        or _safe_int(push.get("ahead_of_upstream_commits")) > 0
        or _safe_int(push.get("pending_publication_commits")) > 0
    )


def _deferred_publication_command(
    ctx_payload: Mapping[str, object],
    *,
    next_command: str,
) -> str:
    push_decision = _mapping(ctx_payload.get("push_decision"))
    command = str(
        push_decision.get("next_step_command")
        or ctx_payload.get("push_next_step_command")
        or ""
    ).strip()
    if command:
        return command
    projected = str(next_command or "").strip()
    if (
        "devctl.py push" in projected
        or "devctl push" in projected
        or "devctl.py commit" in projected
        or "devctl commit" in projected
    ):
        return projected
    return "python3 dev/scripts/devctl.py push --execute"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _observed_topology(ctx_payload: Mapping[str, object]) -> str:
    return str(ctx_payload.get("observed_control_topology") or "").strip()


def _effective_reviewer_mode(ctx_payload: Mapping[str, object]) -> str:
    return str(
        ctx_payload.get("effective_reviewer_mode")
        or ctx_payload.get("reviewer_mode")
        or ""
    ).strip()


def _role(value: object) -> str:
    return str(value or "").strip()


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "DEFER_SAFE_CHECKPOINT_REASONS",
    "DIRTY_EDIT_DEFER_REASONS",
    "DIRTY_EDIT_DEFER_TOPOLOGIES",
    "PublicationDeferDecision",
    "PublicationDeferInput",
    "publication_defer_decision",
]
