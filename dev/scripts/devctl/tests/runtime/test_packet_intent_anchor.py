"""Focused tests for packet-derived plan intent continuity."""

from dev.scripts.devctl.runtime.packet_intent_anchor import (
    packet_intent_anchors_from_packets,
    plan_iteration_session_from_anchors,
)


def test_pending_plan_packet_projects_non_authoritative_anchor() -> None:
    anchors = packet_intent_anchors_from_packets(
        (
            {
                "packet_id": "rev_pkt_2196",
                "kind": "plan_patch_review",
                "status": "pending",
                "from_agent": "claude",
                "target_kind": "plan",
                "target_ref": "plan://MP-377",
                "anchor_refs": ["checklist:MP377-P1-T06"],
                "evidence_refs": ["guard:plan-review"],
                "context_pack_refs": [
                    {
                        "pack_kind": "roadmap",
                        "pack_ref": "packet://rev_pkt_2200",
                    }
                ],
                "semantic_zref": "packet:rev_pkt_2196",
                "source_identity": {"head_sha": "abc123"},
                "summary": "mode vocabulary collapse",
            },
        )
    )

    assert len(anchors) == 1
    assert anchors[0].lifecycle_state == "plan_anchor_pending"
    assert anchors[0].target_plan == "plan://MP-377"
    assert anchors[0].evidence == ("packet:rev_pkt_2196", "guard:plan-review")
    assert anchors[0].semantic_zref == "packet:rev_pkt_2196"
    assert anchors[0].source_identity["head_sha"] == "abc123"
    assert anchors[0].context_pack_refs[0]["pack_kind"] == "roadmap"

    iteration = plan_iteration_session_from_anchors(anchors)
    assert iteration.status == "plan_anchor_pending"
    assert iteration.packet_ids == ("rev_pkt_2196",)


def test_applied_plan_packet_is_the_only_applied_anchor_state() -> None:
    anchors = packet_intent_anchors_from_packets(
        (
            {
                "packet_id": "rev_pkt_applied",
                "kind": "plan_ready_gate",
                "status": "applied",
                "applied_at_utc": "2026-04-29T12:00:00Z",
                "target_ref": "plan://MP-377",
                "anchor_refs": ["checklist:MP377-P0-T16"],
            },
        )
    )

    assert anchors[0].lifecycle_state == "applied"
    assert plan_iteration_session_from_anchors(anchors).status == "applied"
