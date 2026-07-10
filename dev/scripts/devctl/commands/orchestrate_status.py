"""Backward-compat shim -- use `devctl.commands.reporting.orchestrate_status` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable orchestrate-status command module path during commands package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/reporting/orchestrate_status.py

from __future__ import annotations

import sys

from .reporting import orchestrate_status as _impl

sys.modules[__name__] = _impl
