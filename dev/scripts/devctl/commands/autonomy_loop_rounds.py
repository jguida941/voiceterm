"""Backward-compat shim -- use `devctl.commands.autonomy.loop_rounds` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy loop-round helpers during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/loop_rounds.py

from __future__ import annotations

import sys

from .autonomy import loop_rounds as _impl

sys.modules[__name__] = _impl
