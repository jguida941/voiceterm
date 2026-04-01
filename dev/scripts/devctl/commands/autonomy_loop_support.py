"""Backward-compat shim -- use `devctl.commands.autonomy.loop_support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy loop support path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/loop_support.py

from __future__ import annotations

import sys

from .autonomy import loop_support as _impl

sys.modules[__name__] = _impl
