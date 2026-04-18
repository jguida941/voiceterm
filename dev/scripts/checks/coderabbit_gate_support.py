"""Backward-compat shim -- use `coderabbit.gate_support`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable CodeRabbit gate-support import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/coderabbit/gate_support.py

try:
    from dev.scripts.checks.coderabbit.gate_support import *
except ModuleNotFoundError:  # pragma: no cover - direct script fallback
    from coderabbit.gate_support import *
