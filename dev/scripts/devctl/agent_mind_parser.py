"""Backward-compat shim -- use `devctl.cli_parser.agent_mind` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root agent-mind parser import while parser wiring lives under `devctl.cli_parser`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/cli_parser/agent_mind.py

from .cli_parser.agent_mind import *
