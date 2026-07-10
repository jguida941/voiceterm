"""Backward-compat shim -- use `devctl.commands.docs.support` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable docs-check support helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/docs/support.py

from __future__ import annotations

import sys

from .docs import support as _impl

sys.modules[__name__] = _impl
