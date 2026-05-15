import json
from pathlib import Path


def _write_plan_index(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "dev/state/plan_index.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def _row(row_id: str, *, mutation_op: str, packet_id: str = "rev_pkt_4134") -> dict:
    return {
        "contract_id": "PlanRow",
        "schema_version": 1,
        "row_id": row_id,
        "title": row_id,
        "status": "queued",
        "sdlc_stage": "spec",
        "mutation_op": mutation_op,
        "sourced_from_packets": [packet_id],
        "anchor_refs": [f"packet:{packet_id}"],
        "provenance": {
            "contract_id": "IngestionProvenance",
            "schema_version": 1,
            "observed_at_utc": "2026-05-15T21:14:21Z",
        },
    }


def _evaluate(tmp_path: Path, log_text: str):
    from dev.scripts.checks.check_commit_message_row_id_resolves import (
        evaluate_commit_message_row_id_resolves,
    )

    return evaluate_commit_message_row_id_resolves(
        repo_root=tmp_path,
        log_text=log_text,
        plan_index_path=tmp_path / "dev/state/plan_index.jsonl",
    )


def test_commit_referencing_packet_with_zero_plan_rows_fails(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "packet_without_plan_rows"


def test_commit_with_only_pkt_bind_row_fails(tmp_path: Path) -> None:
    _write_plan_index(
        tmp_path,
        [_row("PKT-BIND-REV-PKT-4134", mutation_op="review_only")],
    )

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "packet_only_pkt_bind_rows"


def test_commit_with_mp_new_row_having_ingest_plan_intent_passes(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1",
                mutation_op="ingest_plan_intent",
            )
        ],
    )

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n",
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_commit_without_rev_pkt_ref_is_skipped(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])

    report = _evaluate(
        tmp_path,
        "abc1234\nchore: update docs only\n\x1e\n",
    )

    assert report.ok is True
    assert report.violation_count == 0
