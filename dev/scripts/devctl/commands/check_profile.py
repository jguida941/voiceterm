"""Backward-compat shim -- use `devctl.commands.check.profile` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check profile helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/profile.py

from __future__ import annotations

import sys

from .check import profile as _impl

sys.modules[__name__] = _impl
