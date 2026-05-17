"""YAML/JSON loader wrapper for naming-consistency checks."""

from __future__ import annotations

try:
    from compat_matrix.yaml_json_loader import load_yaml_or_json
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.compat_matrix.yaml_json_loader import load_yaml_or_json

__all__ = ["load_yaml_or_json"]
