"""Shared bootstrap helpers for check scripts."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ENGINE_ROOT = Path(__file__).resolve().parents[3]


def _resolve_repo_root() -> Path:
    """Resolve repo root from DEVCTL_REPO_ROOT env var or file-path fallback."""
    import os
    env_root = os.environ.get("DEVCTL_REPO_ROOT")
    if env_root:
        resolved = Path(env_root).resolve()
        # Keep the engine root on sys.path so engine modules stay importable
        engine_str = str(_ENGINE_ROOT)
        if engine_str not in sys.path:
            sys.path.insert(0, engine_str)
        return resolved
    return _ENGINE_ROOT


REPO_ROOT = _resolve_repo_root()


def _top_level_module_name(module_name: str) -> str:
    return module_name.split(".", 1)[0]


def ensure_repo_root_on_syspath(repo_root: Path) -> None:
    """Add the repo root to `sys.path` once for repo-package imports."""
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def import_local_or_repo_module(
    local_module_name: str,
    repo_module_name: str,
    *,
    repo_root: Path,
) -> Any:
    """Import a helper module in local-script or repo-package execution modes."""
    try:
        return importlib.import_module(local_module_name)
    except ModuleNotFoundError as exc:
        if exc.name != _top_level_module_name(local_module_name):
            raise
    ensure_repo_root_on_syspath(repo_root)
    return importlib.import_module(repo_module_name)


def import_repo_module(module_name: str, *, repo_root: Path) -> Any:
    """Import a repo-owned package module, repairing `sys.path` only when needed."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != _top_level_module_name(module_name):
            raise
    ensure_repo_root_on_syspath(repo_root)
    return importlib.import_module(module_name)


def import_attr(module_name: str, attr_name: str) -> Any:
    """Import an attribute from local-script or package execution contexts."""
    module = import_local_or_repo_module(
        module_name,
        f"dev.scripts.checks.{module_name}",
        repo_root=REPO_ROOT,
    )
    return getattr(module, attr_name)


def resolve_quality_scope_roots(
    scope_id: str,
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    """Resolve repo-configured quality-scope roots for a guard or probe."""
    quality_policy = import_repo_module(
        "dev.scripts.devctl.quality_policy",
        repo_root=repo_root,
    )
    return tuple(
        quality_policy.resolve_quality_scope_roots(
            scope_id,
            repo_root=repo_root,
        )
    )


def resolve_guard_config(
    script_id: str,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Resolve repo-configured per-script settings for a guard or probe."""
    quality_policy = import_repo_module(
        "dev.scripts.devctl.quality_policy",
        repo_root=repo_root,
    )
    config = quality_policy.resolve_guard_config(
        script_id,
        repo_root=repo_root,
    )
    return dict(config) if isinstance(config, dict) else {}


def utc_timestamp() -> str:
    """Return a stable UTC ISO-8601 timestamp for JSON/markdown reports."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_since_ref_format_parser(description: str) -> argparse.ArgumentParser:
    """Build the standard since-ref/head-ref/format parser shared by guards."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used with --since-ref")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def is_under_target_roots(path: Path, *, repo_root: Path, target_roots: tuple[Path, ...]) -> bool:
    """Return whether a repo path falls within one of the configured roots."""
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    return any(relative == root or root in relative.parents for root in target_roots)


def emit_runtime_error(command: str, output_format: str, error: str) -> int:
    """Emit a consistent error report for guard script runtime failures."""
    report = {
        "command": command,
        "timestamp": utc_timestamp(),
        "ok": False,
        "error": error,
    }
    if output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(f"# {command}\n")
        print(f"- ok: False\n- error: {report['error']}")
    return 2
