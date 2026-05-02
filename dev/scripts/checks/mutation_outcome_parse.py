"""Backward-compat shim -- use `mutation_ralph_loop.outcome_parse`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable mutation-outcome parsing helper during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/mutation_ralph_loop/outcome_parse.py

if __package__:
    from .mutation_ralph_loop.outcome_parse import *
else:
    from mutation_ralph_loop.outcome_parse import *
