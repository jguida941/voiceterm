"""Structured lane builders for the Operator Console."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .lane_attention import (
    attention_status_hint,
    operator_state_label,
    prefer_status_hint,
)
from ..core.models import AgentLaneData, ApprovalRequest
from ..sessions.session_trace_reader import SessionTraceSnapshot


def build_codex_lane(
    sections: dict[str, str],
    last_codex_poll: str | None,
    last_worktree_hash: str | None,
    *,
    attention_status: str | None = None,
    attention_summary: str | None = None,
    live_trace: SessionTraceSnapshot | None = None,
) -> AgentLaneData:
    """Build structured Codex reviewer lane data from parsed sections."""
    poll_status = sections.get("Poll Status", "(missing)")
    verdict = sections.get("Current Verdict", "(missing)")
    findings = sections.get("Open Findings", "(missing)")
    live_status = _live_trace_status(live_trace)
    status_hint = prefer_status_hint(
        _lane_status_hint(_codex_status_hint(poll_status, last_codex_poll), live_status),
        attention_status_hint(attention_status),
    )
    state_label = _codex_state_label(poll_status, last_codex_poll)
    risk_label = _codex_risk_label(verdict, findings)
    confidence_label = _codex_confidence_label(verdict, findings)

    raw_parts = [
        f"Last Codex poll: {last_codex_poll or '(unknown)'}",
        f"Last worktree hash: {last_worktree_hash or '(unknown)'}",
        *( _live_trace_raw_parts(live_trace) ),
        f"\nPoll Status:\n{poll_status}",
        f"\nCurrent Verdict:\n{verdict}",
        f"\nOpen Findings:\n{findings}",
    ]
    if attention_summary:
        raw_parts.append(f"\nAttention:\n{attention_summary}")
    rows = [
        ("State", state_label),
    ]
    if live_trace is not None:
        rows.extend(
            [
                ("Session", _live_trace_label(live_trace)),
                ("Updated", live_trace.updated_at or "(unknown)"),
            ]
        )
    rows.extend(
        [
            ("Last Poll", last_codex_poll or "(unknown)"),
            ("Worktree", _truncate(last_worktree_hash or "(unknown)", 16)),
            ("Verdict", _one_line_summary(verdict)),
            ("Findings", _one_line_summary(findings)),
            ("Risk", risk_label),
            ("Confidence", confidence_label),
        ]
    )
    if attention_summary:
        rows.append(("Attention", _one_line_summary(attention_summary)))
    return AgentLaneData(
        provider_name="Codex",
        lane_title="Codex Session Monitor" if live_trace is not None else "Codex Bridge Monitor",
        role_label="Reviewer",
        status_hint=status_hint,
        state_label=state_label,
        rows=tuple(rows),
        raw_text="\n".join(raw_parts),
        risk_label=risk_label,
        confidence_label=confidence_label,
    )

def build_claude_lane(
    sections: dict[str, str],
    *,
    live_trace: SessionTraceSnapshot | None = None,
) -> AgentLaneData:
    """Build structured Claude implementer lane data from parsed sections."""
    status = sections.get("Claude Status", "(missing)")
    questions = sections.get("Claude Questions", "(missing)")
    ack = sections.get("Claude Ack", "(missing)")
    live_status = _live_trace_status(live_trace)
    status_hint = _lane_status_hint(_claude_status_hint(status), live_status)
    state_label = _claude_state_label(status, ack)

    raw_parts = [
        *( _live_trace_raw_parts(live_trace) ),
        f"Claude Status:\n{status}",
        f"\nClaude Questions:\n{questions}",
        f"\nClaude Ack:\n{ack}",
    ]
    rows = [("State", state_label)]
    if live_trace is not None:
        rows.extend(
            [
                ("Session", _live_trace_label(live_trace)),
                ("Updated", live_trace.updated_at or "(unknown)"),
            ]
        )
    rows.extend(
        [
            ("Questions", _one_line_summary(questions)),
            ("Ack", _one_line_summary(ack)),
        ]
    )
    return AgentLaneData(
        provider_name="Claude",
        lane_title="Claude Session Monitor" if live_trace is not None else "Claude Bridge Monitor",
        role_label="Implementer",
        status_hint=status_hint,
        state_label=state_label,
        rows=tuple(rows),
        raw_text="\n".join(raw_parts),
    )


def build_operator_lane(
    sections: dict[str, str],
    pending_approvals: tuple[ApprovalRequest, ...],
    review_state_path: Path | None,
    *,
    attention_status: str | None = None,
    attention_summary: str | None = None,
) -> AgentLaneData:
    """Build structured operator lane data from parsed sections."""
    instruction = sections.get("Current Instruction For Claude", "(missing)")
    scope = sections.get("Last Reviewed Scope", "(missing)")
    approval_count = len(pending_approvals)
    status_hint = prefer_status_hint(
        "warning" if approval_count > 0 else "active",
        attention_status_hint(attention_status),
    )
    state_label = operator_state_label(
        _one_line_summary(instruction),
        approval_count,
        attention_status,
    )

    raw_parts = [
        f"Current Instruction For Claude:\n{instruction}",
        f"\nLast Reviewed Scope:\n{scope}",
        f"\nReview state: {review_state_path or '(not found)'}",
        f"Pending approvals: {approval_count}",
    ]
    if attention_summary:
        raw_parts.append(f"\nAttention:\n{attention_summary}")
    rows = [
        ("State", state_label),
        ("Instruction", _one_line_summary(instruction)),
        ("Scope", _one_line_summary(scope)),
        ("Approvals", str(approval_count)),
        (
            "Review State",
            str(review_state_path) if review_state_path else "(not found)",
        ),
    ]
    if attention_summary:
        rows.append(("Attention", _one_line_summary(attention_summary)))
    return AgentLaneData(
        provider_name="Operator",
        lane_title="Operator Bridge State",
        role_label="Human",
        status_hint=status_hint,
        state_label=state_label,
        rows=tuple(rows),
        raw_text="\n".join(raw_parts),
    )


def build_cursor_lane(
    sections: dict[str, str],
    *,
    live_trace: SessionTraceSnapshot | None = None,
) -> AgentLaneData:
    """Build structured Cursor editor lane data from parsed sections."""
    status = sections.get("Cursor Status", "(missing)")
    focus = sections.get("Cursor Focus", sections.get("Cursor Instruction", "(missing)"))
    live_status = _live_trace_status(live_trace)
    status_hint = _lane_status_hint(
        _cursor_status_hint(status, has_live_trace=live_trace is not None),
        live_status,
    )
    state_label = _cursor_state_label(status, has_live_trace=live_trace is not None)
    rows = [("State", state_label)]
    if live_trace is not None:
        rows.extend(
            [
                ("Session", _live_trace_label(live_trace)),
                ("Updated", live_trace.updated_at or "(unknown)"),
            ]
        )
    rows.extend(
        [
            ("Status", _one_line_summary(status)),
            ("Focus", _one_line_summary(focus)),
        ]
    )
    raw_parts = [
        *(_live_trace_raw_parts(live_trace)),
        f"Cursor Status:\n{status}",
        f"\nCursor Focus:\n{focus}",
    ]
    return AgentLaneData(
        provider_name="Cursor",
        lane_title=(
            "Cursor Session Monitor" if live_trace is not None else "Cursor Bridge Monitor"
        ),
        role_label="Editor",
        status_hint=status_hint,
        state_label=state_label,
        rows=tuple(rows),
        raw_text="\n".join(raw_parts),
    )


def _codex_status_hint(poll_status: str, last_poll: str | None) -> str:
    lower = poll_status.lower()
    if any(word in lower for word in ("active", "running", "polling", "reviewing")):
        return "active"
    if any(word in lower for word in ("blocked", "waiting", "awaiting")):
        return "warning"
    if last_poll and _is_stale_timestamp(last_poll, max_age_minutes=10):
        return "stale"
    if any(word in lower for word in ("error", "fail", "crash")):
        return "stale"
    return "idle"


def _claude_status_hint(claude_status: str) -> str:
    lower = claude_status.lower()
    if any(word in lower for word in ("error", "fail", "crash")):
        return "stale"
    if any(word in lower for word in ("paused", "blocked", "waiting", "pending")):
        return "warning"
    if any(word in lower for word in ("coding", "implementing", "running", "complete")):
        return "active"
    return "idle"


def _cursor_status_hint(cursor_status: str, *, has_live_trace: bool) -> str:
    lower = cursor_status.lower()
    if any(word in lower for word in ("error", "fail", "crash")):
        return "stale"
    if any(word in lower for word in ("paused", "blocked", "waiting", "pending")):
        return "warning"
    if any(
        word in lower
        for word in ("editing", "implementing", "active", "running", "working")
    ):
        return "active"
    if has_live_trace:
        return "active"
    return "idle"


def _codex_state_label(poll_status: str, last_poll: str | None) -> str:
    lower = poll_status.lower()
    if any(word in lower for word in ("error", "fail", "crash")):
        return "Error"
    if last_poll and _is_stale_timestamp(last_poll, max_age_minutes=10):
        return "Stale"
    if any(word in lower for word in ("review", "polling", "watch loop", "active reviewer")):
        return "Reviewing"
    if any(word in lower for word in ("waiting", "awaiting", "blocked")):
        return "Waiting"
    return "Idle"


def _claude_state_label(claude_status: str, ack: str) -> str:
    combined = f"{claude_status}\n{ack}".lower()
    if any(word in combined for word in ("error", "fail", "crash")):
        return "Error"
    if any(word in combined for word in ("blocked", "paused")):
        return "Blocked"
    if any(word in combined for word in ("waiting", "awaiting", "pending")):
        return "Waiting"
    if any(word in combined for word in ("coding", "implementing", "working", "writing")):
        return "Implementing"
    if any(word in combined for word in ("complete", "done", "fixed", "acknowledged")):
        return "Ready"
    return "Idle"


def _cursor_state_label(cursor_status: str, *, has_live_trace: bool) -> str:
    lower = cursor_status.lower()
    if any(word in lower for word in ("error", "fail", "crash")):
        return "Error"
    if any(word in lower for word in ("blocked", "paused")):
        return "Blocked"
    if any(word in lower for word in ("waiting", "awaiting", "pending")):
        return "Waiting"
    if any(word in lower for word in ("editing", "implementing", "working", "running")):
        return "Editing"
    if has_live_trace:
        return "Editing"
    return "Idle"


def _codex_risk_label(verdict: str, findings: str) -> str:
    combined = f"{verdict}\n{findings}".lower()
    if any(word in combined for word in ("critical", "high", "unsafe", "blocker", "breaking")):
        return "High"
    if any(word in combined for word in ("pending", "warning", "finding", "approval", "needs")):
        return "Medium"
    if any(word in combined for word in ("none", "green", "safe", "clean", "accepted")):
        return "Low"
    return "Unknown"


def _codex_confidence_label(verdict: str, findings: str) -> str:
    combined = f"{verdict}\n{findings}".lower()
    if any(word in combined for word in ("green", "safe", "clean", "accepted", "complete")):
        return "High"
    if any(word in combined for word in ("missing", "unknown", "unclear", "blocked", "stale")):
        return "Low"
    return "Medium"


def _is_stale_timestamp(iso_timestamp: str, *, max_age_minutes: int) -> bool:
    try:
        parsed = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        age = datetime.now(tz=timezone.utc) - parsed
        return age.total_seconds() > max_age_minutes * 60
    except (ValueError, TypeError):
        return False


def _one_line_summary(text: str, max_len: int = 80) -> str:
    for line in text.strip().splitlines():
        stripped = line.strip().lstrip("- ")
        if stripped:
            return _truncate(stripped, max_len)
    return "(empty)"


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"


def _lane_status_hint(
    bridge_status: str,
    live_status: tuple[str, str] | None,
) -> str:
    if bridge_status != "idle" or live_status is None:
        return bridge_status
    return live_status[0]

def _live_trace_status(
    live_trace: SessionTraceSnapshot | None,
    *,
    max_age_seconds: int = 300,
    active_age_seconds: int = 120,
) -> tuple[str, str] | None:
    if live_trace is None or live_trace.updated_at is None:
        return None
    age_seconds = _timestamp_age_seconds(live_trace.updated_at)
    if age_seconds is None or age_seconds > max_age_seconds:
        return None
    if age_seconds <= active_age_seconds:
        return ("active", "live")
    return ("warning", "recent")


def _live_trace_label(live_trace: SessionTraceSnapshot) -> str:
    freshness = _live_trace_status(live_trace)
    freshness_label = freshness[1] if freshness is not None else "captured"
    return f"{live_trace.session_name} [{freshness_label}]"


def _live_trace_raw_parts(live_trace: SessionTraceSnapshot | None) -> tuple[str, ...]:
    if live_trace is None:
        return ()
    return (
        f"Live session trace: {live_trace.session_name}",
        f"Live session updated: {live_trace.updated_at or '(unknown)'}",
        f"Live session log: {live_trace.log_path}",
    )


def _timestamp_age_seconds(iso_timestamp: str) -> float | None:
    try:
        parsed = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return (datetime.now(tz=timezone.utc) - parsed).total_seconds()
