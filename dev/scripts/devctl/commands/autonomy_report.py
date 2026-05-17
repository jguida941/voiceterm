"""Backward-compat shim -- use `devctl.commands.autonomy.report` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy report command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/report.py

from __future__ import annotations

import sys

from .autonomy import report as _impl

sys.modules[__name__] = _impl
