"""Backward-compat shim -- use `devctl.cli_parser.entrypoint` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable devctl CLI import path while moving parser/dispatch logic out of the crowded root
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/entrypoint.py

from __future__ import annotations

import sys

from .commands.python_test_runner import command as python_test_command
from .commands.reporting import dogfood
from .commands.development import command as development_command
from .cli_parser import entrypoint as _impl

# Keep the compatibility shim visible to static command-surface guards.
COMMAND_HANDLERS = {
    "develop": development_command.run,
    "dogfood": dogfood.run,
    "test-python": python_test_command.run,
}

sys.modules[__name__] = _impl
