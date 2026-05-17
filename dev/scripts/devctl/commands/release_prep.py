"""Backward-compat shim -- use `devctl.commands.release.prep` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release prep helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/prep.py

from __future__ import annotations

import sys

from .release import prep as _impl

sys.modules[__name__] = _impl
