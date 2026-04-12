"""Shared parser/helpers for naming consistency checks."""

from __future__ import annotations

from pathlib import Path

if __package__:
    from .matrix import _extract_ids, _load_matrix_ids, yaml
    from .provider import (
        _extract_provider_label_tokens,
        _parse_isolation_provider_tokens,
    )
    from .rust_parse import (
        _find_matching_brace,
        _find_matching_bracket,
        _mask_line_comments_and_strings,
        _parse_backend_registry_ids,
        _parse_enum_ids,
        _split_top_level_variants,
        _strip_leading_attributes,
    )
    from .shared import _load_module, _path_for_report
else:  # pragma: no cover - standalone script fallback
    from matrix import _extract_ids, _load_matrix_ids, yaml
    from provider import (
        _extract_provider_label_tokens,
        _parse_isolation_provider_tokens,
    )
    from rust_parse import (
        _find_matching_brace,
        _find_matching_bracket,
        _mask_line_comments_and_strings,
        _parse_backend_registry_ids,
        _parse_enum_ids,
        _split_top_level_variants,
        _strip_leading_attributes,
    )
    from shared import _load_module, _path_for_report


def _expect_str_set(
    value: object, *, label: str, source: Path, errors: list[str]
) -> set[str]:
    if not isinstance(value, (set, frozenset)):
        errors.append(f"{label} in {_path_for_report(source)} must be a set/frozenset")
        return set()
    result = {item for item in value if isinstance(item, str)}
    if len(result) != len(value):
        errors.append(
            f"{label} in {_path_for_report(source)} contains non-string values"
        )
    return result


def _expect_dict_keys(
    value: object, *, label: str, source: Path, errors: list[str]
) -> set[str]:
    if not isinstance(value, dict):
        errors.append(f"{label} in {_path_for_report(source)} must be a dict")
        return set()
    keys = {item for item in value.keys() if isinstance(item, str)}
    if len(keys) != len(value):
        errors.append(f"{label} in {_path_for_report(source)} has non-string keys")
    return keys
