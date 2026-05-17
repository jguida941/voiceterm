"""Backward-compat shim -- use `devctl.commands.check.router` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-router module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/router.py

from __future__ import annotations

import sys

from .check import router as _impl

sys.modules[__name__] = _impl
