from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.operator_console.state.snapshots.ralph_guardrail_snapshot import (
    DEFAULT_RALPH_REPORT_REL,
    RalphGuardrailSnapshot,
    load_ralph_guardrail_snapshot,
)


def _make_valid_payload(**overrides: object) -> dict[str, object]:
    """Return a minimal valid Ralph report payload with optional overrides."""
    base: dict[str, object] = {
        "phase": "running",
        "attempt": 2,
        "max_attempts": 5,
        "total_findings": 12,
        "fixed_count": 7,
        "false_positive_count": 2,
        "pending_count": 3,
        "branch": "feature/guardrails",
        "approval_mode": "auto",
        "last_run_timestamp": "2026-03-09T12:00:00Z",
        "by_architecture": [
            {"name": "rust", "total": 8, "fixed": 5},
            {"name": "python", "total": 4, "fixed": 2},
        ],
        "by_severity": [
            {"name": "critical", "total": 3, "fixed": 3},
            {"name": "high", "total": 5, "fixed": 2},
            {"name": "medium", "total": 4, "fixed": 2},
        ],
    }
    base.update(overrides)
    return base


class RalphGuardrailSnapshotTests(unittest.TestCase):
    def test_load_returns_unavailable_when_report_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot = load_ralph_guardrail_snapshot(Path(tmp_dir))

        self.assertFalse(snapshot.available)
        self.assertEqual(snapshot.phase, "idle")
        self.assertIn("no Ralph report", snapshot.note or "")

    def test_load_returns_unavailable_for_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("{not valid json", encoding="utf-8")

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertFalse(snapshot.available)
        self.assertIn("JSON is invalid", snapshot.note or "")

    def test_load_returns_unavailable_for_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text('"just a string"', encoding="utf-8")

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertFalse(snapshot.available)
        self.assertIn("not a JSON object", snapshot.note or "")

    def test_load_returns_unavailable_when_repo_root_missing(self) -> None:
        snapshot = load_ralph_guardrail_snapshot(Path("/nonexistent/path"))

        self.assertFalse(snapshot.available)
        self.assertIn("repo root is unavailable", snapshot.note or "")

    def test_load_projects_valid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(_make_valid_payload()),
                encoding="utf-8",
            )

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.phase, "running")
        self.assertEqual(snapshot.attempt, 2)
        self.assertEqual(snapshot.max_attempts, 5)
        self.assertEqual(snapshot.total_findings, 12)
        self.assertEqual(snapshot.fixed_count, 7)
        self.assertEqual(snapshot.false_positive_count, 2)
        self.assertEqual(snapshot.pending_count, 3)
        self.assertAlmostEqual(snapshot.fix_rate_pct, 58.3, places=1)
        self.assertEqual(snapshot.branch, "feature/guardrails")
        self.assertEqual(snapshot.approval_mode, "auto")
        self.assertEqual(snapshot.last_run_timestamp, "2026-03-09T12:00:00Z")

    def test_load_projects_architecture_breakdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(_make_valid_payload()),
                encoding="utf-8",
            )

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertEqual(len(snapshot.by_architecture), 2)
        self.assertEqual(snapshot.by_architecture[0], ("rust", 8, 5))
        self.assertEqual(snapshot.by_architecture[1], ("python", 4, 2))

    def test_load_projects_severity_breakdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(_make_valid_payload()),
                encoding="utf-8",
            )

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertEqual(len(snapshot.by_severity), 3)
        self.assertEqual(snapshot.by_severity[0], ("critical", 3, 3))
        self.assertEqual(snapshot.by_severity[1], ("high", 5, 2))
        self.assertEqual(snapshot.by_severity[2], ("medium", 4, 2))

    def test_fix_rate_is_zero_when_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(_make_valid_payload(
                    total_findings=0,
                    fixed_count=0,
                    false_positive_count=0,
                    pending_count=0,
                )),
                encoding="utf-8",
            )

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.fix_rate_pct, 0.0)

    def test_missing_breakdown_fields_yield_empty_tuples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            report_path = repo_root / DEFAULT_RALPH_REPORT_REL
            report_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "phase": "idle",
                "total_findings": 0,
                "fixed_count": 0,
                "false_positive_count": 0,
                "pending_count": 0,
            }
            report_path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            snapshot = load_ralph_guardrail_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.by_architecture, ())
        self.assertEqual(snapshot.by_severity, ())

    def test_snapshot_is_frozen(self) -> None:
        snapshot = RalphGuardrailSnapshot(
            available=True,
            phase="idle",
            attempt=0,
            max_attempts=0,
            total_findings=0,
            fixed_count=0,
            false_positive_count=0,
            pending_count=0,
            fix_rate_pct=0.0,
            by_architecture=(),
            by_severity=(),
            last_run_timestamp=None,
            branch=None,
            approval_mode=None,
        )
        with self.assertRaises(AttributeError):
            snapshot.phase = "running"  # type: ignore[misc]
