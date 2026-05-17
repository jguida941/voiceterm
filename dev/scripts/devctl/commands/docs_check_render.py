"""Backward-compat shim -- use `devctl.commands.docs.render` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable docs-check render helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/docs/render.py

from __future__ import annotations

import sys

from .docs import render as _impl

sys.modules[__name__] = _impl
