"""Typed contract for bounded Python test execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import posixpath
from typing import Final

DEFAULT_PER_TEST_TIMEOUT_SECONDS: Final[int] = 60
DEFAULT_SESSION_TIMEOUT_SECONDS: Final[int] = 900
TARGET_TIMEOUT_FLOOR_SECONDS: Final[dict[str, int]] = {
    "dev/scripts/devctl/tests/commands/test_development_command.py": 900,
    "dev/scripts/devctl/tests/vcs/test_push.py": 240,
}


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
    targets = _resolve_targets(suite, explicit_targets)
    resolved_timeout = _resolved_timeout_seconds(
        targets=targets,
        requested_timeout_seconds=timeout_seconds,
        suite_timeout_seconds=suite.timeout_seconds,
    )
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


def _resolve_targets(
    suite: PythonTestSuite,
    explicit_targets: tuple[str, ...],
) -> tuple[str, ...]:
    if not explicit_targets:
        return suite.targets
    allowed_roots = tuple(_normalize_path_part(target) for target in suite.targets)
    return tuple(
        _normalize_explicit_target(target, allowed_roots=allowed_roots)
        for target in explicit_targets
    )


def _normalize_explicit_target(
    raw_target: str,
    *,
    allowed_roots: tuple[str, ...],
) -> str:
    target = str(raw_target or "")
    if target.strip() != target or not target:
        raise ValueError("unsafe_python_test_target: target must be a non-empty path")
    if any(char in target for char in ("\x00", "\n", "\r")):
        raise ValueError("unsafe_python_test_target: control characters are not allowed")
    path_part, sep, node_id = target.partition("::")
    normalized_path = _normalize_path_part(path_part)
    if sep and not node_id:
        raise ValueError("unsafe_python_test_target: pytest node id must not be empty")
    if node_id and any(char in node_id for char in ("\x00", "\n", "\r")):
        raise ValueError("unsafe_python_test_target: pytest node id is not safe")
    if not any(
        normalized_path == root or normalized_path.startswith(f"{root}/")
        for root in allowed_roots
    ):
        roots = ", ".join(allowed_roots)
        raise ValueError(
            "outside_python_test_suite: explicit --path targets must stay under "
            f"{roots}"
        )
    return f"{normalized_path}{sep}{node_id}" if sep else normalized_path


def _normalize_path_part(path_text: str) -> str:
    if not path_text:
        raise ValueError("unsafe_python_test_target: path must not be empty")
    if path_text.startswith("-"):
        raise ValueError("unsafe_python_test_target: pytest option injection is not allowed")
    if "\\" in path_text:
        raise ValueError("unsafe_python_test_target: use repo-relative POSIX paths")
    path = PurePosixPath(path_text)
    if path.is_absolute():
        raise ValueError("unsafe_python_test_target: absolute paths are not allowed")
    normalized = posixpath.normpath(path_text)
    if normalized in {"", "."}:
        raise ValueError("unsafe_python_test_target: path must name a suite target")
    if any(part in {"", ".", ".."} for part in PurePosixPath(normalized).parts):
        raise ValueError("unsafe_python_test_target: traversal is not allowed")
    return normalized


def _resolved_timeout_seconds(
    *,
    targets: tuple[str, ...],
    requested_timeout_seconds: int | None,
    suite_timeout_seconds: int,
) -> int:
    baseline = (
        requested_timeout_seconds
        if requested_timeout_seconds is not None
        else suite_timeout_seconds
    )
    return max(baseline, _target_timeout_floor_seconds(targets))


def _target_timeout_floor_seconds(targets: tuple[str, ...]) -> int:
    floor = 0
    for target in targets:
        path = str(target or "").split("::", 1)[0]
        floor = max(floor, TARGET_TIMEOUT_FLOOR_SECONDS.get(path, 0))
    return floor
