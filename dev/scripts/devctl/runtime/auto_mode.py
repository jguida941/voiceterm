"""Typed auto-mode state machine for the continuous governance loop.

The auto-mode loop tracks the current phase of the default git-publishing
agent lifecycle: reviewing -> implementing -> testing -> committing -> pushing
-> idle. Non-publishing delivery modes reuse the same phases but skip
commit/push terminal pressure.

AutoModePhase is the typed enum for each phase.  AutoModeState captures
the resolved snapshot including which agents are alive, the last guard
outcome, and the next expected transition.  resolve_auto_mode_phase()
derives the current phase from repo-owned typed state (review_state,
push decision, guard results) so downstream surfaces can render what
the system is doing and what should happen next.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .project_governance_contract import (
    DELIVERY_MODE_GIT_PUSH_REQUIRED,
    DELIVERY_MODE_LIBRARY_IMPORT_ONLY,
    DELIVERY_MODE_LOCAL_EDIT_ONLY,
    delivery_mode_requires_push,
    normalize_delivery_mode,
)
from .enum_compat import StrEnum
from .value_coercion import coerce_bool, coerce_int, coerce_mapping, coerce_string


class AutoModePhase(StrEnum):
    """Named phases of the continuous auto-mode lifecycle."""

    REVIEWING = "reviewing"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    COMMITTING = "committing"
    PUSHING = "pushing"
    IDLE = "idle"


AUTO_MODE_CONTRACT_ID = "AutoModeState"
AUTO_MODE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class AutoModeState:
    """Typed snapshot of the current auto-mode phase and transition hint."""

    phase: str = AutoModePhase.IDLE.value
    phase_started_utc: str = ""
    operator_interaction_mode: str = "local_terminal"
    reviewer_alive: bool = False
    implementer_alive: bool = False
    last_commit_sha: str = ""
    last_guard_ok: bool = True
    pending_action_requests: int = 0
    next_transition: str = ""
    delivery_mode: str = DELIVERY_MODE_GIT_PUSH_REQUIRED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AutoModeInputs:
    """Derived inputs collected from repo-owned typed state."""

    push_decision_action: str = ""
    push_decision_reason: str = ""
    worktree_clean: bool = True
    review_gate_allows_push: bool = False
    reviewer_mode: str = "single_agent"
    implementation_blocked: bool = False
    implementer_status: str = ""
    last_guard_ok: bool = True
    current_head_commit: str = ""
    last_reviewed_sha: str = ""
    pending_action_requests: int = 0
    operator_interaction_mode: str = "local_terminal"
    delivery_mode: str = DELIVERY_MODE_GIT_PUSH_REQUIRED
    timestamp_utc: str = ""


# Phase transition table: maps current conditions to the next expected step
# so operators and agents know what the system expects to happen.
_TRANSITION_AWAIT_CHECKPOINT = "commit current work, then rerun startup-context"
_TRANSITION_AWAIT_REVIEW = "wait for reviewer acceptance before push"
_TRANSITION_AWAIT_PARTICIPANT = (
    "resume a live participant before commit/push can continue"
)
_TRANSITION_RUN_PUSH = "run governed push via devctl push --execute"
_TRANSITION_RUN_GUARDS = "run guard bundle to validate current edits"
_TRANSITION_CONTINUE_IMPLEMENTING = "continue editing toward the current slice"
_TRANSITION_IDLE = "no active work; start a new slice or await instructions"
_TRANSITION_HEAD_DRIFT = "HEAD moved past last reviewed commit; review the new commits"
_TRANSITION_LOCAL_DELIVERY_IDLE = (
    "delivery mode does not require governed push; start the next local or library task"
)


def resolve_auto_mode_phase(inputs: AutoModeInputs) -> AutoModeState:
    """Derive the current auto-mode phase from repo-owned typed state.

    The resolution order mirrors the governance pipeline priority:
    1. Commit/push phases require a live participant.
    2. Push action overrides (committing/pushing phases).
    3. Guard failure forces testing phase.
    4. Reviewer-blocked forces reviewing phase.
    5. Dirty worktree with work in progress forces implementing phase.
    6. Otherwise idle.
    """
    reviewer_alive = inputs.reviewer_mode in (
        "active_dual_agent",
        "dual_agent",
    )
    implementer_alive = inputs.implementer_status in (
        "implementing",
        "active",
        "coding",
    )

    phase, next_transition = _resolve_phase_and_transition(
        inputs,
        reviewer_alive=reviewer_alive,
        implementer_alive=implementer_alive,
    )

    return AutoModeState(
        phase=phase,
        phase_started_utc=inputs.timestamp_utc,
        operator_interaction_mode=inputs.operator_interaction_mode,
        reviewer_alive=reviewer_alive,
        implementer_alive=implementer_alive,
        last_commit_sha=inputs.current_head_commit,
        last_guard_ok=inputs.last_guard_ok,
        pending_action_requests=inputs.pending_action_requests,
        next_transition=next_transition,
        delivery_mode=normalize_delivery_mode(inputs.delivery_mode),
    )


def _resolve_by_non_push_delivery_mode(inputs: AutoModeInputs) -> tuple[str, str] | None:
    delivery_mode = normalize_delivery_mode(inputs.delivery_mode)
    if delivery_mode_requires_push(delivery_mode):
        return None
    if not inputs.last_guard_ok:
        return AutoModePhase.TESTING.value, _TRANSITION_RUN_GUARDS
    if inputs.implementation_blocked:
        return AutoModePhase.REVIEWING.value, _TRANSITION_AWAIT_REVIEW
    if not inputs.worktree_clean:
        return AutoModePhase.IMPLEMENTING.value, _TRANSITION_CONTINUE_IMPLEMENTING
    if delivery_mode == DELIVERY_MODE_LIBRARY_IMPORT_ONLY:
        return AutoModePhase.IDLE.value, _TRANSITION_LOCAL_DELIVERY_IDLE
    if delivery_mode == DELIVERY_MODE_LOCAL_EDIT_ONLY:
        return AutoModePhase.IDLE.value, _TRANSITION_LOCAL_DELIVERY_IDLE
    return AutoModePhase.IDLE.value, _TRANSITION_LOCAL_DELIVERY_IDLE


def _resolve_by_push_decision(
    inputs: AutoModeInputs,
    *,
    reviewer_alive: bool,
    implementer_alive: bool,
) -> tuple[str, str] | None:
    action = inputs.push_decision_action
    if not reviewer_alive and not implementer_alive:
        if action == "run_devctl_push" or (
            action == "await_checkpoint" and not inputs.worktree_clean
        ):
            return (
                AutoModePhase.REVIEWING.value,
                _TRANSITION_AWAIT_PARTICIPANT,
            )
    if action == "run_devctl_push":
        return AutoModePhase.PUSHING.value, _TRANSITION_RUN_PUSH
    if action == "await_checkpoint":
        if inputs.worktree_clean:
            return AutoModePhase.IDLE.value, _TRANSITION_IDLE
        return AutoModePhase.COMMITTING.value, _TRANSITION_AWAIT_CHECKPOINT
    return None


def _resolve_by_runtime_state(inputs: AutoModeInputs) -> tuple[str, str]:
    if not inputs.last_guard_ok:
        return AutoModePhase.TESTING.value, _TRANSITION_RUN_GUARDS
    if inputs.push_decision_action == "await_review":
        return AutoModePhase.REVIEWING.value, _TRANSITION_AWAIT_REVIEW
    if inputs.implementation_blocked:
        return AutoModePhase.REVIEWING.value, _TRANSITION_AWAIT_REVIEW
    if not inputs.worktree_clean:
        return AutoModePhase.IMPLEMENTING.value, _TRANSITION_CONTINUE_IMPLEMENTING
    if _head_has_drifted(inputs):
        return AutoModePhase.REVIEWING.value, _TRANSITION_HEAD_DRIFT
    return AutoModePhase.IDLE.value, _TRANSITION_IDLE


def _resolve_phase_and_transition(
    inputs: AutoModeInputs,
    *,
    reviewer_alive: bool,
    implementer_alive: bool,
) -> tuple[str, str]:
    """Return (phase, next_transition) based on governance signal priority."""
    via_delivery_mode = _resolve_by_non_push_delivery_mode(inputs)
    if via_delivery_mode is not None:
        return via_delivery_mode
    via_push_decision = _resolve_by_push_decision(
        inputs,
        reviewer_alive=reviewer_alive,
        implementer_alive=implementer_alive,
    )
    if via_push_decision is not None:
        return via_push_decision
    return _resolve_by_runtime_state(inputs)


def _head_has_drifted(inputs: AutoModeInputs) -> bool:
    """Return True when HEAD has moved past the last reviewed commit."""
    if not inputs.last_reviewed_sha or not inputs.current_head_commit:
        return False
    return inputs.current_head_commit != inputs.last_reviewed_sha


def auto_mode_state_from_mapping(value: object) -> AutoModeState:
    """Deserialize an AutoModeState from a mapping, defaulting missing fields."""
    mapping: Mapping[str, object] = coerce_mapping(value)
    if not mapping:
        return AutoModeState()
    return AutoModeState(
        phase=coerce_string(mapping.get("phase")) or AutoModePhase.IDLE.value,
        phase_started_utc=coerce_string(mapping.get("phase_started_utc")),
        operator_interaction_mode=(
            coerce_string(mapping.get("operator_interaction_mode"))
            or "local_terminal"
        ),
        reviewer_alive=coerce_bool(mapping.get("reviewer_alive", False)),
        implementer_alive=coerce_bool(mapping.get("implementer_alive", False)),
        last_commit_sha=coerce_string(mapping.get("last_commit_sha")),
        last_guard_ok=coerce_bool(mapping.get("last_guard_ok", True)),
        pending_action_requests=coerce_int(
            mapping.get("pending_action_requests", 0)
        ),
        next_transition=coerce_string(mapping.get("next_transition")),
        delivery_mode=normalize_delivery_mode(mapping.get("delivery_mode")),
    )
