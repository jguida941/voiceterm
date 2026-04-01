"""Backward-compat shim -- use `devctl.commands.autonomy.run` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy run command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/run.py

from __future__ import annotations

import sys

from .autonomy import run as _impl

sys.modules[__name__] = _impl
