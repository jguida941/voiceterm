"""Support helpers for reviewer follow-loop recovery actions."""

from __future__ import annotations

from types import SimpleNamespace

from .collaboration_provider import coding_provider_from_report
from .terminal_mode import resolve_terminal_mode


def resolve_recovery_terminal(args) -> str:
    """Resolve headless vs Terminal.app recovery from the parent daemon args.

    Recovery/rollover should honor the same terminal policy as direct launches:
    explicit terminal wins, remote-control stays headless, otherwise inherit the
    parent follow-loop terminal when present before falling back to Terminal.app.
    """
    return resolve_terminal_mode(
        operator_interaction_mode=str(
            getattr(args, "operator_interaction_mode", "") or ""
        ).strip(),
        parent_terminal=str(getattr(args, "terminal", "") or "").strip(),
    )


def build_recover_action_args(
    args,
    *,
    recover_provider: str,
) -> SimpleNamespace:
    """Return `review-channel --action recover` args for follow automation."""
    payload = vars(args).copy()
    payload.update(
        action="recover",
        follow=False,
        terminal=resolve_recovery_terminal(args),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        recover_provider=recover_provider,
        refresh_bridge_heartbeat_if_stale=True,
    )
    return SimpleNamespace(**payload)


def build_rollover_action_args(
    args,
    *,
    rollover_provider: str = "",
) -> SimpleNamespace:
    """Build rollover args with optional same-provider handoff routing."""
    payload = vars(args).copy()
    payload.update(
        action="rollover",
        follow=False,
        terminal=resolve_recovery_terminal(args),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        rollover_trigger="peer-stale",
        await_ack_seconds=max(1, int(getattr(args, "await_ack_seconds", 180) or 180)),
        refresh_bridge_heartbeat_if_stale=True,
    )
    if rollover_provider:
        payload["rollover_provider"] = rollover_provider
    return SimpleNamespace(**payload)


def build_launch_action_args(args) -> SimpleNamespace:
    """Return `review-channel --action launch` args for follow automation."""
    payload = vars(args).copy()
    payload.update(
        action="launch",
        follow=False,
        terminal=resolve_recovery_terminal(args),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        refresh_bridge_heartbeat_if_stale=True,
    )
    return SimpleNamespace(**payload)


def implementer_ack_current(
    *,
    reviewer_runtime: dict[str, object],
    bridge_liveness: dict[str, object],
) -> bool:
    """Return whether the implementer ACK is current in runtime or bridge state."""
    if "implementer_ack_current" in reviewer_runtime:
        return bool(reviewer_runtime.get("implementer_ack_current"))
    return bool(bridge_liveness.get("claude_ack_current"))


def recover_provider_from_report(report: dict[str, object]) -> str:
    """Return the implementer provider to recover from a report payload."""
    return coding_provider_from_report(report)
