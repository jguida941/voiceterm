from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
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


def test_build_python_test_command_applies_measured_target_timeout_floor() -> None:
    resolved = build_python_test_command(
        suite_id="devctl",
        explicit_targets=(
            "dev/scripts/devctl/tests/commands/test_development_command.py"
            "::test_develop_next_selects_active_leaf_plan_row",
        ),
        timeout_seconds=120,
    )

    assert resolved.timeout_seconds == 900
    assert "--repo-session-timeout-seconds=900" in resolved.command


def test_build_python_test_command_applies_push_target_timeout_floor() -> None:
    resolved = build_python_test_command(
        suite_id="devctl",
        explicit_targets=("dev/scripts/devctl/tests/vcs/test_push.py",),
        timeout_seconds=120,
    )

    assert resolved.timeout_seconds == 600
    assert "--repo-session-timeout-seconds=600" in resolved.command


def test_test_python_command_threads_timeout_to_runner_env() -> None:
    args = SimpleNamespace(
        suite="operator-console",
        path=[],
        timeout_seconds=120,
        per_test_timeout_seconds=15,
        no_fail_fast=False,
        parallel_workers=1,
        no_parallel=False,
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


def test_test_python_cli_accepts_parallel_flags() -> None:
    args = build_parser().parse_args(
        [
            "test-python",
            "--path",
            "dev/scripts/devctl/tests/runtime/test_vcs.py",
            "--parallel-workers",
            "3",
            "--no-parallel",
        ]
    )

    assert args.parallel_workers == 3
    assert args.no_parallel


def test_test_python_parallelizes_explicit_path_shards() -> None:
    args = SimpleNamespace(
        suite="devctl",
        path=[
            "dev/scripts/devctl/tests/runtime/test_vcs.py",
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ],
        timeout_seconds=120,
        per_test_timeout_seconds=15,
        no_fail_fast=False,
        parallel_workers=2,
        no_parallel=False,
        dry_run=False,
        format="json",
    )

    with patch.object(python_tests, "write_output") as write_mock, patch.object(
        python_tests,
        "run_cmd",
        side_effect=[
            {"returncode": 0, "duration_s": 2.0},
            {"returncode": 0, "duration_s": 1.0},
        ],
    ) as run_mock:
        assert python_tests.run(args) == 0

    commands = [call.args[1] for call in run_mock.call_args_list]
    assert len(commands) == 2
    assert all("-p" in command and "no:cacheprovider" in command for command in commands)
    assert any("dev/scripts/devctl/tests/runtime/test_vcs.py" in command for command in commands)
    assert any(
        "dev/scripts/devctl/tests/commands/test_python_tests.py" in command
        for command in commands
    )
    payload = json.loads(write_mock.call_args.args[0])
    assert payload["ok"] is True
    assert payload["parallelized"] is True
    assert payload["parallel_workers"] == 2
    assert len(payload["shards"]) == 2
