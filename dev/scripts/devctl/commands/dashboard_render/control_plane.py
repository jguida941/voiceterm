"""Dedicated control-plane renderers for dashboard terminal/markdown views."""

from __future__ import annotations

from typing import Any

from .helpers import _BOLD, _CYAN, _DIM, _GREEN, _RED, _RESET, _YELLOW


def render_control_plane_terminal(
    snapshot: dict[str, Any],
    lines: list[str],
) -> None:
    """CONTROL PLANE: one organized action/hook surface from the read model."""
    control_plane = snapshot.get("control_plane") or {}
    if not control_plane:
        return

    attention_status = control_plane.get("attention_status", "n/a")
    attention_summary = control_plane.get("attention_summary", "n/a")
    attention_color = _GREEN if attention_status in {"healthy", "none", "n/a"} else _YELLOW
    blocker = control_plane.get("top_blocker", "none")
    blocker_color = _GREEN if blocker == "none" else _RED
    review_accepted = control_plane.get("review_accepted", False)
    review_color = _GREEN if review_accepted else _YELLOW
    push_eligible = control_plane.get("push_eligible", False)
    push_color = _GREEN if push_eligible else _YELLOW
    impl_blocked = control_plane.get("implementation_blocked", False)
    impl_color = _RED if impl_blocked else _GREEN
    last_guard_ok = control_plane.get("last_guard_ok", False)
    guard_color = _GREEN if last_guard_ok else _YELLOW
    check_detail_count = len(control_plane.get("check_details", []) or [])

    lines.append(f"{_BOLD}CONTROL PLANE{_RESET}")
    lines.append(
        "  Workflow   "
        f"phase={_CYAN}{control_plane.get('resolved_phase', 'n/a')}{_RESET}   "
        f"blocker={blocker_color}{blocker}{_RESET}"
    )
    lines.append(f"  Next       {control_plane.get('next_action', 'n/a')}")
    lines.append(f"  Command    {_DIM}{control_plane.get('next_command', 'n/a')}{_RESET}")
    lines.append(
        "  Review     "
        f"mode={control_plane.get('reviewer_mode', 'n/a')}   "
        f"freshness={control_plane.get('reviewer_freshness', 'n/a')}   "
        f"accepted={review_color}{review_accepted}{_RESET}"
    )
    lines.append(
        "  Exec mode  "
        f"{control_plane.get('operator_interaction_mode', 'n/a')}   "
        f"push_eligible={push_color}{push_eligible}{_RESET}   "
        f"impl_blocked={impl_color}{impl_blocked}{_RESET}"
    )
    lines.append(
        "  Health     "
        f"{attention_color}{attention_status}{_RESET}   "
        f"{_DIM}{attention_summary}{_RESET}"
    )
    lines.append(
        "  Quality    "
        f"last_guard_ok={guard_color}{last_guard_ok}{_RESET}   "
        f"detail_rows={check_detail_count}   "
        f"pending_action_requests={control_plane.get('pending_action_requests', 0)}"
    )
    lines.append("")


def render_control_plane_markdown(
    snapshot: dict[str, Any],
    lines: list[str],
) -> None:
    """Control-plane summary for operator and AI readers."""
    control_plane = snapshot.get("control_plane") or {}
    if not control_plane:
        return

    lines.append("## Control Plane")
    lines.append("")
    lines.append(f"- **Resolved phase**: {control_plane.get('resolved_phase', 'n/a')}")
    lines.append(f"- **Top blocker**: {control_plane.get('top_blocker', 'none')}")
    lines.append(f"- **Next action**: {control_plane.get('next_action', 'n/a')}")
    lines.append(f"- **Next command**: `{control_plane.get('next_command', 'n/a')}`")
    lines.append(
        f"- **Review gate**: mode={control_plane.get('reviewer_mode', 'n/a')}, "
        f"freshness={control_plane.get('reviewer_freshness', 'n/a')}, "
        f"accepted={control_plane.get('review_accepted', False)}"
    )
    lines.append(
        f"- **Execution mode**: {control_plane.get('operator_interaction_mode', 'n/a')} "
        f"| push_eligible={control_plane.get('push_eligible', False)} "
        f"| implementation_blocked={control_plane.get('implementation_blocked', False)}"
    )
    lines.append(
        f"- **Runtime health**: {control_plane.get('attention_status', 'n/a')} — "
        f"{control_plane.get('attention_summary', 'n/a')}"
    )
    lines.append(
        f"- **Quality**: last_guard_ok={control_plane.get('last_guard_ok', False)} "
        f"| pending_action_requests={control_plane.get('pending_action_requests', 0)} "
        f"| check_detail_rows={len(control_plane.get('check_details', []) or [])}"
    )
    lines.append("")

