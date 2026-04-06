"""Backward-compat shim -- use `devctl.commands.reporting.auto_mode_status` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable auto-mode command module path during commands package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/reporting/auto_mode_status.py

from __future__ import annotations

import sys

from .reporting import auto_mode_status as _impl

sys.modules[__name__] = _impl
