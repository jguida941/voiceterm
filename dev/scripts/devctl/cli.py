"""Backward-compat shim -- use `devctl.cli_parser.entrypoint` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable devctl CLI import path while moving parser/dispatch logic out of the crowded root
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/entrypoint.py

from __future__ import annotations

import sys

from .cli_parser import entrypoint as _impl


sys.modules[__name__] = _impl
