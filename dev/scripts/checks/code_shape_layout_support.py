"""Directory-organization support rules for check_code_shape."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import resolve_guard_config
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import resolve_guard_config


@dataclass(frozen=True)
class NamespaceFamilyRule:
    """Require crowded flat module families to move into a namespace directory."""

    root: Path
    flat_prefix: str
    namespace_subdir: str
    min_family_size: int


@dataclass(frozen=True)
class NamespaceDocsSyncRule:
    """Require docs to reference newly introduced namespace-module roots."""

    namespace_root: Path
    required_docs: tuple[Path, ...]
    required_token: str


def _coerce_path(value: object) -> Path | None:
    text = str(value or "").strip()
    return Path(text) if text else None


def _load_namespace_family_rules(config: object) -> tuple[NamespaceFamilyRule, ...]:
    if not isinstance(config, list):
        return ()
    rules: list[NamespaceFamilyRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        root = _coerce_path(item.get("root"))
        flat_prefix = str(item.get("flat_prefix") or "").strip()
        namespace_subdir = str(item.get("namespace_subdir") or "").strip()
        try:
            min_family_size = int(item.get("min_family_size"))
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
            )
        )
    return tuple(rules)


def _load_namespace_docs_sync_rules(config: object) -> tuple[NamespaceDocsSyncRule, ...]:
    if not isinstance(config, list):
        return ()
    rules: list[NamespaceDocsSyncRule] = []
    for item in config:
        if not isinstance(item, dict):
            continue
        namespace_root = _coerce_path(item.get("namespace_root"))
        required_token = str(item.get("required_token") or "").strip()
        raw_docs = item.get("required_docs")
        if not isinstance(raw_docs, list):
            continue
        required_docs = tuple(
            doc_path for raw_doc in raw_docs for doc_path in (_coerce_path(raw_doc),) if doc_path is not None
        )
        if namespace_root is None or not required_token or not required_docs:
            continue
        rules.append(
            NamespaceDocsSyncRule(
                namespace_root=namespace_root,
                required_docs=required_docs,
                required_token=required_token,
            )
        )
    return tuple(rules)


def _resolved_layout_rules(
    repo_root: Path,
) -> tuple[tuple[NamespaceFamilyRule, ...], tuple[NamespaceDocsSyncRule, ...]]:
    config = resolve_guard_config("code_shape", repo_root=repo_root)
    family_rules = _load_namespace_family_rules(config.get("namespace_family_rules"))
    docs_sync_rules = _load_namespace_docs_sync_rules(config.get("namespace_docs_sync_rules"))
    return family_rules, docs_sync_rules


def collect_namespace_layout_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
    family_rules: tuple[NamespaceFamilyRule, ...] | None = None,
) -> tuple[list[dict], int]:
    """Return non-regressive namespace-layout violations for changed paths."""
    base_ref = since_ref or "HEAD"
    violations: list[dict] = []
    candidates_scanned = 0
    active_family_rules = family_rules
    if active_family_rules is None:
        active_family_rules, _docs_sync_rules = _resolved_layout_rules(repo_root)

    for rule in active_family_rules:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        family_size = len(list(root_abs.glob(f"{rule.flat_prefix}*.py")))
        if family_size < rule.min_family_size:
            continue

        for changed_path in changed_paths:
            relative = changed_path.relative_to(repo_root) if changed_path.is_absolute() else changed_path
            if relative.suffix != ".py":
                continue
            if relative.parent != rule.root:
                continue
            if not relative.name.startswith(rule.flat_prefix):
                continue
            if _is_backward_compat_shim(
                repo_root / relative,
                namespace_subdir=rule.namespace_subdir,
            ):
                continue
            candidates_scanned += 1
            if read_text_from_ref(relative, base_ref) is not None:
                continue
            target = _recommended_namespace_path(relative, rule)
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": "new_flat_namespace_module_in_crowded_family",
                    "guidance": (
                        f"Flat module family `{rule.flat_prefix}*` has {family_size} files in "
                        f"`{rule.root.as_posix()}`. Add new modules under "
                        f"`{(rule.root / rule.namespace_subdir).as_posix()}` "
                        f"(for example `{target.as_posix()}`) to keep directory organization stable."
                    ),
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
                    "policy_source": f"namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}",
                    "family_size": family_size,
                    "recommended_path": target.as_posix(),
                }
            )

    return violations, candidates_scanned


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
        _family_rules, active_docs_sync_rules = _resolved_layout_rules(repo_root)

    for changed_path in changed_paths:
        relative = changed_path.relative_to(repo_root) if changed_path.is_absolute() else changed_path
        if relative.suffix != ".py":
            continue
        if read_text_from_ref(relative, base_ref) is not None:
            continue

        for rule in active_docs_sync_rules:
            if not _is_under_root(relative, rule.namespace_root):
                continue
            if rule.namespace_root in checked_roots:
                continue
            checked_roots.add(rule.namespace_root)
            candidates_scanned += 1
            if _docs_contain_token(
                read_text_from_worktree=read_text_from_worktree,
                docs=rule.required_docs,
                token=rule.required_token,
            ):
                continue
            docs_label = ", ".join(doc.as_posix() for doc in rule.required_docs)
            violations.append(
                {
                    "path": relative.as_posix(),
                    "reason": "new_namespace_path_missing_docs_reference",
                    "guidance": (
                        f"New module under `{rule.namespace_root.as_posix()}` requires docs "
                        f"coverage for `{rule.required_token}`. Update at least one of: "
                        f"{docs_label}."
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
                    "policy_source": (f"namespace_docs_sync:{rule.namespace_root.as_posix()}"),
                    "required_token": rule.required_token,
                    "required_docs": [doc.as_posix() for doc in rule.required_docs],
                }
            )

    return violations, candidates_scanned


def _recommended_namespace_path(path: Path, rule: NamespaceFamilyRule) -> Path:
    suffix = path.name[len(rule.flat_prefix) :] or path.name
    return rule.root / rule.namespace_subdir / suffix


def _is_under_root(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _docs_contain_token(
    *,
    read_text_from_worktree: Callable[[Path], str | None],
    docs: tuple[Path, ...],
    token: str,
) -> bool:
    return any(token in (read_text_from_worktree(doc) or "") for doc in docs)


def _is_backward_compat_shim(path: Path, *, namespace_subdir: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    stripped = [line.strip() for line in text.splitlines() if line.strip()]
    if len(stripped) > 3:
        return False
    joined = " ".join(stripped)
    return "Backward-compat shim" in joined and f"from .{namespace_subdir}." in joined
