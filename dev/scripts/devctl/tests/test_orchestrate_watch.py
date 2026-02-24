"""Tests for devctl orchestrate-watch command behavior."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import orchestrate_watch


class _DummyPath:
    def __init__(self, text: str) -> None:
        self._text = text

    def read_text(self, encoding: str = "utf-8") -> str:  # noqa: ARG002
        return self._text


def _utc(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _master_row(agent: str, status: str, last_update: str) -> dict:
    return {
        "Agent": agent,
        "Status": status,
        "Last update (UTC)": last_update,
    }


def _instruction_row(
    instruction_id: str,
    due_utc: str,
    status: str,
    ack_token: str = "pending",
) -> dict:
    return {
        "Instruction ID": instruction_id,
        "To": "AGENT-1",
        "Due (UTC)": due_utc,
        "Status": status,
        "Ack token": ack_token,
    }


class OrchestrateWatchCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.orchestrate_watch.write_output")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.collect_git_status")
    @patch(
        "dev.scripts.devctl.commands.orchestrate_watch._run_multi_agent_sync_gate",
        return_value={"ok": True, "errors": [], "warnings": []},
    )
    @patch(
        "dev.scripts.devctl.commands.orchestrate_watch._run_active_plan_sync_gate",
        return_value={"ok": True, "errors": []},
    )
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync._extract_table_rows")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync.MASTER_PLAN_PATH")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync.RUNBOOK_PATH")
    def test_watch_passes_with_fresh_updates(
        self,
        runbook_path_mock,
        master_plan_path_mock,
        extract_table_rows_mock,
        _active_sync_mock,
        _multi_sync_mock,
        collect_git_status_mock,
        write_output_mock,
    ) -> None:
        now = datetime.now(timezone.utc)
        master_plan_path_mock.read_text.return_value = "master"
        runbook_path_mock.read_text.return_value = "runbook"
        extract_table_rows_mock.side_effect = [
            (
                [
                    _master_row("AGENT-1", "in-progress", _utc(now - timedelta(minutes=5))),
                    _master_row("AGENT-2", "planned", _utc(now - timedelta(minutes=4))),
                    _master_row("AGENT-3", "planned", _utc(now - timedelta(minutes=3))),
                ],
                None,
            ),
            (
                [
                    _instruction_row(
                        "INS-1",
                        _utc(now - timedelta(minutes=1)),
                        "completed",
                        ack_token="ACK-AGENT-1",
                    )
                ],
                None,
            ),
        ]
        collect_git_status_mock.return_value = {"branch": "develop", "changes": []}
        args = SimpleNamespace(
            stale_minutes=30,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = orchestrate_watch.run(args)

        self.assertEqual(code, 0)
        output = write_output_mock.call_args.args[0]
        self.assertIn("- ok: True", output)
        self.assertIn("- stale_agent_count: 0", output)

    @patch("dev.scripts.devctl.commands.orchestrate_watch.write_output")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.collect_git_status")
    @patch(
        "dev.scripts.devctl.commands.orchestrate_watch._run_multi_agent_sync_gate",
        return_value={"ok": True, "errors": [], "warnings": []},
    )
    @patch(
        "dev.scripts.devctl.commands.orchestrate_watch._run_active_plan_sync_gate",
        return_value={"ok": True, "errors": []},
    )
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync._extract_table_rows")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync.MASTER_PLAN_PATH")
    @patch("dev.scripts.devctl.commands.orchestrate_watch.check_multi_agent_sync.RUNBOOK_PATH")
    def test_watch_fails_for_stale_agent_and_overdue_ack(
        self,
        runbook_path_mock,
        master_plan_path_mock,
        extract_table_rows_mock,
        _active_sync_mock,
        _multi_sync_mock,
        collect_git_status_mock,
        write_output_mock,
    ) -> None:
        now = datetime.now(timezone.utc)
        master_plan_path_mock.read_text.return_value = "master"
        runbook_path_mock.read_text.return_value = "runbook"
        extract_table_rows_mock.side_effect = [
            (
                [
                    _master_row("AGENT-1", "in-progress", _utc(now - timedelta(minutes=95))),
                    _master_row("AGENT-2", "planned", _utc(now - timedelta(minutes=4))),
                    _master_row("AGENT-3", "planned", _utc(now - timedelta(minutes=3))),
                ],
                None,
            ),
            (
                [
                    _instruction_row(
                        "INS-OVERDUE",
                        _utc(now - timedelta(minutes=10)),
                        "pending",
                        ack_token="pending",
                    )
                ],
                None,
            ),
        ]
        collect_git_status_mock.return_value = {"branch": "develop", "changes": []}
        args = SimpleNamespace(
            stale_minutes=30,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = orchestrate_watch.run(args)

        self.assertEqual(code, 1)
        output = write_output_mock.call_args.args[0]
        self.assertIn("stale update", output)
        self.assertIn("overdue without ACK", output)


if __name__ == "__main__":
    unittest.main()
