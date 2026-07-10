"""Tests for ``runtime.artifact_receipt_ledger.record_artifact_receipt``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.artifact_receipt_ledger import (
    ALLOWED_DELIVERIES,
    DEFAULT_ARTIFACT_RECEIPT_STORE_REL,
    record_artifact_receipt,
)


def _valid_metrics() -> dict[str, object]:
    return {
        "command": "system-map",
        "delivery": "stdout",
        "format": "json",
        "path": None,
        "size_bytes": 1024,
        "estimated_tokens": 256,
        "token_estimator": "bytes_div_4",
        "sha256": "a" * 64,
    }


def _read_rows(repo_root: Path) -> list[dict[str, object]]:
    store_path = repo_root / DEFAULT_ARTIFACT_RECEIPT_STORE_REL
    if not store_path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def test_record_rejects_missing_command(tmp_path: Path) -> None:
    metrics = _valid_metrics()
    with pytest.raises(ValueError):
        record_artifact_receipt(
            metrics,
            command="   ",
            argv=[],
            ok=True,
            summary=None,
            repo_root=tmp_path,
        )
    assert _read_rows(tmp_path) == []


def test_record_rejects_non_mapping_metrics(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        record_artifact_receipt(
            None,  # type: ignore[arg-type]
            command="system-map",
            argv=[],
            ok=True,
            summary=None,
            repo_root=tmp_path,
        )
    with pytest.raises(TypeError):
        record_artifact_receipt(
            ["not", "a", "mapping"],  # type: ignore[arg-type]
            command="system-map",
            argv=[],
            ok=True,
            summary=None,
            repo_root=tmp_path,
        )
    assert _read_rows(tmp_path) == []


def test_record_drops_unknown_delivery_value(tmp_path: Path) -> None:
    metrics = _valid_metrics()
    metrics["delivery"] = "ftp"
    with pytest.raises(ValueError):
        record_artifact_receipt(
            metrics,
            command="system-map",
            argv=[],
            ok=True,
            summary=None,
            repo_root=tmp_path,
        )
    assert _read_rows(tmp_path) == []
    # Sanity: spec invariant — only `file` and `stdout` deliveries persist.
    assert ALLOWED_DELIVERIES == frozenset({"file", "stdout"})


def test_record_does_not_persist_summary_values(tmp_path: Path) -> None:
    metrics = _valid_metrics()
    secret_summary = {"secret": "abc", "other_key": "do-not-leak"}
    result = record_artifact_receipt(
        metrics,
        command="system-map",
        argv=["--slice-id", "MP-SLICE", "--actor", "claude"],
        ok=True,
        summary=secret_summary,
        repo_root=tmp_path,
    )
    assert result.record_count == 1
    rows = _read_rows(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["summary_keys"] == ["other_key", "secret"]
    # PII safety: raw summary values MUST NOT appear anywhere in the row.
    raw = json.dumps(row)
    assert "abc" not in raw
    assert "do-not-leak" not in raw


def test_record_happy_path(tmp_path: Path) -> None:
    metrics = _valid_metrics()
    metrics.update(
        {
            "delivery": "file",
            "path": "dev/state/x.json",
            "size_bytes": 4096,
            "estimated_tokens": 1024,
        }
    )
    result = record_artifact_receipt(
        metrics,
        command="develop",
        argv=["develop", "next", "--slice-id=MP-S1A", "--actor", "claude"],
        ok=True,
        summary=None,
        repo_root=tmp_path,
        now_utc=lambda: "2026-05-17T00:00:00Z",
    )
    assert result.record_count == 1
    rows = _read_rows(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["command"] == "develop"
    assert row["ok"] is True
    assert row["delivery"] == "file"
    assert row["artifact_format"] == "json"
    assert row["artifact_path"] == "dev/state/x.json"
    assert row["size_bytes"] == 4096
    assert row["estimated_tokens"] == 1024
    assert row["artifact_sha256"] == "a" * 64
    assert row["summary_keys"] == []
    assert row["slice_id"] == "MP-S1A"
    assert row["actor"] == "claude"
    assert row["recorded_at_utc"] == "2026-05-17T00:00:00Z"
    assert row["schema_version"] == 1
    assert row["contract_id"] == "ArtifactReceiptRecord"
    assert isinstance(row["receipt_id"], str)
    assert row["receipt_id"].startswith("art_")
