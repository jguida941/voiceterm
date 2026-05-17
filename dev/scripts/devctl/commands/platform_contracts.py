"""Backward-compat shim -- use devctl.platform.contracts_command instead."""
# shim-owner: tooling/platform
# shim-reason: preserve the stable command import while platform-contract rendering moves under `devctl.platform`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/platform/contracts_command.py

from __future__ import annotations

from ..platform.contracts_command import *
