"""Tests for audit metrics analysis helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.audits import audit_metrics


class AuditMetricsLoadTests(unittest.TestCase):
    def test_load_events_skips_invalid_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "events.jsonl"
            input_path.write_text(
                "\n".join(
                    [
                        '{"timestamp":"2026-02-24T00:00:00Z","area":"governance","step":"a","actor":"script","automated":true,"success":true}',
                        "not json",
                        '["array-not-object"]',
                    ]
                ),
                encoding="utf-8",
            )
            events, warnings = audit_metrics._load_events(input_path)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].source_bucket, "script_only")
        self.assertEqual(len(warnings), 2)


class AuditMetricsSummaryTests(unittest.TestCase):
    def test_summary_computes_key_percentages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "events.jsonl"
            rows = [
                {
                    "timestamp": "2026-02-24T09:00:00Z",
                    "area": "governance",
                    "step": "check_active_plan_sync",
                    "execution_source": "script_only",
                    "automated": True,
                    "success": True,
                    "duration_seconds": 2.0,
                    "retries": 0,
                },
                {
                    "timestamp": "2026-02-24T09:01:00Z",
                    "area": "loops",
                    "step": "triage-loop",
                    "execution_source": "ai_assisted",
                    "automated": True,
                    "success": True,
                    "duration_seconds": 20.0,
                    "retries": 1,
                },
                {
                    "timestamp": "2026-02-24T09:02:00Z",
                    "area": "manual-physical",
                    "step": "iphone-validation",
                    "execution_source": "human_manual",
                    "automated": False,
                    "success": False,
                    "duration_seconds": 45.0,
                    "retries": 0,
                    "manual_reason": "mobile_adapter_not_available",
                    "repeated_workaround": True,
                },
            ]
            input_path.write_text(
                "\n".join(json.dumps(row) for row in rows),
                encoding="utf-8",
            )
            events, _warnings = audit_metrics._load_events(input_path)

        summary = audit_metrics._summarize(events)

        self.assertEqual(summary["total_events"], 3)
        self.assertEqual(summary["automation_coverage_pct"], 66.67)
        self.assertEqual(summary["script_only_pct"], 33.33)
        self.assertEqual(summary["ai_assisted_pct"], 33.33)
        self.assertEqual(summary["human_manual_pct"], 33.33)
        self.assertEqual(summary["success_rate_pct"], 66.67)
        self.assertEqual(summary["repeated_workaround_pct"], 33.33)
        self.assertEqual(summary["retry_total"], 1)
        self.assertEqual(summary["manual_reasons"], {"mobile_adapter_not_available": 1})


if __name__ == "__main__":
    unittest.main()
