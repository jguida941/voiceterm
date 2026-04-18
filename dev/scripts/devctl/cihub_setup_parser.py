"""Backward-compat shim -- use `devctl.cli_parser.cihub_setup` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root cihub-setup parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/cihub_setup.py

from .cli_parser.cihub_setup import *
