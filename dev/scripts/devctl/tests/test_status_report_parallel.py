"""Tests for parallel collection probes in status_report.build_project_report."""

import unittest
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.status_report import (
    _run_probes_parallel,
    _run_probes_serial,
    build_project_report,
)


# Deterministic fake collectors for testing.
FAKE_GIT = {"branch": "develop", "changes": [{"status": "M", "path": "a.rs"}]}
FAKE_MUTANTS = {"results": {"score": 85.0}}
FAKE_CI = {"runs": [{"displayTitle": "ci_run", "status": "completed", "conclusion": "success"}]}
FAKE_DEV_LOGS = {
    "dev_root": "/tmp/dev",
    "sessions_scanned": 1,
    "session_files_total": 2,
    "events_scanned": 5,
    "transcript_events": 3,
    "empty_events": 1,
    "error_events": 1,
    "total_words": 20,
    "avg_latency_ms": 150,
    "parse_errors": 0,
    "latest_event_iso": "2026-02-23T00:00:00+00:00",
}


def _fake_git():
    return dict(FAKE_GIT)


def _fake_mutants():
    return dict(FAKE_MUTANTS)


def _fake_ci(_limit=5):
    return dict(FAKE_CI)


def _fake_dev_logs(**_kwargs):
    return dict(FAKE_DEV_LOGS)


class RunProbesSerialTests(unittest.TestCase):
    """Validate _run_probes_serial returns all results in order."""

    def test_serial_returns_all_probe_results(self) -> None:
        probes = [
            ("a", lambda: {"value": 1}),
            ("b", lambda: {"value": 2}),
            ("c", lambda: {"value": 3}),
        ]
        results = _run_probes_serial(probes)
        self.assertEqual(results, {"a": {"value": 1}, "b": {"value": 2}, "c": {"value": 3}})

    def test_serial_empty_probes(self) -> None:
        self.assertEqual(_run_probes_serial([]), {})


class RunProbesParallelTests(unittest.TestCase):
    """Validate _run_probes_parallel returns identical results to serial."""

    def test_parallel_returns_all_probe_results(self) -> None:
        probes = [
            ("a", lambda: {"value": 1}),
            ("b", lambda: {"value": 2}),
            ("c", lambda: {"value": 3}),
        ]
        results = _run_probes_parallel(probes, max_workers=4)
        self.assertEqual(results, {"a": {"value": 1}, "b": {"value": 2}, "c": {"value": 3}})

    def test_parallel_empty_probes(self) -> None:
        self.assertEqual(_run_probes_parallel([], max_workers=4), {})

    def test_parallel_single_probe_falls_back_to_serial(self) -> None:
        probes = [("only", lambda: {"value": 42})]
        results = _run_probes_parallel(probes, max_workers=4)
        self.assertEqual(results, {"only": {"value": 42}})

    def test_parallel_max_workers_one_falls_back_to_serial(self) -> None:
        probes = [
            ("a", lambda: {"value": 1}),
            ("b", lambda: {"value": 2}),
        ]
        results = _run_probes_parallel(probes, max_workers=1)
        self.assertEqual(results, {"a": {"value": 1}, "b": {"value": 2}})

    def test_parallel_matches_serial_output(self) -> None:
        """The core invariant: parallel and serial must produce identical results."""
        probes = [
            ("x", lambda: {"data": "hello"}),
            ("y", lambda: {"data": "world"}),
            ("z", lambda: {"data": "!"}),
        ]
        serial = _run_probes_serial(probes)
        parallel = _run_probes_parallel(probes, max_workers=4)
        self.assertEqual(serial, parallel)


class BuildProjectReportParallelTests(unittest.TestCase):
    """Validate build_project_report produces identical output in parallel vs sequential mode."""

    @patch("dev.scripts.devctl.status_report.collect_dev_log_summary", side_effect=_fake_dev_logs)
    @patch("dev.scripts.devctl.status_report.collect_ci_runs", side_effect=_fake_ci)
    @patch("dev.scripts.devctl.status_report.collect_mutation_summary", side_effect=_fake_mutants)
    @patch("dev.scripts.devctl.status_report.collect_git_status", side_effect=_fake_git)
    def test_parallel_and_serial_produce_same_report_keys(
        self,
        _mock_git,
        _mock_mutants,
        _mock_ci,
        _mock_dev_logs,
    ) -> None:
        """Both modes must produce reports with the same keys and probe data."""
        common_kwargs = dict(
            command="status",
            include_ci=True,
            ci_limit=5,
            include_dev_logs=True,
            dev_root="/tmp/dev",
            dev_sessions_limit=5,
        )
        report_parallel = build_project_report(**common_kwargs, parallel=True)
        report_serial = build_project_report(**common_kwargs, parallel=False)

        # Timestamps differ, so compare everything except timestamp.
        for key in ("command", "git", "mutants", "ci", "dev_logs"):
            self.assertEqual(
                report_parallel[key],
                report_serial[key],
                f"Mismatch in report key '{key}'",
            )

    @patch("dev.scripts.devctl.status_report.collect_mutation_summary", side_effect=_fake_mutants)
    @patch("dev.scripts.devctl.status_report.collect_git_status", side_effect=_fake_git)
    def test_parallel_base_probes_only(
        self,
        _mock_git,
        _mock_mutants,
    ) -> None:
        """When CI and dev_logs are disabled, only git and mutants appear."""
        report = build_project_report(
            command="report",
            include_ci=False,
            ci_limit=5,
            include_dev_logs=False,
            dev_root=None,
            dev_sessions_limit=5,
            parallel=True,
        )
        self.assertIn("git", report)
        self.assertIn("mutants", report)
        self.assertNotIn("ci", report)
        self.assertNotIn("dev_logs", report)

    @patch("dev.scripts.devctl.status_report.collect_mutation_summary", side_effect=_fake_mutants)
    @patch("dev.scripts.devctl.status_report.collect_git_status", side_effect=_fake_git)
    def test_serial_base_probes_only(
        self,
        _mock_git,
        _mock_mutants,
    ) -> None:
        """Sequential path must also work with base probes only."""
        report = build_project_report(
            command="report",
            include_ci=False,
            ci_limit=5,
            include_dev_logs=False,
            dev_root=None,
            dev_sessions_limit=5,
            parallel=False,
        )
        self.assertIn("git", report)
        self.assertIn("mutants", report)
        self.assertNotIn("ci", report)
        self.assertNotIn("dev_logs", report)

    @patch("dev.scripts.devctl.status_report.collect_ci_runs", side_effect=_fake_ci)
    @patch("dev.scripts.devctl.status_report.collect_mutation_summary", side_effect=_fake_mutants)
    @patch("dev.scripts.devctl.status_report.collect_git_status", side_effect=_fake_git)
    def test_report_key_order_is_deterministic(
        self,
        _mock_git,
        _mock_mutants,
        _mock_ci,
    ) -> None:
        """Report keys must appear in probe-definition order regardless of parallelism."""
        report = build_project_report(
            command="status",
            include_ci=True,
            ci_limit=5,
            include_dev_logs=False,
            dev_root=None,
            dev_sessions_limit=5,
            parallel=True,
        )
        keys = list(report.keys())
        # command and timestamp come first, then probes in definition order.
        self.assertEqual(keys[:2], ["command", "timestamp"])
        self.assertEqual(keys[2:], ["git", "mutants", "ci"])

    @patch("dev.scripts.devctl.status_report.collect_dev_log_summary", side_effect=_fake_dev_logs)
    @patch("dev.scripts.devctl.status_report.collect_ci_runs", side_effect=_fake_ci)
    @patch("dev.scripts.devctl.status_report.collect_mutation_summary", side_effect=_fake_mutants)
    @patch("dev.scripts.devctl.status_report.collect_git_status", side_effect=_fake_git)
    def test_report_key_order_all_probes(
        self,
        _mock_git,
        _mock_mutants,
        _mock_ci,
        _mock_dev_logs,
    ) -> None:
        """All four probes in definition order."""
        report = build_project_report(
            command="status",
            include_ci=True,
            ci_limit=5,
            include_dev_logs=True,
            dev_root="/tmp/dev",
            dev_sessions_limit=5,
            parallel=True,
        )
        keys = list(report.keys())
        self.assertEqual(keys[:2], ["command", "timestamp"])
        self.assertEqual(keys[2:], ["git", "mutants", "ci", "dev_logs"])


class ProbeExceptionTests(unittest.TestCase):
    """Validate that probe-level exceptions produce error dicts instead of crashing."""

    def test_serial_probe_exception_returns_error_dict(self) -> None:
        def _exploding():
            raise RuntimeError("boom")

        probes = [
            ("ok", lambda: {"value": 1}),
            ("bad", _exploding),
        ]
        results = _run_probes_serial(probes)
        self.assertEqual(results["ok"], {"value": 1})
        self.assertIn("error", results["bad"])
        self.assertIn("boom", results["bad"]["error"])

    def test_parallel_probe_exception_returns_error_dict(self) -> None:
        def _exploding():
            raise RuntimeError("kaboom")

        probes = [
            ("ok", lambda: {"value": 1}),
            ("bad", _exploding),
            ("also_ok", lambda: {"value": 2}),
        ]
        results = _run_probes_parallel(probes, max_workers=4)
        self.assertEqual(results["ok"], {"value": 1})
        self.assertEqual(results["also_ok"], {"value": 2})
        self.assertIn("error", results["bad"])
        self.assertIn("kaboom", results["bad"]["error"])


class CliNoParallelFlagTests(unittest.TestCase):
    """Validate --no-parallel is accepted by status and report subcommands."""

    def test_status_accepts_no_parallel_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status", "--no-parallel"])
        self.assertTrue(args.no_parallel)

    def test_status_defaults_parallel_enabled(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status"])
        self.assertFalse(args.no_parallel)

    def test_report_accepts_no_parallel_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["report", "--no-parallel"])
        self.assertTrue(args.no_parallel)

    def test_report_defaults_parallel_enabled(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["report"])
        self.assertFalse(args.no_parallel)


if __name__ == "__main__":
    unittest.main()
