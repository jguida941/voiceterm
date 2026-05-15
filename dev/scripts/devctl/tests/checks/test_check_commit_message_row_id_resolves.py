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


def test_commit_subject_without_matching_row_fails(tmp_path: Path) -> None:
    _write_plan_index(tmp_path, [])

    report = _evaluate(
        tmp_path,
        "abc1234\nMP-NEW-P220-PHASE-0B-EXPANDED-P40-S1: Build guard\n\x1e\n",
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "missing_plan_row"


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
