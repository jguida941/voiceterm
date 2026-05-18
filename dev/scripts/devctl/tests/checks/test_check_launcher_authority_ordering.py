"""Tests for check_launcher_authority_ordering.py."""

from __future__ import annotations

import importlib.util
import sys

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = (
    REPO_ROOT / "dev/scripts/checks/launcher_authority_ordering/command.py"
)


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_launcher_authority_ordering_script",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_launcher_authority_ordering.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_repo_authority_ordering_passes() -> None:
    module = _load_script_module()

    report = module._build_report(root=REPO_ROOT)

    assert report["ok"] is True, report.get("violations")
