"""Backward-compat shim -- use `devctl.commands.release.guard` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release guard helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/guard.py

from __future__ import annotations

import sys

from .release import guard as _impl

sys.modules[__name__] = _impl
