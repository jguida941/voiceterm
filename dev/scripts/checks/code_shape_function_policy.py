"""Backward-compat shim -- use `code_shape.code_shape_function_policy`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable code-shape function-policy import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/code_shape_function_policy.py

try:
    from code_shape.code_shape_function_policy import *
except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
    from dev.scripts.checks.code_shape.code_shape_function_policy import *
