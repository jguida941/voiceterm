"""Typed conductor capability contract for the review-channel loop."""

from __future__ import annotations

from .review_state_models import ConductorCapabilityState
from .role_profile import TandemRole, normalize_tandem_role, role_for_provider

_STARTUP_CONTEXT_BASE_COMMAND = "python3 dev/scripts/devctl.py startup-context"
_SESSION_RESUME_BASE_COMMAND = "python3 dev/scripts/devctl.py session-resume"
_CONTEXT_GRAPH_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_DEFAULT_REVIEWER_MODE = "active_dual_agent"
_KNOWN_REVIEWER_MODES = {
    "active_dual_agent",
    "single_agent",
    "tools_only",
    "paused",
    "offline",
}


def startup_context_command_for_role(role: str) -> str:
    """Return the canonical startup receipt command for one role."""
    return f"{_STARTUP_CONTEXT_BASE_COMMAND} --role {role} --format summary"


def session_resume_command_for_role(role: str, *, format: str = "bootstrap") -> str:
    """Return the canonical role-bound session bootstrap packet command."""
    return f"{_SESSION_RESUME_BASE_COMMAND} --role {role} --format {format}"


def context_graph_bootstrap_command() -> str:
    """Return the canonical slim bootstrap context command."""
    return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND


def reviewer_takeover_command() -> str:
    """Return the explicit reviewer takeover command."""
    return (
        f"{_STARTUP_CONTEXT_BASE_COMMAND} --role reviewer "
        "--reviewer-override --format summary"
    )


def build_conductor_capability_state(
    *,
    provider: str,
    reviewer_mode: str,
    role: str | None = None,
) -> ConductorCapabilityState:
    """Return the typed execution capability for one conductor."""
    resolved_role = (
        normalize_tandem_role(role) or role_for_provider(provider)
    ).value
    normalized_mode = normalize_reviewer_mode(reviewer_mode)
    if resolved_role == TandemRole.REVIEWER.value:
        return _reviewer_capability(
            provider=provider,
            reviewer_mode=normalized_mode,
        )
    return _implementer_capability(
        provider=provider,
        reviewer_mode=normalized_mode,
    )


def reviewer_local_implementation_allowed(
    *,
    reviewer_mode: str,
    reviewer_override: bool,
) -> bool:
    """Return True when the reviewer may take local implementation ownership."""
    if reviewer_override:
        return True
    capability = _reviewer_capability(
        provider="codex",
        reviewer_mode=normalize_reviewer_mode(reviewer_mode),
    )
    return capability.may_edit_repo


def normalize_reviewer_mode(reviewer_mode: str) -> str:
    """Normalize reviewer mode without importing review-channel modules."""
    normalized = str(reviewer_mode or "").strip().lower()
    if normalized in _KNOWN_REVIEWER_MODES:
        return normalized
    return _DEFAULT_REVIEWER_MODE


def _reviewer_capability(
    *,
    provider: str,
    reviewer_mode: str,
) -> ConductorCapabilityState:
    startup_command = startup_context_command_for_role(TandemRole.REVIEWER.value)
    takeover_command = reviewer_takeover_command()
    if reviewer_mode == "active_dual_agent":
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.REVIEWER.value,
            startup_context_command=startup_command,
            may_edit_repo=False,
            requires_explicit_takeover=True,
            worker_unavailable_policy="stay_reviewer_only",
            queue_policy="review_only",
            takeover_command=takeover_command,
            status_summary=(
                "Reviewer stays review-only in active_dual_agent until takeover "
                "is explicit."
            ),
        )
    if reviewer_mode == "single_agent":
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.REVIEWER.value,
            startup_context_command=startup_command,
            may_edit_repo=True,
            requires_explicit_takeover=False,
            worker_unavailable_policy="self_execute",
            queue_policy="review_or_implement",
            status_summary="Reviewer owns local implementation in single_agent mode.",
        )
    return ConductorCapabilityState(
        provider=provider,
        role=TandemRole.REVIEWER.value,
        startup_context_command=startup_command,
        may_edit_repo=False,
        requires_explicit_takeover=False,
        worker_unavailable_policy="inactive",
        queue_policy="inactive",
        status_summary=(
            "Reviewer loop is not in an active implementation mode; keep the "
            "session read-only."
        ),
    )


def _implementer_capability(
    *,
    provider: str,
    reviewer_mode: str,
) -> ConductorCapabilityState:
    startup_command = startup_context_command_for_role(TandemRole.IMPLEMENTER.value)
    if reviewer_mode == "active_dual_agent":
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.IMPLEMENTER.value,
            startup_context_command=startup_command,
            may_edit_repo=True,
            requires_explicit_takeover=False,
            worker_unavailable_policy="self_execute",
            queue_policy="implement_assigned_work",
            status_summary=(
                "Implementer may execute the reviewer-owned bounded slice while "
                "active_dual_agent is live."
            ),
        )
    return ConductorCapabilityState(
        provider=provider,
        role=TandemRole.IMPLEMENTER.value,
        startup_context_command=startup_command,
        may_edit_repo=False,
        requires_explicit_takeover=False,
        worker_unavailable_policy="inactive",
        queue_policy="inactive",
        status_summary=(
            "Implementer loop is inactive outside active_dual_agent; wait for a "
            "reviewer-owned relaunch or instruction change."
        ),
    )
