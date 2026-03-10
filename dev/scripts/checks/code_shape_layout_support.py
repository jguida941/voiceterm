"""Directory-organization support rules for check_code_shape."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


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


NAMESPACE_FAMILY_RULES: tuple[NamespaceFamilyRule, ...] = (
    NamespaceFamilyRule(
        root=Path("dev/scripts/devctl"),
        flat_prefix="review_channel_",
        namespace_subdir="review_channel",
        min_family_size=8,
    ),
    NamespaceFamilyRule(
        root=Path("app/operator_console/views"),
        flat_prefix="ui_",
        namespace_subdir="actions",
        min_family_size=6,
    ),
)

NAMESPACE_DOCS_SYNC_RULES: tuple[NamespaceDocsSyncRule, ...] = (
    NamespaceDocsSyncRule(
        namespace_root=Path("dev/scripts/devctl/review_channel"),
        required_docs=(
            Path("AGENTS.md"),
            Path("dev/scripts/README.md"),
            Path("dev/guides/DEVELOPMENT.md"),
            Path("dev/active/MASTER_PLAN.md"),
        ),
        required_token="dev/scripts/devctl/review_channel",
    ),
    NamespaceDocsSyncRule(
        namespace_root=Path("app/operator_console/views/actions"),
        required_docs=(
            Path("app/operator_console/README.md"),
            Path("app/operator_console/views/README.md"),
            Path("dev/active/operator_console.md"),
        ),
        required_token="app/operator_console/views/actions",
    ),
)


def collect_namespace_layout_violations(
    *,
    repo_root: Path,
    changed_paths: list[Path],
    read_text_from_ref: Callable[[Path, str], str | None],
    since_ref: str | None,
) -> tuple[list[dict], int]:
    """Return non-regressive namespace-layout violations for changed paths."""
    base_ref = since_ref or "HEAD"
    violations: list[dict] = []
    candidates_scanned = 0

    for rule in NAMESPACE_FAMILY_RULES:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        family_size = len(list(root_abs.glob(f"{rule.flat_prefix}*.py")))
        if family_size < rule.min_family_size:
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
            if _is_backward_compat_shim(repo_root / relative):
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
) -> tuple[list[dict], int]:
    """Require docs-token coverage when new namespace-root files are added."""
    base_ref = since_ref or "HEAD"
    violations: list[dict] = []
    candidates_scanned = 0
    checked_roots: set[Path] = set()

    for changed_path in changed_paths:
        relative = (
            changed_path.relative_to(repo_root)
            if changed_path.is_absolute()
            else changed_path
        )
        if relative.suffix != ".py":
            continue
        if read_text_from_ref(relative, base_ref) is not None:
            continue

        for rule in NAMESPACE_DOCS_SYNC_RULES:
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
                    "policy_source": (
                        f"namespace_docs_sync:{rule.namespace_root.as_posix()}"
                    ),
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


def _is_backward_compat_shim(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    stripped = [line.strip() for line in text.splitlines() if line.strip()]
    if len(stripped) > 3:
        return False
    joined = " ".join(stripped)
    return "Backward-compat shim" in joined and "from .review_channel." in joined
