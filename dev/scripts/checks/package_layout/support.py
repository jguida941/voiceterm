"""Policy-driven package-layout guard support."""

from __future__ import annotations

from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        docs_contain_tokens,
        is_under_root,
        recommended_namespace_path,
    )
    from .compatibility_redirects import collect_compatibility_redirects
    from .directory_crowding import (
        collect_directory_crowding_violations_from_rules,
    )
    from .namespace_family import (
        collect_namespace_family_violations_from_rules,
    )
    from .rule_resolution import resolve_layout_rules
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        docs_contain_tokens,
        is_under_root,
        recommended_namespace_path,
    )
    from compatibility_redirects import collect_compatibility_redirects
    from directory_crowding import (
        collect_directory_crowding_violations_from_rules,
    )
    from namespace_family import (
        collect_namespace_family_violations_from_rules,
    )
    from rule_resolution import resolve_layout_rules


def _shim_metadata_guidance(missing_fields: tuple[str, ...]) -> str:
    fields_label = ", ".join(f"`shim-{field}: ...`" for field in missing_fields)
    return f" Valid compatibility shims here must also declare metadata fields: {fields_label}."


def collect_flat_root_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    flat_root_rules: tuple[FlatRootRule, ...] | None = None,
) -> tuple[list[dict], int]:
    """Return non-regressive flat-root placement violations for changed paths."""
    base_ref = since_ref or "HEAD"
    violations: list[dict] = []
    candidates_scanned = 0
    active_rules = flat_root_rules
    if active_rules is None:
        active_rules, _family_rules, _docs_sync_rules, _crowding_rules = (
            resolve_layout_rules(repo_root)
        )

    for rule in active_rules:
        for changed_path in changed_paths:
            relative = changed_path.relative_to(repo_root) if changed_path.is_absolute() else changed_path
            if relative.parent != rule.root:
                continue
            if not any(fnmatch(relative.name, pattern) for pattern in rule.include_globs):
                continue
            if read_text_from_ref(relative, base_ref) is not None:
                continue
            candidates_scanned += 1
            if any(fnmatch(relative.name, pattern) for pattern in rule.allowed_new_globs):
                continue
            shim_validation = detect_compatibility_shim(
                repo_root / relative,
                namespace_subdir=rule.recommended_subdir,
                shim_contains_all=rule.shim_contains_all,
                shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
                shim_required_metadata_fields=rule.shim_required_metadata_fields,
            )
            if shim_validation.is_valid:
                continue
            recommended_path = (
                rule.root / rule.recommended_subdir / relative.name
                if rule.recommended_subdir
                else None
            )
            guidance = rule.guidance or (
                f"New helper modules should not land at `{rule.root.as_posix()}` root. "
                "Keep only declared public entrypoints flat and move new support code into "
                "a focused subpackage."
            )
            if recommended_path is not None:
                guidance = f"{guidance} For example: `{recommended_path.as_posix()}`."
            if shim_validation.missing_metadata_fields:
                guidance += _shim_metadata_guidance(
                    shim_validation.missing_metadata_fields
                )
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": "new_flat_root_module_not_allowed",
                    "guidance": guidance,
                    "best_practice_refs": [],
                    "base_lines": None,
                    "current_lines": 0,
                    "growth": None,
                    "policy": {
                        "soft_limit": 1,
                        "hard_limit": 1,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": f"flat_root:{rule.root.as_posix()}",
                    "allowed_new_globs": list(rule.allowed_new_globs),
                    "recommended_path": (
                        recommended_path.as_posix() if recommended_path is not None else ""
                    ),
                }
            )

    return violations, candidates_scanned


def collect_namespace_layout_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    family_rules: tuple[NamespaceFamilyRule, ...] | None = None,
) -> tuple[list[dict], list[dict], int]:
    """Return non-regressive namespace-layout violations for changed paths."""
    active_family_rules = family_rules
    if active_family_rules is None:
        _flat_rules, active_family_rules, _docs_sync_rules, _crowding_rules = (
            resolve_layout_rules(repo_root)
        )
    return collect_namespace_family_violations_from_rules(
        repo_root=repo_root,
        changed_paths=changed_paths,
        read_text_from_ref=read_text_from_ref,
        since_ref=since_ref,
        family_rules=active_family_rules,
    )


def collect_namespace_docs_sync_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    read_text_from_worktree: Callable[[Path], str | None],
    since_ref: str | None,
    docs_sync_rules: tuple[NamespaceDocsSyncRule, ...] | None = None,
) -> tuple[list[dict], int]:
    """Require docs-token coverage when new namespace-root files are added."""
    base_ref = since_ref or "HEAD"
    violations: list[dict] = []
    candidates_scanned = 0
    checked_roots: set[Path] = set()
    active_docs_sync_rules = docs_sync_rules
    if active_docs_sync_rules is None:
        _flat_rules, _family_rules, active_docs_sync_rules, _crowding_rules = (
            resolve_layout_rules(repo_root)
        )

    for changed_path in changed_paths:
        relative = changed_path.relative_to(repo_root) if changed_path.is_absolute() else changed_path
        if relative.suffix != ".py":
            continue
        if read_text_from_ref(relative, base_ref) is not None:
            continue

        for rule in active_docs_sync_rules:
            if not is_under_root(relative, rule.namespace_root):
                continue
            if rule.namespace_root in checked_roots:
                continue
            checked_roots.add(rule.namespace_root)
            candidates_scanned += 1
            tokens = rule.required_tokens or ((rule.required_token,) if rule.required_token else ())
            if docs_contain_tokens(
                read_text_from_worktree=read_text_from_worktree,
                docs=rule.required_docs,
                tokens=tokens,
            ):
                continue
            docs_label = ", ".join(doc.as_posix() for doc in rule.required_docs)
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": "new_namespace_path_missing_docs_reference",
                    "guidance": (
                        f"New module under `{rule.namespace_root.as_posix()}` requires docs "
                        f"coverage for {', '.join(f'`{token}`' for token in tokens)}. "
                        f"Update at least one of: {docs_label}."
                    ),
                    "best_practice_refs": [],
                    "base_lines": None,
                    "current_lines": 0,
                    "growth": None,
                    "policy": {
                        "soft_limit": 1,
                        "hard_limit": 1,
                        "oversize_growth_limit": 0,
                        "hard_lock_growth_limit": 0,
                    },
                    "policy_source": f"namespace_docs_sync:{rule.namespace_root.as_posix()}",
                    "required_tokens": list(tokens),
                    "required_docs": [doc.as_posix() for doc in rule.required_docs],
                }
            )

    return violations, candidates_scanned


def collect_directory_crowding_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    crowding_rules: tuple[DirectoryCrowdingRule, ...] | None = None,
) -> tuple[list[dict], list[dict], int]:
    """Report overcrowded roots and block further flat growth under them."""
    active_rules = crowding_rules
    if active_rules is None:
        _flat_rules, _family_rules, _docs_sync_rules, active_rules = (
            resolve_layout_rules(repo_root)
        )
    return collect_directory_crowding_violations_from_rules(
        repo_root=repo_root,
        changed_paths=changed_paths,
        read_text_from_ref=read_text_from_ref,
        since_ref=since_ref,
        crowding_rules=active_rules,
    )
