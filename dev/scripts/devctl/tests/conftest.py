from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_repo_module(
    name: str,
    relative_path: str,
    *,
    add_module_dir_to_syspath: bool = True,
    register_in_sys_modules: bool = True,
) -> ModuleType:
    """Load a repository script/module from a repo-relative path."""
    module_path = REPO_ROOT / relative_path
    if add_module_dir_to_syspath:
        module_dir = str(module_path.parent)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    if register_in_sys_modules:
        sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def override_module_attrs(testcase: Any, module: ModuleType, /, **overrides: Any) -> None:
    """Override module attributes and restore them automatically via unittest cleanup."""
    for name, value in overrides.items():
        original = getattr(module, name)
        testcase.addCleanup(setattr, module, name, original)
        setattr(module, name, value)


def init_temp_repo_root(testcase: Any, *relative_dirs: str) -> Path:
    """Create a temporary repo-like root and register cleanup on the testcase."""
    import tempfile

    tempdir = tempfile.TemporaryDirectory()
    testcase.addCleanup(tempdir.cleanup)
    root = Path(tempdir.name)
    for relative_dir in relative_dirs:
        (root / relative_dir).mkdir(parents=True, exist_ok=True)
    return root


def init_python_guard_repo_root(testcase: Any) -> Path:
    """Create the common temp repo roots used by Python guard tests."""
    return init_temp_repo_root(
        testcase,
        "dev/scripts",
        "app/operator_console",
    )
