"""Per-provider packet-attention receipts.

This compatibility module keeps the historic `maybe_wake_*` import path, but
packet delivery is not process authority. Packets record typed attention only;
scheduler/runtime controllers own session starts after explicit task
boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .reviewer_follow_guard import ReviewerWakeDeps
from .wake_receipt_models import WakeReceiptExtras, wake_report


@dataclass(frozen=True)
class WakeRoutingContext:
    """Bundle of routing inputs every wake-dispatch helper needs.

    Keeps each downstream function under the parameter-count guard
    threshold (>6 fails for python). Matches the shape of the
    governed-executor's request envelope so the dispatch can later be
    composed with `safe_auto_apply` without re-marshalling.
    """

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    operator_interaction_mode: str


def maybe_wake_waiting_agent_conductor(
    *,
    routing: WakeRoutingContext,
    target_agent: str,
    packet: dict[str, object],
    maybe_wake_reviewer_fn,
    deps: ReviewerWakeDeps | None = None,
) -> dict[str, object] | None:
    """Record provider packet attention without launching a conductor."""

    _ = (routing, maybe_wake_reviewer_fn, deps)
    provider = str(target_agent or "").strip().lower()
    if not provider:
        return None
    return _packet_delivery_no_launch_report(provider=provider, packet=packet)


def _packet_delivery_no_launch_report(
    *,
    provider: str,
    packet: dict[str, object],
) -> dict[str, object]:
    report = wake_report(
        packet=packet,
        attempted=False,
        woke=False,
        reason="packet_delivery_records_typed_attention_only",
        target_agent=provider,
        extras=WakeReceiptExtras(
            target_role=str(packet.get("target_role") or "").strip(),
            target_session_id=str(packet.get("target_session_id") or "").strip(),
            wake_method="none",
            visible_session_woke=False,
            warnings=(
                "Packet attention does not launch or replace provider "
                "sessions; scheduler/runtime controllers own session starts "
                "after explicit task boundaries.",
            ),
        ),
    )
    report["attention_recorded"] = True
    return report
