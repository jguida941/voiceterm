"""Path-aware Python test add-ons for check-router."""

from __future__ import annotations

from ...config import REPO_ROOT

_FOCUSED_DEVCTL_TEST_BASE_TIMEOUT_SECONDS = 420
_FOCUSED_DEVCTL_TEST_PER_TEST_TIMEOUT_SECONDS = 90
_FOCUSED_DEVCTL_TEST_PARALLEL_WORKERS = 1
_FOCUSED_DEVCTL_TEST_SHARDED_PARALLEL_WORKERS = 4
_FOCUSED_DEVCTL_TEST_TARGET_TIMEOUT_SECONDS = {
    "dev/scripts/devctl/tests/commands/test_development_command.py": 900,
    "dev/scripts/devctl/tests/review_channel/test_review_channel.py": 900,
    "dev/scripts/devctl/tests/vcs/test_push.py": 240,
}
_FOCUSED_DEVCTL_TEST_TARGET_SHARDS = {
    "dev/scripts/devctl/tests/vcs/test_push.py": (
        "dev/scripts/devctl/tests/vcs/test_push.py::PushParserTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushCommandTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushBridgeSyncTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushLiveExecutionTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushReceiptTests",
        "dev/scripts/devctl/tests/vcs/test_push.py::PushPipelineStateSyncTests",
    ),
}


def detect_python_test_addons(changed_paths: list[str]) -> list[dict]:
    """Select bounded Python tests from touched paths instead of static bundles."""
    addons: list[dict] = []
    cold_boot_paths = _devctl_cold_boot_paths(changed_paths)
    if cold_boot_paths:
        addons.append(
            {
                "id": "devctl-cold-boot",
                "label": "devctl cold-boot import smoke",
                "matched_paths": cold_boot_paths,
                "commands": [
                    "python3 dev/scripts/checks/check_devctl_cold_boot.py --format md"
                ],
            }
        )

    operator_paths = _operator_console_test_paths(changed_paths)
    if operator_paths:
        addons.append(
            {
                "id": "python-tests.operator-console",
                "label": "Operator Console Python tests",
                "matched_paths": operator_paths,
                "commands": [_operator_console_test_command(operator_paths)],
            }
        )

    devctl_paths = _matching_paths(
        changed_paths,
        (
            "conftest.py",
            "pytest.ini",
            "dev/scripts/checks/",
            "dev/scripts/devctl/",
        ),
    )
    devctl_test_paths = _devctl_test_targets_for(changed_paths)
    if devctl_test_paths:
        addons.append(
            {
                "id": "python-tests.devctl-focused",
                "label": "Focused devctl Python tests",
                "matched_paths": devctl_paths,
                "commands": _devctl_test_commands(devctl_test_paths),
            }
        )
    return addons


def _matching_paths(changed_paths: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(
        {
            path
            for path in changed_paths
            if any(
                path == prefix.rstrip("/") or path.startswith(prefix)
                for prefix in prefixes
            )
        }
    )


def _operator_console_test_paths(changed_paths: list[str]) -> list[str]:
    return [
        path
        for path in _matching_paths(changed_paths, ("app/operator_console/",))
        if path.endswith(".py")
    ]


def _devctl_cold_boot_paths(changed_paths: list[str]) -> list[str]:
    return [
        path
        for path in _matching_paths(
            changed_paths,
            (
                "dev/scripts/devctl/cli.py",
                "dev/scripts/devctl/commands/",
                "dev/scripts/devctl/runtime/",
                "dev/scripts/checks/check_devctl_cold_boot.py",
            ),
        )
        if path.endswith(".py")
    ]


def _operator_console_test_command(matched_paths: list[str]) -> str:
    touched_tests = tuple(
        path
        for path in matched_paths
        if path.startswith("app/operator_console/tests/") and path.endswith(".py")
    )
    if touched_tests:
        paths = " ".join(f"--path {path}" for path in touched_tests)
        return (
            "python3 dev/scripts/devctl.py test-python --suite operator-console "
            f"{paths} --timeout-seconds 300 --per-test-timeout-seconds 30"
        )
    return (
        "python3 dev/scripts/devctl.py test-python --suite operator-console "
        "--timeout-seconds 900 --per-test-timeout-seconds 30"
    )


def _devctl_test_commands(test_paths: tuple[str, ...]) -> list[str]:
    commands: list[str] = []
    for test_path in sorted(test_paths):
        shard_targets = _FOCUSED_DEVCTL_TEST_TARGET_SHARDS.get(test_path)
        if shard_targets:
            commands.append(
                _devctl_test_command_for_targets(
                    shard_targets,
                    timeout_seconds=_devctl_test_timeout_seconds(test_path),
                    parallel_workers=_FOCUSED_DEVCTL_TEST_SHARDED_PARALLEL_WORKERS,
                )
            )
            continue
        commands.append(_devctl_test_command(test_path))
    return commands


def _devctl_test_command(test_path: str) -> str:
    return _devctl_test_command_for_targets(
        (test_path,),
        timeout_seconds=_devctl_test_timeout_seconds(test_path),
        parallel_workers=_FOCUSED_DEVCTL_TEST_PARALLEL_WORKERS,
    )


def _devctl_test_command_for_targets(
    test_targets: tuple[str, ...],
    *,
    timeout_seconds: int,
    parallel_workers: int,
) -> str:
    paths = " ".join(f"--path {test_target}" for test_target in test_targets)
    return (
        "python3 dev/scripts/devctl.py test-python --suite devctl "
        f"{paths} "
        f"--timeout-seconds {timeout_seconds} "
        f"--per-test-timeout-seconds {_FOCUSED_DEVCTL_TEST_PER_TEST_TIMEOUT_SECONDS} "
        f"--parallel-workers {parallel_workers}"
    )


def _devctl_test_timeout_seconds(test_path: str) -> int:
    return _FOCUSED_DEVCTL_TEST_TARGET_TIMEOUT_SECONDS.get(
        test_path,
        _FOCUSED_DEVCTL_TEST_BASE_TIMEOUT_SECONDS,
    )


def _devctl_test_targets_for(changed_paths: list[str]) -> tuple[str, ...]:
    targets: set[str] = set()
    for path in changed_paths:
        if path.startswith("dev/scripts/devctl/tests/") and path.endswith(".py"):
            targets.add(path)
        for source_prefix, test_paths in _DEVCTL_TEST_TARGETS:
            if path == source_prefix.rstrip("/") or path.startswith(source_prefix):
                targets.update(test_paths)
    return tuple(sorted(path for path in targets if (REPO_ROOT / path).exists()))


_DEVCTL_TEST_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "conftest.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_architecture_surface_sync.py",
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "pytest.ini",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/checks/check_pytest_runtime_policy.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/checks/pytest_runtime_policy/",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
        ),
    ),
    (
        "dev/scripts/devctl/cli_parser/python_tests.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/python_tests.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/python_test_runner/",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/runtime/python_test_contract.py",
        (
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
        ),
    ),
    (
        "dev/scripts/devctl/bundles/",
        (
            "dev/scripts/devctl/tests/commands/check/test_check_router.py",
            "dev/scripts/devctl/tests/governance/test_bundle_registry.py",
        ),
    ),
    (
        "dev/scripts/devctl/commands/check/",
        (
            "dev/scripts/devctl/tests/commands/check/test_check_router.py",
        ),
    ),
    (
        "dev/scripts/devctl/governance/script_catalog_registry.py",
        (
            "dev/scripts/devctl/tests/checks/test_check_pytest_runtime_policy.py",
            "dev/scripts/devctl/tests/governance/test_bundle_registry.py",
        ),
    ),
)
