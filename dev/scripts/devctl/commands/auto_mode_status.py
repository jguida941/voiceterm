"""devctl auto-mode command -- emit current auto-mode phase and next transition.

Reads typed state from the governance pipeline (review_state, push decision,
guard results) and projects it as an AutoModeState snapshot.  The output
tells agents and operators which phase the system is in and what should
happen next.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..common import emit_output, write_output
from ..config import REPO_ROOT
from ..repo_packs import active_path_config
from ..review_channel.action_request import action_requests_from_packets
from ..runtime.auto_mode import (
    AUTO_MODE_CONTRACT_ID,
    AUTO_MODE_SCHEMA_VERSION,
    AutoModeInputs,
    AutoModePhase,
    AutoModeState,
    resolve_auto_mode_phase,
)
from ..runtime.governance_scan import scan_repo_governance_safely
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
    inputs = _collect_inputs()
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


def _collect_inputs() -> AutoModeInputs:
    """Build AutoModeInputs from repo-owned typed state sources."""
    push_action, push_reason, worktree_clean, review_allows = (
        _read_push_decision()
    )
    reviewer_mode, impl_blocked, impl_status, pending_actions = (
        _read_review_state()
    )
    guard_ok = _read_guard_status()
    head_commit = _read_head_commit()
    interaction_mode = _resolve_interaction_mode()
    return AutoModeInputs(
        push_decision_action=push_action,
        push_decision_reason=push_reason,
        worktree_clean=worktree_clean,
        review_gate_allows_push=review_allows,
        reviewer_mode=reviewer_mode,
        implementation_blocked=impl_blocked,
        implementer_status=impl_status,
        last_guard_ok=guard_ok,
        current_head_commit=head_commit,
        pending_action_requests=pending_actions,
        operator_interaction_mode=interaction_mode,
        timestamp_utc=utc_timestamp(),
    )


def _read_push_decision() -> tuple[str, str, bool, bool]:
    """Read the latest startup-context push decision from its receipt.

    Derives the receipt path from ``active_path_config()`` so the resolution
    stays portable across repo-packs.
    """
    config = active_path_config()
    receipt_path = (
        REPO_ROOT
        / config.reports_root_rel
        / "startup"
        / "latest"
        / "receipt.json"
    )
    if not receipt_path.is_file():
        return "", "", _worktree_is_clean(), False
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "", "", _worktree_is_clean(), False
    push = payload.get("push_decision") or {}
    return (
        str(push.get("action", "")),
        str(push.get("reason", "")),
        bool(push.get("worktree_clean", _worktree_is_clean())),
        bool(push.get("review_gate_allows_push", False)),
    )


def _read_review_state() -> tuple[str, bool, str, int]:
    """Read reviewer mode, implementation block, and pending actions from review_state.

    Returns (reviewer_mode, implementation_blocked, implementer_status,
    pending_action_requests).  Pending actions are counted from the packet
    queue so the auto-mode state machine reflects live remote-control demand.
    """
    from ..runtime.review_state_locator import resolve_review_state_path

    rs_path = resolve_review_state_path(REPO_ROOT)
    if rs_path is None or not rs_path.is_file():
        return "single_agent", False, "", 0
    try:
        payload = json.loads(rs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "single_agent", False, "", 0
    reviewer_mode = str(payload.get("reviewer_mode", "single_agent"))
    session = payload.get("current_session") or {}
    impl_status = str(session.get("implementer_status", ""))
    blocked = bool(payload.get("implementation_blocked", False))
    packets = payload.get("packets")
    pending_count = (
        len(action_requests_from_packets(packets))
        if isinstance(packets, list)
        else 0
    )
    return reviewer_mode, blocked, impl_status, pending_count


def _read_guard_status() -> bool:
    """Return True when the last guard run passed (or no report exists).

    Derives the report path from ``active_path_config()`` so guard-status
    resolution stays portable across repo-packs.
    """
    config = active_path_config()
    report_path = REPO_ROOT / config.reports_root_rel / "check_report.json"
    if not report_path.is_file():
        return True
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return payload.get("exit_code", 0) == 0


def _read_head_commit() -> str:
    """Return the current HEAD commit SHA."""
    from ..runtime.vcs import run_git_capture

    code, out, _ = run_git_capture(["rev-parse", "HEAD"])
    return out if code == 0 else ""


def _resolve_interaction_mode() -> str:
    """Read operator_interaction_mode from governance, falling back to review_state.

    Governance is the preferred source (matches session-resume).  When
    governance is unavailable the follow-controller's ``operator_interaction_mode``
    field from review_state provides the live runtime value.
    """
    governance = scan_repo_governance_safely(REPO_ROOT)
    if governance is not None:
        mode = str(
            governance.bridge_config.operator_interaction_mode or ""
        ).strip()
        if mode:
            return mode
    from ..runtime.review_state_locator import resolve_review_state_path

    rs_path = resolve_review_state_path(REPO_ROOT)
    if rs_path is not None and rs_path.is_file():
        try:
            payload = json.loads(rs_path.read_text(encoding="utf-8"))
            mode = str(payload.get("operator_interaction_mode") or "").strip()
            if mode:
                return mode
        except (json.JSONDecodeError, OSError):
            pass
    return "local_terminal"


def _worktree_is_clean() -> bool:
    """Return True when the git worktree has no uncommitted changes."""
    from ..runtime.vcs import run_git_capture

    code, out, _ = run_git_capture(["status", "--porcelain"])
    return code == 0 and not out.strip()


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
