"""Backward-compat shim -- use `devctl.commands.check.router_render` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-router render helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/router_render.py

from __future__ import annotations

import sys

from .check import router_render as _impl

sys.modules[__name__] = _impl
