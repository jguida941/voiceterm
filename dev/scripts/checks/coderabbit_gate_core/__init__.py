"""Core helpers shared by CodeRabbit workflow gate scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

try:
    from ..coderabbit_gate_support import render_report_md
except ImportError:  # pragma: no cover - direct script fallback
    from coderabbit_gate_support import render_report_md

_LEGACY_MODULE_NAME = "dev.scripts.checks._coderabbit_gate_core_legacy"


def _load_legacy_module() -> ModuleType:
    module_path = Path(__file__).resolve().parent.parent / "coderabbit_gate_core.py"
    spec = importlib.util.spec_from_file_location(_LEGACY_MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load legacy CodeRabbit core: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LEGACY = _load_legacy_module()

looks_like_sha = _LEGACY.looks_like_sha
parse_iso = _LEGACY.parse_iso
resolve_sha = _LEGACY.resolve_sha
resolve_branch = _LEGACY.resolve_branch
current_branch_name = _LEGACY.current_branch_name
gh_run_list = _LEGACY.gh_run_list
build_report = _LEGACY.build_report
