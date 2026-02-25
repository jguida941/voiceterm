"""Tests for data-science telemetry snapshots and CLI integration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl.data_science_metrics import run_data_science_snapshot


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

            report = run_data_science_snapshot(
                trigger_command="unit-test",
                output_root=str(root / "out"),
                event_log_path=str(event_log),
                swarm_root=str(swarm_root),
                benchmark_root=str(benchmark_root),
                max_events=100,
                max_swarm_files=100,
                max_benchmark_files=100,
            )

            recommendation = (report.get("agent_stats") or {}).get("recommendation") or {}
            self.assertEqual(recommendation.get("selected_agents"), 5)

            summary_json = Path((report.get("paths") or {}).get("summary_json") or "")
            summary_md = Path((report.get("paths") or {}).get("summary_md") or "")
            self.assertTrue(summary_json.exists())
            self.assertTrue(summary_md.exists())
            self.assertTrue((summary_json.parent / "charts" / "command_frequency.svg").exists())
            self.assertTrue(
                (summary_json.parent / "charts" / "agent_recommendation_score.svg").exists()
            )


class DataScienceCliIntegrationTests(unittest.TestCase):
    def test_cli_list_auto_refresh_writes_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_root = root / "data-science"
            event_log = root / "events.jsonl"
            swarm_root = root / "swarms-empty"
            benchmark_root = root / "benchmarks-empty"
            swarm_root.mkdir(parents=True, exist_ok=True)
            benchmark_root.mkdir(parents=True, exist_ok=True)

            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(event_log),
                    "DEVCTL_AUDIT_CYCLE_ID": "unit-cycle",
                    "DEVCTL_EXECUTION_SOURCE": "script_only",
                    "DEVCTL_EXECUTION_ACTOR": "script",
                    "DEVCTL_DATA_SCIENCE_OUTPUT_ROOT": str(output_root),
                    "DEVCTL_DATA_SCIENCE_SWARM_ROOT": str(swarm_root),
                    "DEVCTL_DATA_SCIENCE_BENCHMARK_ROOT": str(benchmark_root),
                    "DEVCTL_DATA_SCIENCE_MAX_EVENTS": "100",
                    "DEVCTL_DATA_SCIENCE_MAX_SWARM_FILES": "10",
                    "DEVCTL_DATA_SCIENCE_MAX_BENCHMARK_FILES": "10",
                },
                clear=False,
            ):
                with patch("sys.argv", ["devctl", "list"]):
                    rc = cli.main()

            self.assertEqual(rc, 0)
            snapshot = output_root / "latest" / "summary.json"
            self.assertTrue(snapshot.exists())
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("trigger_command"), "devctl:list")
            self.assertGreaterEqual(int((payload.get("event_stats") or {}).get("total_events") or 0), 1)


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
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "data-science")
        self.assertEqual(args.output_root, "/tmp/ds")
        self.assertEqual(args.max_events, 500)
        self.assertEqual(args.format, "json")


if __name__ == "__main__":
    unittest.main()
