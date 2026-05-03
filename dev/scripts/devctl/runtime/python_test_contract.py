"""Typed contract for bounded Python test execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DEFAULT_PER_TEST_TIMEOUT_SECONDS: Final[int] = 60
DEFAULT_SESSION_TIMEOUT_SECONDS: Final[int] = 900


@dataclass(frozen=True, slots=True)
class PythonTestSuite:
    """One named pytest suite with bounded default targets."""

    suite_id: str
    targets: tuple[str, ...]
    timeout_seconds: int


PYTHON_TEST_SUITES: Final[dict[str, PythonTestSuite]] = {
    "devctl": PythonTestSuite(
        suite_id="devctl",
        targets=("dev/scripts/devctl/tests",),
        timeout_seconds=900,
    ),
    "operator-console": PythonTestSuite(
        suite_id="operator-console",
        targets=("app/operator_console/tests",),
        timeout_seconds=300,
    ),
    "root": PythonTestSuite(
        suite_id="root",
        targets=("app/operator_console/tests", "dev/scripts/devctl/tests"),
        timeout_seconds=1200,
    ),
}


@dataclass(frozen=True, slots=True)
class PythonTestCommand:
    """Resolved bounded pytest command plus execution limits."""

    suite_id: str
    command: tuple[str, ...]
    targets: tuple[str, ...]
    timeout_seconds: int
    per_test_timeout_seconds: int
    fail_fast: bool


def build_python_test_command(
    *,
    suite_id: str,
    explicit_targets: tuple[str, ...] = (),
    timeout_seconds: int | None = None,
    per_test_timeout_seconds: int = DEFAULT_PER_TEST_TIMEOUT_SECONDS,
    fail_fast: bool = True,
) -> PythonTestCommand:
    """Build the canonical bounded pytest command for one suite."""
    suite = PYTHON_TEST_SUITES[suite_id]
    targets = explicit_targets or suite.targets
    resolved_timeout = timeout_seconds if timeout_seconds is not None else suite.timeout_seconds
    command = [
        "python3",
        "-m",
        "pytest",
        *targets,
        "-q",
        "--tb=short",
        f"--repo-session-timeout-seconds={resolved_timeout}",
        f"--repo-test-timeout-seconds={per_test_timeout_seconds}",
    ]
    if fail_fast:
        command.append("-x")
    else:
        command.append("--maxfail=0")
    return PythonTestCommand(
        suite_id=suite.suite_id,
        command=tuple(command),
        targets=targets,
        timeout_seconds=resolved_timeout,
        per_test_timeout_seconds=per_test_timeout_seconds,
        fail_fast=fail_fast,
    )
