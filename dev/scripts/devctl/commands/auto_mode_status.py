"""devctl auto-mode command -- emit current auto-mode phase and next transition.

Reads typed state from the ControlPlaneReadModel (the single resolved
control-plane snapshot) and projects it as an AutoModeState snapshot.
The output tells agents and operators which phase the system is in and
what should happen next.

All artifact loading is delegated to ``build_control_plane_read_model``
so auto-mode never diverges from the shared read model used by the
dashboard, operator console, and other governance surfaces.
"""

from __future__ import annotations

import json

from ..common import emit_output, write_output
from ..config import REPO_ROOT
from ..runtime.auto_mode import (
    AUTO_MODE_CONTRACT_ID,
    AUTO_MODE_SCHEMA_VERSION,
    AutoModeInputs,
    AutoModeState,
    resolve_auto_mode_phase,
)
from ..runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ..time_utils import utc_timestamp


def add_parser(sub) -> None:
    """Register the ``auto-mode`` subcommand on *sub*."""
    from ..common import add_standard_output_arguments

    cmd = sub.add_parser(
        "auto-mode",
        help="Current auto-mode phase and next transition",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "terminal"),
        default_format="json",
    )


def run(args) -> int:
    """Resolve current auto-mode phase and render the snapshot."""
    model = build_control_plane_read_model(REPO_ROOT)
    inputs = inputs_from_read_model(model)
    state = resolve_auto_mode_phase(inputs)

    if args.format == "json":
        output = _render_json(state)
    elif args.format == "md":
        output = _render_md(state)
    else:
        output = _render_terminal(state)

    pipe_rc = emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return pipe_rc


def inputs_from_read_model(model: ControlPlaneReadModel) -> AutoModeInputs:
    """Derive AutoModeInputs from the shared ControlPlaneReadModel.

    Maps the frozen read-model fields to the auto-mode input contract so
    the state machine receives the same resolved values every governance
    surface uses.
    """
    push_action = _push_action_from_next_action(model.next_action)
    implementer_status = _implementer_status_from_model(model)
    return AutoModeInputs(
        push_decision_action=push_action,
        worktree_clean=model.worktree_clean,
        review_gate_allows_push=model.review_accepted,
        reviewer_mode=model.reviewer_mode,
        implementation_blocked=model.implementation_blocked,
        implementer_status=implementer_status,
        last_guard_ok=model.last_guard_ok,
        current_head_commit=model.head_sha,
        pending_action_requests=model.pending_action_requests,
        operator_interaction_mode=model.operator_interaction_mode,
        timestamp_utc=model.timestamp or utc_timestamp(),
    )


def _implementer_status_from_model(model: ControlPlaneReadModel) -> str:
    """Derive implementer_status from the read model's conductor liveness.

    The ControlPlaneReadModel tracks ``claude_conductor_alive`` from the
    session heartbeat.  When the conductor process is alive, the implementer
    is actively running, so we report ``"active"`` so that
    ``resolve_auto_mode_phase`` can derive ``implementer_alive=True``.
    """
    if model.claude_conductor_alive:
        return "active"
    return ""


def _push_action_from_next_action(next_action: str) -> str:
    """Map the read model's next_action back to a push_decision_action value.

    The ControlPlaneReadModel stores the push action string as
    ``next_action``.  When it defaults to ``"n/a"`` (no receipt), return
    empty string so the auto-mode state machine treats it as no signal.
    """
    if next_action in (
        "run_devctl_push",
        "await_checkpoint",
        "await_review",
        "no_push_needed",
    ):
        return next_action
    return ""


def _render_json(state: AutoModeState) -> str:
    payload = {
        "contract_id": AUTO_MODE_CONTRACT_ID,
        "schema_version": AUTO_MODE_SCHEMA_VERSION,
        **state.to_dict(),
    }
    return json.dumps(payload, indent=2)


def _render_md(state: AutoModeState) -> str:
    lines = [
        "## Auto-Mode Status",
        "",
        f"**Phase**: `{state.phase}`",
        f"**Next transition**: {state.next_transition}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Reviewer alive | {state.reviewer_alive} |",
        f"| Implementer alive | {state.implementer_alive} |",
        f"| Last guard OK | {state.last_guard_ok} |",
        f"| Last commit | `{state.last_commit_sha[:8] if state.last_commit_sha else 'n/a'}` |",
        f"| Pending actions | {state.pending_action_requests} |",
        f"| Operator mode | {state.operator_interaction_mode} |",
        f"| Phase started | {state.phase_started_utc or 'n/a'} |",
    ]
    return "\n".join(lines)


def _render_terminal(state: AutoModeState) -> str:
    phase_display = state.phase.upper()
    lines = [
        f"Auto-Mode: {phase_display}",
        f"  Next: {state.next_transition}",
        f"  Reviewer alive: {state.reviewer_alive}",
        f"  Implementer alive: {state.implementer_alive}",
        f"  Last guard OK: {state.last_guard_ok}",
        f"  Last commit: {state.last_commit_sha[:8] if state.last_commit_sha else 'n/a'}",
        f"  Pending actions: {state.pending_action_requests}",
    ]
    return "\n".join(lines)
