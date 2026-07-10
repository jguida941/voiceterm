"""Backward-compat shim -- use `devctl.commands.check.process_sweep` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check process-sweep helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/process_sweep.py

from __future__ import annotations

import sys

from .check import process_sweep as _impl

sys.modules[__name__] = _impl
