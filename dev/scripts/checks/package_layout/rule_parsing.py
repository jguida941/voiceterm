"""Config parsing helpers for package-layout policy."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

if __package__:
    from .rule_models import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
    )
else:  # pragma: no cover - standalone script fallback
    from rule_models import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
    )


def _coerce_path(value: object) -> Path | None:
    text = str(value or "").strip()
    return Path(text) if text else None


def _coerce_str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def load_flat_root_rules(config: object) -> tuple[FlatRootRule, ...]:
    """Load flat-root rules from a resolved guard config payload."""
    if not isinstance(config, list):
        return ()
    rules: list[FlatRootRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        root = _coerce_path(item.get("root"))
        include_globs = _coerce_str_tuple(item.get("include_globs")) or ("*.py",)
        allowed_new_globs = _coerce_str_tuple(item.get("allowed_new_globs"))
        guidance = str(item.get("guidance") or "").strip()
        recommended_subdir = str(item.get("recommended_subdir") or "").strip()
        shim_contains_all = _coerce_str_tuple(item.get("shim_contains_all"))
        shim_required_metadata_fields = _coerce_str_tuple(
            item.get("shim_required_metadata_fields")
        )
        try:
            shim_max_nonblank_lines = int(item.get("shim_max_nonblank_lines", 0))
        except (TypeError, ValueError):
            shim_max_nonblank_lines = 0
        if root is None or not allowed_new_globs:
            continue
        rules.append(
            FlatRootRule(
                root=root,
                include_globs=include_globs,
                allowed_new_globs=allowed_new_globs,
                guidance=guidance,
                recommended_subdir=recommended_subdir,
                shim_contains_all=shim_contains_all,
                shim_max_nonblank_lines=shim_max_nonblank_lines,
                shim_required_metadata_fields=shim_required_metadata_fields,
            )
        )
    return tuple(rules)


def load_namespace_family_rules(config: object) -> tuple[NamespaceFamilyRule, ...]:
    """Load crowded-family namespace rules from a guard config payload."""
    if not isinstance(config, list):
        return ()
    rules: list[NamespaceFamilyRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        root = _coerce_path(item.get("root"))
        flat_prefix = str(item.get("flat_prefix") or "").strip()
        namespace_subdir = str(item.get("namespace_subdir") or "").strip()
        enforcement_mode = str(item.get("enforcement_mode") or "freeze").strip()
        guidance = str(item.get("guidance") or "").strip()
        shim_required_metadata_fields = _coerce_str_tuple(
            item.get("shim_required_metadata_fields")
        )
        if enforcement_mode not in {"freeze", "strict"}:
            continue
        try:
            min_family_size = int(item.get("min_family_size"))
            shim_max_nonblank_lines = int(item.get("shim_max_nonblank_lines", 0))
        except (TypeError, ValueError):
            continue
        if root is None or not flat_prefix or not namespace_subdir or min_family_size < 1:
            continue
        rules.append(
            NamespaceFamilyRule(
                root=root,
                flat_prefix=flat_prefix,
                namespace_subdir=namespace_subdir,
                min_family_size=min_family_size,
                enforcement_mode=enforcement_mode,
                guidance=guidance,
                shim_max_nonblank_lines=shim_max_nonblank_lines,
                shim_required_metadata_fields=shim_required_metadata_fields,
            )
        )
    return tuple(rules)


def load_namespace_docs_sync_rules(
    config: object,
) -> tuple[NamespaceDocsSyncRule, ...]:
    """Load docs-sync rules from a guard config payload."""
    if not isinstance(config, list):
        return ()
    rules: list[NamespaceDocsSyncRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        namespace_root = _coerce_path(item.get("namespace_root"))
        raw_docs = item.get("required_docs")
        if not isinstance(raw_docs, list):
            continue
        required_docs = tuple(
            doc_path
            for raw_doc in raw_docs
            for doc_path in (_coerce_path(raw_doc),)
            if doc_path is not None
        )
        required_token = str(item.get("required_token") or "").strip()
        required_tokens = _coerce_str_tuple(item.get("required_tokens"))
        if namespace_root is None or not required_docs:
            continue
        if not required_tokens and required_token:
            required_tokens = (required_token,)
        if not required_tokens:
            continue
        rules.append(
            NamespaceDocsSyncRule(
                namespace_root=namespace_root,
                required_docs=required_docs,
                required_token=required_token,
                required_tokens=required_tokens,
            )
        )
    return tuple(rules)


def load_directory_crowding_rules(config: object) -> tuple[DirectoryCrowdingRule, ...]:
    """Load directory-crowding rules from a resolved guard config payload."""
    if not isinstance(config, list):
        return ()
    rules: list[DirectoryCrowdingRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        root = _coerce_path(item.get("root"))
        include_globs = _coerce_str_tuple(item.get("include_globs")) or ("*.py",)
        guidance = str(item.get("guidance") or "").strip()
        recommended_subdir = str(item.get("recommended_subdir") or "").strip()
        enforcement_mode = str(item.get("enforcement_mode") or "freeze").strip()
        shim_contains_all = _coerce_str_tuple(item.get("shim_contains_all"))
        shim_required_metadata_fields = _coerce_str_tuple(
            item.get("shim_required_metadata_fields")
        )
        if enforcement_mode not in {"freeze", "strict"}:
            continue
        try:
            max_files = int(item.get("max_files"))
            shim_max_nonblank_lines = int(item.get("shim_max_nonblank_lines", 0))
        except (TypeError, ValueError):
            continue
        if root is None or max_files < 1:
            continue
        rules.append(
            DirectoryCrowdingRule(
                root=root,
                include_globs=include_globs,
                max_files=max_files,
                enforcement_mode=enforcement_mode,
                guidance=guidance,
                recommended_subdir=recommended_subdir,
                shim_contains_all=shim_contains_all,
                shim_max_nonblank_lines=shim_max_nonblank_lines,
                shim_required_metadata_fields=shim_required_metadata_fields,
            )
        )
    return tuple(rules)


def recommended_namespace_path(path: Path, rule: NamespaceFamilyRule) -> Path:
    """Return the namespace path a crowded-family module should use."""
    suffix = path.name[len(rule.flat_prefix) :] or path.name
    return rule.root / rule.namespace_subdir / suffix


def is_under_root(path: Path, root: Path) -> bool:
    """Return whether one repo-relative path falls under the given root."""
    return path == root or root in path.parents


def docs_contain_tokens(
    *,
    read_text_from_worktree: Callable[[Path], str | None],
    docs: tuple[Path, ...],
    tokens: tuple[str, ...],
) -> bool:
    """Return whether any required doc contains all required tokens."""
    return any(
        all(token in (read_text_from_worktree(doc) or "") for token in tokens)
        for doc in docs
    )


__all__ = [
    "docs_contain_tokens",
    "is_under_root",
    "load_directory_crowding_rules",
    "load_flat_root_rules",
    "load_namespace_docs_sync_rules",
    "load_namespace_family_rules",
    "recommended_namespace_path",
]
