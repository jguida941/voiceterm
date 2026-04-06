"""Command and scope extraction for review-candidate builders."""

from __future__ import annotations

import re

from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import is_pending_implementer_state

_BACKTICK_RE = re.compile(r"`([^`]+)`")
_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|rs|md|json|ya?ml|toml|txt|tsx?|jsx?|sh))"
)
_COMMAND_PREFIXES = (
    "python3 ",
    "python -m ",
    "pytest",
    "cargo test",
    "cargo clippy",
    "cargo fmt",
    "make ",
    "uv run ",
)
_COMPLETION_MARKERS = (
    "ready for review",
    "awaiting review",
    "review pending",
    "tests passed",
    "checks passed",
    "guard bundle passed",
    "all green",
    "completed the slice",
    "implemented the requested",
    "implemented the exact",
    "landed the requested",
)


def extract_execution_commands(
    current_session: ReviewCurrentSessionState,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (tests_run, guards_run) from implementer status/ack text."""
    commands = candidate_commands(
        f"{current_session.implementer_status}\n{current_session.implementer_ack}"
    )
    tests: list[str] = []
    guards: list[str] = []
    for command in commands:
        lowered = command.lower()
        if _is_test_command(lowered):
            tests.append(command)
        elif _is_guard_command(lowered):
            guards.append(command)
    return tuple(tests), tuple(guards)


def candidate_commands(text: str) -> tuple[str, ...]:
    """Extract devctl/test command candidates from freeform text."""
    commands: list[str] = []
    for match in _BACKTICK_RE.finditer(text):
        _append_command(commands, match.group(1))
    for raw_line in text.splitlines():
        stripped = raw_line.strip().lstrip("-").strip()
        _append_command(commands, stripped)
    return tuple(commands)


def completion_claimed(
    *,
    current_session: ReviewCurrentSessionState,
    tests_run: tuple[str, ...],
    guards_run: tuple[str, ...],
) -> bool:
    """Return True when the implementer claims a completed review-ready slice."""
    if is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    ):
        return False
    if current_session.implementer_ack_state != "current":
        return False
    combined = (
        f"{current_session.implementer_status}\n{current_session.implementer_ack}"
    ).lower()
    return bool(
        tests_run
        or guards_run
        or any(marker in combined for marker in _COMPLETION_MARKERS)
    )


def extract_scope_paths(*texts: str) -> tuple[str, ...]:
    """Extract file paths from instruction/scope text."""
    scope_paths: list[str] = []
    for text in texts:
        for match in _PATH_RE.finditer(text):
            path = match.group("path").strip().lstrip("./")
            if path and path not in scope_paths:
                scope_paths.append(path)
    return tuple(scope_paths)


def _append_command(commands: list[str], candidate: str) -> None:
    normalized = candidate.strip()
    lowered = normalized.lower()
    if not normalized:
        return
    if not any(lowered.startswith(prefix) for prefix in _COMMAND_PREFIXES):
        return
    if normalized not in commands:
        commands.append(normalized)


def _is_test_command(command: str) -> bool:
    return (
        "pytest" in command
        or "cargo test" in command
        or "unittest" in command
        or re.search(r"\btest\b", command) is not None
    )


def _is_guard_command(command: str) -> bool:
    return (
        "devctl.py check" in command
        or "docs-check" in command
        or "render-surfaces" in command
        or "check_" in command
    )
