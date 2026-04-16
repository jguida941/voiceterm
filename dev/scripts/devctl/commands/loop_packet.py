"""Backward-compat shim -- use `devctl.commands.packets.loop_packet` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable loop-packet command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/packets/loop_packet.py

from __future__ import annotations

import sys

from .packets import loop_packet as _impl

sys.modules[__name__] = _impl
