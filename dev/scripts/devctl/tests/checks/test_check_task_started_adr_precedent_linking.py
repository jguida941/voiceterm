import json
from pathlib import Path

from dev.scripts.checks.check_task_started_adr_precedent_linking import (
    evaluate_task_started_adr_precedent_linking,
)


def _write_events(tmp_path: Path, events: list[dict]) -> Path:
    path = tmp_path / "dev/reports/review_channel/events/trace.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(event, sort_keys=True) for event in events)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")
    return path


def _task_started(
    packet_id: str,
    *,
    event_type: str = "packet_posted",
    plan_id: str = "MP-378",
    summary: str = "TASK_STARTED MP-378 guard work",
    body: str = "",
    evidence_refs: list[str] | None = None,
    anchor_refs: list[str] | None = None,
    from_agent: str = "codex",
) -> dict:
    return {
        "event_type": event_type,
        "from_agent": from_agent,
        "kind": "task_started",
        "packet_id": packet_id,
        "plan_id": plan_id,
        "summary": summary,
        "body": body,
        "evidence_refs": evidence_refs or [],
        "anchor_refs": anchor_refs or [],
        "guidance_refs": [],
    }


def test_precedent_linked_task_started_accepts_evidence_anchor_and_adr_block(
    tmp_path: Path,
) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_5001",
                body=(
                    "precedent_packet_ids:\n"
                    "- rev_pkt_4017\n"
                    "status: extends rev_pkt_4017\n"
                    "adoption_rationale: carry the guard mandate forward."
                ),
                evidence_refs=["packet:rev_pkt_4017"],
                anchor_refs=["packet:rev_pkt_4017", "plan:MP-378-GUARD-P7"],
            )
        ],
    )

    report = evaluate_task_started_adr_precedent_linking(
        repo_root=tmp_path,
        event_log_path=event_path,
    )

    assert report.ok is True
    assert report.would_fail is False
    assert report.precedent_linked_count == 1
    assert report.violation_count == 0


def test_body_observed_precedent_without_evidence_reports_missing_links(
    tmp_path: Path,
) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_4018",
                plan_id="MP-377",
                summary="MP-378 guard charter started",
                body="Body-observed rev_pkt_4017. Building Guard P1.",
                evidence_refs=[],
                anchor_refs=["packet:rev_pkt_4017"],
            )
        ],
    )

    report = evaluate_task_started_adr_precedent_linking(
        repo_root=tmp_path,
        event_log_path=event_path,
    )

    assert report.ok is True
    assert report.report_only is True
    assert report.would_fail is True
    assert report.violation_count == 1
    violation = report.violations[0]
    assert violation["packet_id"] == "rev_pkt_4018"
    assert violation["expected_plan_family"] == "MP-378"
    assert violation["missing"] == [
        "evidence_refs.packet",
        "anchor_refs.plan_or_section",
        "adr_precedent_block",
        "plan_id_matches_work_family",
    ]


def test_unlinked_task_started_packet_is_not_precedent_scoped(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_5001",
                body="Starting a local maintenance slice.",
                anchor_refs=["plan:MP-378-MAINTENANCE"],
            )
        ],
    )

    report = evaluate_task_started_adr_precedent_linking(
        repo_root=tmp_path,
        event_log_path=event_path,
    )

    assert report.precedent_linked_count == 0
    assert report.violation_count == 0


def test_latest_transition_event_replaces_initial_post_shape(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_5001",
                plan_id="MP-377",
                body="Body-observed rev_pkt_4017.",
            ),
            _task_started(
                "rev_pkt_5001",
                event_type="packet_applied",
                plan_id="MP-378",
                body=(
                    "precedent_packet_ids:\n"
                    "- rev_pkt_4017\n"
                    "status: refines rev_pkt_4017\n"
                    "adoption_rationale: applied event carries full evidence."
                ),
                evidence_refs=["packet:rev_pkt_4017"],
                anchor_refs=["packet:rev_pkt_4017", "section:MP-378"],
            ),
        ],
    )

    report = evaluate_task_started_adr_precedent_linking(
        repo_root=tmp_path,
        event_log_path=event_path,
    )

    assert report.task_started_count == 1
    assert report.precedent_linked_count == 1
    assert report.violation_count == 0
