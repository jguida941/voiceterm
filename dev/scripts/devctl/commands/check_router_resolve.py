"""Backward-compat shim -- use `devctl.commands.check.router_resolve` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-router config resolver path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/router_resolve.py

from __future__ import annotations

import sys

from .check import router_resolve as _impl

sys.modules[__name__] = _impl
