"""Backward-compat shim -- use `devctl.cli_parser.entrypoint` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable devctl CLI import path while moving parser/dispatch logic out of the crowded root
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/entrypoint.py

from __future__ import annotations

import sys

from .commands.python_test_runner import command as python_test_command
from .commands.reporting import dogfood, progress_status
from .commands.development import command as development_command
from .commands.governance import relaunch_loop, session as governance_session
from .commands.remote_control import command as remote_control_command
from .cli_parser import entrypoint as _impl

# Keep the compatibility shim visible to static command-surface guards.
COMMAND_HANDLER_ROWS = (
    ("develop", development_command.run),
    ("dogfood", dogfood.run),
    ("progress-status", progress_status.run),
    ("relaunch-loop", relaunch_loop.run),
    ("remote-control", remote_control_command.run),
    ("session", governance_session.run),
    ("test-python", python_test_command.run),
)
COMMAND_HANDLERS = dict(COMMAND_HANDLER_ROWS)

sys.modules[__name__] = _impl
