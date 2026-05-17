"""History outcome helpers for event-backed review-channel actions."""

from __future__ import annotations

from ...review_channel.packet_outcomes import (
    attach_packet_outcomes,
    build_packet_outcome_ledger,
)


def attach_history_outcomes_if_requested(
    *,
    args,
    bundle,
    packets: list[dict[str, object]],
    generated_at_utc: str,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    """Attach a PacketOutcomeLedger to history rows when the CLI asks for it."""
    if not getattr(args, "include_outcomes", False):
        return packets, None
    ledger = build_packet_outcome_ledger(
        packets=packets,
        events=bundle.events,
        generated_at_utc=generated_at_utc,
        source="review-channel history --include-outcomes",
    )
    return attach_packet_outcomes(packets, ledger), ledger.to_dict()
