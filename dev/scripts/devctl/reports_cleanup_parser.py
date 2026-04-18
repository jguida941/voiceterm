"""Backward-compat shim -- use `devctl.cli_parser.reports_cleanup` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root reports-cleanup parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/reports_cleanup.py

from .cli_parser.reports_cleanup import *
