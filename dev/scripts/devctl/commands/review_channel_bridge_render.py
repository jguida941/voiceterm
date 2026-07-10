"""Backward-compat shim -- use `devctl.commands.review_channel.bridge_render` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable review-channel bridge-render module path during package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/commands/review_channel/bridge_render.py

from __future__ import annotations

import sys

from .review_channel import bridge_render as _impl

sys.modules[__name__] = _impl
