"""Backward-compat shim -- use `devctl.commands.check.support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check support helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/support.py

from __future__ import annotations

import sys

from .check import support as _impl

sys.modules[__name__] = _impl
