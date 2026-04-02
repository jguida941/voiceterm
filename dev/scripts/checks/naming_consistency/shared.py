"""Shared file/system helpers for naming-consistency checks."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_module(path: Path, module_name: str) -> tuple[ModuleType | None, str | None]:
    if not path.exists():
        return None, f"missing required module: {_path_for_report(path)}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None, f"failed to load module spec: {_path_for_report(path)}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - broad-except: allow reason=guard module loading must collapse arbitrary import-time failures into one deterministic error string fallback=return structured module-load failure
        return None, f"failed to import {_path_for_report(path)}: {exc}"
    return module, None
