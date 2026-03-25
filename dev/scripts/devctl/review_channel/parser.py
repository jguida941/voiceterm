"""Parser wiring for the transitional `devctl review-channel` surface."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from ..approval_mode import APPROVAL_MODE_CHOICES, DEFAULT_APPROVAL_MODE
from ..common import add_standard_output_arguments
from .core import (
    DEFAULT_BRIDGE_REL,
    DEFAULT_REVIEW_CHANNEL_REL,
    DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
    DEFAULT_ROLLOVER_DIR_REL,
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    DEFAULT_TERMINAL_PROFILE,
)
from .events import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
    DEFAULT_REVIEW_STATE_JSON_REL,
)
from .parser_argument_groups import (
    build_event_context_arguments,
    build_packet_arguments,
    build_query_arguments,
)
from .parser_bridge_controls import build_bridge_control_arguments
from .state import DEFAULT_REVIEW_STATUS_DIR_REL
from .peer_liveness import REVIEWER_MODE_CLI_CHOICES, ReviewerMode


@dataclass(frozen=True, slots=True)
class ArgumentDef:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


AGENT_CHOICES = ("codex", "claude", "operator", "system")
REVIEW_ACTION_CHOICES = (
    "launch",
    "rollover",
    "status",
    "implementer-wait",
    "reviewer-wait",
    "ensure",
    "stop",
    "reviewer-heartbeat",
    "reviewer-checkpoint",
    "promote",
    "post",
    "watch",
    "inbox",
    "ack",
    "dismiss",
    "apply",
    "history",
    "bridge-poll",
)


def _arg(*flags: str, **kwargs: Any) -> ArgumentDef:
    return ArgumentDef(flags=tuple(flags), kwargs=kwargs)


LAUNCH_ARGUMENTS: list[ArgumentDef] = [
    _arg(
        "--terminal",
        choices=["terminal-app", "none"],
        default="terminal-app",
        help="Launch via Terminal.app on macOS or just emit scripts/report output",
    ),
    _arg(
        "--terminal-profile",
        default=DEFAULT_TERMINAL_PROFILE,
        help=(
            "Terminal.app profile to apply on live launch. "
            "`auto-dark` picks a dark built-in profile when available; "
            "`default` leaves Terminal.app unchanged."
        ),
    ),
    _arg(
        "--review-channel-path",
        default=DEFAULT_REVIEW_CHANNEL_REL,
        help="Path to the active review-channel plan markdown",
    ),
    _arg("--bridge-path", default=DEFAULT_BRIDGE_REL, help="Path to the live markdown bridge file"),
    _arg(
        "--rollover-dir",
        default=DEFAULT_ROLLOVER_DIR_REL,
        help="Directory where repo-visible rollover handoff bundles are written",
    ),
    _arg(
        "--status-dir",
        default=DEFAULT_REVIEW_STATUS_DIR_REL,
        help="Directory where latest bridge-backed status projections are written",
    ),
    _arg(
        "--promotion-plan",
        default=None,
        help=("Active-plan checklist used for repo-owned next-task promotion and " "derived queue projections"),
    ),
    _arg(
        "--artifact-root",
        default=DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
        help="Root directory for canonical event-backed review-channel artifacts",
    ),
    _arg(
        "--state-json",
        default=DEFAULT_REVIEW_STATE_JSON_REL,
        help="Canonical reduced review-channel state JSON path",
    ),
    _arg(
        "--emit-projections",
        default=DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
        help="Directory where canonical event-backed projections are written",
    ),
    _arg(
        "--rollover-threshold-pct",
        type=int,
        default=DEFAULT_ROLLOVER_THRESHOLD_PCT,
        help=("Context-remaining percentage that should trigger a planned self-relaunch " "before compaction"),
    ),
    _arg(
        "--rollover-trigger",
        choices=["context-threshold", "manual", "peer-stale"],
        default="context-threshold",
        help="Reason recorded in the rollover handoff bundle",
    ),
    _arg(
        "--await-ack-seconds",
        type=int,
        default=DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
        help=(
            "How long a live launch should wait for a fresh Codex reviewer "
            "heartbeat, and how long a live rollover should wait for visible "
            "Codex/Claude ACK lines from the fresh conductor sessions before "
            "failing closed. Must be greater than zero for rollover."
        ),
    ),
    _arg("--codex-workers", type=int, default=8, help="Requested Codex reviewer-worker budget"),
    _arg("--claude-workers", type=int, default=8, help="Requested Claude coding-worker budget"),
    _arg(
        "--approval-mode",
        choices=list(APPROVAL_MODE_CHOICES),
        default=DEFAULT_APPROVAL_MODE,
        help=(
            "Shared approval policy for conductor launches. `balanced` is the "
            "safe default, `trusted` enables provider no-prompt modes, and "
            "`strict` reserves dangerous/publish-class actions for explicit "
            "approval surfaces."
        ),
    ),
    _arg(
        "--dangerous",
        action="store_true",
        help=(
            "Legacy compatibility alias for `--approval-mode trusted`; uses "
            "provider no-prompt flags (`codex --dangerously-bypass-...`, "
            "`claude --dangerously-skip-permissions`)"
        ),
    ),
    _arg(
        "--scope",
        default=None,
        help=(
            "Active-plan doc to auto-scope the launch. Rewrites "
            "`Current Instruction For Claude` from the plan's first unchecked "
            "execution-checklist item before launching conductors. Accepts a "
            "plan filename (e.g. `review_probes`), a full relative path "
            "(e.g. `dev/active/review_probes.md`), or an MP id (e.g. `MP-368`)."
        ),
    ),
    _arg(
        "--daemon-kind",
        choices=["publisher", "reviewer_supervisor", "all"],
        default="all",
        help="Daemon target for repo-owned review-channel stop actions.",
    ),
    _arg(
        "--stop-grace-seconds",
        type=float,
        default=5.0,
        help=(
            "How long `review-channel --action stop` should wait for a daemon "
            "to record stopped lifecycle state after SIGINT."
        ),
    ),
    _arg("--script-dir", help="Optional directory for generated conductor launch scripts"),
    _arg(
        "--dry-run",
        action="store_true",
        help="Build the launch bundle without opening Terminal.app windows",
    ),
    *build_bridge_control_arguments(
        _arg,
        reviewer_mode_choices=REVIEWER_MODE_CLI_CHOICES,
        default_reviewer_mode=ReviewerMode.ACTIVE_DUAL_AGENT,
    ),
]

PACKET_ARGUMENTS: list[ArgumentDef] = build_packet_arguments(_arg)
QUERY_ARGUMENTS: list[ArgumentDef] = build_query_arguments(_arg)
EVENT_CONTEXT_ARGUMENTS: list[ArgumentDef] = build_event_context_arguments(_arg)


def _register_arguments(cmd: argparse.ArgumentParser, arguments: list[ArgumentDef]) -> None:
    for arg_def in arguments:
        cmd.add_argument(*arg_def.flags, **arg_def.kwargs)


def _build_review_channel_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    cmd = sub.add_parser(
        "review-channel",
        help="Manage review-channel launch, status, and packet state",
    )
    cmd.add_argument(
        "--action",
        choices=REVIEW_ACTION_CHOICES,
        required=True,
        help="Review-channel action",
    )
    cmd.add_argument(
        "--execution-mode",
        choices=["auto", "markdown-bridge", "overlay"],
        default="auto",
        help=(
            "Auto-detect the current review-channel transport. Today only the "
            "markdown bridge is implemented; overlay mode is reserved for later."
        ),
    )
    return cmd


def add_review_channel_parser(sub: argparse._SubParsersAction) -> None:
    cmd = _build_review_channel_parser(sub)
    _register_arguments(cmd, LAUNCH_ARGUMENTS)
    _register_arguments(cmd, PACKET_ARGUMENTS)
    _register_arguments(cmd, QUERY_ARGUMENTS)
    _register_arguments(cmd, EVENT_CONTEXT_ARGUMENTS)
    add_standard_output_arguments(cmd)
