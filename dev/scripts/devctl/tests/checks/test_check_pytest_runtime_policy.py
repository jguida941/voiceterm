from __future__ import annotations

from unittest.mock import patch

from dev.scripts.checks.pytest_runtime_policy import bundle_scan, reporting, shell_command


def test_raw_pytest_bundle_command_is_violation() -> None:
    assert shell_command.is_unbounded_pytest_command("python3 -m pytest tests -q")


def test_wrapped_raw_pytest_bundle_command_is_violation() -> None:
    command = "env PYTHONPATH=. python3 -m pytest dev/scripts/devctl/tests -q"

    assert shell_command.is_unbounded_pytest_command(command)


def test_assignment_prefixed_raw_pytest_bundle_command_is_violation() -> None:
    assert shell_command.is_unbounded_pytest_command(
        "CI=1 python3.11 -m pytest tests -q"
    )


def test_env_timeout_wrapped_pytest_binary_is_violation() -> None:
    assert shell_command.is_unbounded_pytest_command(
        "env CI=1 timeout 30 pytest tests -q"
    )


def test_direct_pytest_binary_bundle_command_is_violation() -> None:
    assert shell_command.is_unbounded_pytest_command("uv run pytest tests -q")


def test_run_wrapper_options_before_pytest_binary_are_violation() -> None:
    command = "uv run --with pytest --group dev pytest tests -q"

    assert shell_command.is_unbounded_pytest_command(command)


def test_pytest_word_as_argument_is_not_violation() -> None:
    assert not shell_command.is_unbounded_pytest_command(
        "python3 tools/render.py --label pytest"
    )


def test_pytest_module_example_as_argument_is_not_violation() -> None:
    command = "python3 tools/render.py --command python3 -m pytest tests"

    assert not shell_command.is_unbounded_pytest_command(command)


def test_devctl_test_python_bundle_command_is_allowed() -> None:
    command = "python3 dev/scripts/devctl.py test-python --suite operator-console"

    assert not shell_command.is_unbounded_pytest_command(command)


def test_bundle_report_flags_raw_pytest_command() -> None:
    with patch.object(
        bundle_scan,
        "bundle_registry",
        return_value={
            "bundle.tooling": ("python3 -m pytest app/operator_console/tests -q",)
        },
    ), patch.object(reporting.config_policy, "config_violations", return_value=[]):
        report = reporting.build_report()

    assert not report["ok"]
    assert report["violations"] == [
        {
            "kind": "raw_pytest_bundle_command",
            "bundle": "bundle.tooling",
            "command": "python3 -m pytest app/operator_console/tests -q",
        }
    ]
