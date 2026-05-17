"""Backward-compat shim -- use `python_analysis.python_default_trap_core`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Python default-trap helper surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_analysis/python_default_trap_core.py

from python_analysis.python_default_trap_core import *
