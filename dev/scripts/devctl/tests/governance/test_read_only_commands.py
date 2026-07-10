"""Tests verifying read-only commands skip audit events and telemetry refresh.

Moved from tests/test_read_only_commands.py to reduce root test directory
crowding and align with the governance test package that already covers
startup-context and context-graph behavior.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from dev.scripts.devctl import cli
from dev.scripts.devctl.cli import ARTIFACT_WRITES_ENV, READ_ONLY_COMMANDS
from dev.scripts.devctl.cli_parser.artifact_suppression import (
    read_only_command_suppresses_artifact_writes,
)


class ReadOnlyCommandSetTests(unittest.TestCase):
    """Sanity checks on the READ_ONLY_COMMANDS constant."""

    def test_known_read_only_commands_present(self) -> None:
        expected = {
            "auto-mode",
            "startup-context",
            "session",
            "session-resume",
            "context-graph",
            "develop",
            "demo",
            "exceptions",
            "review-channel",
            "quality-policy",
            "orphan-inventory",
            "platform-contracts",
            "system-map",
            "mcp",
            "dashboard",
            "claude-loop",
            "agent-loop",
            "agent-supervise",
            "discover",
            "findings-priority",
            "progress-status",
            "graph-walk",
            "view",
            "list",
            "rollout-tail",
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


class ArtifactWriteSuppressionTests(unittest.TestCase):
    """Verify in-handler artifact writes are suppressed for read-only commands."""

    def test_env_var_set_for_read_only_commands(self) -> None:
        """cli.main() sets DEVCTL_NO_ARTIFACT_WRITES=1 for READ_ONLY_COMMANDS."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(cli.COMMAND_HANDLERS, {"list": spy_handler}):
            with patch("sys.argv", ["devctl", "list"]):
                cli.main()

        self.assertEqual(captured_env.get("val"), "1")

    def test_context_graph_bootstrap_does_not_auto_suppress_artifacts(self) -> None:
        """Bootstrap graph snapshots are the command's managed freshness artifact."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ARTIFACT_WRITES_ENV, None)
            with patch("dev.scripts.devctl.cli.enforce_startup_gate", return_value=None):
                with patch.dict(cli.COMMAND_HANDLERS, {"context-graph": spy_handler}):
                    with patch("sys.argv", ["devctl", "context-graph", "--mode", "bootstrap"]):
                        cli.main()

        self.assertEqual(captured_env.get("val"), "")

    def test_session_does_not_suppress_orientation_child_artifacts(self) -> None:
        """The session orientation graph child must be able to save its snapshot."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ARTIFACT_WRITES_ENV, None)
            with patch("dev.scripts.devctl.cli.enforce_startup_gate", return_value=None):
                with patch.dict(cli.COMMAND_HANDLERS, {"session": spy_handler}):
                    with patch(
                        "sys.argv",
                        ["devctl", "session", "--role", "implementer"],
                    ):
                        cli.main()

        self.assertEqual(captured_env.get("val"), "")

    def test_review_channel_show_does_not_auto_suppress_body_observation_write(self) -> None:
        args = SimpleNamespace(command="review-channel", action="show")

        self.assertFalse(
            read_only_command_suppresses_artifact_writes(args, READ_ONLY_COMMANDS)
        )

    def test_review_channel_history_still_suppresses_artifact_writes(self) -> None:
        args = SimpleNamespace(command="review-channel", action="history")

        self.assertTrue(
            read_only_command_suppresses_artifact_writes(args, READ_ONLY_COMMANDS)
        )

    def test_develop_drain_packets_does_not_auto_suppress_artifacts(self) -> None:
        """Packet-drain mode is an explicit managed sink behind /develop."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ARTIFACT_WRITES_ENV, None)
            with patch("dev.scripts.devctl.cli.enforce_startup_gate", return_value=None):
                with patch.dict(cli.COMMAND_HANDLERS, {"develop": spy_handler}):
                    with patch(
                        "sys.argv",
                        ["devctl", "develop", "audit-packets", "--drain-packets"],
                    ):
                        cli.main()

        self.assertEqual(captured_env.get("val"), "")

    def test_exceptions_request_is_not_slice_one_command(self) -> None:
        """Slice 1 exposes only read-only pending/validate actions."""
        with patch("sys.argv", ["devctl", "exceptions", "request"]):
            with self.assertRaises(SystemExit):
                cli.main()

    def test_context_graph_bootstrap_respects_external_suppression(self) -> None:
        """Explicit DEVCTL_NO_ARTIFACT_WRITES=1 still suppresses bootstrap writes."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(os.environ, {ARTIFACT_WRITES_ENV: "1"}, clear=False):
            with patch("dev.scripts.devctl.cli.enforce_startup_gate", return_value=None):
                with patch.dict(cli.COMMAND_HANDLERS, {"context-graph": spy_handler}):
                    with patch("sys.argv", ["devctl", "context-graph", "--mode", "bootstrap"]):
                        cli.main()

        self.assertEqual(captured_env.get("val"), "1")

    def test_env_var_cleared_after_handler(self) -> None:
        """The suppression env var is cleaned up after the handler returns."""
        with patch.dict(cli.COMMAND_HANDLERS, {"list": lambda _: 0}):
            with patch("sys.argv", ["devctl", "list"]):
                cli.main()

        self.assertNotIn(ARTIFACT_WRITES_ENV, os.environ)

    def test_env_var_not_set_for_write_commands(self) -> None:
        """Write commands must NOT suppress artifact writes."""
        captured_env: dict[str, str] = {}

        def spy_handler(_args):
            captured_env["val"] = os.environ.get(ARTIFACT_WRITES_ENV, "")
            return 0

        with patch.dict(
            "os.environ",
            {"DEVCTL_DATA_SCIENCE_DISABLE": "1"},
            clear=False,
        ):
            with patch.dict(cli.COMMAND_HANDLERS, {"status": spy_handler}):
                with patch("sys.argv", ["devctl", "status", "--format", "json"]):
                    cli.main()

        self.assertNotEqual(captured_env.get("val"), "1")

    def test_external_suppression_skips_machine_output_receipt_for_write_command(self) -> None:
        """DEVCTL_NO_ARTIFACT_WRITES also suppresses dispatcher ledger receipts."""

        def spy_handler(_args):
            return 0

        metrics = {
            "command": "status",
            "delivery": "stdout",
            "format": "json",
            "size_bytes": 10,
            "estimated_tokens": 3,
            "sha256": "a" * 64,
            "path": "",
            "summary_keys": [],
        }
        with patch.dict(
            os.environ,
            {
                ARTIFACT_WRITES_ENV: "1",
                "DEVCTL_DATA_SCIENCE_DISABLE": "1",
            },
            clear=False,
        ):
            with (
                patch("dev.scripts.devctl.cli.enforce_startup_gate", return_value=None),
                patch.dict(cli.COMMAND_HANDLERS, {"status": spy_handler}),
                patch(
                    "dev.scripts.devctl.cli.consume_machine_output_metrics",
                    return_value=metrics,
                ),
                patch(
                    "dev.scripts.devctl.cli.append_artifact_receipt_record"
                ) as append_mock,
                patch("sys.argv", ["devctl", "status", "--format", "json"]),
            ):
                cli.main()

        append_mock.assert_not_called()

    def test_startup_context_writes_receipt_even_when_suppressed(self) -> None:
        """startup-context must still write the receipt under suppression.

        The receipt is the command's primary output — the launcher validates
        it to gate subsequent actions.  Only a true read-only filesystem
        (OSError) should prevent the write.
        """
        from dev.scripts.devctl.commands.governance import startup_context as sc_mod

        mock_write = MagicMock(return_value=Path("/fake/receipt.json"))
        mock_ctx = MagicMock()
        mock_ctx.to_dict.return_value = {
            "reviewer_gate": {"reviewer_mode": "single_agent"},
            "push_decision": MagicMock(
                action="no_push_needed",
                publication_backlog=MagicMock(backlog_urgent=False),
                publication_guidance="",
            ),
            "governance": None,
        }
        mock_receipt = MagicMock()
        mock_receipt.head_commit_sha = "abc123"

        with patch.dict(os.environ, {ARTIFACT_WRITES_ENV: "1"}):
            with (
                patch.object(sc_mod, "build_startup_context", return_value=mock_ctx),
                patch.object(sc_mod, "build_startup_receipt", return_value=mock_receipt),
                patch.object(sc_mod, "write_startup_receipt", mock_write),
                patch.object(sc_mod, "build_startup_authority_report", return_value={"ok": True}),
                patch.object(sc_mod, "emit_machine_artifact_output", return_value=0),
            ):
                sc_mod.run(SimpleNamespace(
                    format="json",
                    role=None,
                    reviewer_override=False,
                    apply_safe_fixes=False,
                    repair=False,
                ))

        mock_write.assert_called_once()

    def test_startup_context_degrades_on_read_only_filesystem(self) -> None:
        """On a truly read-only filesystem, the receipt write degrades gracefully."""
        from dev.scripts.devctl.commands.governance import startup_context as sc_mod

        mock_write = MagicMock(side_effect=OSError("read-only filesystem"))
        mock_ctx = MagicMock()
        mock_ctx.to_dict.return_value = {
            "reviewer_gate": {"reviewer_mode": "single_agent"},
            "push_decision": MagicMock(
                action="no_push_needed",
                publication_backlog=MagicMock(backlog_urgent=False),
                publication_guidance="",
            ),
            "governance": None,
        }
        mock_receipt = MagicMock()
        mock_receipt.head_commit_sha = "abc123"

        with patch.dict(os.environ, {ARTIFACT_WRITES_ENV: "1"}):
            with (
                patch.object(sc_mod, "build_startup_context", return_value=mock_ctx),
                patch.object(sc_mod, "build_startup_receipt", return_value=mock_receipt),
                patch.object(sc_mod, "write_startup_receipt", mock_write),
                patch.object(
                    sc_mod,
                    "startup_receipt_path",
                    return_value=Path("/fake/receipt.json"),
                ),
                patch.object(sc_mod, "build_startup_authority_report", return_value={"ok": True}),
                patch.object(sc_mod, "emit_machine_artifact_output", return_value=0),
            ):
                sc_mod.run(SimpleNamespace(
                    format="json",
                    role=None,
                    reviewer_override=False,
                    apply_safe_fixes=False,
                    repair=False,
                ))

        mock_write.assert_called_once()

    def test_context_graph_skips_snapshot_in_bootstrap_when_suppressed(self) -> None:
        """context-graph bootstrap must not write a snapshot under suppression."""
        from dev.scripts.devctl.context_graph.command import _maybe_write_snapshot

        args = SimpleNamespace(save_snapshot=False)
        with patch.dict(os.environ, {ARTIFACT_WRITES_ENV: "1"}):
            result = _maybe_write_snapshot(args, [], [], "bootstrap")

        self.assertIsNone(result)

    def test_context_graph_explicit_save_overrides_suppression(self) -> None:
        """--save-snapshot still writes even when artifact writes are suppressed."""
        from dev.scripts.devctl.context_graph.command import _maybe_write_snapshot
        from dev.scripts.devctl.context_graph.snapshot import (
            ContextGraphSnapshotReceipt,
            CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
        )

        receipt = ContextGraphSnapshotReceipt(
            path="dev/reports/graph_snapshots/abc.json",
            schema_version=1,
            contract_id=CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
            branch="feature/test",
            commit_hash="abc123",
            generated_at_utc="2026-03-22T16:00:00Z",
            source_mode="query",
            node_count=0,
            edge_count=0,
            temperature_distribution={"average": 0.0, "buckets": {}, "minimum": 0.0, "maximum": 0.0},
        )
        args = SimpleNamespace(save_snapshot=True)
        with patch.dict(os.environ, {ARTIFACT_WRITES_ENV: "1"}):
            with patch(
                "dev.scripts.devctl.context_graph.command.write_context_graph_snapshot",
                return_value=receipt,
            ) as write_mock:
                result = _maybe_write_snapshot(args, [], [], "query")

        write_mock.assert_called_once()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
