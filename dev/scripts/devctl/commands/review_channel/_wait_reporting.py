"""Report/render helpers for the implementer wait loop."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

from ...review_channel.peer_liveness import AttentionStatus

STOP_REASON_REVIEWER_UPDATE_OBSERVED: Final = "reviewer_update_observed"
STOP_REASON_REVIEWER_UPDATE_READY: Final = "reviewer_update_ready"
STOP_REASON_NOT_WAITING: Final = "not_waiting"
STOP_REASON_REVIEWER_UNHEALTHY: Final = "reviewer_unhealthy"
STOP_REASON_TIMED_OUT: Final = "timed_out"

_REVIEWER_UPDATE_MESSAGES: Final[dict[AttentionStatus, str]] = {
    AttentionStatus.CLAUDE_ACK_STALE: (
        "Reviewer state advanced and Claude ACK is now stale. "
        "Repoll `bridge.md`, acknowledge the current instruction revision, "
        "and only then continue coding."
    ),
    AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED: (
        "Reviewer follow-up is still required on the current tree. "
        "Keep waiting on Codex review instead of widening the slice."
    ),
}
_TIMEOUT_MESSAGES: Final[dict[AttentionStatus, str]] = {
    AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED: (
        "Timed out while reviewer follow-up was still required on the current tree. "
        "Codex still owes a re-review pass."
    ),
    AttentionStatus.CLAUDE_ACK_STALE: (
        "Timed out while Claude ACK remained stale against the current instruction revision. "
        "Repoll the bridge and acknowledge the latest reviewer instruction."
    ),
}


@dataclass(frozen=True, slots=True)
class ImplementerWaitState:
    """Rendered wait-state payload."""

    mode: str
    stop_reason: str
    polls_observed: int
    wait_interval_seconds: int
    wait_timeout_seconds: int
    baseline_instruction_revision: str
    current_instruction_revision: str
    baseline_attention_status: str
    current_attention_status: str
    baseline_attention_summary: str
    current_attention_summary: str
    reviewer_update_observed: bool

    def to_report(self) -> dict[str, object]:
        """Return the stable report payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ImplementerWaitReportUpdate:
    """Typed top-level fields added to an implementer-wait status report."""

    action: str
    ok: bool
    exit_ok: bool
    exit_code: int
    wait_state: dict[str, object]
    wait_attention_status: str
    wait_attention_summary: str
    wait_attention_recommended_action: str

    def apply(self, report: dict[str, object]) -> None:
        """Mutate the existing status report with stable wait fields."""
        report.update(asdict(self))


def finalize_implementer_wait_report(
    *,
    baseline,
    current,
    args,
    outcome,
) -> tuple[dict[str, object], int]:
    """Attach stable wait-state output to the current status report."""
    report = dict(current.report)
    update = _build_wait_report_update(
        baseline=baseline,
        current=current,
        args=args,
        outcome=outcome,
    )
    update.apply(report)

    _append_wait_message(
        report,
        stop_reason=outcome.stop_reason,
        baseline=baseline,
        current=current,
    )

    return report, outcome.exit_code


def _build_wait_report_update(
    *,
    baseline,
    current,
    args,
    outcome,
) -> ImplementerWaitReportUpdate:
    wait_state = _build_wait_state(
        baseline=baseline,
        current=current,
        outcome=outcome,
    )

    return ImplementerWaitReportUpdate(
        action=getattr(args, "action", "implementer-wait"),
        ok=outcome.exit_code == 0,
        exit_ok=outcome.exit_code == 0,
        exit_code=outcome.exit_code,
        wait_state=wait_state,
        wait_attention_status=current.attention_status,
        wait_attention_summary=current.attention_summary,
        wait_attention_recommended_action=current.attention_recommended_action,
    )


def _build_wait_state(*, baseline, current, outcome) -> dict[str, object]:
    return ImplementerWaitState(
        mode="implementer_wait",
        stop_reason=outcome.stop_reason,
        polls_observed=outcome.polls_observed,
        wait_interval_seconds=outcome.wait_interval_seconds,
        wait_timeout_seconds=outcome.wait_timeout_seconds,
        baseline_instruction_revision=baseline.current_instruction_revision,
        current_instruction_revision=current.current_instruction_revision,
        baseline_attention_status=baseline.attention_status,
        current_attention_status=current.attention_status,
        baseline_attention_summary=baseline.attention_summary,
        current_attention_summary=current.attention_summary,
        reviewer_update_observed=outcome.stop_reason in {
            STOP_REASON_REVIEWER_UPDATE_OBSERVED,
            STOP_REASON_REVIEWER_UPDATE_READY,
        },
    ).to_report()


def _append_wait_message(
    report: dict[str, object],
    *,
    stop_reason: str,
    baseline,
    current,
) -> None:
    payload = _resolve_wait_message(
        stop_reason=stop_reason,
        baseline=baseline,
        current=current,
    )
    if payload is None:
        return

    entries = report.setdefault(payload["field"], [])
    if not isinstance(entries, list):
        return

    entries.append(payload["text"])


def _resolve_wait_message(
    *,
    stop_reason: str,
    baseline,
    current,
) -> dict[str, str] | None:
    if stop_reason in {
        STOP_REASON_REVIEWER_UPDATE_OBSERVED,
        STOP_REASON_REVIEWER_UPDATE_READY,
    }:
        return {
            "field": "warnings",
            "text": _reviewer_update_message(current),
        }

    if stop_reason == STOP_REASON_NOT_WAITING:
        return {
            "field": "errors",
            "text": (
                "Implementer wait requires pending review work. The current tree already matches the reviewed hash and Claude ACK is current."
            ),
        }

    if stop_reason == STOP_REASON_REVIEWER_UNHEALTHY:
        return {
            "field": "errors",
            "text": (
                "Implementer wait stopped because the reviewer loop is unhealthy. "
                f"Current attention status: `{current.attention_status or 'unknown'}`. "
                "Restore the reviewer heartbeat/supervisor instead of waiting silently."
            ),
        }

    if stop_reason == STOP_REASON_TIMED_OUT:
        return {
            "field": "errors",
            "text": _timeout_message(baseline, current),
        }

    return None


def _reviewer_update_message(current) -> str:
    typed_status = _attention_status(current.attention_status)
    if typed_status in _REVIEWER_UPDATE_MESSAGES:
        return _REVIEWER_UPDATE_MESSAGES[typed_status]

    if current.attention_summary:
        return current.attention_summary

    return (
        "Reviewer-owned bridge content or a fresh Claude-targeted review packet changed. "
        "Re-read `bridge.md`, poll the review-channel inbox, and resume from the new reviewer state."
    )


def _timeout_message(baseline, current) -> str:
    effective_status = _attention_status(
        current.attention_status or baseline.attention_status
    )
    if effective_status in _TIMEOUT_MESSAGES:
        return _TIMEOUT_MESSAGES[effective_status]

    return "Timed out waiting for a meaningful reviewer-owned bridge or packet update."


def _attention_status(raw_status: str) -> AttentionStatus | None:
    try:
        return AttentionStatus(raw_status)
    except ValueError:
        return None
