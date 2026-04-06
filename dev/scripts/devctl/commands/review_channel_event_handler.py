"""Backward-compat shim -- use `devctl.commands.review_channel.event_handler` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable review-channel event-handler module path during package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/review_channel/event_handler.py

from __future__ import annotations

import sys

from .review_channel import event_handler as _impl

sys.modules[__name__] = _impl
