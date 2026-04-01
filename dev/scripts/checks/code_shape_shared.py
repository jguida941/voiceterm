"""Backward-compat shim -- use `code_shape.code_shape_shared`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable code-shape shared-model import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/code_shape_shared.py

from code_shape.code_shape_shared import *
