"""Tests for `devctl process-cleanup` command behavior."""

from __future__ import annotations

import json
from unittest import TestCase, mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import process_cleanup


def _proc(
    pid: int,
    *,
    ppid: int = 1,
    etime: str = "00:00",
    elapsed_seconds: int = 0,
    command: str = "cargo test --bin voiceterm",
    lineage_depth: int = 0,
    match_source: str = "direct",
    **extra,
) -> dict:
    """Build a process row dict with sensible defaults."""
    row = {
        "pid": pid,
        "ppid": ppid,
        "etime": etime,
        "elapsed_seconds": elapsed_seconds,
        "command": command,
        "lineage_depth": lineage_depth,
        "match_source": match_source,
    }
    row.update(extra)
    return row


def _state(
    *,
    rows: list[dict] | None = None,
    orphaned_rows: list[dict] | None = None,
    stale_active_rows: list[dict] | None = None,
    active_recent_rows: list[dict] | None = None,
    recent_detached_rows: list[dict] | None = None,
    scan_warnings: list[str] | None = None,
) -> dict:
    rows = rows or []
    orphaned_rows = orphaned_rows or []
    stale_active_rows = stale_active_rows or []
    active_recent_rows = active_recent_rows or []
    return {
        "rows": rows,
        "scan_warnings": scan_warnings or [],
        "orphaned_rows": orphaned_rows,
        "stale_active_rows": stale_active_rows,
        "active_recent_rows": active_recent_rows,
        "recent_detached_rows": recent_detached_rows or [],
        "direct_matches": len(rows),
        "descendant_matches": 0,
    }


class ProcessCleanupParserTests(TestCase):
    def test_cli_accepts_process_cleanup_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["process-cleanup", "--dry-run", "--verify", "--format", "json"]
        )

        self.assertEqual(args.command, "process-cleanup")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verify)
        self.assertEqual(args.format, "json")


class ProcessCleanupCommandTests(TestCase):
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_dry_run_reports_targets_without_killing(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        orphan_root = _proc(100, etime="08:00", elapsed_seconds=480)
        recent_child = _proc(
            101, ppid=100, etime="00:20", elapsed_seconds=20,
            command="cat", lineage_depth=1, match_source="descendant",
        )
        collect_mock.return_value = _state(
            rows=[orphan_root, recent_child],
            orphaned_rows=[orphan_root],
        )
        args = build_parser().parse_args(
            ["process-cleanup", "--dry-run", "--format", "json"]
        )

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        kill_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["cleanup_target_count"], 2)
        self.assertEqual(payload["killed_count"], 0)
        self.assertTrue(payload["ok"])

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_kills_full_tree_for_orphaned_and_stale_roots(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        orphan_root = {
            "pid": 100,
            "ppid": 1,
            "etime": "08:00",
            "elapsed_seconds": 480,
            "command": "cargo test --bin voiceterm",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        orphan_child_recent = {
            "pid": 101,
            "ppid": 100,
            "etime": "00:20",
            "elapsed_seconds": 20,
            "command": "cat",
            "lineage_depth": 1,
            "match_source": "descendant",
        }
        stale_root = {
            "pid": 200,
            "ppid": 50,
            "etime": "12:00",
            "elapsed_seconds": 720,
            "command": "voiceterm-feedface --nocapture",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        stale_child_recent = {
            "pid": 201,
            "ppid": 200,
            "etime": "00:15",
            "elapsed_seconds": 15,
            "command": "helper-child",
            "lineage_depth": 1,
            "match_source": "descendant",
        }
        unrelated_recent = {
            "pid": 300,
            "ppid": 60,
            "etime": "00:30",
            "elapsed_seconds": 30,
            "command": "cargo test --bin voiceterm -- --nocapture",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        collect_mock.return_value = _state(
            rows=[
                orphan_root,
                orphan_child_recent,
                stale_root,
                stale_child_recent,
                unrelated_recent,
            ],
            orphaned_rows=[orphan_root],
            stale_active_rows=[stale_root],
            active_recent_rows=[
                orphan_child_recent,
                stale_child_recent,
                unrelated_recent,
            ],
        )
        kill_mock.return_value = ([201, 101, 200, 100], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        targeted_rows = kill_mock.call_args.args[0]
        self.assertEqual([row["pid"] for row in targeted_rows], [101, 201, 200, 100])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["cleanup_target_count"], 4)
        self.assertEqual(payload["active_recent_count_pre"], 3)
        self.assertEqual(payload["killed_count"], 4)

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_kills_repo_tooling_orphan_roots_and_descendants(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        orphan_root = {
            "pid": 210,
            "ppid": 1,
            "etime": "2-00:00",
            "elapsed_seconds": 172800,
            "command": "/bin/zsh -c python3 dev/scripts/devctl.py docs-check --strict-tooling",
            "lineage_depth": 0,
            "match_source": "direct",
            "match_scope": "repo_tooling",
        }
        orphan_descendant = {
            "pid": 211,
            "ppid": 210,
            "etime": "1-23:59",
            "elapsed_seconds": 172799,
            "command": "/opt/homebrew/bin/qemu-system-riscv64",
            "lineage_depth": 1,
            "match_source": "descendant",
            "match_scope": "repo_tooling",
        }
        collect_mock.return_value = _state(
            rows=[orphan_root, orphan_descendant],
            orphaned_rows=[orphan_root],
        )
        kill_mock.return_value = ([211, 210], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        targeted_rows = kill_mock.call_args.args[0]
        self.assertEqual([row["pid"] for row in targeted_rows], [211, 210])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["cleanup_target_count"], 2)
        self.assertEqual(payload["killed_count"], 2)

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_kills_repo_background_orphan_helpers(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        orphan_root = {
            "pid": 310,
            "ppid": 1,
            "etime": "12:00",
            "elapsed_seconds": 720,
            "command": "/usr/bin/python3 -c import time; time.sleep(600)",
            "lineage_depth": 0,
            "match_source": "direct",
            "match_scope": "repo_background",
            "cwd": "/Users/jguida941/testing_upgrade/codex-voice",
        }
        orphan_descendant = {
            "pid": 311,
            "ppid": 310,
            "etime": "11:59",
            "elapsed_seconds": 719,
            "command": "cat",
            "lineage_depth": 1,
            "match_source": "descendant",
            "match_scope": "repo_background",
            "cwd": "/Users/jguida941/testing_upgrade/codex-voice",
        }
        collect_mock.return_value = _state(
            rows=[orphan_root, orphan_descendant],
            orphaned_rows=[orphan_root],
        )
        kill_mock.return_value = ([311, 310], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        targeted_rows = kill_mock.call_args.args[0]
        self.assertEqual([row["pid"] for row in targeted_rows], [311, 310])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["cleanup_target_count"], 2)
        self.assertEqual(payload["killed_count"], 2)

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.build_process_audit_report")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_verify_fails_when_post_cleanup_audit_still_dirty(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
        verify_mock,
    ) -> None:
        orphan_root = {
            "pid": 100,
            "ppid": 1,
            "etime": "08:00",
            "elapsed_seconds": 480,
            "command": "cargo test --bin voiceterm",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        collect_mock.return_value = _state(rows=[orphan_root], orphaned_rows=[orphan_root])
        kill_mock.return_value = ([100], [])
        verify_mock.return_value = {
            "command": "process-audit",
            "strict": True,
            "rows": [],
            "orphaned_rows": [],
            "stale_active_rows": [],
            "active_recent_rows": [
                {
                    "pid": 200,
                    "ppid": 50,
                    "etime": "00:20",
                    "elapsed_seconds": 20,
                    "command": "cargo test --bin voiceterm",
                    "match_source": "direct",
                }
            ],
            "total_detected": 1,
            "direct_matches": 1,
            "descendant_matches": 0,
            "orphaned_count": 0,
            "stale_active_count": 0,
            "active_recent_count": 1,
            "warnings": [],
            "errors": ["Active VoiceTerm-related host processes are still running"],
            "ok": False,
        }
        args = build_parser().parse_args(
            ["process-cleanup", "--verify", "--format", "json"]
        )

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["verify_ok"])
        self.assertIn("Host process cleanup verification failed.", payload["errors"])

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_warns_when_recent_detached_rows_are_skipped(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        recent_detached = {
            "pid": 410,
            "ppid": 1,
            "etime": "00:10",
            "elapsed_seconds": 10,
            "command": "python3 -c import time; time.sleep(300)",
            "lineage_depth": 0,
            "match_source": "direct",
            "match_scope": "repo_tooling",
        }
        collect_mock.return_value = _state(
            rows=[recent_detached],
            active_recent_rows=[recent_detached],
            recent_detached_rows=[recent_detached],
        )
        kill_mock.return_value = ([], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        kill_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["recent_detached_count_pre"], 1)
        self.assertEqual(payload["cleanup_target_count"], 0)
        self.assertIn("Recent detached repo-related processes were not killed yet", payload["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_skipped_recent_rows_excludes_cleanup_targets(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        """Recent descendants of orphaned/stale roots that are already cleanup
        targets must not appear in skipped_recent_rows or trigger the warning."""
        orphan_root = {
            "pid": 100,
            "ppid": 1,
            "etime": "08:00",
            "elapsed_seconds": 480,
            "command": "cargo test --bin voiceterm",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        orphan_child_recent = {
            "pid": 101,
            "ppid": 100,
            "etime": "00:20",
            "elapsed_seconds": 20,
            "command": "cat",
            "lineage_depth": 1,
            "match_source": "descendant",
        }
        collect_mock.return_value = _state(
            rows=[orphan_root, orphan_child_recent],
            orphaned_rows=[orphan_root],
            active_recent_rows=[orphan_child_recent],
        )
        kill_mock.return_value = ([101, 100], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        # orphan_child_recent is a cleanup target, so it must NOT be skipped
        self.assertEqual(payload["skipped_recent_rows"], [])
        # No warning should fire because all recent rows are cleanup targets
        self.assertEqual(payload["warnings"], [])

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.kill_processes")
    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_skipped_recent_rows_warns_for_non_cleanup_targets(
        self,
        collect_mock,
        write_output_mock,
        kill_mock,
    ) -> None:
        """Recent active rows NOT in cleanup_target_rows should still produce
        a warning and appear in skipped_recent_rows."""
        orphan_root = {
            "pid": 100,
            "ppid": 1,
            "etime": "08:00",
            "elapsed_seconds": 480,
            "command": "cargo test --bin voiceterm",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        orphan_child_recent = {
            "pid": 101,
            "ppid": 100,
            "etime": "00:20",
            "elapsed_seconds": 20,
            "command": "cat",
            "lineage_depth": 1,
            "match_source": "descendant",
        }
        unrelated_recent = {
            "pid": 300,
            "ppid": 60,
            "etime": "00:30",
            "elapsed_seconds": 30,
            "command": "cargo test --bin voiceterm -- --nocapture",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        collect_mock.return_value = _state(
            rows=[orphan_root, orphan_child_recent, unrelated_recent],
            orphaned_rows=[orphan_root],
            active_recent_rows=[orphan_child_recent, unrelated_recent],
        )
        kill_mock.return_value = ([101, 100], [])
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        # Only unrelated_recent should be skipped; orphan_child_recent is a target
        skipped_pids = [row["pid"] for row in payload["skipped_recent_rows"]]
        self.assertEqual(skipped_pids, [300])
        # Warning should fire because unrelated_recent IS truly skipped
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertIn("not killed", payload["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_markdown_skipped_recent_overflow_uses_only_skipped_rows(
        self,
        collect_mock,
        write_output_mock,
    ) -> None:
        orphan_root = {
            "pid": 100,
            "ppid": 1,
            "etime": "08:00",
            "elapsed_seconds": 480,
            "command": "cargo test --bin voiceterm",
            "lineage_depth": 0,
            "match_source": "direct",
        }
        orphan_child_recent = {
            "pid": 101,
            "ppid": 100,
            "etime": "00:20",
            "elapsed_seconds": 20,
            "command": "cat",
            "lineage_depth": 1,
            "match_source": "descendant",
        }
        skipped_recent_rows = [
            {
                "pid": pid,
                "ppid": 60,
                "etime": f"00:{pid - 200:02d}",
                "elapsed_seconds": pid - 200,
                "command": f"cargo test helper {pid}",
                "lineage_depth": 0,
                "match_source": "direct",
            }
            for pid in range(201, 216)
        ]
        collect_mock.return_value = _state(
            rows=[orphan_root, orphan_child_recent, *skipped_recent_rows],
            orphaned_rows=[orphan_root],
            active_recent_rows=[orphan_child_recent, *skipped_recent_rows],
        )
        args = build_parser().parse_args(["process-cleanup", "--dry-run", "--format", "md"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 0)
        markdown = write_output_mock.call_args.args[0]
        self.assertIn("- active_recent_pre: 16", markdown)
        self.assertIn("- ... 3 more recent active processes", markdown)
        self.assertNotIn("- ... 4 more recent active processes", markdown)

    @mock.patch("dev.scripts.devctl.commands.process_cleanup.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.process_cleanup.collect_process_audit_state"
    )
    def test_run_fails_when_host_scan_is_unavailable(
        self,
        collect_mock,
        write_output_mock,
    ) -> None:
        collect_mock.return_value = _state(
            scan_warnings=["Process sweep skipped: ps returned 1 (denied)"]
        )
        args = build_parser().parse_args(["process-cleanup", "--format", "json"])

        rc = process_cleanup.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("Host process cleanup unavailable", payload["errors"][0])
