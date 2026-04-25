"""Control-plane and session-cache field-route closure proofs."""

from __future__ import annotations

from .field_routes_surface_state import (
    _build_coverage,
    _build_violation,
    _source_contains_any,
)


def check_push_eligible_dashboard_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify ControlPlaneReadModel.push_eligible reaches the dashboard."""
    consumer = "dev.scripts.devctl.commands.dashboard_builders"
    coverage = _build_coverage(
        "ControlPlaneReadModel",
        "push_eligible",
        "dashboard",
        consumer,
    )
    if _source_contains_any(consumer, ("push_eligible", "push_eligible_now")):
        coverage["detail"] = (
            "ControlPlaneReadModel.push_eligible is referenced in the "
            "dashboard builder surface through the push_eligible_now "
            "receipt projection."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.push_eligible is not referenced in the "
        "dashboard builder surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_push_eligible_session_resume_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify ControlPlaneReadModel.push_eligible reaches session-resume."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    coverage = _build_coverage(
        "ControlPlaneReadModel",
        "push_eligible",
        "session_resume",
        consumer,
    )
    if _source_contains_any(model, ("push_eligible",)) and _source_contains_any(
        consumer, ("next_command", "next_action")
    ):
        coverage["detail"] = (
            "ControlPlaneReadModel.push_eligible flows into next_command, "
            "which session-resume consumes from the read model."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.push_eligible does not reach the "
        "session-resume surface through the next_command projection."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_top_blocker_dashboard_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify ControlPlaneReadModel.top_blocker reaches the dashboard."""
    consumer = "dev.scripts.devctl.commands.dashboard_render"
    coverage = _build_coverage(
        "ControlPlaneReadModel",
        "top_blocker",
        "dashboard",
        consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "dashboard render surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "dashboard render surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_top_blocker_session_resume_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify ControlPlaneReadModel.top_blocker reaches session-resume."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "ControlPlaneReadModel",
        "top_blocker",
        "session_resume",
        consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "session-resume support surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "session-resume support surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_top_blocker_phone_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify ControlPlaneReadModel.top_blocker reaches the phone surface."""
    consumer = "dev.scripts.devctl.commands.phone_status"
    coverage = _build_coverage(
        "ControlPlaneReadModel",
        "top_blocker",
        "phone",
        consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "phone status surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "phone status surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_auto_mode_phase_session_resume_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify AutoModeState.phase reaches session-resume via resolved_phase."""
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    builder = (
        "dev.scripts.devctl.commands.governance.session_resume_cache_packet_builder"
    )
    renderer = "dev.scripts.devctl.commands.governance.session_resume_render"
    coverage = _build_coverage("AutoModeState", "phase", "session_resume", consumer)
    if (
        _source_contains_any(model, ("auto_state.phase", "resolved_phase"))
        and (
            _source_contains_any(consumer, ("resolved_phase",))
            or _source_contains_any(builder, ("resolved_phase",))
        )
        and _source_contains_any(renderer, ("resolved_phase",))
    ):
        coverage["detail"] = (
            "AutoModeState.phase flows through ControlPlaneReadModel.resolved_phase "
            "into SessionCachePacket.resolved_phase and the session-resume renderer."
        )
        return coverage, None
    detail = (
        "AutoModeState.phase does not reach the session-resume surface "
        "through the resolved_phase projection in SessionCachePacket and "
        "the renderer."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_last_reviewed_sha_compact_route() -> (
    tuple[dict[str, object], dict[str, object] | None]
):
    """Verify SessionCachePacket.last_reviewed_sha reaches compact projection."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "SessionCachePacket",
        "last_reviewed_sha",
        "compact_projection",
        consumer,
    )
    if _source_contains_any(consumer, ("last_reviewed_sha",)):
        coverage["detail"] = (
            "SessionCachePacket.last_reviewed_sha is referenced in the "
            "session-resume compact projection surface."
        )
        return coverage, None
    detail = (
        "SessionCachePacket.last_reviewed_sha is not referenced in the "
        "session-resume compact projection surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)
