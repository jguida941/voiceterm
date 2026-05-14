"""Runtime snapshot refresh helpers for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from .doctor_support import attach_status_runtime_snapshot
from .reviewer_runtime_snapshot import attach_reviewer_runtime_snapshot
from .sync_status_agent_loop import agent_loop_decisions_for_work_board

_RUNTIME_SNAPSHOT_REPORT_KEYS = (
    "authority_snapshot",
    "reviewer_runtime",
    "doctor",
    "commit_pipeline",
    "recovery_assessment",
    "current_session",
    "coordination",
    "coordination_state",
    "agent_sync",
    "agent_work_board",
    "agent_loop_decisions",
    "session_status_projection",
    "observed_control_topology",
    "implementation_permission",
    "reviewer_mode",
    "effective_reviewer_mode",
    "reviewer_freshness",
    "current_instruction_revision",
    "implementer_ack_state",
    "safe_to_fanout",
    "resync_required",
    "ownership_status",
    "next_command",
    "last_codex_poll",
    "last_codex_poll_utc",
    "snapshot_id",
    "zref",
)


def refresh_report_runtime_snapshot(report: dict[str, object]) -> None:
    """Rehydrate top-level runtime fields from the fresh typed projection bundle."""
    typed_review_state = report.pop("_typed_review_state", None)
    for key in _RUNTIME_SNAPSHOT_REPORT_KEYS:
        report.pop(key, None)
    if typed_review_state is not None:
        attention = report.get("attention") if isinstance(report.get("attention"), Mapping) else None
        attach_reviewer_runtime_snapshot(
            report,
            review_state=typed_review_state,
            attention=attention,
        )
        _refresh_report_work_board_identity(report)
        return
    attach_status_runtime_snapshot(report)
    _refresh_report_work_board_identity(report)


def _refresh_report_work_board_identity(report: dict[str, object]) -> None:
    work_board = report.get("agent_work_board")
    if not isinstance(work_board, Mapping):
        return
    from ...review_channel.status_bundle import (
        _refresh_preserved_work_board_runtime_identity,
    )

    refreshed = _refresh_preserved_work_board_runtime_identity(
        work_board,
        collaboration=report.get("collaboration"),
    )
    if refreshed is work_board:
        return
    report["agent_work_board"] = refreshed
    if isinstance(refreshed, Mapping):
        report["agent_loop_decisions"] = agent_loop_decisions_for_work_board(
            review_state=report,
            work_board=refreshed,
        )
