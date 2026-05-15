"""Parser wiring for the transitional `devctl review-channel` surface."""

from __future__ import annotations

import argparse
from typing import Any

from ..common import add_standard_output_arguments
from .parser_argument_groups import (
    build_event_context_arguments,
    build_packet_arguments,
    build_query_arguments,
)
from .parser_launch_arguments import build_launch_arguments
from .parser_types import ArgumentDef


AGENT_CHOICES = ("codex", "claude", "operator", "system")
REVIEW_ACTION_CHOICES = (
    "launch",
    "rollover",
    "recover",
    "status",
    "doctor",
    "implementer-wait",
    "reviewer-wait",
    "ensure",
    "stop",
    "reviewer-heartbeat",
    "reviewer-checkpoint",
    "implementer-ack",
    "reset-implementer-state",
    "reset-roles",
    "promote",
    "post",
    "watch",
    "inbox",
    "operator-inbox",
    "sync-status",
    "expire-packets",
    "ack",
    "dismiss",
    "apply",
    "history",
    "show",
    "check-ack-freshness",
    "bridge-poll",
    "render-bridge",
    "attach-remote-control",
)


def _arg(*flags: str, **kwargs: Any) -> ArgumentDef:
    return ArgumentDef(flags=tuple(flags), kwargs=kwargs)


LAUNCH_ARGUMENTS: list[ArgumentDef] = build_launch_arguments(_arg)

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
    cmd.add_argument(
        "--ack-freshness-mode",
        choices=["on_demand", "scheduled", "disabled"],
        default="on_demand",
        help=(
            "Automation-toggle mode for `--action check-ack-freshness`; "
            "scheduled is reserved for poller use."
        ),
    )
    cmd.add_argument(
        "--recovery-probe",
        action="store_true",
        help=(
            "Attach the CLIHealthProbeAutomation recovery probe to "
            "`review-channel --action status` output."
        ),
    )
    cmd.add_argument(
        "--recovery-probe-mode",
        choices=["scheduled", "on_error", "disabled"],
        default="scheduled",
        help=(
            "P152 toggle mode for `--recovery-probe`: scheduled always "
            "emits probe evidence, on_error emits active recovery evidence "
            "only when status detects a recovery condition, and disabled "
            "records a disabled probe."
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
