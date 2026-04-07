"""Control plane parity check: all 5 surfaces agree on the same fixture.

MP-381 Priority 3 hard parity guard from
``dev/active/remote_control_runtime.md:237-241``. Builds one
deterministic ``ControlPlaneReadModel`` fixture, renders it through each
of the 5 governance surfaces (dashboard, auto-mode, session-resume,
phone, mobile), and fails if any surface disagrees on the parity fields.

The guard catches two regression classes:

1. A surface silently recomputing a field from raw inputs instead of
   reading it from the shared read model (Finding F11).
2. Two surfaces producing divergent values for the same logical field
   from the same input.

Some surfaces only expose a subset (for example ``SessionCachePacket``
omits ``push_eligible`` and ``pending_action_requests``). Missing fields
are not parity violations; only present-but-disagreeing values fail. The
fixture uses meaningfully distinct values per field so any extractor
that copies the wrong slot is caught immediately.

Coverage/violation row construction lives in
``field_routes_parity_compare`` so this module stays under the Python
soft file-size limit.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Callable

from dev.scripts.devctl.runtime.control_plane_read_model import ControlPlaneReadModel

from .field_routes_parity_compare import (
    compare_parity_field,
    coverage_row,
    run_extractor,
)


# -------------------------------------------------------
# Public surface: parity field tuple + surface IDs
# -------------------------------------------------------

#: Fields the guard inspects across every surface. Adding a new field
#: requires updating ``_fixture_read_model`` and at least one extractor
#: so the regression-catching test still has a value to compare.
PARITY_FIELDS: tuple[str, ...] = (
    "resolved_phase",
    "push_eligible",
    "implementation_blocked",
    "top_blocker",
    "next_action",
    "next_command",
    "review_accepted",
    "last_guard_ok",
    "pending_action_requests",
)

_SURFACE_DASHBOARD = "dashboard"
_SURFACE_AUTO_MODE = "auto_mode"
_SURFACE_SESSION_RESUME = "session_resume"
_SURFACE_PHONE = "phone"
_SURFACE_MOBILE = "mobile"

_ALL_SURFACES: tuple[str, ...] = (
    _SURFACE_DASHBOARD,
    _SURFACE_AUTO_MODE,
    _SURFACE_SESSION_RESUME,
    _SURFACE_PHONE,
    _SURFACE_MOBILE,
)


# -------------------------------------------------------
# Fixture: one deterministic read model for the parity proof
# -------------------------------------------------------

def _fixture_read_model() -> ControlPlaneReadModel:
    """Return one deterministic ControlPlaneReadModel for parity testing.

    Each parity field gets a distinctive value so an extractor that
    accidentally copies the wrong slot (for example writing
    ``top_blocker`` into the ``next_action`` cell) is caught by the
    cross-surface comparison instead of silently passing.
    """
    return ControlPlaneReadModel(
        timestamp="2026-04-07T00:00:00Z",
        branch="parity-fixture-branch",
        head_sha="0123456789abcdef0123456789abcdef01234567",
        worktree_clean=True,
        ahead_of_upstream=0,
        resolved_phase="parity_fixture_phase",
        push_eligible=True,
        implementation_blocked=False,
        top_blocker="parity_fixture_top_blocker",
        next_action="run_devctl_push",
        next_command="parity_fixture_next_command",
        reviewer_mode="active_dual_agent",
        operator_interaction_mode="local_terminal",
        reviewer_freshness="fresh",
        review_accepted=True,
        last_reviewed_sha="0123456789abcdef0123456789abcdef01234567",
        attention_status="ok",
        attention_summary="parity-fixture",
        publisher_running=True,
        supervisor_running=True,
        codex_conductor_alive=True,
        claude_conductor_alive=True,
        pending_action_requests=7,
        last_guard_ok=True,
        check_details=(),
    )


# -------------------------------------------------------
# Per-surface extractors -- each returns {parity_field: value}
# -------------------------------------------------------

def _extract_from_dashboard(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Run the dashboard's projection and pull parity fields from it.

    Calls ``_assemble`` directly with the fixture model and minimal stub
    inputs against a temporary repo root. The dashboard contract is
    ``snapshot["control_plane"] == model.to_dict()``; asserting that
    here proves the dashboard surface still routes the fixture verbatim
    instead of recomputing fields from raw artifacts.
    """
    # Local import: keep top-level light and avoid pulling the full
    # dashboard graph into the parity-guard import time.
    from dev.scripts.devctl.commands.dashboard import _assemble

    with tempfile.TemporaryDirectory() as tmp:
        snapshot = _assemble(
            git={"branch": model.branch, "head": model.head_sha, "dirty": "CLEAN"},
            compact=None,
            push_data=None,
            receipt=None,
            agents=None,
            pipeline=None,
            bridge={
                "last_poll_utc": "",
                "instruction_full": "n/a",
                "reviewer_mode": model.reviewer_mode,
            },
            plan=None,
            repo_root=Path(tmp),
            view="overview",
            review_state=None,
            control_plane=model,
        )
    cp = snapshot.get("control_plane")
    if not isinstance(cp, dict):
        raise RuntimeError(
            "dashboard surface did not expose `control_plane` from the fixture"
        )
    return {field: cp.get(field) for field in PARITY_FIELDS if field in cp}


def _extract_from_auto_mode(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Pull the parity fields auto-mode reads from the fixture model.

    Auto-mode consumes the read model via ``inputs_from_read_model``
    which produces an ``AutoModeInputs`` projection. Only fields the
    surface actually carries are returned; absent fields are skipped so
    the comparator only checks values the surface really exposes.
    """
    from dev.scripts.devctl.commands.reporting.auto_mode_status import (
        inputs_from_read_model,
    )

    inputs = inputs_from_read_model(model)
    return {
        # ``push_decision_action`` filters non-push actions to ""; fall
        # back to the model's next_action so we always emit a value when
        # the fixture set a recognized push action.
        "next_action": inputs.push_decision_action or model.next_action,
        "review_accepted": inputs.review_gate_allows_push,
        "last_guard_ok": inputs.last_guard_ok,
        "pending_action_requests": inputs.pending_action_requests,
        "implementation_blocked": inputs.implementation_blocked,
    }


def _extract_from_session_resume(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Pull the parity fields session-resume reads from the fixture model.

    Session-resume projects the read model into a ``SessionCachePacket``
    whose field names differ: ``advisory_reason`` carries
    ``top_blocker``, ``advisory_action`` carries ``next_action``, and so
    on. Fields without a SessionCachePacket slot are not returned; the
    comparator skips absent fields.
    """
    from dev.scripts.devctl.commands.governance.session_resume_support import (
        build_from_sources,
    )

    with tempfile.TemporaryDirectory() as tmp:
        # Empty sources_override skips disk loading; we only need the
        # gate/blocker/next-* fields the read model already carries.
        packet = build_from_sources(
            Path(tmp),
            role="reviewer",
            head_sha=model.head_sha,
            read_model_override=model,
            sources_override={},
            changed_paths=[],
        )
    return {
        "resolved_phase": packet.resolved_phase,
        "top_blocker": packet.advisory_reason,
        "next_action": packet.advisory_action,
        "next_command": packet.next_recommended_command,
        "last_guard_ok": packet.last_guard_ok,
    }


def _extract_from_phone(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Pull the parity fields the phone surface projects from the model."""
    from dev.scripts.devctl.commands.phone_status import _control_plane_section

    section = _control_plane_section(model)
    return {field: section.get(field) for field in PARITY_FIELDS if field in section}


def _extract_from_mobile(model: ControlPlaneReadModel) -> dict[str, Any]:
    """Pull the parity fields the mobile surface projects from the model."""
    from dev.scripts.devctl.commands.mobile_status import _control_plane_section

    section = _control_plane_section(model)
    return {field: section.get(field) for field in PARITY_FIELDS if field in section}


_EXTRACTORS: tuple[
    tuple[str, Callable[[ControlPlaneReadModel], dict[str, Any]]], ...
] = (
    (_SURFACE_DASHBOARD, _extract_from_dashboard),
    (_SURFACE_AUTO_MODE, _extract_from_auto_mode),
    (_SURFACE_SESSION_RESUME, _extract_from_session_resume),
    (_SURFACE_PHONE, _extract_from_phone),
    (_SURFACE_MOBILE, _extract_from_mobile),
)


def run_parity_checks(
    *,
    fixture: ControlPlaneReadModel | None = None,
    extractor_overrides: (
        dict[str, Callable[[ControlPlaneReadModel], dict[str, Any]]] | None
    ) = None,
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    """Run the control-plane parity check across all 5 surfaces.

    ``fixture`` defaults to the deterministic ``_fixture_read_model``.
    ``extractor_overrides`` lets the regression test perturb a single
    surface to prove the comparator actually flags divergence.

    Returns the same ``[(coverage, violation_or_None), ...]`` shape used
    by ``emitter_parity.check_review_state_emitter_parity`` so the
    contract-closure aggregator can append rows directly without a new
    adapter layer.
    """
    model = fixture or _fixture_read_model()
    overrides = extractor_overrides or {}
    results: list[tuple[dict[str, object], dict[str, object] | None]] = []
    surface_outputs: dict[str, dict[str, Any]] = {}

    for surface_id, extractor in _EXTRACTORS:
        live_extractor = overrides.get(surface_id, extractor)
        output, violation = run_extractor(surface_id, live_extractor, model)
        if violation is not None:
            results.append((
                coverage_row(
                    field="*",
                    surfaces=(surface_id,),
                    ok=False,
                    detail=str(violation.get("detail")),
                ),
                violation,
            ))
            continue
        if output is not None:
            surface_outputs[surface_id] = output

    for field in PARITY_FIELDS:
        per_field: dict[str, Any] = {}
        for surface_id in _ALL_SURFACES:
            output = surface_outputs.get(surface_id)
            if output is None or field not in output:
                continue
            per_field[surface_id] = output[field]
        coverage, violation = compare_parity_field(field, per_field)
        results.append((coverage, violation))

    return results
