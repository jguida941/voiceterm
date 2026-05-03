"""Launch adapters used by reviewer wake orchestration."""

from __future__ import annotations

from pathlib import Path

from ..approval_mode import auto_elevated_approval_mode


def resolved_wake_approval_mode(*, args: object, interaction_mode: str) -> str:
    """Apply typed-state-driven approval-mode auto-elevation for reviewer wake."""
    explicit = getattr(args, "approval_mode", None)
    elevated = auto_elevated_approval_mode(
        explicit_mode=explicit,
        interaction_mode=interaction_mode,
    )
    return str(elevated or "")


def artifact_root(value: object) -> Path | None:
    if value is None:
        return None
    root = getattr(value, "artifact_root", None)
    return root if isinstance(root, Path) else None


def provider_target(provider: str) -> str:
    return str(provider or "").strip().lower()


def visible_session_woke(
    *,
    visible_launch: bool,
    is_delegate: bool,
    woke: bool,
) -> bool | None:
    if visible_launch:
        return woke
    if is_delegate:
        return False
    return None


def launch_sessions_headless(
    sessions: list[dict[str, object]],
    warnings: list[str],
) -> bool:
    from ..commands.review_channel.bridge_launch_headless import (
        launch_sessions_headless as launch_headless,
    )

    return launch_headless(sessions, warnings)


def launch_sessions_visible(
    sessions: list[dict[str, object]],
    warnings: list[str],
) -> bool:
    from .core import AUTO_DARK_TERMINAL_PROFILES, DEFAULT_TERMINAL_PROFILE
    from .terminal_app import launch_terminal_sessions

    try:
        launch_terminal_sessions(
            sessions,
            terminal_profile=None,
            default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
            auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
        )
    except (OSError, ValueError) as exc:
        warnings.append(f"Visible launch failed: {exc}")
        return False
    return True
