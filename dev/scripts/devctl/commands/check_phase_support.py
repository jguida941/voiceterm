"""Backward-compat shim -- use `devctl.commands.check.phase_support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check helper import during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/phase_support.py

from __future__ import annotations

import sys

from .check import phase_support as _impl

sys.modules[__name__] = _impl
