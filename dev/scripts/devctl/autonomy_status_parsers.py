"""Parser helpers for autonomy status/report command surfaces."""

from __future__ import annotations

import argparse


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
