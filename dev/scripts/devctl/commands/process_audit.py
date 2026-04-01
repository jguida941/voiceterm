"""Backward-compat shim -- use `devctl.commands.process.audit` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-audit command path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/process/audit.py

from __future__ import annotations

import sys

from .process import audit as _impl

sys.modules[__name__] = _impl
