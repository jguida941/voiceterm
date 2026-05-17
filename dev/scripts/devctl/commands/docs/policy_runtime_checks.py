"""Policy-consumer query functions for docs-check.

Extracted from policy_runtime.py to keep each module under the code-shape
soft limit. These functions query the resolved DocsCheckPolicy without
participating in building it.
"""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from .policy_runtime import resolve_docs_check_policy


def is_tooling_change(
    path: str,
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> bool:
    """Return True when the changed path is considered tooling/process scope."""
    policy = resolve_docs_check_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    return path in policy.tooling_change_exact or path.startswith(
        policy.tooling_change_prefixes
    )


def resolve_tooling_doc_requirements(
    changed_paths: set[str] | list[str] | tuple[str, ...],
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return matched rule ids and required docs for the changed tooling paths."""
    policy = resolve_docs_check_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    matched_rule_ids: list[str] = []
    required_docs: list[str] = []
    for rule in policy.tooling_doc_requirement_rules:
        matched = False
        for path in changed_paths:
            if path in rule.trigger_exact_paths:
                matched = True
                break
            if any(path.startswith(prefix) for prefix in rule.trigger_prefixes):
                matched = True
                break
        if not matched:
            continue
        if rule.rule_id not in matched_rule_ids:
            matched_rule_ids.append(rule.rule_id)
        for doc in rule.required_docs:
            if doc not in required_docs:
                required_docs.append(doc)
    return tuple(matched_rule_ids), tuple(required_docs)


def requires_evolution_update(
    path: str,
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> bool:
    """Return True when a path requires an engineering-evolution log update."""
    policy = resolve_docs_check_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    return path in policy.evolution_change_exact or path.startswith(
        policy.evolution_change_prefixes
    )


def scan_deprecated_references(
    repo_root: Path,
    *,
    policy_path: str | None = None,
) -> list[dict]:
    """Find legacy helper-script references in governance-controlled files."""
    policy = resolve_docs_check_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    violations = []
    for relative in policy.deprecated_reference_targets:
        path = repo_root / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            for spec in policy.deprecated_reference_patterns:
                if spec.regex.search(line):
                    violations.append(
                        {
                            "file": relative,
                            "line": lineno,
                            "pattern": spec.name,
                            "line_text": line.strip(),
                            "replacement": spec.replacement,
                        }
                    )
    return violations
