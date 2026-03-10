"""Tests for devctl mobile-app parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands import mobile_app


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "action": "list-devices",
        "device_id": None,
        "open_xcode": True,
        "dry_run": False,
        "live_review": False,
        "development_team": None,
        "allow_provisioning_updates": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class MobileAppParserTests(unittest.TestCase):
    def test_cli_accepts_mobile_app_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "mobile-app",
                "--action",
                "device-install",
                "--device-id",
                "device-123",
                "--development-team",
                "TEAM12345",
                "--allow-provisioning-updates",
                "--live-review",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "mobile-app")
        self.assertEqual(args.action, "device-install")
        self.assertEqual(args.device_id, "device-123")
        self.assertEqual(args.development_team, "TEAM12345")
        self.assertTrue(args.allow_provisioning_updates)
        self.assertTrue(args.live_review)
        self.assertEqual(args.format, "json")

    def test_cli_dispatch_uses_mobile_app_handler(self) -> None:
        self.assertIs(COMMAND_HANDLERS["mobile-app"], mobile_app.run)


class MobileAppCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.mobile_app.list_available_simulators")
    @patch("dev.scripts.devctl.commands.mobile_app.list_physical_devices")
    def test_list_devices_reports_both_kinds(
        self,
        list_physical_devices_mock,
        list_available_simulators_mock,
    ) -> None:
        list_available_simulators_mock.return_value = [
            {"name": "iPhone 15", "identifier": "SIM-1", "state": "Shutdown"}
        ]
        list_physical_devices_mock.return_value = [
            {"name": "John iPhone", "runtime": "18.0", "identifier": "DEV-1"}
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(output=str(output_path))
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["action"], "list-devices")
        self.assertEqual(len(payload["result"]["simulators"]), 1)
        self.assertEqual(len(payload["result"]["devices"]), 1)

    @patch("dev.scripts.devctl.commands.mobile_app.run_cmd")
    @patch("dev.scripts.devctl.commands.mobile_app.select_simulator")
    def test_simulator_demo_runs_guided_script(
        self,
        select_simulator_mock,
        run_cmd_mock,
    ) -> None:
        select_simulator_mock.return_value = "SIM-123"
        run_cmd_mock.return_value = {
            "name": "mobile-app-simulator-demo",
            "returncode": 0,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(action="simulator-demo", output=str(output_path))
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["selected_device_id"], "SIM-123")
        run_cmd_mock.assert_called_once()

    @patch("dev.scripts.devctl.commands.mobile_app.run_cmd")
    @patch("dev.scripts.devctl.commands.mobile_app.select_simulator")
    def test_simulator_demo_refreshes_review_state_in_live_review_mode(
        self,
        select_simulator_mock,
        run_cmd_mock,
    ) -> None:
        select_simulator_mock.return_value = "SIM-123"
        run_cmd_mock.side_effect = [
            {"name": "mobile-app-review-status", "returncode": 0},
            {"name": "mobile-app-simulator-demo", "returncode": 0},
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(
                action="simulator-demo",
                output=str(output_path),
                live_review=True,
            )
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["result"]["live_review"])
        self.assertEqual(run_cmd_mock.call_count, 2)

    @patch("dev.scripts.devctl.commands.mobile_app.run_cmd")
    @patch("dev.scripts.devctl.commands.mobile_app.list_physical_devices")
    def test_device_wizard_opens_xcode_when_requested(
        self,
        list_physical_devices_mock,
        run_cmd_mock,
    ) -> None:
        list_physical_devices_mock.return_value = [
            {"name": "John iPhone", "runtime": "18.0", "identifier": "DEV-1"}
        ]
        run_cmd_mock.return_value = {
            "name": "mobile-app-open-xcode",
            "returncode": 0,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(
                action="device-wizard",
                output=str(output_path),
            )
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["result"]["devices"]), 1)
        self.assertIn("wizard_steps", payload["result"])

    @patch("dev.scripts.devctl.commands.mobile_app.resolve_development_team")
    @patch("dev.scripts.devctl.commands.mobile_app.select_physical_device")
    @patch("dev.scripts.devctl.commands.mobile_app.list_physical_devices")
    def test_device_install_requires_team(
        self,
        list_physical_devices_mock,
        select_physical_device_mock,
        resolve_development_team_mock,
    ) -> None:
        list_physical_devices_mock.return_value = [
            {"name": "John iPhone", "runtime": "18.0", "identifier": "DEV-1"}
        ]
        select_physical_device_mock.return_value = "DEV-1"
        resolve_development_team_mock.return_value = None
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(action="device-install", output=str(output_path))
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("no Apple Development Team configured", payload["errors"][0])

    @patch("dev.scripts.devctl.commands.mobile_app.run_cmd")
    @patch("dev.scripts.devctl.commands.mobile_app.resolve_development_team")
    @patch("dev.scripts.devctl.commands.mobile_app.select_physical_device")
    @patch("dev.scripts.devctl.commands.mobile_app.list_physical_devices")
    def test_device_install_runs_build_install_and_launch(
        self,
        list_physical_devices_mock,
        select_physical_device_mock,
        resolve_development_team_mock,
        run_cmd_mock,
    ) -> None:
        list_physical_devices_mock.return_value = [
            {"name": "John iPhone", "runtime": "18.0", "identifier": "DEV-1"}
        ]
        select_physical_device_mock.return_value = "DEV-1"
        resolve_development_team_mock.return_value = "TEAM12345"
        run_cmd_mock.side_effect = [
            {"name": "mobile-app-device-build", "returncode": 0},
            {"name": "mobile-app-device-install", "returncode": 0},
            {"name": "mobile-app-device-launch", "returncode": 0},
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "report.json"
            args = make_args(
                action="device-install",
                output=str(output_path),
                development_team="TEAM12345",
                allow_provisioning_updates=True,
            )
            rc = mobile_app.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["selected_device_id"], "DEV-1")
        self.assertEqual(payload["result"]["development_team"], "TEAM12345")
        self.assertEqual(run_cmd_mock.call_count, 3)
