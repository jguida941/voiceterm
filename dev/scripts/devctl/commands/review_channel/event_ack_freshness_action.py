"""Implementer ACK freshness action for event-backed review-channel state."""

from __future__ import annotations

from ...review_channel.ack_freshness_authority import (
    build_implementer_ack_freshness_projection,
)
from .event_action_support import EventActionContext


def run_check_ack_freshness_action(
    *,
    context: EventActionContext,
    bundle,
) -> tuple[dict, int]:
    """Report whether bridge-visible implementer ACK is typed-authority backed."""
    ack_freshness = build_implementer_ack_freshness_projection(
        review_state=bundle.review_state,
        events=tuple(bundle.events or ()),
        mode=getattr(context.args, "ack_freshness_mode", "on_demand"),
    )
    report, _ = context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
    )
    report["ack_freshness"] = ack_freshness
    report["ok"] = bool(report.get("ok")) and bool(ack_freshness.get("ok"))
    report["exit_ok"] = report["ok"]
    report["exit_code"] = 0 if report["ok"] else 1
    report["status"] = "ok" if report["ok"] else "blocked"
    if not ack_freshness.get("ok"):
        errors = report.setdefault("errors", [])
        if isinstance(errors, list):
            errors.append(str(ack_freshness.get("detail") or "ACK freshness failed"))
    return report, int(report["exit_code"])
