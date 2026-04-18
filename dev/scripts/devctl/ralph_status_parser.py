"""Backward-compat shim -- use `devctl.cli_parser.ralph_status` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root ralph-status parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/ralph_status.py

from .cli_parser.ralph_status import *
