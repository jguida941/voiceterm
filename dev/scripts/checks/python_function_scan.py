"""Backward-compat shim -- use `code_shape.python_function_scan`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable python-function-scan import surface during code-shape package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/python_function_scan.py

try:
    from code_shape.python_function_scan import *
except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
    from dev.scripts.checks.code_shape.python_function_scan import *
