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
    observed_at_utc: str = "2026-05-15T21:59:46Z",
) -> Path:
    path = tmp_path / "dev/config/devctl_repo_policy.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "repo_governance": {
                    "guard_mandates": {
                        "check_commit_message_row_id_resolves": {
                            "mandate_packet_id": "rev_pkt_4136",
                            "observed_at_utc": observed_at_utc,
                            "enforced_row_prefixes": prefixes,
                        }
                    }
                }
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _row(
    row_id: str,
    *,
    title: str = "Build guard",
    status: str = "queued",
    commit_anchor_ref: str = "",
) -> dict:
    return {
        "contract_id": "PlanRow",
        "schema_version": 1,
        "row_id": row_id,
        "title": title,
        "status": status,
        "sdlc_stage": "impl",
        "commit_anchor_ref": commit_anchor_ref,
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


def test_commit_subject_with_matching_row_id_passes(tmp_path: Path) -> None:
    _write_plan_index(
        tmp_path,
        [_row("MP-NEW-P220-PHASE-0B-EXPANDED-P40-S1", title="Build guard")],
    )

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: Build guard\n\x1e\n",
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_commit_subject_with_legacy_mp377_row_id_passes(tmp_path: Path) -> None:
    _write_plan_index(
        tmp_path,
        [_row("MP377-P0-T22AN-AB", title="Existing reducer-selected row")],
    )

    report = _evaluate(
        tmp_path,
        "abc1234\nMP377-P0-T22AN-AB: continue selected reducer row\n\x1e\n",
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_commit_subject_without_matching_row_fails(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: Build guard\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "missing_plan_row"


def test_policy_enforces_p207_s5_family(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P207-"])

    report = _evaluate(
        tmp_path,
        (
            "abc1234\x002026-05-15T22:40:00+00:00\n"
            "MP-NEW-P207-S5-FPR-V2-CONTRACTREF-S1: extend contract ref\n\x1e\n"
        ),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "missing_plan_row"
    assert report.enforced_row_prefixes == ("MP-NEW-P207-",)


def test_refresh_external_review_snapshot_is_allowlisted(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])

    report = _evaluate(
        tmp_path,
        "abc1234\nRefresh external review snapshot for 71579a7e\n\x1e\n",
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_applied_commit_requires_commit_anchor_ref_field(tmp_path: Path) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1",
                status="applied",
            )
        ],
    )

    report = _evaluate(
        tmp_path,
        "52f7c49f\nMP-NEW-P220-PHASE-0C-COMMIT-ANCHOR-REF-S1: apply field\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "applied_row_missing_commit_anchor_ref"


def test_commit_subject_with_corrupted_row_title_fails(tmp_path: Path) -> None:
    _write_plan_index(
        tmp_path,
        [
            _row(
                "MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1",
                title="MP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1..S5",
            )
        ],
    )

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P210-EXTEND-SYSTEM-PICTURE-S1: Extend graph\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "corrupted_title_persisted"


def test_report_echoes_scan_range_metadata(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])
    _write_guard_policy(tmp_path, prefixes=["MP-NEW-P220-"])

    report = _evaluate(
        tmp_path,
        (
            "newsha\x002026-05-15T22:40:00+00:00\n"
            "docs: no row\n\x1e\n"
            "oldsha\x002026-05-15T22:39:00+00:00\n"
            "docs: no row\n\x1e\n"
        ),
    )

    assert report.head_ref == "newsha"
    assert report.newest_scanned_commit == "newsha"
    assert report.since_ref == "oldsha"
    assert report.oldest_scanned_commit == "oldsha"
    assert report.range_mode == "max_count"
    assert report.max_count == 200
    assert report.observed_at_utc == "2026-05-15T21:59:46Z"
