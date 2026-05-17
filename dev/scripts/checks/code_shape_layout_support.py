"""Backward-compat shim -- use `code_shape.code_shape_layout_support`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable code-shape layout-support import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/code_shape_layout_support.py

from code_shape.code_shape_layout_support import *
