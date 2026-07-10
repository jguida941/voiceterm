"""Backward-compat shim -- use `code_shape.code_shape_policy`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable code-shape policy import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/code_shape_policy.py

from code_shape.code_shape_policy import *
