"""Typed conductor capability contract for the review-channel loop."""

from __future__ import annotations

from collections.abc import Mapping

from .devctl_interpreter import devctl_interpreter
from .reviewer_mode import (
    ReviewerMode,
    authority_reviewer_mode,
    normalize_reviewer_mode,
    normalize_reviewer_mode_value,
    resolve_reviewer_mode,
    reviewer_mode_allows_implementer,
    reviewer_mode_allows_reviewer_mutation,
)
from .review_state_models import ConductorCapabilityState
from .role_profile import TandemRole, normalize_tandem_role, role_capability_class
from .topology_authority_facts import (
    live_implementer_present,
    live_provider_has_role,
    live_reviewer_present,
)

# Resolve via the shared helper so the rendered token is always
# ``python3``-prefixed (codex finding 2026-04-24): venv binaries
# named plain ``python`` and pyenv shims that resolve to broken
# 3.10 both flow through the same portable resolution.
_DEVCTL_INTERPRETER = devctl_interpreter()
_STARTUP_CONTEXT_BASE_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py startup-context"
)
_SESSION_RESUME_BASE_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py session-resume"
)
_CONTEXT_GRAPH_BOOTSTRAP_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py context-graph --mode bootstrap --format md"
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
    collaboration: Mapping[str, object] | None = None,
) -> ConductorCapabilityState:
    """Return the typed execution capability for one conductor.

    v4.55.3 (rev_pkt_4772/4777): when `collaboration` (typed
    CollaborationSessionState) is supplied, gate authority decisions
    on typed `role_assignments` (`live_reviewer_present` /
    `live_implementer_present`) so legacy `reviewer_mode` strings cannot
    grant `may_edit_repo` alone. Callers that do NOT supply
    `collaboration` retain the legacy reviewer_mode-based behavior for
    back-compat.
    """
    resolved = normalize_tandem_role(role) or role_capability_class(role)
    resolved_role = resolved.value if resolved is not None else ""
    normalized_mode = normalize_reviewer_mode_value(
        reviewer_mode,
        default=ReviewerMode.TOOLS_ONLY,
    )
    if resolved_role == TandemRole.REVIEWER.value:
        return _reviewer_capability(
            provider=provider,
            reviewer_mode=normalized_mode,
            collaboration=collaboration,
        )
    if resolved_role == TandemRole.IMPLEMENTER.value:
        return _implementer_capability(
            provider=provider,
            reviewer_mode=normalized_mode,
            collaboration=collaboration,
        )
    return ConductorCapabilityState(
        provider=provider,
        role="unbound",
        startup_context_command="",
        may_edit_repo=False,
        requires_explicit_takeover=False,
        worker_unavailable_policy="inactive",
        queue_policy="inactive",
        status_summary="Provider has no typed role assignment.",
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
        reviewer_mode=normalize_reviewer_mode_value(
            reviewer_mode,
            default=ReviewerMode.TOOLS_ONLY,
        ),
    )
    return capability.may_edit_repo


def _reviewer_capability(
    *,
    provider: str,
    reviewer_mode: str,
    collaboration: Mapping[str, object] | None = None,
) -> ConductorCapabilityState:
    startup_command = startup_context_command_for_role(TandemRole.REVIEWER.value)
    takeover_command = reviewer_takeover_command()
    # Typed collaboration must carry a live implementation-capable lane before
    # the bounded implementer branch opens. Legacy reviewer-mode labels are only
    # compatibility inputs; they do not grant that lane.
    if (
        collaboration is not None
        and reviewer_mode_allows_implementer(reviewer_mode)
        and not live_implementer_present(
            collaboration, legacy_label=reviewer_mode
        )
    ):
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.REVIEWER.value,
            startup_context_command=startup_command,
            may_edit_repo=False,
            requires_explicit_takeover=False,
            worker_unavailable_policy="inactive",
            queue_policy="inactive",
            status_summary=(
                "Reviewer capability gated by typed role_assignments: no "
                "live implementation-capable lane, so reviewer_mode cannot "
                "open the bounded-implementer branch."
            ),
        )
    if reviewer_mode_allows_implementer(reviewer_mode):
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
    # Single-actor mutation still needs typed implementation or mutation
    # capability on this provider. Review/test/architecture roles do not become
    # mutation authority just because an old reviewer-mode label says so.
    if (
        collaboration is not None
        and reviewer_mode_allows_reviewer_mutation(reviewer_mode)
        and not live_provider_has_role(
            collaboration,
            role_id="implementation",
            provider=provider,
        )
    ):
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.REVIEWER.value,
            startup_context_command=startup_command,
            may_edit_repo=False,
            requires_explicit_takeover=False,
            worker_unavailable_policy="inactive",
            queue_policy="inactive",
            status_summary=(
                "Reviewer capability gated by typed role_assignments: no "
                "live implementation or mutation grants, so reviewer_mode "
                "cannot open the reviewer-mutation branch."
            ),
        )
    if reviewer_mode_allows_reviewer_mutation(reviewer_mode):
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
    collaboration: Mapping[str, object] | None = None,
) -> ConductorCapabilityState:
    startup_command = startup_context_command_for_role(TandemRole.IMPLEMENTER.value)
    # Typed implementer capability requires a live implementation-capable lane,
    # not an old topology label or old role id string.
    if collaboration is not None and not live_provider_has_role(
        collaboration,
        role_id="implementation",
        provider=provider,
    ):
        return ConductorCapabilityState(
            provider=provider,
            role=TandemRole.IMPLEMENTER.value,
            startup_context_command=startup_command,
            may_edit_repo=False,
            requires_explicit_takeover=False,
            worker_unavailable_policy="inactive",
            queue_policy="inactive",
            status_summary=(
                "Implementer capability gated by typed role_assignments: "
                "no live implementation or mutation grants, so reviewer_mode "
                "cannot grant edit capability alone."
            ),
        )
    if reviewer_mode_allows_implementer(reviewer_mode):
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
