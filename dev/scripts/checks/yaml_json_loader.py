"""Backward-compat shim -- use `compat_matrix.yaml_json_loader`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable YAML/JSON loader import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/compat_matrix/yaml_json_loader.py

from compat_matrix.yaml_json_loader import *
