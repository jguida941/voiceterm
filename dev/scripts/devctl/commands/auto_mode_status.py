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
from ..runtime.auto_mode import (
    AUTO_MODE_CONTRACT_ID,
    AUTO_MODE_SCHEMA_VERSION,
    AutoModeInputs,
    AutoModePhase,
    AutoModeState,
    resolve_auto_mode_phase,
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
    reviewer_mode, impl_blocked, impl_status = _read_review_state()
    guard_ok = _read_guard_status()
    head_commit = _read_head_commit()
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
        pending_action_requests=0,
        operator_interaction_mode="local_terminal",
        timestamp_utc=utc_timestamp(),
    )


def _read_push_decision() -> tuple[str, str, bool, bool]:
    """Read the latest startup-context push decision from its receipt."""
    receipt_path = REPO_ROOT / "dev" / "reports" / "startup_receipt.json"
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


def _read_review_state() -> tuple[str, bool, str]:
    """Read reviewer mode and implementation block from review_state.json."""
    from ..runtime.review_state_locator import resolve_review_state_path

    rs_path = resolve_review_state_path(REPO_ROOT)
    if rs_path is None or not rs_path.is_file():
        return "single_agent", False, ""
    try:
        payload = json.loads(rs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "single_agent", False, ""
    reviewer_mode = str(payload.get("reviewer_mode", "single_agent"))
    session = payload.get("current_session") or {}
    impl_status = str(session.get("implementer_status", ""))
    blocked = bool(payload.get("implementation_blocked", False))
    return reviewer_mode, blocked, impl_status


def _read_guard_status() -> bool:
    """Return True when the last guard run passed (or no report exists)."""
    report_path = REPO_ROOT / "dev" / "reports" / "check_report.json"
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
