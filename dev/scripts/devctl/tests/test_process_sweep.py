"""Unit tests for shared process-sweep helpers."""

from __future__ import annotations

import subprocess
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl import process_sweep


class ProcessSweepTests(TestCase):
    @patch("dev.scripts.devctl.process_sweep.subprocess.run")
    def test_scan_voiceterm_test_binaries_matches_path_and_basename(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "123 1 05:00 /tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4\n"
                "124 1 04:00 voiceterm-feedface --nocapture\n"
                "125 1 03:00 /usr/bin/python3 some_script.py\n"
                "126 1 02:00 /tmp/project/target/debug/deps/voiceterm-nothex --nocapture\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_binaries(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [123, 124])
        self.assertTrue(all("voiceterm-" in row["command"] for row in rows))

    @patch("dev.scripts.devctl.process_sweep.subprocess.run")
    def test_scan_voiceterm_test_binaries_respects_skip_pid(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "223 1 05:00 voiceterm-deadbeef --nocapture\n"
                "224 1 04:00 voiceterm-feedface --nocapture\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_binaries(skip_pid=224)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["pid"], 223)
