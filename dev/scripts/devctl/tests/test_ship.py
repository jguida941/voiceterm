"""Tests for devctl ship release/distribution safety guards."""

import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.commands import release_guard, ship, ship_common, ship_steps


def make_args() -> SimpleNamespace:
    return SimpleNamespace(
        version="1.2.3",
        prepare_release=False,
        verify=False,
        verify_docs=False,
        tag=False,
        notes=False,
        github=False,
        github_fail_on_no_commits=False,
        pypi=False,
        homebrew=False,
        verify_pypi=False,
        notes_output=None,
        yes=True,
        allow_ci=True,
        dry_run=True,
        format="text",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


class ShipReleaseParityTests(TestCase):
    def test_ship_selected_steps_puts_prepare_first(self) -> None:
        args = make_args()
        args.prepare_release = True
        args.verify = True
        args.tag = True
        self.assertEqual(
            ship._selected_steps(args), ["prepare-release", "verify", "tag"]
        )

    def test_check_release_version_parity_matches_requested_version(self) -> None:
        payload = {"ok": True, "versions_present": ["1.2.3"], "missing": []}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        with patch(
            "dev.scripts.devctl.commands.release_guard.subprocess.run",
            return_value=completed,
        ):
            ok, details = release_guard.check_release_version_parity("1.2.3")

        self.assertTrue(ok)
        self.assertEqual(details["version"], "1.2.3")

    def test_check_release_version_parity_rejects_mismatched_requested_version(
        self,
    ) -> None:
        payload = {"ok": True, "versions_present": ["2.0.0"], "missing": []}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        with patch(
            "dev.scripts.devctl.commands.release_guard.subprocess.run",
            return_value=completed,
        ):
            ok, details = release_guard.check_release_version_parity("1.2.3")

        self.assertFalse(ok)
        self.assertEqual(
            details["reason"], "requested version does not match release metadata"
        )

    def test_run_verify_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship_steps.run_verify_step(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "verify")
        self.assertEqual(
            result["details"]["reason"], "release version parity check failed"
        )

    def test_run_verify_dry_run_prepare_release_skips_expected_parity_mismatch(
        self,
    ) -> None:
        args = make_args()
        args.dry_run = True
        args.prepare_release = True
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(
                False,
                {
                    "reason": "requested version does not match release metadata",
                    "requested": "1.2.3",
                    "detected": "1.2.2",
                },
            ),
        ):
            result = ship_steps.run_verify_step(args, context)

        self.assertTrue(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["name"], "verify")

    @patch("dev.scripts.devctl.commands.ship_steps.run_cmd")
    def test_run_verify_fails_when_coderabbit_gate_fails(self, run_cmd_mock) -> None:
        args = make_args()
        args.dry_run = False
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        run_cmd_mock.return_value = {
            "name": "coderabbit-gate",
            "cmd": [
                "python3",
                "dev/scripts/checks/check_coderabbit_gate.py",
                "--format",
                "json",
            ],
            "cwd": ".",
            "returncode": 1,
            "duration_s": 0.01,
            "skipped": False,
            "error": "gate failed",
        }
        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(True, {"version": "1.2.3"}),
        ):
            result = ship_steps.run_verify_step(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "verify")
        self.assertEqual(result["details"]["failed_substep"], "coderabbit-gate")
        self.assertEqual(result["details"]["reason"], "gate failed")

    @patch("dev.scripts.devctl.commands.ship_steps.run_cmd")
    def test_run_verify_checks_coderabbit_gate_first(self, run_cmd_mock) -> None:
        args = make_args()
        args.dry_run = False
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        run_cmd_mock.return_value = {
            "name": "ok",
            "cmd": [],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }
        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(True, {"version": "1.2.3"}),
        ):
            result = ship_steps.run_verify_step(args, context)

        self.assertTrue(result["ok"])
        first_call = run_cmd_mock.call_args_list[0]
        self.assertEqual(first_call.args[0], "coderabbit-gate")
        self.assertIn("dev/scripts/checks/check_coderabbit_gate.py", first_call.args[1])
        self.assertIn("--branch", first_call.args[1])
        self.assertIn("master", first_call.args[1])
        second_call = run_cmd_mock.call_args_list[1]
        self.assertEqual(second_call.args[0], "coderabbit-ralph-gate")
        self.assertIn(
            "dev/scripts/checks/check_coderabbit_ralph_gate.py", second_call.args[1]
        )
        self.assertIn("--branch", second_call.args[1])
        self.assertIn("master", second_call.args[1])

    def test_run_pypi_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship_steps.run_pypi_step(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "pypi")
        self.assertEqual(
            result["details"]["reason"], "release version parity check failed"
        )

    def test_run_pypi_dry_run_prepare_release_skips_expected_parity_mismatch(
        self,
    ) -> None:
        args = make_args()
        args.dry_run = True
        args.prepare_release = True
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(
                False,
                {
                    "reason": "requested version does not match release metadata",
                    "requested": "1.2.3",
                    "detected": "1.2.2",
                },
            ),
        ):
            result = ship_steps.run_pypi_step(args, context)

        self.assertTrue(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["name"], "pypi")

    def test_run_homebrew_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship_steps.run_homebrew_step(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "homebrew")
        self.assertEqual(
            result["details"]["reason"], "release version parity check failed"
        )

    def test_run_homebrew_dry_run_prepare_release_skips_expected_parity_mismatch(
        self,
    ) -> None:
        args = make_args()
        args.dry_run = True
        args.prepare_release = True
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship_steps.check_release_version_parity",
            return_value=(
                False,
                {
                    "reason": "requested version does not match release metadata",
                    "requested": "1.2.3",
                    "detected": "1.2.2",
                },
            ),
        ):
            result = ship_steps.run_homebrew_step(args, context)

        self.assertTrue(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["name"], "homebrew")

    @patch(
        "dev.scripts.devctl.commands.ship_common.subprocess.check_output",
        side_effect=FileNotFoundError("missing"),
    )
    def test_run_checked_returns_structured_error_when_binary_missing(
        self, _mock_check_output
    ) -> None:
        code, output = ship_common.run_checked(["definitely-missing-binary"])
        self.assertEqual(code, 127)
        self.assertIn("missing", output)

    @patch("dev.scripts.devctl.commands.ship_steps.prepare_release_metadata")
    def test_run_prepare_release_step_returns_success_details(
        self, mock_prepare_release_metadata
    ) -> None:
        args = make_args()
        args.dry_run = False
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}
        mock_prepare_release_metadata.return_value = {
            "version": "1.2.3",
            "release_date": "2026-02-23",
            "changed_files": ["src/Cargo.toml"],
            "unchanged_files": [],
            "dry_run": False,
        }

        result = ship_steps.run_prepare_release_step(args, context)
        self.assertTrue(result["ok"])
        self.assertEqual(result["name"], "prepare-release")
        self.assertIn("changed_files", result["details"])

    @patch(
        "dev.scripts.devctl.commands.ship_steps.prepare_release_metadata",
        side_effect=RuntimeError("boom"),
    )
    def test_run_prepare_release_step_surfaces_failures(
        self, _mock_prepare_release_metadata
    ) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        result = ship_steps.run_prepare_release_step(args, context)
        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "prepare-release")
        self.assertEqual(result["details"]["reason"], "boom")
