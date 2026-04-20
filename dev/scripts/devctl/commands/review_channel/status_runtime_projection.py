"""Runtime snapshot refresh helpers for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from .doctor_support import attach_status_runtime_snapshot
from .reviewer_runtime_snapshot import attach_reviewer_runtime_snapshot

_RUNTIME_SNAPSHOT_REPORT_KEYS = (
    "authority_snapshot",
    "reviewer_runtime",
    "doctor",
    "commit_pipeline",
    "recovery_assessment",
    "current_session",
    "coordination",
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
        return
    attach_status_runtime_snapshot(report)
