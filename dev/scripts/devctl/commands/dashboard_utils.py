"""Backward-compat shim -- use `devctl.commands.reporting.dashboard_utils`."""

# shim-reason: preserve dashboard utility imports while reporting helpers live under `commands/reporting`
# shim-owner: tooling/devctl
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/reporting/dashboard_utils.py

import sys as _sys

from .reporting import dashboard_utils as _impl

_sys.modules[__name__] = _impl
