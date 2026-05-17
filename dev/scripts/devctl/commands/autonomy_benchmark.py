"""Backward-compat shim -- use `devctl.commands.autonomy.benchmark` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy benchmark command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/benchmark.py

from __future__ import annotations

import sys

from .autonomy import benchmark as _impl

sys.modules[__name__] = _impl
