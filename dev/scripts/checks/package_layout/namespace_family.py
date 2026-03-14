"""Crowded-namespace-family helpers for `check_package_layout.py`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

if __package__:
    from .bootstrap import (
        CompatibilityShimValidation,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        is_adoption_scan,
        recommended_namespace_path,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        CompatibilityShimValidation,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        is_adoption_scan,
        recommended_namespace_path,
    )


def _shim_validation_for_path(
    path: Path,
    *,
    rule: NamespaceFamilyRule,
) -> CompatibilityShimValidation:
    return detect_compatibility_shim(
        path,
        namespace_subdir=rule.namespace_subdir,
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.shim_required_metadata_fields,
    )


def _shim_metadata_guidance(missing_fields: tuple[str, ...]) -> str:
    fields_label = ", ".join(f"`shim-{field}: ...`" for field in missing_fields)
    return f" Thin compatibility wrappers here must also declare metadata fields: {fields_label}."


def collect_namespace_family_violations_from_rules(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    family_rules: tuple[NamespaceFamilyRule, ...],
) -> tuple[list[dict], list[dict], int]:
    """Report crowded flat families and block further flat growth under them."""
    base_ref = since_ref or "HEAD"
    adoption_scan = is_adoption_scan(since_ref=since_ref, head_ref=None)
    violations: list[dict] = []
    crowded_families: list[dict] = []
    candidates_scanned = 0

    for rule in family_rules:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        family_paths = sorted(
            path for path in root_abs.glob(f"{rule.flat_prefix}*.py") if path.is_file()
        )
        shim_validations = {
            path: _shim_validation_for_path(path, rule=rule) for path in family_paths
        }
        shim_count = sum(1 for validation in shim_validations.values() if validation.is_valid)
        total_family_size = len(family_paths)
        family_size = total_family_size - shim_count
        if family_size < rule.min_family_size:
            continue
        crowded_families.append(
            {
                "root": rule.root.as_posix(),
                "flat_prefix": rule.flat_prefix,
                "namespace_subdir": rule.namespace_subdir,
                "current_files": family_size,
                "total_files": total_family_size,
                "shim_files": shim_count,
                "min_family_size": rule.min_family_size,
                "enforcement_mode": rule.enforcement_mode,
                "policy_source": (
                    f"namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}"
                ),
            }
        )
        if adoption_scan:
            candidates_scanned += family_size
            namespace_root = rule.root / rule.namespace_subdir
            guidance = rule.guidance or (
                f"Flat module family `{rule.flat_prefix}*` already has {family_size} files in "
                f"`{rule.root.as_posix()}` and exceeds the crowded-family threshold."
            )
            if shim_count:
                guidance = (
                    f"{guidance} Approved compatibility shims are tracked separately "
                    f"({shim_count} excluded from the density count)."
                )
            violations.append(
                {
                    "path": rule.root.as_posix(),
                    "reason": "crowded_namespace_family_baseline_violation",
                    "guidance": (
                        f"{guidance} Reorganize the existing family under "
                        f"`{namespace_root.as_posix()}` before treating layout policy as clean."
                    ),
                    "best_practice_refs": [],
                    "base_lines": rule.min_family_size,
                    "current_lines": family_size,
                    "growth": family_size - rule.min_family_size,
                    "policy": {
                        "soft_limit": rule.min_family_size,
                        "hard_limit": rule.min_family_size,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": (
                        f"namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}"
                    ),
                    "enforcement_mode": rule.enforcement_mode,
                    "family_size": family_size,
                    "recommended_path": namespace_root.as_posix(),
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
            if relative.suffix != ".py":
                continue
            if relative.parent != rule.root:
                continue
            if not relative.name.startswith(rule.flat_prefix):
                continue
            validation = shim_validations.get(repo_root / relative)
            if validation is None:
                validation = _shim_validation_for_path(repo_root / relative, rule=rule)
            if validation.is_valid:
                continue
            candidates_scanned += 1
            is_new_file = read_text_from_ref(relative, base_ref) is None
            if rule.enforcement_mode == "freeze" and not is_new_file:
                continue
            target = recommended_namespace_path(relative, rule)
            guidance = rule.guidance or (
                f"Flat module family `{rule.flat_prefix}*` already has {family_size} files in "
                f"`{rule.root.as_posix()}`. Move implementation into "
                f"`{(rule.root / rule.namespace_subdir).as_posix()}` and keep only thin "
                "compatibility wrappers at the root when needed."
            )
            if validation.missing_metadata_fields:
                guidance += _shim_metadata_guidance(validation.missing_metadata_fields)
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": (
                        "new_flat_namespace_module_in_crowded_family"
                        if is_new_file
                        else "changed_flat_namespace_module_in_crowded_family"
                    ),
                    "guidance": f"{guidance} For example: `{target.as_posix()}`.",
                    "best_practice_refs": [],
                    "base_lines": None,
                    "current_lines": family_size,
                    "growth": None,
                    "policy": {
                        "soft_limit": rule.min_family_size,
                        "hard_limit": rule.min_family_size,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": (
                        f"namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}"
                    ),
                    "enforcement_mode": rule.enforcement_mode,
                    "family_size": family_size,
                    "recommended_path": target.as_posix(),
                    "shim_files": shim_count,
                }
            )

    return violations, crowded_families, candidates_scanned
