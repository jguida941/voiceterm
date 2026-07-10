"""Backward-compat shim -- use `devctl.cli_parser.path_audit` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root path-audit parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/path_audit.py

from .cli_parser.path_audit import *
