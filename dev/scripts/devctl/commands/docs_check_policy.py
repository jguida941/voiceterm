"""Backward-compat shim -- use `devctl.commands.docs.policy` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable docs-check policy helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/docs/policy.py

from __future__ import annotations

import sys

from .docs import policy as _impl

sys.modules[__name__] = _impl
