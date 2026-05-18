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


def test_live_pending_packets_excludes_failed_action_request() -> None:
    packets = [
        _packet(
            packet_id="failed",
            expires_at_utc="2999-01-01T00:00:00Z",
        )
        | {"execution_failed_at_utc": "2026-04-29T13:00:00Z"},
        _packet(
            packet_id="apply-pending",
            expires_at_utc="2999-01-01T00:00:00Z",
        )
        | {"apply_pending_after_execution_at_utc": "2026-04-29T13:01:00Z"},
        _packet(
            packet_id="live",
            expires_at_utc="2999-01-01T00:00:00Z",
        ),
    ]

    live_packets = live_pending_packets(packets)

    assert [packet["packet_id"] for packet in live_packets] == ["live"]


def test_live_pending_packets_keeps_absorbed_action_request_until_consumed() -> None:
    packet = _packet(
        packet_id="absorbed-action-request",
        kind="action_request",
        requested_action="stage_commit_pipeline",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-action-request",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-action-request:test"
            ),
            "action_item_dispositions": [
                "absorbed-action-request:stage_commit_pipeline:accepted"
            ],
            "resulting_decision": "stage_commit_pipeline_action_request_parsed",
            "decision_rationale": "action_request still awaits governed commit consumption",
            "evidence_refs": ["packet:absorbed-action-request#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert [row["packet_id"] for row in live_packets] == ["absorbed-action-request"]


def test_live_pending_packets_excludes_absorbed_action_request_after_consumption() -> None:
    packet = _packet(
        packet_id="absorbed-action-request",
        kind="action_request",
        requested_action="stage_commit_pipeline",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "apply_pending_after_execution_at_utc": "2026-05-17T18:46:00Z",
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-action-request",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-action-request:test"
            ),
            "action_item_dispositions": [
                "absorbed-action-request:stage_commit_pipeline:accepted"
            ],
            "resulting_decision": "stage_commit_pipeline_action_request_parsed",
            "decision_rationale": "action_request was consumed by governed commit",
            "evidence_refs": ["packet:absorbed-action-request#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert live_packets == ()


def test_live_pending_packets_keeps_acked_actionable_without_absorption() -> None:
    packets = [
        _packet(
            packet_id="acked-finding",
            status="acked",
            kind="finding",
            expires_at_utc="2999-01-01T00:00:00Z",
        ),
        _packet(
            packet_id="acked-system-notice",
            status="acked",
            kind="system_notice",
        ),
    ]

    live_packets = live_pending_packets(packets)

    assert [packet["packet_id"] for packet in live_packets] == ["acked-finding"]


def test_live_pending_packets_keeps_body_observed_without_absorption() -> None:
    packets = [
        _packet(
            packet_id="observed-finding",
            status="pending",
            kind="finding",
            expires_at_utc="2999-01-01T00:00:00Z",
        )
        | {
            "body_observed_at_utc": "2026-05-17T18:45:00Z",
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "session-1",
            "body_observed_event_id": "rev_evt_observed",
        }
    ]

    live_packets = live_pending_packets(packets)

    assert [packet["packet_id"] for packet in live_packets] == ["observed-finding"]


def test_live_pending_packets_excludes_acked_actionable_with_absorption() -> None:
    packets = [
        _packet(
            packet_id="absorbed-finding",
            status="acked",
            kind="finding",
            expires_at_utc="2999-01-01T00:00:00Z",
        )
        | {
            "absorption_receipt": {
                "contract_id": "PacketAbsorptionReceipt",
                "packet_id": "absorbed-finding",
                "body_sha256": "abc123",
                "absorbed_by_actor": "codex",
                "absorbed_by_role": "reviewer",
                "absorbed_by_session_id": "session-1",
                "absorbed_at_utc": "2026-05-17T18:45:00Z",
                "source_semantic_ingestion_receipt_id": (
                    "packet_semantic_ingestion:absorbed-finding:test"
                ),
                "action_item_dispositions": ["P235:deferred"],
                "resulting_decision": "continue_output_consumption_slice",
                "decision_rationale": "packet action items were classified",
                "defer_reason": "current output-consumption slice is blocking",
                "next_slice_refs": ["MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1"],
                "evidence_refs": ["packet:absorbed-finding#body_observed"],
            }
        }
    ]

    live_packets = live_pending_packets(packets)

    assert live_packets == ()


def test_live_pending_packets_keeps_absorbed_plan_without_durable_binding() -> None:
    packet = _packet(
        packet_id="absorbed-plan",
        status="pending",
        kind="plan_patch_review",
        requested_action="ingest_plan_intent",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "target_kind": "plan",
        "target_ref": "plan:MP-377",
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-plan",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-plan:test"
            ),
            "action_item_dispositions": ["accepted"],
            "resulting_decision": "plan_intent_requires_durable_binding",
            "decision_rationale": "packet plan intent was parsed",
            "evidence_refs": ["packet:absorbed-plan#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert [row["packet_id"] for row in live_packets] == ["absorbed-plan"]


def test_live_pending_packets_excludes_absorbed_plan_with_durable_binding() -> None:
    packet = _packet(
        packet_id="absorbed-plan",
        status="pending",
        kind="plan_patch_review",
        requested_action="ingest_plan_intent",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "target_kind": "plan",
        "target_ref": "plan:MP-377",
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "durable_binding": {
            "contract_id": "PacketCreationBinding",
            "status": "recorded",
            "binding_target_kind": "plan_row",
            "binding_target": "PKT-BIND-ABSORBED-PLAN",
        },
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-plan",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-plan:test"
            ),
            "action_item_dispositions": ["accepted"],
            "resulting_decision": "plan_intent_bound_to_plan_row",
            "decision_rationale": "packet plan intent was parsed and bound",
            "evidence_refs": ["packet:absorbed-plan#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert live_packets == ()


def test_live_pending_packets_excludes_absorbed_plan_with_deferred_disposition() -> None:
    packet = _packet(
        packet_id="absorbed-plan-deferred",
        status="pending",
        kind="plan_patch_review",
        requested_action="ingest_plan_intent",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "target_kind": "plan",
        "target_ref": "plan:MP-377",
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-plan-deferred",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-plan-deferred:test"
            ),
            "action_item_dispositions": ["deferred"],
            "resulting_decision": "plan_intent_deferred",
            "decision_rationale": "packet plan intent was parsed and deferred",
            "defer_reason": "current checkpoint authority lane is blocking",
            "next_slice_refs": ["MP377-P0-MAY17-CLOUD-DASHBOARD-REPO-SPLIT-S1"],
            "evidence_refs": ["packet:absorbed-plan-deferred#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert live_packets == ()


def test_live_pending_packets_keeps_absorbed_plan_with_incomplete_terminal_evidence() -> None:
    packet = _packet(
        packet_id="absorbed-plan-deferred-incomplete",
        status="pending",
        kind="plan_patch_review",
        requested_action="ingest_plan_intent",
        expires_at_utc="2999-01-01T00:00:00Z",
    ) | {
        "target_kind": "plan",
        "target_ref": "plan:MP-377",
        "lifecycle_current_state": "absorbed",
        "disposition": {"sink": "absorbed"},
        "absorption_receipt": {
            "contract_id": "PacketAbsorptionReceipt",
            "packet_id": "absorbed-plan-deferred-incomplete",
            "body_sha256": "abc123",
            "absorbed_by_actor": "codex",
            "absorbed_by_role": "reviewer",
            "absorbed_by_session_id": "session-1",
            "absorbed_at_utc": "2026-05-17T18:45:00Z",
            "source_semantic_ingestion_receipt_id": (
                "packet_semantic_ingestion:absorbed-plan-deferred-incomplete:test"
            ),
            "action_item_dispositions": ["deferred"],
            "resulting_decision": "plan_intent_deferred",
            "decision_rationale": "packet plan intent was parsed and deferred",
            "defer_reason": "missing target slice evidence must not clear pressure",
            "evidence_refs": ["packet:absorbed-plan-deferred-incomplete#body_observed"],
        },
    }

    live_packets = live_pending_packets([packet])

    assert [row["packet_id"] for row in live_packets] == [
        "absorbed-plan-deferred-incomplete"
    ]


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
    assert "expired_runtime_transport_hidden_from_inbox_total: 1" in markdown
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

    def _append_top_level_error_lines(lines: list[str], report: dict) -> None:
        return None

    class _BridgeSuccessReportRequest:
        pass

    def _build_bridge_success_report(*args, **kwargs) -> dict:
        return {}

    def _render_bridge_md(report: dict) -> str:
        return ""

    stub.append_common_report_sections = _append_common_report_sections
    stub.append_top_level_error_lines = _append_top_level_error_lines
    stub.BridgeSuccessReportRequest = _BridgeSuccessReportRequest
    stub.build_bridge_success_report = _build_bridge_success_report
    stub.render_bridge_md = _render_bridge_md
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
        assert (
            "expired runtime transport packets are archived audit rows "
            "whose TTL elapsed"
        ) in markdown
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
                kind="system_notice",
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

    assert reconciliation.live_pending_total == 7
    assert reconciliation.stale_pending_total == 1
    assert reconciliation.history_total == 1
    assert reconciliation.history_shown_total == 1
    assert reconciliation.history_truncated is False
    assert reconciliation.pending_total_matches_queue is False
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
