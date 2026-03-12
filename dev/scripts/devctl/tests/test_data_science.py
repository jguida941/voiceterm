"""Tests for data-science telemetry snapshots and CLI integration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.data_science.metrics import run_data_science_snapshot
from dev.scripts.devctl.watchdog import load_watchdog_summary_artifact


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class DataScienceSnapshotTests(unittest.TestCase):
    def test_snapshot_generates_summary_and_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            event_log = root / "events.jsonl"
            event_log.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "command": "check",
                                "execution_source": "script_only",
                                "success": True,
                                "duration_seconds": 9.5,
                            }
                        ),
                        json.dumps(
                            {
                                "command": "autonomy-benchmark",
                                "execution_source": "ai_assisted",
                                "success": True,
                                "duration_seconds": 3.0,
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            swarm_root = root / "swarms"
            _write_json(
                swarm_root / "s1" / "summary.json",
                {
                    "ok": True,
                    "summary": {"selected_agents": 1},
                    "agents": [{"tasks_completed": 2}],
                },
            )
            _write_json(
                swarm_root / "s5" / "summary.json",
                {
                    "ok": True,
                    "summary": {"selected_agents": 5},
                    "agents": [{"tasks_completed": 20}],
                },
            )

            benchmark_root = root / "benchmarks"
            _write_json(
                benchmark_root / "b1" / "summary.json",
                {
                    "scenarios": [
                        {
                            "swarms": [
                                {
                                    "selected_agents": 1,
                                    "tasks_completed_total": 2,
                                    "elapsed_seconds": 0.5,
                                    "ok": True,
                                },
                                {
                                    "selected_agents": 5,
                                    "tasks_completed_total": 20,
                                    "elapsed_seconds": 1.0,
                                    "ok": True,
                                },
                            ]
                        }
                    ]
                },
            )
            watchdog_root = root / "watchdog"
            watchdog_root.mkdir(parents=True, exist_ok=True)
            (watchdog_root / "guarded_coding_episode.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "provider": "codex",
                                "guard_family": "python",
                                "time_to_green_seconds": 30,
                                "guard_runtime_seconds": 6,
                                "retry_count": 1,
                                "escaped_findings_count": 0,
                                "reviewer_verdict": "accepted",
                                "guard_result": "pass",
                            }
                        ),
                        json.dumps(
                            {
                                "provider": "claude",
                                "guard_family": "rust",
                                "time_to_green_seconds": 0,
                                "guard_runtime_seconds": 10,
                                "retry_count": 2,
                                "escaped_findings_count": 1,
                                "reviewer_verdict": "rejected",
                                "guard_result": "noisy",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            governance_review_log = root / "governance_reviews.jsonl"
            governance_review_log.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "finding_id": "probe-1",
                                "timestamp_utc": "2026-03-11T00:00:00Z",
                                "repo_name": "demo",
                                "repo_path": str(root),
                                "signal_type": "probe",
                                "check_id": "probe_single_use_helpers",
                                "verdict": "false_positive",
                                "file_path": "demo.py",
                            }
                        ),
                        json.dumps(
                            {
                                "finding_id": "guard-1",
                                "timestamp_utc": "2026-03-11T00:05:00Z",
                                "repo_name": "demo",
                                "repo_path": str(root),
                                "signal_type": "guard",
                                "check_id": "python_design_complexity",
                                "verdict": "fixed",
                                "file_path": "worker.py",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = run_data_science_snapshot(
                trigger_command="unit-test",
                output_root=str(root / "out"),
                event_log_path=str(event_log),
                swarm_root=str(swarm_root),
                benchmark_root=str(benchmark_root),
                watchdog_root=str(watchdog_root),
                governance_review_log=str(governance_review_log),
                max_events=100,
                max_swarm_files=100,
                max_benchmark_files=100,
                max_watchdog_rows=100,
                max_governance_review_rows=100,
            )

            recommendation = (report.get("agent_stats") or {}).get("recommendation") or {}
            self.assertEqual(recommendation.get("selected_agents"), 5)
            watchdog_stats = report.get("watchdog_stats") or {}
            self.assertEqual(watchdog_stats.get("total_episodes"), 2)
            self.assertEqual(watchdog_stats.get("success_rate_pct"), 50.0)
            self.assertEqual(watchdog_stats.get("avg_time_to_green_seconds"), 30.0)
            self.assertEqual(watchdog_stats.get("avg_retry_count"), 1.5)
            self.assertEqual(watchdog_stats.get("known_provider_pct"), 100.0)
            governance_review_stats = report.get("governance_review_stats") or {}
            self.assertEqual(governance_review_stats.get("total_findings"), 2)
            self.assertEqual(governance_review_stats.get("false_positive_count"), 1)
            self.assertEqual(governance_review_stats.get("fixed_count"), 1)
            self.assertEqual(governance_review_stats.get("false_positive_rate_pct"), 50.0)

            summary_json = Path((report.get("paths") or {}).get("summary_json") or "")
            summary_md = Path((report.get("paths") or {}).get("summary_md") or "")
            self.assertTrue(summary_json.exists())
            self.assertTrue(summary_md.exists())
            self.assertIn(
                "Governance Review Metrics",
                summary_md.read_text(encoding="utf-8"),
            )
            self.assertTrue((summary_json.parent / "charts" / "command_frequency.svg").exists())
            self.assertTrue((summary_json.parent / "charts" / "agent_recommendation_score.svg").exists())
            self.assertTrue((summary_json.parent / "charts" / "watchdog_guard_family_frequency.svg").exists())

    def test_load_watchdog_summary_artifact_returns_typed_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary_path = Path(tmp_dir) / "summary.json"
            _write_json(
                summary_path,
                {
                    "generated_at": "2026-03-10T03:00:00Z",
                    "trigger_command": "unit-test",
                    "watchdog_stats": {
                        "total_episodes": 3,
                        "success_rate_pct": 66.67,
                        "avg_time_to_green_seconds": 12.5,
                        "p50_time_to_green_seconds": 10.0,
                        "avg_guard_runtime_seconds": 4.0,
                        "avg_retry_count": 1.33,
                        "avg_escaped_findings": 0.33,
                        "false_positive_rate_pct": 33.33,
                        "known_provider_pct": 100.0,
                        "providers": [
                            {"provider": "codex", "episodes": 2},
                            {"provider": "claude", "episodes": 1},
                        ],
                        "guard_families": [
                            {
                                "guard_family": "python",
                                "episodes": 2,
                                "success_rate_pct": 50.0,
                                "avg_time_to_green_seconds": 15.0,
                            }
                        ],
                    },
                },
            )

            snapshot = load_watchdog_summary_artifact(summary_path)

            self.assertTrue(snapshot.available)
            self.assertEqual(snapshot.metrics.total_episodes, 3)
            self.assertEqual(snapshot.metrics.providers[0].provider, "codex")
            self.assertEqual(snapshot.metrics.providers[0].episodes, 2)
            self.assertEqual(snapshot.metrics.guard_families[0].guard_family, "python")
            self.assertEqual(snapshot.metrics.guard_families[0].episodes, 2)
            self.assertEqual(snapshot.summary_path, str(summary_path))


class DataScienceCliIntegrationTests(unittest.TestCase):
    def test_cli_list_auto_refresh_writes_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_root = root / "data-science"
            event_log = root / "events.jsonl"
            swarm_root = root / "swarms-empty"
            benchmark_root = root / "benchmarks-empty"
            watchdog_root = root / "watchdog-empty"
            governance_review_log = root / "governance-reviews.jsonl"
            swarm_root.mkdir(parents=True, exist_ok=True)
            benchmark_root.mkdir(parents=True, exist_ok=True)
            watchdog_root.mkdir(parents=True, exist_ok=True)
            governance_review_log.write_text("", encoding="utf-8")

            with (
                patch.dict(
                    "os.environ",
                    {
                        "DEVCTL_AUDIT_EVENT_LOG": str(event_log),
                        "DEVCTL_AUDIT_CYCLE_ID": "unit-cycle",
                        "DEVCTL_EXECUTION_SOURCE": "script_only",
                        "DEVCTL_EXECUTION_ACTOR": "script",
                        "DEVCTL_DATA_SCIENCE_OUTPUT_ROOT": str(output_root),
                        "DEVCTL_DATA_SCIENCE_SWARM_ROOT": str(swarm_root),
                        "DEVCTL_DATA_SCIENCE_BENCHMARK_ROOT": str(benchmark_root),
                        "DEVCTL_DATA_SCIENCE_WATCHDOG_ROOT": str(watchdog_root),
                        "DEVCTL_DATA_SCIENCE_GOVERNANCE_REVIEW_LOG": str(governance_review_log),
                        "DEVCTL_DATA_SCIENCE_MAX_EVENTS": "100",
                        "DEVCTL_DATA_SCIENCE_MAX_SWARM_FILES": "10",
                        "DEVCTL_DATA_SCIENCE_MAX_BENCHMARK_FILES": "10",
                        "DEVCTL_DATA_SCIENCE_MAX_WATCHDOG_ROWS": "25",
                        "DEVCTL_DATA_SCIENCE_MAX_GOVERNANCE_REVIEW_ROWS": "25",
                    },
                    clear=False,
                ),
                patch("sys.argv", ["devctl", "list"]),
            ):
                rc = cli.main()

            self.assertEqual(rc, 0)
            snapshot = output_root / "latest" / "summary.json"
            self.assertTrue(snapshot.exists())
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("trigger_command"), "devctl:list")
            self.assertGreaterEqual(int((payload.get("event_stats") or {}).get("total_events") or 0), 1)
            self.assertEqual(
                payload.get("governance_review_log"),
                str(governance_review_log.resolve()),
            )


class DataScienceParserTests(unittest.TestCase):
    def test_cli_accepts_data_science_flags(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "data-science",
                "--output-root",
                "/tmp/ds",
                "--max-events",
                "500",
                "--watchdog-root",
                "/tmp/watchdog",
                "--max-watchdog-rows",
                "250",
                "--governance-review-log",
                "/tmp/reviews.jsonl",
                "--max-governance-review-rows",
                "120",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "data-science")
        self.assertEqual(args.output_root, "/tmp/ds")
        self.assertEqual(args.max_events, 500)
        self.assertEqual(args.watchdog_root, "/tmp/watchdog")
        self.assertEqual(args.max_watchdog_rows, 250)
        self.assertEqual(args.governance_review_log, "/tmp/reviews.jsonl")
        self.assertEqual(args.max_governance_review_rows, 120)
        self.assertEqual(args.format, "json")


if __name__ == "__main__":
    unittest.main()
