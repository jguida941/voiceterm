"""Tests for the platform finding-ingest seam."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.governance.ledger_helpers import latest_rows_by_finding
from dev.scripts.devctl.governance_review.log import (
    read_governance_review_rows,
    resolve_governance_review_log_path,
)
from dev.scripts.devctl.runtime.dogfood_log import build_dogfood_record
from dev.scripts.devctl.runtime.dogfood_log import read_dogfood_rows
from dev.scripts.devctl.runtime.dogfood_log import resolve_dogfood_log_path
from dev.scripts.devctl.runtime.dogfood_models import DogfoodRecordInput
from dev.scripts.devctl.runtime.finding_backlog import load_finding_backlog
from dev.scripts.devctl.runtime.platform_finding_ingest import (
    AUTO_INGEST_DISABLE_ENV,
    AUTO_INGEST_ENV,
    DogfoodFindingIngestOptions,
    PlatformFindingIngest,
    PlatformFindingIngestResult,
    maybe_auto_ingest_devctl_result,
)
from dev.scripts.devctl.runtime.startup_signals import load_startup_quality_signals


def test_platform_finding_ingest_records_dogfood_through_backlog(tmp_path: Path) -> None:
    governance_log = tmp_path / "finding_reviews.jsonl"
    summary_root = tmp_path / "summary"
    promotion_queue = tmp_path / "promotion.jsonl"
    record = build_dogfood_record(
        record_input=DogfoodRecordInput(
            target_kind="command",
            target_id="review-channel",
            status="blocked",
            source_command=(
                "python3 dev/scripts/devctl.py review-channel --action status"
            ),
        ),
        repo_root=tmp_path,
    )

    result = PlatformFindingIngest(
        repo_root=tmp_path,
        governance_log_path=governance_log,
        governance_summary_root=summary_root,
        promotion_queue_path=promotion_queue,
    ).record_dogfood_result(
        record,
        options=DogfoodFindingIngestOptions(
            file_path="dev/scripts/devctl/commands/review_channel.py",
        ),
    )

    assert result.status == "recorded"
    assert result.row is not None
    assert result.row["signal_type"] == "dogfood"
    assert result.row["verdict"] == "confirmed_issue"
    assert result.finding is not None
    assert result.finding["contract_id"] == "Finding"
    assert (summary_root / "review_summary.json").is_file()
    rows = [
        json.loads(line)
        for line in governance_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1
    assert rows[0]["finding_id"] == result.row["finding_id"]


def test_auto_ingest_records_failed_command_by_default(tmp_path: Path) -> None:
    recorded = PlatformFindingIngestResult(
        status="recorded",
        reason="finding_recorded",
        log_path=str(tmp_path / "finding_reviews.jsonl"),
    )
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.object(
            PlatformFindingIngest,
            "record_dogfood_result",
            return_value=recorded,
        ) as record_mock,
    ):
        result = maybe_auto_ingest_devctl_result(
            command="push",
            returncode=1,
            argv=["push", "--format", "json"],
            read_only=False,
            repo_root=tmp_path,
        )

    assert result is recorded
    record_mock.assert_called_once()
    dogfood_record = record_mock.call_args.args[0]
    assert dogfood_record.target_kind == "command"
    assert dogfood_record.target_id == "push"
    assert dogfood_record.status == "failed"
    assert record_mock.call_args.kwargs["persist_run"] is True
    assert record_mock.call_args.kwargs["refresh_dogfood_summary"] is True


def test_auto_ingest_disable_env_is_report_only_opt_out(tmp_path: Path) -> None:
    with patch.dict("os.environ", {AUTO_INGEST_DISABLE_ENV: "1"}, clear=True):
        result = maybe_auto_ingest_devctl_result(
            command="push",
            returncode=1,
            argv=["push", "--format", "json"],
            read_only=False,
            repo_root=tmp_path,
        )

    assert result.status == "skipped"
    assert result.reason == "disabled_by_env"


def test_auto_ingest_false_auto_record_env_is_compat_opt_out(tmp_path: Path) -> None:
    with patch.dict("os.environ", {AUTO_INGEST_ENV: "0"}, clear=True):
        result = maybe_auto_ingest_devctl_result(
            command="push",
            returncode=1,
            argv=["push", "--format", "json"],
            read_only=False,
            repo_root=tmp_path,
        )

    assert result.status == "skipped"
    assert result.reason == "auto_record_disabled_by_env"


def test_auto_ingest_skips_read_only_even_when_enabled(tmp_path: Path) -> None:
    with patch.dict("os.environ", {AUTO_INGEST_ENV: "1"}, clear=False):
        result = maybe_auto_ingest_devctl_result(
            command="startup-context",
            returncode=1,
            argv=["startup-context", "--format", "json"],
            read_only=True,
            repo_root=tmp_path,
        )

    assert result.status == "skipped"
    assert result.reason == "read_only_command"


def test_auto_ingest_dedupes_backlog_and_updates_report_surfaces(
    tmp_path: Path,
) -> None:
    with (
        patch.dict("os.environ", {}, clear=True),
        patch(
            "dev.scripts.devctl.runtime.dogfood_governance."
            "resolve_dogfood_target_path",
            return_value="dev/scripts/devctl/commands/vcs/push.py",
        ),
    ):
        first = maybe_auto_ingest_devctl_result(
            command="push",
            returncode=1,
            argv=["push", "--format", "json"],
            read_only=False,
            repo_root=tmp_path,
        )
        second = maybe_auto_ingest_devctl_result(
            command="push",
            returncode=1,
            argv=["push", "--format", "json"],
            read_only=False,
            repo_root=tmp_path,
        )

    assert first.status == "recorded"
    assert second.status == "recorded"
    governance_rows = read_governance_review_rows(
        resolve_governance_review_log_path(repo_root=tmp_path),
        max_rows=100,
    )
    assert len(governance_rows) == 2
    assert len(latest_rows_by_finding(governance_rows)) == 1

    backlog = load_finding_backlog(
        repo_root=tmp_path,
        governance=None,
    )
    assert backlog.total_rows == 2
    assert backlog.total_findings == 1
    assert len(backlog.open_rows) == 1

    dogfood_rows = read_dogfood_rows(
        resolve_dogfood_log_path(repo_root=tmp_path),
        max_rows=100,
    )
    assert len(dogfood_rows) == 2
    assert all(row["governance_finding_ids"] for row in dogfood_rows)

    quality_signals = load_startup_quality_signals(tmp_path)
    assert quality_signals["finding_backlog"]["total_findings"] == 1
    assert quality_signals["finding_backlog"]["open_finding_count"] == 1
    assert quality_signals["governance_review"]["total_findings"] == 1
