"""Backward-compat shim -- use `devctl.cli_parser.rollout_tail` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root rollout-tail parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/rollout_tail.py

from .cli_parser.rollout_tail import *
