"""Backward-compat shim -- use `devctl.commands.process.cleanup` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-cleanup command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/process/cleanup.py

from __future__ import annotations

import sys

from .process import cleanup as _impl

sys.modules[__name__] = _impl
