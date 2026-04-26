"""Tests for the platform finding-ingest seam."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.runtime.dogfood_log import build_dogfood_record
from dev.scripts.devctl.runtime.dogfood_models import DogfoodRecordInput
from dev.scripts.devctl.runtime.platform_finding_ingest import (
    AUTO_INGEST_ENV,
    DogfoodFindingIngestOptions,
    PlatformFindingIngest,
    PlatformFindingIngestResult,
    maybe_auto_ingest_devctl_result,
)


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


def test_auto_ingest_skips_until_enabled() -> None:
    result = maybe_auto_ingest_devctl_result(
        command="push",
        returncode=1,
        argv=["push", "--format", "json"],
        read_only=False,
    )

    assert result.status == "skipped"
    assert result.reason == "auto_record_not_enabled"


def test_auto_ingest_records_failed_command_when_enabled(tmp_path: Path) -> None:
    recorded = PlatformFindingIngestResult(
        status="recorded",
        reason="finding_recorded",
        log_path=str(tmp_path / "finding_reviews.jsonl"),
    )
    with (
        patch.dict("os.environ", {AUTO_INGEST_ENV: "1"}, clear=False),
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
