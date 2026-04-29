"""Regression coverage for actionable review-channel packet cleanup."""

from __future__ import annotations

import importlib
import sys
import types

from dev.scripts.devctl.review_channel.action_request import action_requests_from_packets
from dev.scripts.devctl.review_channel.current_session_render import current_focus_line
from dev.scripts.devctl.review_channel.current_session_support import (
    event_current_instruction,
)
from dev.scripts.devctl.review_channel.events import (
    filter_history_packets as public_filter_history_packets,
)
from dev.scripts.devctl.review_channel.pending_packets import (
    live_pending_packets,
    reconcile_review_state_packet_queue,
)
from dev.scripts.devctl.review_channel.projection_bundle_markdown import (
    render_latest_markdown,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewPacketState
from dev.scripts.devctl.review_channel.event_reducer import filter_history_packets


def _packet(
    *,
    packet_id: str,
    status: str = "pending",
    expires_at_utc: str = "",
    kind: str = "action_request",
    summary: str = "Packet summary",
    requested_action: str = "commit",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "from_agent": "codex",
        "to_agent": "operator",
        "summary": summary,
        "body": "body",
        "status": status,
        "policy_hint": "",
        "requested_action": requested_action,
        "approval_required": True,
        "posted_at": "2026-04-08T00:00:00Z",
        "expires_at_utc": expires_at_utc,
        "target_kind": "runtime",
        "target_ref": "remote_commit_pipeline:pipeline-123",
        "target_revision": "gen-123",
        "pipeline_generation": "gen-123",
        "staged_snapshot_hash": "tree-123",
        "guard_results_summary": "{\"action_id\":\"quality.guard_bundle\",\"reason\":\"\",\"status\":\"pass\"}",
    }


def test_live_pending_packets_excludes_expired_history() -> None:
    packets = [
        _packet(
            packet_id="live",
            expires_at_utc="2999-01-01T00:00:00Z",
        ),
        _packet(
            packet_id="stale",
            expires_at_utc="2000-01-01T00:00:00Z",
        ),
        _packet(
            packet_id="resolved",
            status="applied",
        ),
    ]

    live_packets = live_pending_packets(packets)

    assert [packet["packet_id"] for packet in live_packets] == ["live"]


def test_live_pending_packets_preserves_typed_packets() -> None:
    packet = ReviewPacketState(
        packet_id="typed-live",
        kind="action_request",
        from_agent="codex",
        to_agent="operator",
        summary="Typed packet stays actionable",
        body="body",
        status="pending",
        policy_hint="",
        requested_action="commit",
        approval_required=True,
        posted_at="2026-04-08T00:00:00Z",
        expires_at_utc="2999-01-01T00:00:00Z",
    )

    live_packets = live_pending_packets([packet])

    assert live_packets == (packet,)


def test_action_request_projection_ignores_expired_packets() -> None:
    packets = [
        _packet(
            packet_id="live",
            expires_at_utc="2999-01-01T00:00:00Z",
            summary="Approve the live commit request",
        ),
        _packet(
            packet_id="stale",
            expires_at_utc="2000-01-01T00:00:00Z",
            summary="Expired request should not render",
        ),
    ]

    projected = action_requests_from_packets(packets)

    assert [item.id for item in projected] == ["live"]


def test_current_focus_line_uses_typed_queue_instruction() -> None:
    review_state = {
        "current_session": {},
        "bridge": {
            "current_instruction": "Bridge text should stay a compatibility surface",
        },
        "queue": {
            "derived_next_instruction": "Live request should stay visible",
        },
        "packets": [
            _packet(
                packet_id="stale",
                expires_at_utc="2000-01-01T00:00:00Z",
                summary="Expired request should not become the focus",
            ),
            _packet(
                packet_id="live",
                expires_at_utc="2999-01-01T00:00:00Z",
                summary="Live request should stay visible",
            ),
        ],
    }

    assert current_focus_line(review_state) == "Live request should stay visible"


def test_current_focus_line_ignores_live_findings_without_instruction_payload() -> None:
    review_state = {
        "current_session": {},
        "bridge": {},
        "queue": {},
        "packets": [
            _packet(
                packet_id="finding",
                kind="finding",
                summary="Finding should remain a finding",
                requested_action="review_only",
                expires_at_utc="2999-01-01T00:00:00Z",
            )
        ],
    }

    assert current_focus_line(review_state) == "(missing)"


def test_event_current_instruction_does_not_fallback_to_packet_summary() -> None:
    review_state = {
        "queue": {
            "derived_next_instruction": "",
        },
        "packets": [
            _packet(
                packet_id="finding",
                kind="finding",
                summary="Finding should remain a finding",
                requested_action="review_only",
                expires_at_utc="2999-01-01T00:00:00Z",
            ),
            _packet(
                packet_id="instruction",
                kind="instruction",
                summary="Packet summary should not bypass the typed queue",
                requested_action="review_only",
                expires_at_utc="2999-01-01T00:00:00Z",
            ),
        ],
    }

    assert event_current_instruction(review_state) == ""


def test_latest_markdown_separates_live_packets_from_history() -> None:
    review_state = {
        "timestamp": "2026-04-08T00:00:00Z",
        "ok": True,
        "review": {
            "plan_id": "MP-377",
            "session_id": "markdown-bridge",
            "bridge_path": "bridge.md",
            "review_channel_path": "dev/active/review_channel.md",
        },
        "queue": {
            "pending_total": 1,
            "stale_packet_count": 1,
            "derived_next_instruction": "",
            "derived_next_instruction_source": {},
        },
        "current_session": {
            "current_instruction": "",
            "current_instruction_revision": "",
            "implementer_status": "",
            "implementer_ack_state": "current",
            "last_reviewed_scope": "",
        },
        "bridge": {},
        "review_candidate": {},
        "registry": {"agents": []},
        "packets": [
            _packet(
                packet_id="live",
                expires_at_utc="2999-01-01T00:00:00Z",
                summary="Live request should render in the actionable queue",
            ),
            _packet(
                packet_id="stale",
                expires_at_utc="2000-01-01T00:00:00Z",
                summary="Expired request should render only in history",
            ),
        ],
        "_compat": {},
    }

    markdown = render_latest_markdown(review_state, {"agents": []})

    assert "## Packet Queue Reconciliation" in markdown
    assert "expired_pending_hidden_from_inbox_total: 1" in markdown
    assert "## Live Packets" in markdown
    assert "## Packet History" in markdown
    assert "Live request should render in the actionable queue" in markdown
    assert "Expired request should render only in history" in markdown
    assert markdown.index("## Live Packets") < markdown.index("## Packet History")


def test_event_markdown_separates_live_packets_from_history() -> None:
    stub_name = "dev.scripts.devctl.commands.review_channel_bridge_render"
    event_render_name = "dev.scripts.devctl.review_channel.event_render"
    previous_stub = sys.modules.get(stub_name)
    previous_event_render = sys.modules.get(event_render_name)
    stub = types.ModuleType(stub_name)

    def _append_common_report_sections(lines: list[str], report: dict) -> None:
        return None

    stub.append_common_report_sections = _append_common_report_sections
    sys.modules[stub_name] = stub
    sys.modules.pop(event_render_name, None)
    try:
        render_event_md = importlib.import_module(event_render_name).render_event_md

        report = {
            "ok": True,
            "action": "status",
            "execution_mode": "markdown-bridge",
            "queue": {"pending_total": 1, "stale_packet_count": 1},
            "queue_reconciliation": {
                "live_pending_total": 1,
                "history_total": 1,
                "stale_pending_total": 1,
                "queue_pending_total": 1,
                "queue_stale_total": 1,
                "stale_pending_hidden_from_inbox_total": 1,
                "history_shown_total": 1,
                "history_truncated": False,
                "needs_attention": True,
            },
            "packet": None,
            "packets": [
                _packet(
                    packet_id="live",
                    expires_at_utc="2999-01-01T00:00:00Z",
                    summary="Live request should render in the actionable queue",
                ),
                _packet(
                    packet_id="stale",
                    expires_at_utc="2000-01-01T00:00:00Z",
                    summary="Expired request should render only in history",
                ),
            ],
            "history": [],
            "packet_outcome_ledger": {
                "contract_id": "PacketOutcomeLedger",
                "record_count": 1,
                "outcome_counts": {"archived": 1},
            },
        }

        markdown = render_event_md(report)

        assert "## Packet Queue Reconciliation" in markdown
        assert "expired pending packets are archived audit rows whose TTL elapsed" in markdown
        assert "## Live Packets" in markdown
        assert "## Packet History" in markdown
        assert "stale: pending (expired)" in markdown
        assert "## Packet Outcome Ledger" in markdown
        assert "outcome_counts: archived=1" in markdown
    finally:
        if previous_stub is None:
            sys.modules.pop(stub_name, None)
        else:
            sys.modules[stub_name] = previous_stub
        if previous_event_render is None:
            sys.modules.pop(event_render_name, None)
        else:
            sys.modules[event_render_name] = previous_event_render


def test_latest_markdown_surfaces_history_cap_explicitly() -> None:
    review_state = {
        "timestamp": "2026-04-08T00:00:00Z",
        "ok": True,
        "review": {
            "plan_id": "MP-377",
            "session_id": "markdown-bridge",
            "bridge_path": "bridge.md",
            "review_channel_path": "dev/active/review_channel.md",
        },
        "queue": {
            "pending_total": 0,
            "stale_packet_count": 6,
            "derived_next_instruction": "",
            "derived_next_instruction_source": {},
        },
        "current_session": {
            "current_instruction": "",
            "current_instruction_revision": "",
            "implementer_status": "",
            "implementer_ack_state": "current",
            "last_reviewed_scope": "",
        },
        "bridge": {},
        "review_candidate": {},
        "registry": {"agents": []},
        "packets": [
            _packet(
                packet_id=f"stale-{idx}",
                expires_at_utc="2000-01-01T00:00:00Z",
                summary=f"Expired request {idx}",
            )
            for idx in range(6)
        ],
        "_compat": {},
    }

    markdown = render_latest_markdown(review_state, {"agents": []})

    assert "## Packet Queue Reconciliation" in markdown
    assert "history_shown_total: 5" in markdown
    assert "history_truncated: True" in markdown
    assert "showing latest 5 of 6 history packets" in markdown


def test_filter_history_packets_uses_reduced_packet_queue() -> None:
    review_state = {
        "packets": [
            _packet(
                packet_id="live",
                expires_at_utc="2999-01-01T00:00:00Z",
                summary="Live request should stay out of history",
            ),
            _packet(
                packet_id="stale",
                expires_at_utc="2000-01-01T00:00:00Z",
                summary="Expired request should remain in history",
            ),
            _packet(
                packet_id="acked",
                status="acked",
                summary="Acked request should remain in history",
            ),
        ]
    }

    history_packets = filter_history_packets(review_state)

    assert [packet["packet_id"] for packet in history_packets] == ["stale", "acked"]


def test_reconcile_review_state_packet_queue_surfaces_stale_history_split() -> None:
    review_state = {
        "queue": {"pending_total": 1, "stale_packet_count": 1},
        "packets": [
            _packet(
                packet_id="live",
                expires_at_utc="2999-01-01T00:00:00Z",
            ),
            _packet(
                packet_id="stale",
                expires_at_utc="2000-01-01T00:00:00Z",
            ),
            *[
                _packet(
                    packet_id=f"acked-{idx}",
                    status="acked",
                    summary=f"Acked request {idx}",
                )
                for idx in range(6)
            ],
        ],
    }

    reconciliation = reconcile_review_state_packet_queue(
        review_state,
        history_limit=5,
    )

    assert reconciliation.live_pending_total == 1
    assert reconciliation.stale_pending_total == 1
    assert reconciliation.history_total == 7
    assert reconciliation.history_shown_total == 5
    assert reconciliation.history_truncated is True
    assert reconciliation.pending_total_matches_queue is True
    assert reconciliation.stale_total_matches_queue is True
    assert reconciliation.stale_pending_hidden_from_inbox_total == 1


def test_public_events_surface_exports_filter_history_packets() -> None:
    review_state = {
        "packets": [
            _packet(
                packet_id="live",
                expires_at_utc="2999-01-01T00:00:00Z",
            ),
            _packet(
                packet_id="stale",
                expires_at_utc="2000-01-01T00:00:00Z",
            ),
        ]
    }

    history_packets = public_filter_history_packets(review_state)

    assert [packet["packet_id"] for packet in history_packets] == ["stale"]
