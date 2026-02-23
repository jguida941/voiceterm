"""Tests for devctl security command behavior."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import security


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "min_cvss": 7.0,
        "fail_on_kind": None,
        "allowlist_file": "dev/security/rustsec_allowlist.md",
        "allow_unknown_severity": False,
        "rustsec_output": "rustsec-audit.json",
        "with_zizmor": False,
        "require_optional_tools": False,
        "dry_run": False,
        "offline": False,
        "cargo_home": None,
        "cargo_target_dir": None,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def rustsec_ok_step() -> dict:
    return {
        "name": "rustsec-audit",
        "cmd": ["cargo", "audit", "--json"],
        "cwd": ".",
        "returncode": 0,
        "duration_s": 0.02,
        "skipped": False,
        "details": {"report_path": "rustsec-audit.json", "cargo_audit_exit_code": 0},
    }


class SecurityCommandTests(unittest.TestCase):
    """Validate parser wiring and security command step behavior."""

    def test_cli_accepts_security_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "security",
                "--with-zizmor",
                "--require-optional-tools",
                "--min-cvss",
                "8.5",
                "--offline",
                "--cargo-home",
                "/tmp/cargo-home",
            ]
        )
        self.assertEqual(args.command, "security")
        self.assertTrue(args.with_zizmor)
        self.assertTrue(args.require_optional_tools)
        self.assertEqual(args.min_cvss, 8.5)
        self.assertTrue(args.offline)
        self.assertEqual(args.cargo_home, "/tmp/cargo-home")

    @patch("dev.scripts.devctl.commands.security.write_output")
    @patch("dev.scripts.devctl.commands.security.run_cmd")
    @patch("dev.scripts.devctl.commands.security._run_rustsec_audit_step")
    def test_run_uses_default_fail_on_kinds_for_policy(
        self,
        audit_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        audit_mock.return_value = (rustsec_ok_step(), [])
        run_cmd_mock.return_value = {
            "name": "rustsec-policy",
            "cmd": [],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.02,
            "skipped": False,
        }

        rc = security.run(make_args())
        self.assertEqual(rc, 0)

        policy_call = run_cmd_mock.call_args_list[0]
        cmd = policy_call.args[1]
        self.assertIn("--fail-on-kind", cmd)
        self.assertIn("yanked", cmd)
        self.assertIn("unsound", cmd)
        self.assertEqual(policy_call.args[0], "rustsec-policy")
        self.assertTrue(write_output_mock.called)

    @patch("dev.scripts.devctl.commands.security.shutil.which", return_value=None)
    @patch("dev.scripts.devctl.commands.security.write_output")
    @patch("dev.scripts.devctl.commands.security.run_cmd")
    @patch("dev.scripts.devctl.commands.security._run_rustsec_audit_step")
    def test_run_skips_missing_optional_tool_when_not_required(
        self,
        audit_mock,
        run_cmd_mock,
        write_output_mock,
        _which_mock,
    ) -> None:
        audit_mock.return_value = (rustsec_ok_step(), [])
        run_cmd_mock.return_value = {
            "name": "rustsec-policy",
            "cmd": [],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }

        rc = security.run(make_args(with_zizmor=True, require_optional_tools=False))
        self.assertEqual(rc, 0)

        output = write_output_mock.call_args.args[0]
        report = json.loads(output)
        self.assertTrue(any("zizmor is not installed" in item for item in report["warnings"]))
        zizmor_step = next(step for step in report["steps"] if step["name"] == "zizmor")
        self.assertTrue(zizmor_step["skipped"])
        self.assertEqual(zizmor_step["returncode"], 0)

    @patch("dev.scripts.devctl.commands.security.shutil.which", return_value=None)
    @patch("dev.scripts.devctl.commands.security.write_output")
    @patch("dev.scripts.devctl.commands.security.run_cmd")
    @patch("dev.scripts.devctl.commands.security._run_rustsec_audit_step")
    def test_run_fails_when_optional_tool_missing_and_required(
        self,
        audit_mock,
        run_cmd_mock,
        write_output_mock,
        _which_mock,
    ) -> None:
        audit_mock.return_value = (rustsec_ok_step(), [])
        run_cmd_mock.return_value = {
            "name": "rustsec-policy",
            "cmd": [],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }

        rc = security.run(make_args(with_zizmor=True, require_optional_tools=True))
        self.assertEqual(rc, 1)

        output = write_output_mock.call_args.args[0]
        report = json.loads(output)
        zizmor_step = next(step for step in report["steps"] if step["name"] == "zizmor")
        self.assertFalse(zizmor_step["skipped"])
        self.assertEqual(zizmor_step["returncode"], 127)
        self.assertIn("not installed", zizmor_step["error"])

    @patch("dev.scripts.devctl.commands.security.write_output")
    @patch("dev.scripts.devctl.commands.security.run_cmd")
    @patch("dev.scripts.devctl.commands.security._run_rustsec_audit_step")
    def test_run_skips_policy_when_rustsec_audit_fails(
        self,
        audit_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        audit_mock.return_value = (
            {
                "name": "rustsec-audit",
                "cmd": ["cargo", "audit", "--json"],
                "cwd": ".",
                "returncode": 2,
                "duration_s": 0.01,
                "skipped": False,
                "error": "cargo audit failed",
            },
            [],
        )

        rc = security.run(make_args())
        self.assertEqual(rc, 1)
        run_cmd_mock.assert_not_called()

        output = write_output_mock.call_args.args[0]
        report = json.loads(output)
        policy_step = next(step for step in report["steps"] if step["name"] == "rustsec-policy")
        self.assertTrue(policy_step["skipped"])


if __name__ == "__main__":
    unittest.main()
