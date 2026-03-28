#!/usr/bin/env python3
"""Registry loading helpers for the bundle-registry DRY guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Final

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REGISTRY_PATH: Final[str] = "dev/scripts/devctl/bundle_registry.py"


def resolve_registry_module_path(module_path: Path) -> Path:
    try:
        text = module_path.read_text(encoding="utf-8")
    except OSError:
        return module_path

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("# shim-target:"):
            continue

        target = line.split(":", 1)[1].strip()
        if target:
            resolved = (REPO_ROOT / target).resolve()
            repo_root_resolved = REPO_ROOT.resolve()
            try:
                resolved.relative_to(repo_root_resolved)
            except ValueError as exc:
                raise RuntimeError(
                    f"shim-target for {module_path} escapes repo root: {target}"
                ) from exc
            if not resolved.is_file():
                raise RuntimeError(
                    f"shim-target for {module_path} does not resolve to a file: {target}"
                )
            return resolved

    return module_path


def load_registry():
    module_path = resolve_registry_module_path(REPO_ROOT / REGISTRY_PATH)
    spec = importlib.util.spec_from_file_location("bundle_registry", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
