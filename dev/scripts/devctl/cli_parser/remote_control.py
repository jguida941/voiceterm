"""Parser wiring for the typed remote-control lifecycle command."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments

REMOTE_CONTROL_ACTIONS = (
    "start",
    "enter",
    "heartbeat",
    "exit",
    "hook",
    "status",
    "doctor",
    "dry-run",
)


def add_remote_control_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``remote-control`` subcommand."""
    cmd = sub.add_parser(
        "remote-control",
        help="Typed remote-control lifecycle over review-channel attachment state",
    )
    cmd.add_argument(
        "action",
        nargs="?",
        choices=REMOTE_CONTROL_ACTIONS,
        default="status",
        help="Lifecycle action to run.",
    )
    cmd.add_argument(
        "--action",
        dest="action_flag",
        choices=REMOTE_CONTROL_ACTIONS,
        default="",
        help="Lifecycle action override for flag-style callers.",
    )
    cmd.add_argument(
        "--provider",
        choices=("claude", "codex", "cursor"),
        default="claude",
        help="Remote-control provider attachment to read or update.",
    )
    cmd.add_argument(
        "--role",
        choices=("implementer", "reviewer", "operator"),
        default="operator",
        help="Role owned by the external remote-control session.",
    )
    cmd.add_argument(
        "--session-name",
        default="VoiceTerm Remote Control",
        help="Human-readable remote-control session label.",
    )
    cmd.add_argument("--session-url", default="", help="Known provider session URL.")
    cmd.add_argument(
        "--remote-session-id",
        "--session-id",
        dest="remote_session_id",
        default="",
        help="Known provider remote session id.",
    )
    cmd.add_argument(
        "--launcher-source",
        default="remote-control",
        help="Source that is entering the typed lifecycle.",
    )
    cmd.add_argument(
        "--invocation-origin",
        default="",
        help="Authoritative hook/runtime origin for audit receipts, when proven.",
    )
    cmd.add_argument(
        "--entrypoint",
        default="claude_builtin_remote_control",
        help="Slash command or launcher entrypoint using this lifecycle.",
    )
    cmd.add_argument(
        "--host-pid",
        type=int,
        default=None,
        help="Host process pid to store in typed lifecycle state.",
    )
    cmd.add_argument(
        "--host-session-label",
        default="",
        help="Host-side session label to store in typed lifecycle state.",
    )
    cmd.add_argument(
        "--heartbeat-ttl-seconds",
        type=int,
        default=900,
        help="Seconds before the remote-control attachment heartbeat expires.",
    )
    cmd.add_argument(
        "--physical-remote-control-confirmed",
        action="store_true",
        default=False,
        help=(
            "Provider slash adapter observed Claude's built-in remote-control "
            "mode as active before recording typed state."
        ),
    )
    cmd.add_argument(
        "--status-dir",
        default="",
        help="Override review status directory for tests or portable repo packs.",
    )
    cmd.add_argument(
        "--hook-input-file",
        default="",
        help="Read Claude hook JSON from this file instead of stdin.",
    )
    cmd.add_argument(
        "--hook-poll-seconds",
        type=float,
        default=30.0,
        help="Seconds for remote-control hook handling to poll transcript evidence.",
    )
    cmd.add_argument(
        "--bootstrap-review-channel",
        action="store_true",
        default=False,
        help="Request review-channel bootstrap guidance before launching.",
    )
    cmd.add_argument(
        "--no-caffeinate",
        action="store_true",
        default=False,
        help="Compatibility flag accepted by remote-bridge-loop wrapper.",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview lifecycle writes and launch command without mutating state.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json"),
        default_format="md",
    )


__all__ = ["REMOTE_CONTROL_ACTIONS", "add_remote_control_parser"]
