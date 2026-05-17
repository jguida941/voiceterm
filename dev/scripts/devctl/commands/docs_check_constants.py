"""Backward-compat shim -- use `devctl.commands.docs.check_constants` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable docs-check constants helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/docs/check_constants.py

from __future__ import annotations

import sys

from .docs import check_constants as _impl

sys.modules[__name__] = _impl
