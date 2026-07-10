"""Command rendering helpers for review-channel launch flows."""

from __future__ import annotations

import os
import shlex
import sys

from ..approval_mode import DEFAULT_APPROVAL_MODE, normalize_approval_mode

_DEVCTL_INTERPRETER = os.path.basename(sys.executable)


def build_rollover_command(
    *,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
    bypass_receipt_id: str = "",
    interpreter: str = _DEVCTL_INTERPRETER,
) -> str:
    """Return the canonical self-relaunch command for planned rollovers."""
    command = [
        interpreter,
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "rollover",
        "--rollover-threshold-pct",
        str(rollover_threshold_pct),
        "--await-ack-seconds",
        str(await_ack_seconds),
        "--terminal",
        "terminal-app",
    ]
    resolved_mode = normalize_approval_mode(approval_mode, dangerous=dangerous)
    command.extend(["--approval-mode", resolved_mode])
    if bypass_receipt_id:
        command.extend(["--bypass-receipt-id", bypass_receipt_id])
    return shlex.join(command)


def build_promote_command(
    *,
    promotion_plan_rel: str,
    interpreter: str = _DEVCTL_INTERPRETER,
) -> str:
    """Return the canonical typed next-task promotion command."""
    command = [
        interpreter,
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "promote",
        "--promotion-plan",
        promotion_plan_rel,
        "--terminal",
        "none",
        "--format",
        "md",
    ]
    return shlex.join(command)


__all__ = ["build_promote_command", "build_rollover_command"]
