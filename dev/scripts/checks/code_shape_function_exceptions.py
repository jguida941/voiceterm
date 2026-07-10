"""Backward-compat shim -- use `code_shape.code_shape_function_exceptions`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable code-shape function-exceptions import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/code_shape_function_exceptions.py

from code_shape.code_shape_function_exceptions import *
