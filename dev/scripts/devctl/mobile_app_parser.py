"""Parser wiring for `devctl mobile-app`."""

from __future__ import annotations

import argparse


def add_mobile_app_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `mobile-app` parser."""
    cmd = sub.add_parser(
        "mobile-app",
        help=(
            "Run the real iPhone app simulator demo or a physical-device install wizard"
        ),
    )
    cmd.add_argument(
        "--action",
        choices=["simulator-demo", "device-wizard", "device-install", "list-devices"],
        required=True,
        help="Mobile app action to run",
    )
    cmd.add_argument(
        "--device-id",
        help="Optional simulator or physical-device identifier",
    )
    cmd.add_argument(
        "--open-xcode",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Open the Xcode project during device-wizard flow",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended actions without running them",
    )
    cmd.add_argument(
        "--live-review",
        action="store_true",
        help=(
            "Refresh live review-channel state before simulator sync so the app "
            "shows the current Ralph/review loop data from this repo"
        ),
    )
    cmd.add_argument(
        "--development-team",
        help=(
            "Apple Development Team ID to use for physical-device builds; "
            "falls back to VOICETERM_IOS_DEVELOPMENT_TEAM when omitted"
        ),
    )
    cmd.add_argument(
        "--allow-provisioning-updates",
        action="store_true",
        help="Pass -allowProvisioningUpdates during physical-device builds",
    )
    cmd.add_argument("--format", choices=["json", "md"], default="md")
    cmd.add_argument("--output")
    cmd.add_argument("--json-output")
    cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
