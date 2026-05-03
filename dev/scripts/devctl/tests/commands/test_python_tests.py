from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import python_tests
from dev.scripts.devctl.runtime.python_test_contract import build_python_test_command


def test_build_python_test_command_is_bounded_and_fail_fast() -> None:
    resolved = build_python_test_command(suite_id="operator-console")

    assert resolved.targets == ("app/operator_console/tests",)
    assert resolved.timeout_seconds == 300
    assert "--repo-session-timeout-seconds=300" in resolved.command
    assert "--repo-test-timeout-seconds=60" in resolved.command
    assert "-x" in resolved.command


def test_build_python_test_command_allows_explicit_paths() -> None:
    resolved = build_python_test_command(
        suite_id="devctl",
        explicit_targets=("dev/scripts/devctl/tests/test_common.py",),
        timeout_seconds=120,
        fail_fast=False,
    )

    assert resolved.targets == ("dev/scripts/devctl/tests/test_common.py",)
    assert "--repo-session-timeout-seconds=120" in resolved.command
    assert "-x" not in resolved.command
    assert "--maxfail=0" in resolved.command


def test_test_python_command_threads_timeout_to_runner_env() -> None:
    args = SimpleNamespace(
        suite="operator-console",
        path=[],
        timeout_seconds=120,
        per_test_timeout_seconds=15,
        no_fail_fast=False,
        dry_run=False,
        format="json",
    )

    with patch.object(python_tests, "write_output"), patch.object(
        python_tests,
        "run_cmd",
        return_value={"returncode": 0, "duration_s": 1.0},
    ) as run_mock:
        assert python_tests.run(args) == 0

    _name, command = run_mock.call_args.args[:2]
    env = run_mock.call_args.kwargs["env"]
    assert "dev/scripts/devctl.py" not in command
    assert "--repo-session-timeout-seconds=120" in command
    assert "--repo-test-timeout-seconds=15" in command
    assert env["VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS"] == "150"
