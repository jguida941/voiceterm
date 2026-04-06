"""Tests for the launcher-discipline pre-flight validation (F21).

Locks the field-by-field decision rules for
``validate_visible_launch_in_local_mode``. Every rule branch from the
function docstring has at least one positive case (the rule fires) and
one negative case (the rule does NOT fire when its precondition is
absent). The function is pure, so tests inject every input and assert
on the verdict shape.
"""

from __future__ import annotations

import pytest

from dev.scripts.devctl.commands.review_channel.launcher_discipline import (
    LauncherDisciplineVerdict,
    validate_visible_launch_in_local_mode,
)


# ---------- Decision rule 1: malformed terminal_arg fails closed ----------


def test_invalid_terminal_arg_returns_invalid_terminal_arg_denial() -> None:
    """A non-`terminal-app`/`none` terminal value fails closed."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="docker",
    )
    assert isinstance(verdict, LauncherDisciplineVerdict)
    assert verdict.allowed is False
    assert verdict.denial_reason == "invalid_terminal_arg"
    assert "docker" in verdict.operator_message


def test_empty_terminal_arg_returns_invalid_terminal_arg_denial() -> None:
    """Empty string terminal arg also fails closed (no silent default)."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason == "invalid_terminal_arg"


# ---------- Decision rule 2: terminal-app is always allowed ----------


def test_terminal_app_in_local_terminal_mode_is_allowed() -> None:
    """The canonical local-operator path: visible Terminal in local mode."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="terminal-app",
    )
    assert verdict.allowed is True
    assert verdict.denial_reason == ""
    assert verdict.operator_message == ""


def test_terminal_app_in_remote_control_mode_is_allowed() -> None:
    """Remote operator can still legitimately request a visible launch."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="remote_control",
        terminal_arg="terminal-app",
    )
    assert verdict.allowed is True


def test_terminal_app_with_unresolved_interaction_mode_is_allowed() -> None:
    """Unknown interaction mode + visible Terminal: still allowed (visible is safe)."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="",
        terminal_arg="terminal-app",
    )
    assert verdict.allowed is True


# ---------- Decision rule 3: headless in remote_control is allowed ----------


def test_headless_in_remote_control_mode_is_allowed() -> None:
    """The canonical remote-operator path: headless launch in remote_control."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="remote_control",
        terminal_arg="none",
    )
    assert verdict.allowed is True
    assert verdict.denial_reason == ""


def test_headless_in_remote_control_with_extra_whitespace_is_allowed() -> None:
    """Whitespace around the interaction_mode value must not break the match."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="  remote_control  ",
        terminal_arg="none",
    )
    assert verdict.allowed is True


# ---------- Decision rule 4: explicit operator override is allowed ----------


def test_headless_with_explicit_override_is_allowed_in_local_mode() -> None:
    """Explicit operator override permits headless even in local mode.

    This is the escape hatch for legitimate cases (CI runs, automated
    test harnesses). The caller is responsible for justifying it; the
    gate trusts the override flag once set.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="none",
        allow_headless_override=True,
    )
    assert verdict.allowed is True


def test_headless_with_explicit_override_is_allowed_in_unresolved_mode() -> None:
    """Override also bypasses the unresolved-mode fail-closed default."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="",
        terminal_arg="none",
        allow_headless_override=True,
    )
    assert verdict.allowed is True


def test_headless_with_explicit_override_is_allowed_in_unknown_mode() -> None:
    """Override also bypasses the unknown-mode fail-closed default."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="some_future_mode_value",
        terminal_arg="none",
        allow_headless_override=True,
    )
    assert verdict.allowed is True


# ---------- Decision rule 5: F21 trap fires (the main reason this guard exists) ----------


def test_headless_in_local_terminal_mode_is_denied_without_override() -> None:
    """The F21 trap: implementer launching headless Codex in local mode.

    This is the exact pattern the implementer hit 4+ times in one
    session despite CLAUDE.md saying use `terminal-app` in local mode.
    The headless Codex CLI hangs on auth prompts; the publisher
    heartbeat then fakes aliveness (F4 false-positive). The gate must
    fail-closed here.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="none",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason == "headless_launch_in_local_mode"
    assert "local_terminal" in verdict.operator_message
    assert "remote_control" in verdict.operator_message
    assert "terminal-app" in verdict.operator_message


def test_headless_with_unresolved_interaction_mode_is_denied_without_override() -> None:
    """Unresolved typed mode + headless = fail closed.

    If the typed authority cannot tell us whether the operator is local
    or remote, we must NOT silently default to headless. The
    `interaction_mode` enum has an explicit `unresolved` value precisely
    so this gate has something to fail closed on.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="unresolved",
        terminal_arg="none",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason == "headless_launch_in_local_mode"


def test_headless_with_empty_interaction_mode_is_denied_without_override() -> None:
    """Empty string typed mode (the bare-default case) also fails closed.

    `BridgeConfig.operator_interaction_mode` defaults to `local_terminal`
    today (`project_governance_contract.py:208`), but the policy scanner
    at `draft_policy_scan.py:177-236` does not actually populate the
    field. So an unconfigured repo can present an empty string. That
    must NOT bypass the gate by accident.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="",
        terminal_arg="none",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason == "headless_launch_in_local_mode"


# ---------- Decision rule 6: unknown interaction_mode fails closed ----------


def test_headless_with_unknown_interaction_mode_is_denied_without_override() -> None:
    """A future enum value not in the recognized set must NOT bypass the gate.

    If someone adds a new `interaction_mode` value (e.g. `mobile_relay`)
    without updating this guard's set, the gate must still fail closed
    on headless launches in that mode. The fix-forward path is to
    explicitly add the new value to either the visible-required set or
    the headless-permitted set.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="mobile_relay",
        terminal_arg="none",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason == "headless_launch_unknown_interaction_mode"


# ---------- Verdict shape invariants ----------


def test_allowed_verdict_carries_no_denial_reason_or_message() -> None:
    """An `allowed=True` verdict must have empty denial_reason and operator_message.

    Operator surfaces and dashboards branch on these fields. An allowed
    verdict that carries a stray reason string would confuse downstream
    rendering.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="terminal-app",
    )
    assert verdict.allowed is True
    assert verdict.denial_reason == ""
    assert verdict.operator_message == ""


def test_denied_verdict_carries_both_denial_reason_and_message() -> None:
    """A `denied` verdict must always have both `denial_reason` and `operator_message`.

    The denial reason is the typed branch token; the operator message is
    the human-readable explanation. Both are required so dashboards can
    show one and structured surfaces can branch on the other.
    """
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="none",
    )
    assert verdict.allowed is False
    assert verdict.denial_reason
    assert verdict.operator_message


def test_verdict_is_frozen_dataclass() -> None:
    """The verdict dataclass must be immutable so callers cannot mutate it after returning."""
    verdict = validate_visible_launch_in_local_mode(
        interaction_mode="local_terminal",
        terminal_arg="terminal-app",
    )
    with pytest.raises((AttributeError, TypeError)):
        verdict.allowed = False  # type: ignore[misc]
