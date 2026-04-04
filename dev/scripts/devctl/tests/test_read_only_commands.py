"""Tests verifying read-only commands skip audit events and telemetry refresh."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from dev.scripts.devctl import cli
from dev.scripts.devctl.cli import READ_ONLY_COMMANDS


class ReadOnlyCommandSetTests(unittest.TestCase):
    """Sanity checks on the READ_ONLY_COMMANDS constant."""

    def test_known_read_only_commands_present(self) -> None:
        expected = {
            "startup-context",
            "context-graph",
            "review-channel",
            "quality-policy",
            "platform-contracts",
            "mcp",
            "dashboard",
            "list",
        }
        self.assertEqual(set(READ_ONLY_COMMANDS), expected)

    def test_read_only_commands_is_frozenset(self) -> None:
        self.assertIsInstance(READ_ONLY_COMMANDS, frozenset)

    def test_write_commands_not_in_read_only(self) -> None:
        write_commands = {"check", "push", "triage", "ship", "release"}
        for cmd in write_commands:
            self.assertNotIn(cmd, READ_ONLY_COMMANDS)


class ReadOnlyAuditSkipTests(unittest.TestCase):
    """Verify read-only commands do not write audit events or trigger telemetry."""

    def test_list_skips_audit_and_telemetry(self) -> None:
        """The 'list' command should not write to the audit log or refresh telemetry."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "devctl-events.jsonl"
            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(log_path),
                    "DEVCTL_DATA_SCIENCE_DISABLE": "1",
                },
                clear=False,
            ):
                with patch("sys.argv", ["devctl", "list"]):
                    rc = cli.main()

            self.assertEqual(rc, 0)
            # Audit log should not exist because read-only commands skip writes
            self.assertFalse(
                log_path.exists(),
                "read-only command 'list' should not create audit event log",
            )

    def test_dashboard_skips_audit_and_telemetry(self) -> None:
        """Dashboard is read-only; verify no audit write or telemetry refresh."""
        mock_telemetry = MagicMock()
        mock_handler = MagicMock(return_value=0)
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "devctl-events.jsonl"
            with patch.dict(
                "os.environ",
                {"DEVCTL_AUDIT_EVENT_LOG": str(log_path)},
                clear=False,
            ):
                with patch(
                    "dev.scripts.devctl.cli.maybe_auto_refresh_data_science",
                    mock_telemetry,
                ):
                    with patch.dict(
                        cli.COMMAND_HANDLERS,
                        {"dashboard": mock_handler},
                    ):
                        with patch("sys.argv", ["devctl", "dashboard", "--format", "json"]):
                            rc = cli.main()

            self.assertEqual(rc, 0)
            mock_handler.assert_called_once()
            self.assertFalse(
                log_path.exists(),
                "read-only command 'dashboard' should not create audit event log",
            )
            mock_telemetry.assert_not_called()

    def test_write_command_still_emits_audit(self) -> None:
        """Non-read-only commands should still write audit events normally."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "devctl-events.jsonl"
            with patch.dict(
                "os.environ",
                {
                    "DEVCTL_AUDIT_EVENT_LOG": str(log_path),
                    "DEVCTL_AUDIT_CYCLE_ID": "write-test",
                    "DEVCTL_DATA_SCIENCE_DISABLE": "1",
                },
                clear=False,
            ):
                with patch("sys.argv", ["devctl", "status", "--format", "json"]):
                    cli.main()

            self.assertTrue(
                log_path.exists(),
                "write command 'status' should still emit audit events",
            )
            rows = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(rows), 1)
            last_row = json.loads(rows[-1])
            self.assertEqual(last_row["command"], "status")


if __name__ == "__main__":
    unittest.main()
