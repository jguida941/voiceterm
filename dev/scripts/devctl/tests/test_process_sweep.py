"""Unit tests for shared process-sweep helpers."""

from __future__ import annotations

import subprocess
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.process_sweep import core as process_sweep


class ProcessSweepTests(TestCase):
    def test_extend_process_row_markdown_uses_requested_overflow_label(self) -> None:
        rows = [
            {
                "pid": 100,
                "ppid": 1,
                "etime": "08:00",
                "command": "cargo test --bin voiceterm",
                "match_scope": "voiceterm",
                "match_source": "direct",
            },
            {
                "pid": 101,
                "ppid": 100,
                "etime": "07:59",
                "command": "cat",
                "match_scope": "voiceterm",
                "match_source": "descendant",
            },
            {
                "pid": 102,
                "ppid": 101,
                "etime": "07:58",
                "command": "helper-child",
                "match_scope": "voiceterm",
                "match_source": "descendant",
            },
        ]
        lines = ["## Rows"]

        process_sweep.extend_process_row_markdown(
            lines,
            rows,
            row_limit=2,
            overflow_label="cleanup targets",
        )

        self.assertEqual(len(lines), 4)
        self.assertIn("pid=100", lines[1])
        self.assertIn("pid=101", lines[2])
        self.assertEqual(lines[3], "- ... 1 more cleanup targets")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_voiceterm_test_binaries_matches_path_and_basename(
        self, run_mock
    ) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "123 1 ?? 05:00 /tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4\n"
                "124 1 ?? 04:00 voiceterm-feedface --nocapture\n"
                "125 1 ?? 03:30 cargo test --bin voiceterm\n"
                "126 1 ?? 03:00 /bin/zsh -c cd /repo/rust && cargo test --bin voiceterm 2>&1 | tail -5\n"
                "127 1 ?? 03:00 /usr/bin/python3 some_script.py\n"
                "128 1 ?? 02:00 /tmp/project/target/debug/deps/voiceterm-nothex --nocapture\n"
                "129 1 ?? 01:00 cargo test --bin not-voiceterm\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_binaries(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [123, 124, 125, 126])
        self.assertTrue(
            any("cargo test --bin voiceterm" in row["command"] for row in rows)
        )

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_voiceterm_test_binaries_respects_skip_pid(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "223 1 ?? 05:00 voiceterm-deadbeef --nocapture\n"
                "224 1 ?? 04:00 voiceterm-feedface --nocapture\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_binaries(skip_pid=224)

        self.assertEqual(warnings, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["pid"], 223)

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_voiceterm_test_binaries_matches_stale_stress_screen_sessions(
        self, run_mock
    ) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "901 1 ?? 20:00 SCREEN -dmS vt_hud_stress_90274 bash -lc cd /repo; ./target/debug/voiceterm --logs --claude\n"
                "902 1 ?? 19:59 SCREEN -dmS vt_other_session bash -lc echo nope\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_binaries(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [901])
        self.assertIn("vt_hud_stress_", rows[0]["command"])

    def test_split_stale_processes_uses_elapsed_age_threshold(self) -> None:
        rows = [
            {"pid": 11, "elapsed_seconds": 601},
            {"pid": 12, "elapsed_seconds": 120},
            {"pid": 13, "elapsed_seconds": -1},
        ]

        stale, recent = process_sweep.split_stale_processes(rows, min_age_seconds=600)

        self.assertEqual([row["pid"] for row in stale], [11])
        self.assertEqual([row["pid"] for row in recent], [12, 13])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_voiceterm_test_process_tree_includes_descendants(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            process_sweep.PROCESS_SWEEP_CMD,
            0,
            stdout=(
                "100 1 ?? 08:00 cargo test --bin voiceterm\n"
                "101 100 ?? 07:59 /tmp/project/target/debug/deps/voiceterm-deadbeef --nocapture\n"
                "102 101 ?? 07:58 cat\n"
                "103 102 ?? 07:57 helper-child\n"
                "104 1 ?? 07:56 /usr/bin/python3 other_script.py\n"
            ),
            stderr="",
        )

        rows, warnings = process_sweep.scan_voiceterm_test_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [100, 101, 102, 103])
        self.assertEqual(rows[0]["match_source"], "direct")
        self.assertEqual(rows[1]["lineage_depth"], 1)
        self.assertEqual(rows[2]["match_source"], "descendant")
        self.assertEqual(rows[2]["lineage_depth"], 2)
        self.assertEqual(rows[3]["lineage_depth"], 3)

    def test_expand_cleanup_target_rows_includes_recent_descendants(self) -> None:
        rows = [
            {
                "pid": 100,
                "ppid": 1,
                "etime": "08:00",
                "elapsed_seconds": 480,
                "command": "cargo test --bin voiceterm",
                "lineage_depth": 0,
            },
            {
                "pid": 101,
                "ppid": 100,
                "etime": "00:20",
                "elapsed_seconds": 20,
                "command": "cat",
                "lineage_depth": 1,
            },
            {
                "pid": 102,
                "ppid": 101,
                "etime": "00:10",
                "elapsed_seconds": 10,
                "command": "helper-child",
                "lineage_depth": 2,
            },
        ]

        expanded = process_sweep.expand_cleanup_target_rows(rows, [rows[0]])

        self.assertEqual([row["pid"] for row in expanded], [102, 101, 100])

    @patch("dev.scripts.devctl.process_sweep.internals.os.kill")
    def test_kill_processes_stops_descendants_before_parents(self, kill_mock) -> None:
        rows = [
            {"pid": 100, "elapsed_seconds": 400, "lineage_depth": 0},
            {"pid": 101, "elapsed_seconds": 390, "lineage_depth": 1},
            {"pid": 102, "elapsed_seconds": 380, "lineage_depth": 2},
        ]

        killed, warnings = process_sweep.kill_processes(rows)

        self.assertEqual(warnings, [])
        self.assertEqual(killed, [102, 101, 100])
        self.assertEqual([call.args[0] for call in kill_mock.call_args_list], [102, 101, 100])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_includes_descendants(self, run_mock) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "210 1 ?? 2-00:00 /bin/zsh -c python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
                    "211 210 ?? 1-23:59 /opt/homebrew/bin/qemu-system-riscv64\n"
                    "212 1 ?? 00:30 /usr/bin/python3 unrelated_script.py\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "210"],
                0,
                stdout=(
                    "p210\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "210,211,212"],
                0,
                stdout="",
                stderr="",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [210, 211])
        self.assertEqual(rows[0]["match_scope"], "repo_tooling")
        self.assertEqual(rows[1]["match_source"], "descendant")

    @patch("dev.scripts.devctl.process_sweep.scans.os.getpid", return_value=900)
    @patch("dev.scripts.devctl.process_sweep.scans.os.getppid", return_value=901)
    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_skips_current_ancestor_tree(
        self,
        run_mock,
        _getppid_mock,
        _getpid_mock,
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "900 901 ?? 00:02 python3 dev/scripts/devctl.py process-audit --strict --format json\n"
                    "901 777 ?? 00:03 /bin/zsh -c python3 dev/scripts/devctl.py process-audit --strict --format json\n"
                    "904 900 ?? 00:01 lsof -n -w -F pfn0 -a -d cwd -p 900\n"
                    "905 904 ?? 00:01 cat\n"
                    "902 1 ?? 2-00:00 /bin/zsh -c python3 dev/scripts/devctl.py hygiene --strict-warnings\n"
                    "903 902 ?? 1-23:59 /opt/homebrew/bin/qemu-system-riscv64\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "902"],
                0,
                stdout=(
                    "p902\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "902,903"],
                0,
                stdout="",
                stderr="",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree()

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [902, 903])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_matches_direct_repo_scripts(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "220 1 ?? 05:00 bash dev/scripts/tests/wake_word_guard.sh\n"
                    "221 220 ?? 04:59 helper-child\n"
                    "222 1 ?? 04:00 ./scripts/macros.sh validate --project-dir .\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "220,222"],
                0,
                stdout=(
                    "p220\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p222\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "220"],
                0,
                stdout="",
                stderr="",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [220, 221, 222])
        self.assertEqual(rows[0]["match_scope"], "repo_tooling")
        self.assertEqual(rows[2]["match_source"], "direct")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_ignores_attached_interactive_generic_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "340 77 ttys035 15:25 /Users/jguida941/.pyenv/versions/3.10.4/bin/python3 -\n"
                    "341 1 ?? 12:00 /usr/bin/python3 -c import time; time.sleep(600)\n"
                    "342 341 ?? 11:59 cat\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "341"],
                0,
                stdout=(
                    "p341\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [341, 342])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_matches_tty_attached_repo_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "350 77 ttys035 15:25 /usr/bin/python3 -m unittest discover -s app/operator_console/tests\n"
                    "351 350 ttys035 15:24 cat\n"
                    "352 77 ttys036 15:25 /usr/bin/python3 -\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "350"],
                0,
                stdout=(
                    "p350\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [350, 351])
        self.assertEqual(rows[0]["match_scope"], "repo_tooling")
        self.assertEqual(rows[1]["match_source"], "descendant")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_matches_tty_attached_pytest_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "360 77 ttys035 15:25 /opt/homebrew/bin/pytest app/operator_console/tests -q\n"
                    "361 360 ttys035 15:24 cat\n"
                    "362 77 ttys036 15:25 /usr/bin/python3 -\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "360"],
                0,
                stdout=(
                    "p360\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [360, 361])
        self.assertEqual(rows[0]["match_scope"], "repo_tooling")
        self.assertEqual(rows[1]["match_source"], "descendant")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_matches_repo_cwd_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "310 1 ?? 12:00 /usr/bin/python3 -c import time; time.sleep(600)\n"
                    "311 310 ?? 11:59 cat\n"
                    "312 1 ttys000 12:00 /usr/bin/python3 -c print('interactive')\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "310,311,312"],
                0,
                stdout=(
                    "p310\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p311\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p312\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [310, 311])
        self.assertEqual(rows[0]["match_scope"], "repo_background")
        self.assertEqual(rows[1]["match_scope"], "repo_background")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_matches_direct_shell_script_wrappers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "320 1 ?? 12:00 /bin/bash dev/scripts/tests/measure_latency.sh --ci-guard\n"
                    "321 320 ?? 11:59 /opt/homebrew/bin/qemu-system-riscv64\n"
                    "322 1 ?? 12:00 /bin/zsh -il\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "320,321,322"],
                0,
                stdout=(
                    "p320\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p321\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p322\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [320, 321])
        self.assertEqual(rows[0]["match_scope"], "repo_background")
        self.assertEqual(rows[1]["match_scope"], "repo_background")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_matches_tty_attached_orphan_repo_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "325 1 ttys001 12:00 /usr/local/bin/helper-child --serve\n"
                    "326 325 ttys001 11:59 nested-helper\n"
                    "327 1 ttys002 12:00 /bin/zsh -il\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "325,326,327"],
                0,
                stdout=(
                    "p325\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p326\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p327\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [325, 326])
        self.assertEqual(rows[0]["match_scope"], "repo_background")
        self.assertEqual(rows[1]["match_source"], "descendant")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_matches_detached_pytest_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "328 1 ?? 12:00 /opt/homebrew/bin/pytest app/operator_console/tests -q\n"
                    "329 328 ?? 11:59 cat\n"
                    "330 1 ?? 12:00 /usr/bin/python3 -\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "328,329,330"],
                0,
                stdout=(
                    "p328\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p329\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p330\0fcwd\0n/tmp/elsewhere\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [328, 329])
        self.assertEqual(rows[0]["match_scope"], "repo_background")
        self.assertEqual(rows[1]["match_scope"], "repo_background")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_does_not_treat_bare_system_commands_as_repo_paths(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "330 1 ?? 12:00 autofsd\n"
                    "331 1 ?? 12:00 aslmanager\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "330,331"],
                0,
                stdout=(
                    "p330\0fcwd\0n/\0"
                    "p331\0fcwd\0n/\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual(rows, [])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_lookup_process_cwds_parses_newline_prefixed_lsof_tokens(
        self, run_mock
    ) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "330"],
            0,
            stdout="p330\0\nfcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0\n".encode(
                "utf-8"
            ),
            stderr=b"",
        )

        cwd_map, warnings = process_sweep.lookup_process_cwds([{"pid": 330}])

        self.assertEqual(warnings, [])
        self.assertEqual(
            cwd_map,
            {330: "/Users/jguida941/testing_upgrade/codex-voice"},
        )

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_background_process_tree_ignores_bare_relative_app_helpers(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "520 1 ?? 12:00 Contents/Resources/ChatGPTHelper\n"
                    "521 1 ?? 12:00 /usr/bin/python3 -c import time; time.sleep(600)\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "520,521"],
                0,
                stdout=(
                    "p520\0fcwd\0n/\0"
                    "p521\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_background_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [521])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_runtime_process_tree_matches_repo_cwd_cargo_commands(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "410 1 ?? 08:00 cargo test -p overlay_core\n"
                    "411 410 ?? 07:59 /usr/bin/python3 helper.py\n"
                    "412 1 ?? 08:00 cargo test -p unrelated\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "410,412"],
                0,
                stdout=(
                    "p410\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p412\0fcwd\0n/tmp/elsewhere\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_runtime_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [410, 411])
        self.assertEqual(rows[0]["match_scope"], "repo_runtime")
        self.assertEqual(rows[1]["match_source"], "descendant")

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_hygiene_process_tree_merges_voiceterm_tooling_and_background(
        self, run_mock
    ) -> None:
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "100 1 ?? 08:00 cargo test --bin voiceterm\n"
                    "101 100 ?? 07:59 cat\n"
                    "150 1 ?? 06:00 cargo test -p overlay_core\n"
                    "151 150 ?? 05:59 /usr/bin/python3 helper.py\n"
                    "210 1 ?? 2-00:00 /bin/zsh -c python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
                    "211 210 ?? 1-23:59 /opt/homebrew/bin/qemu-system-riscv64\n"
                    "310 1 ?? 12:00 /usr/bin/python3 -c import time; time.sleep(600)\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "100,101,150,151,210,211,310"],
                0,
                stdout=(
                    "p100\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p101\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p150\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p151\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p210\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p211\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p310\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "100,150"],
                0,
                stdout=(
                    "p100\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                    "p150\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice/rust\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "210"],
                0,
                stdout=(
                    "p210\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "151,210,211,310"],
                0,
                stdout=(
                    "p210\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                    "p310\0fcwd\0n/Users/jguida941/testing_upgrade/codex-voice\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_hygiene_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual([row["pid"] for row in rows], [210, 211, 310, 100, 101, 150, 151])
        self.assertEqual(
            [row["match_scope"] for row in rows],
            [
                "repo_tooling",
                "repo_tooling",
                "repo_tooling",
                "voiceterm",
                "voiceterm",
                "repo_runtime",
                "repo_runtime",
            ],
        )

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_runtime_process_tree_ignores_relative_binary_outside_this_checkout(
        self, run_mock
    ) -> None:
        """Relative target-binary paths from another checkout are not classified."""
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "500 1 ?? 08:00 ./target/debug/deps/voiceterm-deadbeef01 --nocapture\n"
                    "501 500 ?? 07:59 cat\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "500"],
                0,
                stdout=(
                    "p500\0fcwd\0n/tmp/other-checkout\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_runtime_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual(rows, [])

    @patch("dev.scripts.devctl.process_sweep.scans.subprocess.run")
    def test_scan_repo_tooling_process_tree_ignores_relative_scripts_outside_this_checkout(
        self, run_mock
    ) -> None:
        """Relative dev/scripts paths from another checkout are not classified."""
        run_mock.side_effect = [
            subprocess.CompletedProcess(
                process_sweep.PROCESS_SWEEP_CMD,
                0,
                stdout=(
                    "600 1 ?? 08:00 python3 dev/scripts/devctl.py check --profile ci\n"
                    "601 600 ?? 07:59 helper\n"
                ),
                stderr="",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "600"],
                0,
                stdout=(
                    "p600\0fcwd\0n/tmp/other-checkout\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
            subprocess.CompletedProcess(
                [*process_sweep.PROCESS_CWD_LOOKUP_PREFIX, "600"],
                0,
                stdout=(
                    "p600\0fcwd\0n/tmp/other-checkout\0"
                ).encode("utf-8"),
                stderr=b"",
            ),
        ]

        rows, warnings = process_sweep.scan_repo_tooling_process_tree(skip_pid=9999)

        self.assertEqual(warnings, [])
        self.assertEqual(rows, [])
