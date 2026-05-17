"""Backward-compat shim -- use `devctl.commands.check.router_constants` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-router constants path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/router_constants.py

from __future__ import annotations

import sys

from .check import router_constants as _impl

sys.modules[__name__] = _impl
