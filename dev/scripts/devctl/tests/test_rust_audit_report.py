"""Tests for Rust audit aggregation and markdown rendering."""

from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import patch

from dev.scripts.devctl import rust_audit_report


def _completed(payload: dict, *, returncode: int = 1) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["python3"],
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr="",
    )


class RustAuditReportTests(unittest.TestCase):
    def test_collect_rust_audit_report_aggregates_categories_and_hotspots(self) -> None:
        best_practices = {
            "ok": False,
            "files_changed": 20,
            "files_considered": 20,
            "totals": {
                "allow_without_reason_growth": 0,
                "undocumented_unsafe_blocks_growth": 0,
                "pub_unsafe_fn_missing_safety_docs_growth": 0,
                "unsafe_impl_missing_safety_comment_growth": 0,
                "mem_forget_calls_growth": 0,
                "result_string_types_growth": 2,
                "expect_on_join_recv_growth": 0,
                "unwrap_on_join_recv_growth": 0,
                "dropped_send_results_growth": 3,
                "env_mutation_calls_growth": 0,
            },
            "violations": [
                {
                    "path": "rust/src/bin/voiceterm/dev_command/broker/mod.rs",
                    "growth": {
                        "result_string_types": 2,
                        "dropped_send_results": 3,
                    },
                }
            ],
        }
        lint_debt = {
            "ok": False,
            "files_changed": 20,
            "files_considered": 20,
            "dead_code_instance_count": 4,
            "dead_code_without_reason_count": 1,
            "totals": {
                "allow_attrs_growth": 0,
                "dead_code_allow_attrs_growth": 1,
                "unwrap_expect_calls_growth": 2,
                "unchecked_unwrap_expect_calls_growth": 0,
                "panic_macro_calls_growth": 0,
            },
            "violations": [
                {
                    "path": "rust/src/bin/voiceterm/dev_panel/review_surface.rs",
                    "growth": {"unwrap_expect_calls": 2},
                }
            ],
        }
        runtime_panic = {
            "ok": True,
            "files_changed": 20,
            "files_considered": 20,
            "totals": {"unallowlisted_panic_calls_growth": 0},
            "violations": [],
        }
        with patch(
            "dev.scripts.devctl.rust_audit_report.subprocess.run",
            side_effect=[
                _completed(best_practices),
                _completed(lint_debt),
                _completed(runtime_panic, returncode=0),
            ],
        ):
            report = rust_audit_report.collect_rust_audit_report(mode="absolute")

        self.assertTrue(report["collection_ok"])
        self.assertEqual(report["summary"]["total_violation_files"], 2)
        self.assertEqual(report["summary"]["total_active_findings"], 8)
        self.assertEqual(report["summary"]["dead_code_without_reason_count"], 1)
        self.assertEqual(report["categories"][0]["category"], "dropped_send_results")
        self.assertEqual(
            report["hotspots"][0]["path"],
            "rust/src/bin/voiceterm/dev_command/broker/mod.rs",
        )

    def test_render_rust_audit_markdown_includes_reason_and_fix(self) -> None:
        lines = rust_audit_report.render_rust_audit_markdown(
            {
                "mode": "absolute",
                "ok": False,
                "summary": {
                    "total_violation_files": 1,
                    "total_active_findings": 3,
                    "active_categories": 1,
                    "dead_code_without_reason_count": 0,
                },
                "guards": [
                    {
                        "guard": "best_practices",
                        "ok": False,
                        "files_considered": 10,
                        "violations": 1,
                    }
                ],
                "categories": [
                    {
                        "label": "dropped send results",
                        "count": 3,
                        "severity": "high",
                        "why": "Ignoring send results can silently lose signals.",
                        "fix": "Handle `send` failure explicitly.",
                    }
                ],
                "hotspots": [
                    {
                        "path": "rust/src/bin/voiceterm/dev_command/broker/mod.rs",
                        "score": 9,
                        "count": 3,
                        "signals": ["dropped send results"],
                    }
                ],
                "warnings": [],
                "errors": [],
                "charts": [],
            }
        )
        markdown = "\n".join(lines)
        self.assertIn("Why These Findings Matter", markdown)
        self.assertIn("Ignoring send results can silently lose signals.", markdown)
        self.assertIn("Handle `send` failure explicitly.", markdown)


if __name__ == "__main__":
    unittest.main()
