"""Tests for compact startup continuity projections."""

from __future__ import annotations

from dev.scripts.devctl.runtime.review_state_packet_models import ReviewPacketState
from dev.scripts.devctl.runtime.startup_continuity import (
    startup_packet_carry_forward_debt,
    startup_packet_continuity_index,
)


class ReviewStateLike:
    def __init__(self, packets: tuple[ReviewPacketState, ...]) -> None:
        self.packets = packets

    def to_dict(self) -> dict[str, object]:
        raise AssertionError("startup continuity must not deep-copy full ReviewState")


def test_startup_continuity_uses_narrow_packet_projection(tmp_path) -> None:
    review_state = ReviewStateLike(
        (
            ReviewPacketState(
                packet_id="rev_pkt_9999",
                kind="finding",
                from_agent="claude",
                to_agent="codex",
                summary="Needs durable ownership",
                body="promote this finding into plan state",
                status="acked",
                policy_hint="",
                requested_action="",
                approval_required=False,
                posted_at="2026-05-16T00:00:00Z",
                target_kind="plan",
                latest_event_id="rev_evt_9999",
                acked_at_utc="2026-05-16T00:01:00Z",
            ),
        )
    )

    debts = startup_packet_carry_forward_debt(
        repo_root=tmp_path,
        review_state=review_state,
    )
    continuity = startup_packet_continuity_index(review_state)

    assert debts[0]["packet_id"] == "rev_pkt_9999"
    assert debts[0]["reason"] == "acked_without_terminal_or_durable_owner"
    assert continuity["rows"][0]["packet_id"] == "rev_pkt_9999"
    assert continuity["rows"][0]["sink"] == "carry_forward_debt"
