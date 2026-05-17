"""Backward-compat shim -- use devctl.platform.system_map_command instead."""
# shim-owner: tooling/platform
# shim-reason: preserve the stable command import while system-map rendering lives under `devctl.platform`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/platform/system_map_command.py

from __future__ import annotations

from ..platform.system_map_command import *
