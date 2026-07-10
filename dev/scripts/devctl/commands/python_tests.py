"""Backward-compat shim -- use commands.python_test_runner.command instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable test-python command import while the implementation lives under `commands/python_test_runner`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/python_test_runner/command.py

from __future__ import annotations

import sys

from .python_test_runner import command as _impl

sys.modules[__name__] = _impl
