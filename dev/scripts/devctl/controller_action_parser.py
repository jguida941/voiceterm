"""Backward-compat shim -- use `devctl.cli_parser.controller_action` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root controller-action parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/controller_action.py

from .cli_parser.controller_action import *
