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
from .role_profile import TandemRole, normalize_tandem_role, role_for_provider
from .topology_authority_facts import (
    live_implementer_present,
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
    resolved_role = (normalize_tandem_role(role) or role_for_provider(provider)).value
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
    return _implementer_capability(
        provider=provider,
        reviewer_mode=normalized_mode,
        collaboration=collaboration,
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
    # v4.55.3 (rev_pkt_4777): when typed collaboration is supplied AND
    # the legacy reviewer_mode is `active_dual_agent`, require a live
    # coding_agent role_assignment before opening the bounded-implementer
    # branch. `single_agent` / `tools_only` modes do NOT require a typed
    # coding_agent (the reviewer mutates alone in those modes), so the
    # gate must be scoped to the active_dual_agent path.
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
                "live coding_agent grants, so reviewer_mode=active_dual_agent "
                "cannot open the bounded-implementer branch."
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
    # v4.55.3 (rev_pkt_4783): when typed collaboration is supplied AND
    # the legacy reviewer_mode is `single_agent`, require a live
    # `review_agent` role_assignment before granting the reviewer-mutation
    # branch (`may_edit_repo=True`). Symmetric with the active_dual_agent
    # gate above: typed `role_assignments` decide authority, not the
    # legacy reviewer_mode string alone.
    if (
        collaboration is not None
        and reviewer_mode_allows_reviewer_mutation(reviewer_mode)
        and not live_reviewer_present(
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
                "live review_agent grants, so reviewer_mode=single_agent "
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
    # v4.55.3 (rev_pkt_4777): typed implementer capability requires a
    # live coding_agent role_assignment, not just a legacy
    # reviewer_mode=active_dual_agent string. Without typed evidence,
    # may_edit_repo stays False even when the legacy label suggests
    # active dual-agent.
    if collaboration is not None and not live_implementer_present(
        collaboration, legacy_label=reviewer_mode
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
                "no live coding_agent grants, so reviewer_mode label cannot "
                "grant edit capability alone."
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
