"""Backward-compat shim -- use `devctl.commands.autonomy.swarm_core` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable autonomy swarm core helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/autonomy/swarm_core.py

from __future__ import annotations

import sys

from .autonomy import swarm_core as _impl

sys.modules[__name__] = _impl
