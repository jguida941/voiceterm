"""Backward-compat shim -- use `devctl.commands.release.ship` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable ship command module path during commands package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/release/ship.py

from __future__ import annotations

import sys

from .release import ship as _impl

sys.modules[__name__] = _impl
