"""Matrix/config extraction helpers for naming-consistency checks."""

from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

if __package__:
    from .shared import _path_for_report
    from .yaml_json_loader import load_yaml_or_json
else:  # pragma: no cover - standalone script fallback
    from shared import _path_for_report
    from yaml_json_loader import load_yaml_or_json


def _extract_ids(items: object, section: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        errors.append(f"`{section}` must be a list")
        return set()
    values: set[str] = set()
    invalid = 0
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            invalid += 1
            continue
        values.add(item["id"])
    if invalid:
        errors.append(f"`{section}` contains {invalid} entries without a string `id`")
    return values


def _load_matrix_ids(path: Path) -> tuple[set[str], set[str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return set(), set(), [f"missing matrix file: {_path_for_report(path)}"]
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return set(), set(), [f"failed to read matrix file: {exc}"]
    try:
        payload = load_yaml_or_json(raw, yaml_module=yaml)
    except Exception as exc:  # broad-except: allow reason=compatibility-matrix parsing may fail through yaml/json backends with heterogeneous exception types fallback=return one stable guard parse error
        return set(), set(), [f"failed to parse matrix file: {exc}"]
    if not isinstance(payload, dict):
        return set(), set(), ["matrix root must be an object"]
    return (
        _extract_ids(payload.get("hosts"), "hosts", errors),
        _extract_ids(payload.get("providers"), "providers", errors),
        errors,
    )
