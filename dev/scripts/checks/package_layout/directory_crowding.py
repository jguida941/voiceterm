"""Crowded-directory policy helpers for `check_package_layout.py`."""

from __future__ import annotations

from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import (
        CompatibilityShimValidation,
        DirectoryCrowdingRule,
        detect_compatibility_shim,
        is_adoption_scan,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        CompatibilityShimValidation,
        DirectoryCrowdingRule,
        detect_compatibility_shim,
        is_adoption_scan,
    )


def _shim_validation_for_path(
    path: Path,
    *,
    rule: DirectoryCrowdingRule,
) -> CompatibilityShimValidation:
    return detect_compatibility_shim(
        path,
        namespace_subdir=rule.recommended_subdir,
        shim_contains_all=rule.shim_contains_all,
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.shim_required_metadata_fields,
    )


def _shim_metadata_guidance(missing_fields: tuple[str, ...]) -> str:
    fields_label = ", ".join(f"`shim-{field}: ...`" for field in missing_fields)
    return f" Thin compatibility wrappers here must also declare metadata fields: {fields_label}."


def collect_directory_crowding_violations_from_rules(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    crowding_rules: tuple[DirectoryCrowdingRule, ...],
) -> tuple[list[dict], list[dict], int]:
    """Report overcrowded roots and block further flat growth under them."""
    base_ref = since_ref or "HEAD"
    adoption_scan = is_adoption_scan(since_ref=since_ref, head_ref=None)
    violations: list[dict] = []
    crowded_directories: list[dict] = []
    candidates_scanned = 0

    for rule in crowding_rules:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        current_files = [
            child
            for child in root_abs.iterdir()
            if child.is_file()
            and any(fnmatch(child.name, pattern) for pattern in rule.include_globs)
        ]
        shim_validations = {
            child: _shim_validation_for_path(child, rule=rule) for child in current_files
        }
        shim_count = sum(1 for validation in shim_validations.values() if validation.is_valid)
        total_file_count = len(current_files)
        current_count = total_file_count - shim_count
        if current_count <= rule.max_files:
            continue
        crowded_directories.append(
            {
                "root": rule.root.as_posix(),
                "current_files": current_count,
                "total_files": total_file_count,
                "shim_files": shim_count,
                "max_files": rule.max_files,
                "enforcement_mode": rule.enforcement_mode,
                "policy_source": f"directory_crowding:{rule.root.as_posix()}",
            }
        )
        if adoption_scan:
            candidates_scanned += current_count
            recommended_path = (
                rule.root / rule.recommended_subdir if rule.recommended_subdir else rule.root
            )
            guidance = rule.guidance or (
                f"`{rule.root.as_posix()}` already has {current_count} files matching "
                f"{', '.join(rule.include_globs)} and exceeds the crowded-root threshold."
            )
            if shim_count:
                guidance = (
                    f"{guidance} Approved compatibility shims are tracked separately "
                    f"({shim_count} excluded from the density count)."
                )
            violations.append(
                {
                    "path": rule.root.as_posix(),
                    "reason": "crowded_directory_baseline_violation",
                    "guidance": (
                        f"{guidance} Reorganize the existing flat files before treating the "
                        f"layout as clean. Target namespace: `{recommended_path.as_posix()}`."
                    ),
                    "best_practice_refs": [],
                    "base_lines": rule.max_files,
                    "current_lines": current_count,
                    "growth": current_count - rule.max_files,
                    "policy": {
                        "soft_limit": rule.max_files,
                        "hard_limit": rule.max_files,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": f"directory_crowding:{rule.root.as_posix()}",
                    "recommended_path": recommended_path.as_posix(),
                    "enforcement_mode": rule.enforcement_mode,
                    "shim_files": shim_count,
                }
            )
            continue

        for changed_path in changed_paths:
            relative = (
                changed_path.relative_to(repo_root)
                if changed_path.is_absolute()
                else changed_path
            )
            if relative.parent != rule.root:
                continue
            if not any(fnmatch(relative.name, pattern) for pattern in rule.include_globs):
                continue
            candidates_scanned += 1
            is_new_file = read_text_from_ref(relative, base_ref) is None
            validation = shim_validations.get(repo_root / relative)
            if validation is None:
                validation = _shim_validation_for_path(repo_root / relative, rule=rule)
            if validation.is_valid:
                continue
            if rule.enforcement_mode == "freeze" and not is_new_file:
                continue
            recommended_path = (
                rule.root / rule.recommended_subdir / relative.name
                if rule.recommended_subdir
                else None
            )
            guidance = rule.guidance or (
                f"`{rule.root.as_posix()}` already has {current_count} files matching "
                f"{', '.join(rule.include_globs)} and is frozen against further flat growth."
            )
            if recommended_path is not None:
                guidance = (
                    f"{guidance} For example: `{recommended_path.as_posix()}`."
                )
            if validation.missing_metadata_fields:
                guidance += _shim_metadata_guidance(validation.missing_metadata_fields)
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": (
                        "new_file_in_crowded_directory"
                        if is_new_file
                        else "changed_file_in_crowded_directory"
                    ),
                    "guidance": guidance,
                    "best_practice_refs": [],
                    "base_lines": None,
                    "current_lines": current_count,
                    "growth": None,
                    "policy": {
                        "soft_limit": rule.max_files,
                        "hard_limit": rule.max_files,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": f"directory_crowding:{rule.root.as_posix()}",
                    "recommended_path": (
                        recommended_path.as_posix()
                        if recommended_path is not None
                        else ""
                    ),
                    "enforcement_mode": rule.enforcement_mode,
                    "shim_files": shim_count,
                }
            )

    return violations, crowded_directories, candidates_scanned
