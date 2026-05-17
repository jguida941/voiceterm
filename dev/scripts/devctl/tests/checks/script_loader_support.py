"""Shared repository-script loader helpers for check tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_module_from_repo_path(
    *,
    module_name: str,
    repo_root: Path,
    relative_path: str,
):
    """Load one repo-owned script module from a repo-relative path."""
    module_path = (repo_root / relative_path).resolve()
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
