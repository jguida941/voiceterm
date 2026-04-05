"""Shared terminal-mode selection policy for review-channel actions."""

from __future__ import annotations


def resolve_terminal_mode(
    explicit_terminal: str = "",
    *,
    operator_interaction_mode: str = "",
    parent_terminal: str = "",
) -> str:
    """Resolve the effective terminal mode for launch or recovery actions.

    Policy:
    - An explicit terminal mode wins.
    - Governed remote-control sessions stay headless.
    - Follow/recovery actions inherit an existing parent terminal mode.
    - Local launches default to a visible Terminal.app window.
    """
    terminal = str(explicit_terminal or "").strip()
    if terminal in {"terminal-app", "none"}:
        return terminal

    interaction_mode = str(operator_interaction_mode or "").strip()
    if interaction_mode == "remote_control":
        return "none"

    inherited_terminal = str(parent_terminal or "").strip()
    if inherited_terminal in {"terminal-app", "none"}:
        return inherited_terminal

    return "terminal-app"
