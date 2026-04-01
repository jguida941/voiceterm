"""Backward-compat shim -- use `devctl.commands.check.progress` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check progress helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/progress.py

from __future__ import annotations

import sys

from .check import progress as _impl

sys.modules[__name__] = _impl
