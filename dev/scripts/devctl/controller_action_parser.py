"""Parser wiring for `devctl controller-action` arguments."""

from __future__ import annotations

import argparse


def add_controller_action_parser(sub) -> None:
    """Register the `controller-action` command parser."""
    controller_cmd = sub.add_parser(
        "controller-action",
        help=(
            "Run one policy-gated controller action "
            "(refresh-status|dispatch-report-only|pause-loop|resume-loop)"
        ),
    )
    controller_cmd.add_argument(
        "--action",
        choices=[
            "refresh-status",
            "dispatch-report-only",
            "pause-loop",
            "resume-loop",
        ],
        required=True,
        help="Controller action to execute",
    )
    controller_cmd.add_argument(
        "--repo",
        help="owner/repo (optional; falls back to env/repo detection)",
    )
    controller_cmd.add_argument(
        "--branch",
        default="develop",
        help="Target branch for dispatch-report-only action",
    )
    controller_cmd.add_argument(
        "--workflow",
        default=".github/workflows/coderabbit_ralph_loop.yml",
        help="Workflow path for dispatch-report-only action",
    )
    controller_cmd.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Max attempts forwarded to dispatch-report-only workflow input",
    )
    controller_cmd.add_argument(
        "--phone-json",
        default="dev/reports/autonomy/queue/phone/latest.json",
        help="Phone status JSON input path used by refresh-status action",
    )
    controller_cmd.add_argument(
        "--view",
        choices=["full", "compact", "trace", "actions"],
        default="compact",
        help="Status projection used by refresh-status action",
    )
    controller_cmd.add_argument(
        "--mode-file",
        default="dev/reports/autonomy/queue/phone/controller_mode.json",
        help="Local controller mode state artifact used by pause/resume actions",
    )
    controller_cmd.add_argument(
        "--remote",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Apply pause/resume writes to GitHub repo variable AUTONOMY_MODE",
    )
    controller_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended action details without executing remote writes",
    )
    controller_cmd.add_argument("--format", choices=["json", "md"], default="md")
    controller_cmd.add_argument("--output")
    controller_cmd.add_argument("--json-output")
    controller_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    controller_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
