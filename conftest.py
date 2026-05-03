"""Repository-wide pytest safety rails.

The root pytest entrypoint is a human convenience, not a license for agents to
run unbounded suites. Keep defaults fail-fast and wall-clock bounded so a bad
test selection cannot burn a session for hours.
"""

from __future__ import annotations

import os
import signal
import threading
import time
from collections.abc import Generator
from types import FrameType

import pytest

from dev.scripts.devctl.tests.conftest import (
    init_python_guard_repo_root,
    init_temp_repo_root,
    load_repo_module,
    override_module_attrs,
)

DEFAULT_SESSION_TIMEOUT_SECONDS = 1800.0
DEFAULT_TEST_TIMEOUT_SECONDS = 60.0


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("voiceterm")
    group.addoption(
        "--repo-session-timeout-seconds",
        type=float,
        default=None,
        help="Maximum wall-clock seconds for a root pytest session; 0 disables.",
    )
    group.addoption(
        "--repo-test-timeout-seconds",
        type=float,
        default=None,
        help="Maximum wall-clock seconds for one Python test call; 0 disables.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: intentional long-running test; still subject to repo session timeout",
    )
    config._voiceterm_session_started = time.monotonic()  # type: ignore[attr-defined]


def pytest_runtest_setup(item: pytest.Item) -> None:
    timeout = _timeout_value(
        item.config,
        option_name="repo_session_timeout_seconds",
        env_name="VOICETERM_PYTEST_SESSION_TIMEOUT_SECONDS",
        default=DEFAULT_SESSION_TIMEOUT_SECONDS,
    )
    if timeout <= 0:
        return
    started = getattr(item.config, "_voiceterm_session_started", time.monotonic())
    elapsed = time.monotonic() - float(started)
    if elapsed > timeout:
        pytest.exit(
            f"repo pytest session timed out after {timeout:.0f}s",
            returncode=124,
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None]:
    timeout = _timeout_value(
        item.config,
        option_name="repo_test_timeout_seconds",
        env_name="VOICETERM_PYTEST_TEST_TIMEOUT_SECONDS",
        default=DEFAULT_TEST_TIMEOUT_SECONDS,
    )
    if timeout <= 0 or not _can_use_signal_alarm():
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    signal.signal(signal.SIGALRM, _timeout_handler(item.nodeid, timeout))
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def _timeout_value(
    config: pytest.Config,
    *,
    option_name: str,
    env_name: str,
    default: float,
) -> float:
    explicit = config.getoption(option_name)
    if explicit is not None:
        return max(0.0, float(explicit))
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        return max(0.0, float(raw))
    except ValueError:
        return default


def _can_use_signal_alarm() -> bool:
    return (
        hasattr(signal, "SIGALRM")
        and hasattr(signal, "setitimer")
        and threading.current_thread() is threading.main_thread()
    )


def _timeout_handler(nodeid: str, timeout: float):
    def raise_timeout(_signum: int, _frame: FrameType | None) -> None:
        raise TimeoutError(f"pytest test timed out after {timeout:.0f}s: {nodeid}")

    return raise_timeout
