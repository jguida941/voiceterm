"""Backward-compat shim -- use `devctl.commands.process.watch` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-watch command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/process/watch.py

from __future__ import annotations

import sys

from .process import watch as _impl

sys.modules[__name__] = _impl
