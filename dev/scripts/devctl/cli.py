"""Backward-compat shim -- use `devctl.cli_parser.entrypoint` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable devctl CLI import path while moving parser/dispatch logic out of the crowded root
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/entrypoint.py

from __future__ import annotations

import sys

from .commands.python_test_runner import command as python_test_command
from .commands.reporting import dogfood, progress_status
from .commands import demo as demo_command
from .commands import raw_git as raw_git_command
from .commands.bypass import command as bypass_command
from .commands.development import command as development_command
from .commands.governance import (
    exceptions as governance_exceptions,
    relaunch_loop,
    session as governance_session,
)
from .commands.remote_control import command as remote_control_command
from .commands.runtime import agent_supervise
from .commands.runtime import peer_spawn as peer_spawn_command
from .cli_parser import entrypoint as _impl

# Keep the compatibility shim visible to static command-surface guards.
COMMAND_HANDLERS = {
    "agent-supervise": agent_supervise.run,
    "peer-spawn": peer_spawn_command.run_peer_spawn,
    "peer-terminate": peer_spawn_command.run_peer_terminate,
    "bypass": bypass_command.run,
    "develop": development_command.run,
    "demo": demo_command.run,
    "dogfood": dogfood.run,
    "exceptions": governance_exceptions.run,
    "progress-status": progress_status.run,
    "raw-git": raw_git_command.run,
    "relaunch-loop": relaunch_loop.run,
    "remote-control": remote_control_command.run,
    "session": governance_session.run,
    "test-python": python_test_command.run,
}
COMMAND_HANDLER_ROWS = tuple(COMMAND_HANDLERS.items())

sys.modules[__name__] = _impl
