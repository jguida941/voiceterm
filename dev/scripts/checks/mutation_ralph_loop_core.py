"""Backward-compat shim -- use `mutation_ralph_loop.core`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable mutation-loop helper import surface while implementation lives under `mutation_ralph_loop/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/mutation_ralph_loop/core.py

from .mutation_ralph_loop.core import *
