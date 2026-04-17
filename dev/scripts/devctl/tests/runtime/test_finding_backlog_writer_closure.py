"""Regression coverage for the canonical FindingBacklog writer closure.

The writer must round-trip the appended row into a typed FindingRecord so
callers can verify the write reached the same consumer-side projection that
load_finding_backlog() produces. Without the typed closure, a writer failure
can silently produce a JSONL line that never re-projects into the backlog.
"""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.governance_review_models import GovernanceReviewInput
from dev.scripts.devctl.runtime.finding_backlog import (
    FindingBacklog,
    FindingBacklogWriteResult,
    load_finding_backlog_from_log,
    record_finding_backlog_row,
)
from dev.scripts.devctl.runtime.finding_contracts import (
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingRecord,
)


def _review_input() -> GovernanceReviewInput:
    return GovernanceReviewInput(
        signal_type="audit",
        check_id="writer_closure_regression",
        verdict="confirmed_issue",
        file_path="dev/scripts/devctl/runtime/finding_backlog.py",
        line=199,
        severity="high",
        repo_name="demo-repo",
        repo_path="",
        finding_class="contract_mismatch",
        recurrence_risk="recurring",
        prevention_surface="guard",
        notes="regression probe",
    )


def test_record_finding_backlog_row_returns_typed_write_result(tmp_path: Path) -> None:
    log_path = tmp_path / "finding_reviews.jsonl"

    result = record_finding_backlog_row(
        review_input=_review_input(),
        repo_root=tmp_path,
        governance=None,
        log_path=log_path,
    )

    assert isinstance(result, FindingBacklogWriteResult)
    assert result.log_path == str(log_path)
    assert isinstance(result.finding, FindingRecord)
    assert result.finding.contract_id == FINDING_CONTRACT_ID
    assert result.finding.schema_version == FINDING_SCHEMA_VERSION
    assert result.finding.check_id == "writer_closure_regression"
    assert result.finding.file_path == (
        "dev/scripts/devctl/runtime/finding_backlog.py"
    )
    assert result.finding.severity == "high"
    assert result.finding.ai_instruction == "regression probe"


def test_record_finding_backlog_row_projects_same_record_reader_sees(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "finding_reviews.jsonl"

    write_result = record_finding_backlog_row(
        review_input=_review_input(),
        repo_root=tmp_path,
        governance=None,
        log_path=log_path,
    )

    backlog = load_finding_backlog_from_log(
        log_path=log_path,
        repo_name=tmp_path.name,
        repo_path=str(tmp_path),
    )

    assert write_result.finding is not None
    writer_finding_id = write_result.finding.finding_id
    reader_ids = {finding.finding_id for finding in backlog.open_findings}
    assert writer_finding_id in reader_ids, (
        "Writer closure must project the same finding_id the reader observes "
        "so callers can verify the append landed in the canonical backlog."
    )


def test_record_finding_backlog_row_result_exposes_raw_row(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "finding_reviews.jsonl"

    result = record_finding_backlog_row(
        review_input=_review_input(),
        repo_root=tmp_path,
        governance=None,
        log_path=log_path,
    )

    assert result.row["check_id"] == "writer_closure_regression"
    assert result.row["verdict"] == "confirmed_issue"
    assert "finding_id" in result.row


def test_finding_backlog_to_dict_includes_contract_metadata(tmp_path: Path) -> None:
    backlog = FindingBacklog.from_rows(
        rows=[],
        log_path=tmp_path / "finding_reviews.jsonl",
        repo_name="demo-repo",
        repo_path=str(tmp_path),
    )

    payload = backlog.to_dict()

    assert payload["schema_version"] == 1
    assert payload["contract_id"] == "FindingBacklog"
