"""Backward-compat shim -- use `devctl.commands.packets.loop_packet_helpers` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve loop-packet helper imports during command package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/packets/loop_packet_helpers.py

from __future__ import annotations

import sys

from .packets import loop_packet_helpers as _impl

sys.modules[__name__] = _impl
