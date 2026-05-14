import json
from datetime import UTC, datetime
from pathlib import Path

from dev.scripts.checks.packet_pkt_bind_completeness import (
    evaluate_packet_pkt_bind_completeness,
)
from dev.scripts.checks.packet_pkt_bind_completeness.constants import (
    LIFECYCLE_PACKET_KINDS,
    TASK_PRODUCED_KIND,
    TASK_STARTED_KIND,
)


NOW = datetime(2026, 5, 14, 17, 0, tzinfo=UTC)


def _write_jsonl(tmp_path: Path, relative_path: str, rows: list[dict]) -> Path:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")
    return path


def _write_events(tmp_path: Path, events: list[dict]) -> Path:
    return _write_jsonl(
        tmp_path,
        "dev/reports/review_channel/events/trace.ndjson",
        events,
    )


def _write_plan_index(tmp_path: Path, rows: list[dict]) -> Path:
    return _write_jsonl(
        tmp_path,
        "dev/state/plan_index.jsonl",
        rows,
    )


def _task_started(
    packet_id: str,
    *,
    timestamp_utc: str = "2026-05-14T15:45:00Z",
    correlation_id: str = "corr-1",
    from_agent: str = "codex",
) -> dict:
    return {
        "event_type": "packet_posted",
        "from_agent": from_agent,
        "kind": "task_started",
        "packet_id": packet_id,
        "timestamp_utc": timestamp_utc,
        "summary": f"TASK_STARTED {packet_id}",
        "correlation_id": correlation_id,
        "target_ref": "plan:MP-378",
    }


def _task_produced(
    packet_id: str,
    *,
    timestamp_utc: str = "2026-05-14T15:50:00Z",
    correlation_id: str = "corr-1",
) -> dict:
    return {
        "event_type": "packet_posted",
        "from_agent": "codex",
        "kind": "task_produced",
        "packet_id": packet_id,
        "timestamp_utc": timestamp_utc,
        "summary": f"TASK_PRODUCED {packet_id}",
        "correlation_id": correlation_id,
        "target_ref": "plan:MP-378",
    }


def _binding_row(packet_id: str) -> dict:
    return {
        "contract_id": "PlanRow",
        "schema_version": 1,
        "row_id": "PKT-BIND-" + packet_id.upper().replace("_", "-"),
        "status": "applied",
        "mutation_op": "task_started_packet_binding",
        "sourced_from_packets": [packet_id],
        "anchor_refs": [f"packet:{packet_id}", "commit:abc1234"],
        "work_evidence_ids": [f"packet:{packet_id}"],
    }


def test_post_mandate_task_started_requires_pkt_bind_row(tmp_path: Path) -> None:
    event_path = _write_events(tmp_path, [_task_started("rev_pkt_5001")])
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1
    assert report["violations"][0]["packet_id"] == "rev_pkt_5001"
    assert report["violations"][0]["deadline_reason"] == "grace_minutes"


def test_pkt_bind_row_satisfies_post_mandate_task_started(tmp_path: Path) -> None:
    event_path = _write_events(tmp_path, [_task_started("rev_pkt_5001")])
    plan_path = _write_plan_index(tmp_path, [_binding_row("rev_pkt_5001")])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["bound_task_started_count"] == 1


def test_pre_mandate_gap_is_legacy_by_default(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_3999",
                timestamp_utc="2026-05-14T15:00:00Z",
            )
        ],
    )
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
    )

    assert report["ok"] is True
    assert report["legacy_gap_count"] == 1
    assert report["violation_count"] == 0


def test_strict_legacy_promotes_legacy_gap_to_violation(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_3999",
                timestamp_utc="2026-05-14T15:00:00Z",
            )
        ],
    )
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
        strict_legacy=True,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1


def test_recent_unbound_packet_is_pending_until_grace_expires(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_5001",
                timestamp_utc="2026-05-14T16:55:00Z",
            )
        ],
    )
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
    )

    assert report["ok"] is True
    assert report["pending_within_grace_count"] == 1
    assert report["violation_count"] == 0


def test_paired_task_produced_shortens_binding_deadline(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [
            _task_started(
                "rev_pkt_5001",
                timestamp_utc="2026-05-14T16:55:00Z",
                correlation_id="corr-close",
            ),
            _task_produced(
                "rev_pkt_5002",
                timestamp_utc="2026-05-14T16:56:00Z",
                correlation_id="corr-close",
            ),
        ],
    )
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
        grace_minutes=10,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1
    assert report["violations"][0]["deadline_reason"] == "paired_task_produced"


def test_non_codex_task_started_packets_are_ignored(tmp_path: Path) -> None:
    event_path = _write_events(
        tmp_path,
        [_task_started("rev_pkt_5001", from_agent="claude")],
    )
    plan_path = _write_plan_index(tmp_path, [])

    report = evaluate_packet_pkt_bind_completeness(
        repo_root=tmp_path,
        event_log_path=event_path,
        plan_index_path=plan_path,
        now_utc=NOW,
    )

    assert report["ok"] is True
    assert report["task_started_count"] == 0
    assert report["human_summary"]["blind_pass_warning"]


def test_task_packet_kinds_match_canonical_lifecycle_membership() -> None:
    assert TASK_STARTED_KIND in LIFECYCLE_PACKET_KINDS
    assert TASK_PRODUCED_KIND in LIFECYCLE_PACKET_KINDS
