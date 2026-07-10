"""Rule loading for the compatibility-shim review probe."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import (
        STANDARD_SHIM_METADATA_FIELDS,
        load_directory_crowding_rules,
        load_namespace_family_rules,
        resolve_guard_config,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        STANDARD_SHIM_METADATA_FIELDS,
        load_directory_crowding_rules,
        load_namespace_family_rules,
        resolve_guard_config,
    )

DEFAULT_ROOT_SHIM_BUDGET = 8
DEFAULT_FAMILY_SHIM_BUDGET = 4
DEFAULT_SHIM_MAX_NONBLANK_LINES = 6


@dataclass(frozen=True)
class ShimRootRule:
    root: Path
    include_globs: tuple[str, ...]
    namespace_subdir: str = ""
    shim_contains_all: tuple[str, ...] = ()
    shim_max_nonblank_lines: int = DEFAULT_SHIM_MAX_NONBLANK_LINES
    required_metadata_fields: tuple[str, ...] = STANDARD_SHIM_METADATA_FIELDS
    max_shims: int = DEFAULT_ROOT_SHIM_BUDGET
    guidance: str = ""
    policy_source: str = ""


@dataclass(frozen=True)
class ShimFamilyRule:
    root: Path
    flat_prefix: str
    namespace_subdir: str
    shim_max_nonblank_lines: int = DEFAULT_SHIM_MAX_NONBLANK_LINES
    required_metadata_fields: tuple[str, ...] = STANDARD_SHIM_METADATA_FIELDS
    max_shims: int = DEFAULT_FAMILY_SHIM_BUDGET
    guidance: str = ""
    policy_source: str = ""


@dataclass(frozen=True)
class ShimFinding:
    relative_path: Path
    metadata: dict[str, str]
    missing_metadata_fields: tuple[str, ...]
    is_valid: bool


@dataclass(frozen=True)
class PublicShimContract:
    path: Path | None = None
    glob: str = ""
    reason: str = ""
    policy_source: str = ""

    def matches(self, relative_path: Path) -> bool:
        if self.path is not None and relative_path == self.path:
            return True
        return bool(self.glob) and fnmatch(relative_path.as_posix(), self.glob)


@dataclass(frozen=True)
class ShimProbePolicy:
    root_rules: tuple[ShimRootRule, ...]
    family_rules: tuple[ShimFamilyRule, ...]
    public_contracts: tuple[PublicShimContract, ...] = ()
    usage_scan_exclude_roots: tuple[Path, ...] = ()


def _coerce_path(value: object) -> Path | None:
    text = str(value or "").strip()
    return Path(text) if text else None


def _coerce_positive_int(value: object, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _coerce_str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _coerce_path_tuple(value: object) -> tuple[Path, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(path for item in value for path in (_coerce_path(item),) if path is not None)


def _default_required_metadata_fields(config: dict[str, object]) -> tuple[str, ...]:
    configured = _coerce_str_tuple(config.get("default_required_metadata_fields"))
    return configured or STANDARD_SHIM_METADATA_FIELDS


def _load_probe_root_rules(
    config: dict[str, object],
    *,
    default_required_metadata_fields: tuple[str, ...],
    default_root_budget: int,
) -> tuple[ShimRootRule, ...]:
    raw_rules = config.get("root_rules")
    if not isinstance(raw_rules, list):
        return ()
    rules: list[ShimRootRule] = []
    for item in raw_rules:
        if not isinstance(item, dict):
            continue
        root = _coerce_path(item.get("root"))
        include_globs = _coerce_str_tuple(item.get("include_globs")) or ("*.py",)
        if root is None:
            continue
        rules.append(
            ShimRootRule(
                root=root,
                include_globs=include_globs,
                namespace_subdir=str(item.get("namespace_subdir") or "").strip(),
                shim_contains_all=_coerce_str_tuple(item.get("shim_contains_all")),
                shim_max_nonblank_lines=_coerce_positive_int(
                    item.get("shim_max_nonblank_lines"),
                    default=DEFAULT_SHIM_MAX_NONBLANK_LINES,
                ),
                required_metadata_fields=(
                    _coerce_str_tuple(item.get("required_metadata_fields"))
                    or default_required_metadata_fields
                ),
                max_shims=_coerce_positive_int(
                    item.get("max_shims"),
                    default=default_root_budget,
                ),
                guidance=str(item.get("guidance") or "").strip(),
                policy_source=(
                    str(item.get("policy_source") or "").strip()
                    or f"probe_compatibility_shims:{root.as_posix()}"
                ),
            )
        )
    return tuple(rules)


def _package_layout_root_rules(
    package_layout_config: dict[str, object],
    *,
    default_required_metadata_fields: tuple[str, ...],
    default_root_budget: int,
) -> tuple[ShimRootRule, ...]:
    rules: list[ShimRootRule] = []
    for rule in load_directory_crowding_rules(
        package_layout_config.get("directory_crowding_rules")
    ):
        if not rule.shim_contains_all and not rule.shim_required_metadata_fields:
            continue
        rules.append(
            ShimRootRule(
                root=rule.root,
                include_globs=rule.include_globs,
                namespace_subdir=rule.recommended_subdir,
                shim_contains_all=rule.shim_contains_all,
                shim_max_nonblank_lines=rule.shim_max_nonblank_lines
                or DEFAULT_SHIM_MAX_NONBLANK_LINES,
                required_metadata_fields=(
                    rule.shim_required_metadata_fields or default_required_metadata_fields
                ),
                max_shims=default_root_budget,
                guidance=rule.guidance,
                policy_source=f"package_layout.directory_crowding:{rule.root.as_posix()}",
            )
        )
    return tuple(rules)


def _package_layout_family_rules(
    package_layout_config: dict[str, object],
    *,
    default_required_metadata_fields: tuple[str, ...],
    default_family_budget: int,
) -> tuple[ShimFamilyRule, ...]:
    rules: list[ShimFamilyRule] = []
    for rule in load_namespace_family_rules(
        package_layout_config.get("namespace_family_rules")
    ):
        rules.append(
            ShimFamilyRule(
                root=rule.root,
                flat_prefix=rule.flat_prefix,
                namespace_subdir=rule.namespace_subdir,
                shim_max_nonblank_lines=rule.shim_max_nonblank_lines
                or DEFAULT_SHIM_MAX_NONBLANK_LINES,
                required_metadata_fields=(
                    rule.shim_required_metadata_fields or default_required_metadata_fields
                ),
                max_shims=default_family_budget,
                guidance=rule.guidance,
                policy_source=(
                    f"package_layout.namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}"
                ),
            )
        )
    return tuple(rules)


def _load_public_shim_contracts(
    config: dict[str, object],
) -> tuple[PublicShimContract, ...]:
    raw_contracts = config.get("allowed_public_shims")
    if not isinstance(raw_contracts, list):
        return ()
    contracts: list[PublicShimContract] = []
    for item in raw_contracts:
        if not isinstance(item, dict):
            continue
        path = _coerce_path(item.get("path"))
        glob = str(item.get("glob") or "").strip()
        if path is None and not glob:
            continue
        policy_source = str(item.get("policy_source") or "").strip()
        path_label = path.as_posix() if path is not None else glob
        contracts.append(
            PublicShimContract(
                path=path,
                glob=glob,
                reason=str(item.get("reason") or "").strip(),
                policy_source=policy_source or f"probe_compatibility_shims:{path_label}",
            )
        )
    return tuple(contracts)


def _load_usage_scan_exclude_roots(config: dict[str, object]) -> tuple[Path, ...]:
    return _coerce_path_tuple(config.get("usage_scan_exclude_roots"))


def load_shim_probe_policy(repo_root: Path) -> ShimProbePolicy:
    """Load the full compatibility-shim probe policy for one repo."""
    probe_config = resolve_guard_config("probe_compatibility_shims", repo_root=repo_root)
    package_layout_config = resolve_guard_config("package_layout", repo_root=repo_root)
    default_required_metadata_fields = _default_required_metadata_fields(probe_config)
    default_root_budget = _coerce_positive_int(
        probe_config.get("default_root_shim_budget"),
        default=DEFAULT_ROOT_SHIM_BUDGET,
    )
    default_family_budget = _coerce_positive_int(
        probe_config.get("default_family_shim_budget"),
        default=DEFAULT_FAMILY_SHIM_BUDGET,
    )
    root_rules = _package_layout_root_rules(
        package_layout_config,
        default_required_metadata_fields=default_required_metadata_fields,
        default_root_budget=default_root_budget,
    ) + _load_probe_root_rules(
        probe_config,
        default_required_metadata_fields=default_required_metadata_fields,
        default_root_budget=default_root_budget,
    )
    family_rules = _package_layout_family_rules(
        package_layout_config,
        default_required_metadata_fields=default_required_metadata_fields,
        default_family_budget=default_family_budget,
    )
    return ShimProbePolicy(
        root_rules=root_rules,
        family_rules=family_rules,
        public_contracts=_load_public_shim_contracts(probe_config),
        usage_scan_exclude_roots=_load_usage_scan_exclude_roots(probe_config),
    )


def load_shim_probe_rules(
    repo_root: Path,
) -> tuple[tuple[ShimRootRule, ...], tuple[ShimFamilyRule, ...]]:
    """Load active root/family shim rules for the probe."""
    policy = load_shim_probe_policy(repo_root)
    return policy.root_rules, policy.family_rules


__all__ = [
    "DEFAULT_FAMILY_SHIM_BUDGET",
    "DEFAULT_ROOT_SHIM_BUDGET",
    "DEFAULT_SHIM_MAX_NONBLANK_LINES",
    "PublicShimContract",
    "ShimFamilyRule",
    "ShimFinding",
    "ShimProbePolicy",
    "ShimRootRule",
    "load_shim_probe_policy",
    "load_shim_probe_rules",
]
