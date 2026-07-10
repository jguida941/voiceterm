"""Backward-compat shim -- use `devctl.commands.release.ship_verify_pypi_step` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable ship verify-pypi helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/ship_verify_pypi_step.py

from __future__ import annotations

import sys

from .release import ship_verify_pypi_step as _impl

sys.modules[__name__] = _impl
