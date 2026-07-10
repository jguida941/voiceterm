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


def _write_guard_policy(
    tmp_path: Path,
    *,
    prefixes: list[str],
    valid_packet_dispositions: list[str] | None = None,
) -> Path:
    mandate = {
        "mandate_packet_id": "rev_pkt_4136",
        "observed_at_utc": "2026-05-15T21:59:46Z",
        "enforced_row_prefixes": prefixes,
    }
    if valid_packet_dispositions is not None:
        mandate["valid_packet_dispositions"] = valid_packet_dispositions
    path = tmp_path / "dev/config/devctl_repo_policy.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "repo_governance": {
                    "guard_mandates": {
                        "check_commit_message_row_id_resolves": mandate
                    }
                }
            },
            sort_keys=True,
        ),
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


def test_packet_decomposition_not_skipped_for_unenforced_row_prefix(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [_row("PKT-BIND-REV-PKT-4134", mutation_op="review_only")],
    )
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P220-"])

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P219-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n"
        ),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "packet_only_pkt_bind_rows"


def test_packet_decomposition_ignores_plan_rows_outside_policy_prefixes(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row("PKT-BIND-REV-PKT-4134", mutation_op="review_only"),
            _row("MP-NEW-P999-UNSCOPED-S1", mutation_op="ingest_plan_intent"),
        ],
    )
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P220-"])

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P220-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n"
        ),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "packet_only_pkt_bind_rows"


def test_packet_decomposition_accepts_policy_prefix_plan_rows(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row("PKT-BIND-REV-PKT-4134", mutation_op="review_only"),
            _row("MP-NEW-P207-S5-FPR-V2-CONTRACTREF-S1", mutation_op="ingest_plan_intent"),
        ],
    )
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P207-"])

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P207-S5-FPR-V2-CONTRACTREF-S1: work\n\nPacket: rev_pkt_4134\n\x1e\n"
        ),
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_packet_decomposition_accepts_policy_valid_terminal_disposition(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row("PKT-BIND-REV-PKT-4134", mutation_op="review_only"),
            _row("MP-NEW-P220-DECIDED-NO-OP-S1", mutation_op="decided_no_op"),
        ],
    )
    _write_guard_policy(
        tmp_path,
        prefixes=["MP-NEW-P220-"],
        valid_packet_dispositions=[
            "ingest_plan_intent",
            "decided_no_op",
            "superseded",
            "rejected_with_evidence",
        ],
    )

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P220-DECIDED-NO-OP-S1: decide no-op\n\nPacket: rev_pkt_4134\n\x1e\n"
        ),
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_packet_decomposition_rejects_terminal_disposition_without_policy(
    tmp_path: Path,
) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row("PKT-BIND-REV-PKT-4134", mutation_op="review_only"),
            _row("MP-NEW-P220-DECIDED-NO-OP-S1", mutation_op="decided_no_op"),
        ],
    )
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P220-"])

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P220-DECIDED-NO-OP-S1: decide no-op\n\nPacket: rev_pkt_4134\n\x1e\n"
        ),
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
