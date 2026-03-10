"""Parser helpers for autonomy status/report command surfaces."""

from __future__ import annotations

import argparse

from ..approval_mode import APPROVAL_MODE_CHOICES, DEFAULT_APPROVAL_MODE
from ..review_channel.core import DEFAULT_BRIDGE_REL, DEFAULT_REVIEW_CHANNEL_REL
from ..review_channel.state import DEFAULT_REVIEW_STATUS_DIR_REL


def add_autonomy_report_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `autonomy-report` parser."""
    autonomy_report_cmd = sub.add_parser(
        "autonomy-report",
        help="Build a dated human-readable autonomy bundle (summary + charts)",
    )
    autonomy_report_cmd.add_argument(
        "--source-root",
        default="dev/reports/autonomy",
        help="Source directory containing loop/orchestration artifacts",
    )
    autonomy_report_cmd.add_argument(
        "--library-root",
        default="dev/reports/autonomy/library",
        help="Output directory for dated report bundles",
    )
    autonomy_report_cmd.add_argument(
        "--run-label",
        help="Optional explicit bundle label (default: UTC timestamp)",
    )
    autonomy_report_cmd.add_argument(
        "--event-log",
        default="dev/reports/audits/devctl_events.jsonl",
        help="Audit event log path for event-count context",
    )
    autonomy_report_cmd.add_argument(
        "--refresh-orchestrate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Refresh orchestrate-status/watch JSON snapshots before bundling",
    )
    autonomy_report_cmd.add_argument(
        "--copy-sources",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Copy source JSON artifacts into the dated bundle",
    )
    autonomy_report_cmd.add_argument(
        "--charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate matplotlib charts in the dated bundle",
    )
    autonomy_report_cmd.add_argument("--format", choices=["json", "md"], default="md")
    autonomy_report_cmd.add_argument("--output")
    autonomy_report_cmd.add_argument("--json-output")
    autonomy_report_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    autonomy_report_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )


def add_phone_status_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `phone-status` parser."""
    phone_status_cmd = sub.add_parser(
        "phone-status",
        help="Render phone-friendly autonomy status views from latest queue artifacts",
    )
    phone_status_cmd.add_argument(
        "--phone-json",
        default="dev/reports/autonomy/queue/phone/latest.json",
        help="Path to phone status JSON artifact emitted by autonomy-loop",
    )
    phone_status_cmd.add_argument(
        "--view",
        choices=["full", "compact", "trace", "actions"],
        default="compact",
        help="Select the rendered status projection",
    )
    phone_status_cmd.add_argument(
        "--emit-projections",
        help=(
            "Optional output directory for projection files "
            "(full.json, compact.json, trace.ndjson, actions.json, latest.md)"
        ),
    )
    phone_status_cmd.add_argument("--format", choices=["json", "md"], default="md")
    phone_status_cmd.add_argument("--output")
    phone_status_cmd.add_argument("--json-output")
    phone_status_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    phone_status_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )


def add_mobile_status_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `mobile-status` parser."""
    mobile_status_cmd = sub.add_parser(
        "mobile-status",
        help=(
            "Render one phone-safe merged control snapshot from autonomy "
            "phone-status and review-channel state"
        ),
    )
    mobile_status_cmd.add_argument(
        "--phone-json",
        default="dev/reports/autonomy/queue/phone/latest.json",
        help="Path to phone status JSON artifact emitted by autonomy-loop",
    )
    mobile_status_cmd.add_argument(
        "--review-channel-path",
        default=DEFAULT_REVIEW_CHANNEL_REL,
        help="Path to the active review-channel plan markdown",
    )
    mobile_status_cmd.add_argument(
        "--bridge-path",
        default=DEFAULT_BRIDGE_REL,
        help="Path to the live markdown bridge file",
    )
    mobile_status_cmd.add_argument(
        "--review-status-dir",
        default=DEFAULT_REVIEW_STATUS_DIR_REL,
        help=(
            "Directory where refreshed latest review-channel projections are written "
            "before merge"
        ),
    )
    mobile_status_cmd.add_argument(
        "--execution-mode",
        choices=["auto", "markdown-bridge", "overlay"],
        default="auto",
        help=(
            "Review-channel transport mode. 'markdown-bridge' forces the bridge "
            "path for status even when event artifacts exist on disk."
        ),
    )
    mobile_status_cmd.add_argument(
        "--state-backend",
        choices=["auto", "markdown-bridge", "review-event", "unified-json"],
        default="auto",
        help=(
            "State backend experiment to use for mobile projections. "
            "'auto' keeps current behavior, 'review-event' forces event-backed "
            "review state, and 'unified-json' loads one merged experimental "
            "controller_state-style payload from --unified-state-json."
        ),
    )
    mobile_status_cmd.add_argument(
        "--unified-state-json",
        help=(
            "Path to an experimental merged controller/review JSON payload used "
            "when --state-backend=unified-json"
        ),
    )
    mobile_status_cmd.add_argument(
        "--approval-mode",
        choices=list(APPROVAL_MODE_CHOICES),
        default=DEFAULT_APPROVAL_MODE,
        help=(
            "Shared approval policy to project into phone/PyQt/client surfaces. "
            "This does not bypass destructive/publish confirmation."
        ),
    )
    mobile_status_cmd.add_argument(
        "--view",
        choices=["full", "compact", "actions", "alert"],
        default="compact",
        help="Select the rendered mobile projection",
    )
    mobile_status_cmd.add_argument(
        "--emit-projections",
        help=(
            "Optional output directory for merged mobile projection files "
            "(full.json, compact.json, alert.json, actions.json, latest.md)"
        ),
    )
    mobile_status_cmd.add_argument("--format", choices=["json", "md"], default="md")
    mobile_status_cmd.add_argument("--output")
    mobile_status_cmd.add_argument("--json-output")
    mobile_status_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    mobile_status_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
