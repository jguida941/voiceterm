"""Regression coverage for readable review-channel packet projections."""

from __future__ import annotations

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.review_channel.readable_packet_projection import (
    HISTORY_OPERATIONAL_SUMMARY_SENTINEL,
    build_operational_summary_view,
    render_operational_summary_view,
)


def _packet(
    packet_id: str,
    *,
    kind: str,
    status: str = "pending",
    from_agent: str = "codex",
    to_agent: str = "operator",
    target_ref: str = "",
    requested_action: str = "review_only",
    summary: str = "Packet summary",
    expires_at_utc: str = "2999-01-01T00:00:00Z",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": kind,
        "status": status,
        "summary": summary,
        "requested_action": requested_action,
        "target_ref": target_ref,
        "posted_at": "2026-05-13T00:00:00Z",
        "expires_at_utc": expires_at_utc,
    }


def test_operational_summary_groups_commit_pipeline_packets() -> None:
    view = build_operational_summary_view(
        {
            "packets": [
                _packet(
                    "rev_pkt_1",
                    kind="action_request",
                    target_ref="remote_commit_pipeline:pipeline-abc123",
                    requested_action="stage_commit_pipeline",
                    summary="Stage pipeline",
                ),
                _packet(
                    "rev_pkt_2",
                    kind="commit_approval",
                    target_ref="remote_commit_pipeline:pipeline-abc123",
                    requested_action="approve",
                    status="applied",
                    summary="Approval applied",
                ),
                _packet(
                    "rev_pkt_3",
                    kind="action_request",
                    requested_action="repair_reviewer_loop",
                    summary="Orphan action request",
                ),
                _packet(
                    "rev_pkt_4",
                    kind="finding",
                    summary="Active claim",
                ),
                _packet(
                    "rev_pkt_5",
                    kind="action_request",
                    requested_action="commit",
                    expires_at_utc="2000-01-01T00:00:00Z",
                    summary="Expired request",
                ),
            ],
        },
        sample_limit=10,
        generated_at_utc="2026-05-13T00:10:00Z",
    )

    assert view["contract_id"] == "OperationalSummaryView"
    assert view["generated_at_utc"] == "2026-05-13T00:10:00Z"
    assert view["packet_freshness_stale_after_seconds"] == 3600
    assert view["packet_total"] == 5
    assert view["live_pending_total"] == 3
    assert view["stale_awaiting_reaper_total"] == 1
    assert view["stage_counts"] == {
        "applied": 1,
        "expired_without_disposition": 1,
        "pending": 3,
    }
    assert len(view["pipeline_transit"]) == 1
    pipeline = view["pipeline_transit"][0]
    assert pipeline["pipeline_id"] == "pipeline-abc123"
    assert pipeline["packet_total"] == 2
    assert pipeline["stage_counts"] == {"applied": 1, "pending": 1}
    assert [row["packet_id"] for row in view["orphan_action_requests"]] == [
        "rev_pkt_3",
        "rev_pkt_5",
    ]
    assert [row["packet_id"] for row in view["active_claims"]] == ["rev_pkt_4"]
    assert view["active_claims"][0]["packet_age_seconds"] == 600
    assert view["active_claims"][0]["packet_freshness_status"] == "fresh"


def test_operational_summary_markdown_names_readable_sections() -> None:
    view = build_operational_summary_view(
        {
            "packets": [
                _packet(
                    "rev_pkt_1",
                    kind="action_request",
                    target_ref="remote_commit_pipeline:pipeline-abc123",
                    requested_action="stage_commit_pipeline",
                ),
                _packet(
                    "rev_pkt_2",
                    kind="action_request",
                    requested_action="repair_reviewer_loop",
                    summary="Unpaired request",
                ),
            ],
        },
        generated_at_utc="2026-05-13T00:10:00Z",
    )

    rendered = "\n".join(render_operational_summary_view(view))

    assert "## Operational Summary View" in rendered
    assert "generated_at_utc: 2026-05-13T00:10:00Z" in rendered
    assert "### Pipeline Transit" in rendered
    assert "pipeline-abc123" in rendered
    assert "latest_age_seconds=600" in rendered
    assert "### Orphan Action Requests" in rendered
    assert "age_seconds=600" in rendered
    assert "Unpaired request" in rendered


def test_operational_summary_surfaces_guard_error_details() -> None:
    view = build_operational_summary_view(
        {
            "packets": [
                {
                    **_packet(
                        "rev_pkt_guard_failed",
                        kind="action_request",
                        target_ref="remote_commit_pipeline:pipeline-guard",
                        requested_action="stage_commit_pipeline",
                        status="failed",
                        summary="Pipeline guard failed",
                    ),
                    "disposition": {
                        "sink": "recovery_required",
                        "status": "failed",
                        "resolution_anchor": "packet:rev_pkt_guard_failed",
                        "guard_error_detail": {
                            "contract_id": "PacketGuardErrorDetail",
                            "failure_source": "action_request_lifecycle_event",
                            "reason": "guard_failed",
                            "full_guard_bundle_evidence": (
                                "failure_envelope:commit_failed,guard_failed"
                            ),
                        },
                    },
                }
            ],
        },
        generated_at_utc="2026-05-13T00:10:00Z",
    )

    pipeline = view["pipeline_transit"][0]
    assert pipeline["guard_error_total"] == 1
    assert pipeline["latest_guard_error_reason"] == "guard_failed"

    rendered = "\n".join(render_operational_summary_view(view))

    assert "guard_errors=1" in rendered
    assert "latest_guard_error=guard_failed" in rendered


def test_history_summary_flag_sets_operational_summary_sentinel() -> None:
    args = build_parser().parse_args(
        ["review-channel", "--action", "history", "--summary"]
    )

    assert args.summary == HISTORY_OPERATIONAL_SUMMARY_SENTINEL


def test_history_grouped_flag_is_available() -> None:
    args = build_parser().parse_args(
        ["review-channel", "--action", "history", "--grouped"]
    )

    assert args.grouped is True


def test_post_summary_text_still_parses_as_packet_summary() -> None:
    args = build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "post",
            "--from-agent",
            "codex",
            "--to-agent",
            "claude",
            "--kind",
            "finding",
            "--summary",
            "Readable packet projection landed",
            "--body",
            "body",
            "--evidence-ref",
            "test:readable-packet-projection",
        ]
    )

    assert args.summary == "Readable packet projection landed"
