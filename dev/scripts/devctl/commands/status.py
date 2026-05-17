"""Backward-compat shim -- use `devctl.commands.reporting.status` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable status command module path during commands package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/reporting/status.py

from __future__ import annotations

import sys

from .reporting import status as _impl

sys.modules[__name__] = _impl
