"""Shared matrix parsing helpers for compat-matrix guards."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

try:
    from .yaml_json_loader import load_yaml_or_json
except ImportError:  # pragma: no cover
    from yaml_json_loader import load_yaml_or_json


def path_for_report(path: Path) -> str:
    """Render a repo-relative path when possible for guard output."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_matrix(
    path: Path,
    *,
    yaml_module=None,
) -> tuple[dict | None, str | None]:
    """Load a compat-matrix YAML/JSON object from disk."""
    if not path.exists():
        return None, f"missing matrix file: {path_for_report(path)}"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"failed to parse matrix file: {exc}"
    try:
        payload = load_yaml_or_json(raw, yaml_module=yaml_module)
    # broad-except: allow reason=compat-matrix guards must normalize parser backend failures into one stable report string fallback=return a stable parse error tuple for guard reporting.
    except Exception as exc:
        return None, f"failed to parse matrix file: {exc}"
    if not isinstance(payload, dict):
        return None, "matrix root must be an object"
    return payload, None


def coerce_list_field(payload: dict, field_name: str, errors: list[str]) -> list:
    """Read a list field or record a schema error."""
    value = payload.get(field_name, [])
    if isinstance(value, list):
        return value
    errors.append(f"`{field_name}` must be a list")
    return []
