"""Surface-state field-route closure proofs for platform contract enforcement.

Each check verifies that a key field from a surface-state contract
(ControlPlaneReadModel, AutoModeState, SessionCachePacket) is consumed
in the declared target surface renderer by inspecting the actual
source code for field-access references.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _source_contains_any(module_path: str, tokens: tuple[str, ...]) -> bool:
    """Return True when the source at *module_path* contains any of *tokens*.

    Resolves dotted module paths to filesystem paths relative to the
    repo root. Accepts both flat modules (``foo/bar.py``) and packages
    (``foo/bar/__init__.py``); for packages, scans every ``*.py`` file
    in the package root so tokens rendered by submodules still count.
    """
    rel_module = module_path.replace(".", "/")
    flat_path = _REPO_ROOT / f"{rel_module}.py"
    if flat_path.is_file():
        text = flat_path.read_text(encoding="utf-8", errors="replace")
        return any(token in text for token in tokens)

    package_dir = _REPO_ROOT / rel_module
    if package_dir.is_dir():
        for py_file in sorted(package_dir.glob("*.py")):
            text = py_file.read_text(encoding="utf-8", errors="replace")
            if any(token in text for token in tokens):
                return True
    return False


def _build_coverage(
    contract_id: str,
    field_name: str,
    route_id: str,
    consumer: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": contract_id,
        "field_name": field_name,
        "route_id": route_id,
        "consumer": consumer,
        "ok": True,
    }


def _build_violation(
    coverage: dict[str, object],
    detail: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": coverage["contract_id"],
        "field_name": coverage["field_name"],
        "route_id": coverage["route_id"],
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


# -- ControlPlaneReadModel.push_eligible routes --

def check_push_eligible_dashboard_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.push_eligible reaches the dashboard."""
    # The dashboard renders push eligibility through the receipt's
    # push_eligible_now field and through ControlPlaneReadModel passed
    # to the builder.  Both paths carry the same resolved truth.
    consumer = "dev.scripts.devctl.commands.dashboard_builders"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "push_eligible", "dashboard", consumer,
    )
    if _source_contains_any(consumer, ("push_eligible",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.push_eligible is referenced in the "
            "dashboard builder surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.push_eligible is not referenced in the "
        "dashboard builder surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_push_eligible_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.push_eligible reaches session-resume."""
    # push_eligible flows into ControlPlaneReadModel.next_command
    # (set to devctl push --execute when push_eligible is True),
    # and session-resume consumes model.next_command.
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "push_eligible", "session_resume", consumer,
    )
    if (
        _source_contains_any(model, ("push_eligible",))
        and _source_contains_any(consumer, ("next_command", "next_action"))
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


# -- ControlPlaneReadModel.top_blocker routes --

def check_top_blocker_dashboard_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches the dashboard."""
    consumer = "dev.scripts.devctl.commands.dashboard_render"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "dashboard", consumer,
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


def check_top_blocker_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches session-resume."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "session_resume", consumer,
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


def check_top_blocker_phone_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches the phone surface."""
    consumer = "dev.scripts.devctl.commands.phone_status"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "phone", consumer,
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


# -- AutoModeState.phase routes --

def check_auto_mode_phase_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify AutoModeState.phase reaches session-resume via resolved_phase.

    AutoModeState.phase flows into ControlPlaneReadModel.resolved_phase
    via ``auto_state.phase`` in the read-model builder.  The closure proof
    requires that ``resolved_phase`` is present as a field in
    SessionCachePacket AND that the session-resume renderer outputs it.
    """
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    renderer = "dev.scripts.devctl.commands.governance.session_resume_render"
    coverage = _build_coverage("AutoModeState", "phase", "session_resume", consumer)
    if (
        _source_contains_any(model, ("auto_state.phase", "resolved_phase"))
        and _source_contains_any(consumer, ("resolved_phase",))
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


# -- SessionCachePacket.last_reviewed_sha routes --

def check_last_reviewed_sha_compact_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify SessionCachePacket.last_reviewed_sha reaches compact projection."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "SessionCachePacket", "last_reviewed_sha", "compact_projection", consumer,
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
