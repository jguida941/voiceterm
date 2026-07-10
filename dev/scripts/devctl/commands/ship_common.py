"""Backward-compat shim -- use `devctl.commands.release.ship_common` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable ship common helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/ship_common.py

from __future__ import annotations

import sys

from .release import ship_common as _impl

sys.modules[__name__] = _impl
