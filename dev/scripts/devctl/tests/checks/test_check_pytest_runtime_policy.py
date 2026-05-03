from __future__ import annotations

from unittest.mock import patch

from dev.scripts.checks.pytest_runtime_policy import command as guard


def test_raw_pytest_bundle_command_is_violation() -> None:
    assert guard._is_unbounded_pytest_command("python3 -m pytest tests -q")


def test_devctl_test_python_bundle_command_is_allowed() -> None:
    command = "python3 dev/scripts/devctl.py test-python --suite operator-console"

    assert not guard._is_unbounded_pytest_command(command)


def test_bundle_report_flags_raw_pytest_command() -> None:
    with patch.object(
        guard,
        "_bundle_registry",
        return_value={
            "bundle.tooling": ("python3 -m pytest app/operator_console/tests -q",)
        },
    ), patch.object(guard, "_config_violations", return_value=[]):
        report = guard.build_report()

    assert not report["ok"]
    assert report["violations"] == [
        {
            "kind": "raw_pytest_bundle_command",
            "bundle": "bundle.tooling",
            "command": "python3 -m pytest app/operator_console/tests -q",
        }
    ]
