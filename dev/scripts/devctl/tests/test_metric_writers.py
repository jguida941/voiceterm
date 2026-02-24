"""Tests for devctl.metric_writers JSONL append helpers."""

import json
import tempfile
from pathlib import Path
from unittest import mock


def test_append_metric_creates_file():
    """Write to a temp dir, verify the JSONL line parses with correct source/ts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "metrics"
        with mock.patch("devctl.metric_writers.METRICS_DIR", metrics_dir):
            from devctl.metric_writers import append_metric

            append_metric("status", {"branch": "develop", "commit_count": 42})
            path = metrics_dir / "status.jsonl"
            assert path.exists()
            with path.open() as f:
                line = f.readline()
            record = json.loads(line)
            assert record["source"] == "status"
            assert "ts" in record
            assert record["branch"] == "develop"
            assert record["commit_count"] == 42


def test_append_failure_kb_creates_file():
    """Write an issue to the failure KB, verify JSONL contains all fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = Path(tmpdir) / "failure_kb.jsonl"
        with mock.patch("devctl.metric_writers.FAILURE_KB", kb_path):
            from devctl.metric_writers import append_failure_kb

            issue = {
                "category": "test",
                "severity": "high",
                "owner": "platform",
                "source": "devctl.triage",
                "summary": "unit test failed",
            }
            append_failure_kb(issue)
            assert kb_path.exists()
            with kb_path.open() as f:
                line = f.readline()
            record = json.loads(line)
            assert "ts" in record
            assert "fingerprint" in record
            assert record["category"] == "test"
            assert record["severity"] == "high"
            assert record["owner"] == "platform"
            assert record["source"] == "devctl.triage"
            assert record["summary"] == "unit test failed"


def test_failure_kb_fingerprint_is_deterministic_for_same_issue():
    """Repeated writes of equivalent issues should produce the same fingerprint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = Path(tmpdir) / "failure_kb.jsonl"
        with mock.patch("devctl.metric_writers.FAILURE_KB", kb_path):
            from devctl.metric_writers import append_failure_kb

            issue_a = {
                "category": "security",
                "severity": "high",
                "owner": "security",
                "source": "devctl.triage",
                "summary": "unsafe interpolation in shell command",
            }
            issue_b = dict(issue_a)
            append_failure_kb(issue_a)
            append_failure_kb(issue_b)

            with kb_path.open() as handle:
                first = json.loads(handle.readline())
                second = json.loads(handle.readline())
            assert first["fingerprint"] == second["fingerprint"]


def test_append_metric_multiple():
    """Write 3 records, verify 3 lines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "metrics"
        with mock.patch("devctl.metric_writers.METRICS_DIR", metrics_dir):
            from devctl.metric_writers import append_metric

            for i in range(3):
                append_metric("report", {"index": i})
            path = metrics_dir / "report.jsonl"
            with path.open() as f:
                lines = f.readlines()
            assert len(lines) == 3
            for i, line in enumerate(lines):
                record = json.loads(line)
                assert record["source"] == "report"
                assert record["index"] == i


def test_append_metric_string_record():
    """Verify a string record is wrapped in a text field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "metrics"
        with mock.patch("devctl.metric_writers.METRICS_DIR", metrics_dir):
            from devctl.metric_writers import append_metric

            append_metric("status", "# Status Report\n\nAll good.")
            path = metrics_dir / "status.jsonl"
            with path.open() as f:
                record = json.loads(f.readline())
            assert record["source"] == "status"
            assert "text" in record
