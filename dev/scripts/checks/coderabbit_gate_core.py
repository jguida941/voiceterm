"""Backward-compat shim -- use `coderabbit.gate_core`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable CodeRabbit gate-core import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/coderabbit/gate_core.py

from coderabbit.gate_core import *
