"""Backward-compat shim -- use `devctl.commands.release.ship_steps` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable ship step helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/ship_steps.py

from __future__ import annotations

import sys

from .release import ship_steps as _impl

sys.modules[__name__] = _impl
