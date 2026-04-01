"""Backward-compat shim -- use `devctl.commands.release.gates` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release-gates module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/gates.py

from __future__ import annotations

import sys

from .release import gates as _impl

sys.modules[__name__] = _impl
