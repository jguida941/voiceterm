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
from .promotion import DEFAULT_PROMOTION_PLAN_REL
from .state import DEFAULT_REVIEW_STATUS_DIR_REL


@dataclass(frozen=True, slots=True)
class ArgumentDef:
    flags: tuple[str, ...]
    kwargs: dict[str, Any]


AGENT_CHOICES = ("codex", "claude", "operator", "system")
REVIEW_ACTION_CHOICES = (
    "launch",
    "rollover",
    "status",
    "promote",
    "post",
    "watch",
    "inbox",
    "ack",
    "dismiss",
    "apply",
    "history",
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
        default=DEFAULT_PROMOTION_PLAN_REL,
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
    _arg("--script-dir", help="Optional directory for generated conductor launch scripts"),
    _arg(
        "--dry-run",
        action="store_true",
        help="Build the launch bundle without opening Terminal.app windows",
    ),
    _arg(
        "--refresh-bridge-heartbeat-if-stale",
        action="store_true",
        help=(
            "When the markdown bridge is otherwise launchable but reviewer heartbeat "
            "metadata is stale or missing, refresh it before launch continues."
        ),
    ),
    _arg(
        "--auto-promote",
        action="store_true",
        help=(
            "When the bridge shows an accepted verdict with no open findings "
            "and an idle instruction, automatically promote the next unchecked "
            "plan item into the bridge before continuing."
        ),
    ),
]

PACKET_ARGUMENTS: list[ArgumentDef] = [
    _arg("--from-agent", choices=AGENT_CHOICES, help="Posting agent for packet writes"),
    _arg("--to-agent", choices=AGENT_CHOICES, help="Target agent for packet writes"),
    _arg(
        "--kind",
        choices=[
            "finding",
            "question",
            "draft",
            "action_request",
            "approval_request",
            "decision",
            "system_notice",
        ],
        help="Review packet kind for `--action post`",
    ),
    _arg("--summary", help="Short packet summary for post/watch/history views"),
    _arg("--body", help="Inline packet body for `--action post`"),
    _arg("--body-file", help="Optional UTF-8 markdown/text file used as the packet body"),
    _arg("--evidence-ref", action="append", default=[], help="Repeatable evidence reference"),
    _arg("--confidence", type=float, default=1.0, help="Packet confidence between 0.0 and 1.0"),
    _arg("--requested-action", default="review_only", help="Requested action on a packet"),
    _arg(
        "--policy-hint",
        choices=["review_only", "stage_draft", "operator_approval_required", "safe_auto_apply"],
        default="review_only",
        help="Policy hint attached to a packet",
    ),
    _arg(
        "--approval-required",
        action="store_true",
        help="Mark packet as requiring explicit operator approval",
    ),
    _arg(
        "--context-pack-ref",
        action="append",
        default=[],
        help=(
            "Repeatable attached memory-pack ref in kind:path form, for example "
            "`task_pack:.voiceterm/memory/exports/task_pack.json`"
        ),
    ),
    _arg(
        "--context-pack-adapter-profile",
        choices=["canonical", "codex", "claude", "gemini"],
        default="canonical",
        help="Adapter profile recorded on attached context-pack refs",
    ),
]

QUERY_ARGUMENTS: list[ArgumentDef] = [
    _arg("--packet-id", help="Packet id for ack/dismiss/apply or explicit post id override"),
    _arg("--trace-id", help="Trace id for history queries or explicit post trace override"),
    _arg("--actor", choices=AGENT_CHOICES, help="Actor applying an ack/dismiss/apply transition"),
    _arg("--target", choices=AGENT_CHOICES, help="Target agent filter for inbox/watch"),
    _arg(
        "--status",
        choices=["pending", "acked", "dismissed", "applied", "expired"],
        help="Packet status filter for inbox/watch",
    ),
    _arg("--limit", type=int, default=20, help="Limit rows returned by inbox/history/watch"),
    _arg(
        "--follow",
        action="store_true",
        help="Request a watch/follow view; current CLI emits one snapshot per run",
    ),
    _arg("--stale-minutes", type=int, default=30, help="Staleness threshold for watch views"),
]

EVENT_CONTEXT_ARGUMENTS: list[ArgumentDef] = [
    _arg(
        "--session-id",
        default=DEFAULT_REVIEW_CHANNEL_SESSION_ID,
        help="Stable session id for event-backed packet writes",
    ),
    _arg(
        "--plan-id",
        default=DEFAULT_REVIEW_CHANNEL_PLAN_ID,
        help="Plan id recorded on event-backed packet writes",
    ),
    _arg("--controller-run-id", help="Optional controller run id on packet writes"),
    _arg(
        "--expires-in-minutes",
        type=int,
        default=DEFAULT_PACKET_TTL_MINUTES,
        help="Expiry horizon for newly posted packets",
    ),
]


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
