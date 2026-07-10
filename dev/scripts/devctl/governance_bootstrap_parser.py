"""Backward-compat shim -- use `devctl.cli_parser.governance_bootstrap` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root governance-bootstrap parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/governance_bootstrap.py

from .cli_parser.governance_bootstrap import *
