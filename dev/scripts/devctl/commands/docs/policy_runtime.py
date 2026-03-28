"""Repo-policy resolution helpers for docs-check."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from ...config import REPO_ROOT
from ...governance.governed_doc_routing import resolve_governed_doc_routing
from ...repo_policy import load_repo_governance_section
from .policy_defaults import (
    DEPRECATED_REFERENCE_PATTERNS,
    DEPRECATED_REFERENCE_TARGETS,
    EVOLUTION_CHANGE_EXACT,
    EVOLUTION_CHANGE_PREFIXES,
    EVOLUTION_DOC,
    TOOLING_CHANGE_EXACT,
    TOOLING_CHANGE_PREFIXES,
    TOOLING_REQUIRED_DOC_ALIASES,
    TOOLING_REQUIRED_DOCS,
    USER_DOCS,
    DeprecatedReferencePattern,
    DocsCheckPolicy,
    ToolingDocRequirementRule,
    )


def _append_unique(values: list[str], candidate: str) -> None:
    text = str(candidate or "").strip()
    if text and text not in values:
        values.append(text)


def _existing_relative_path(repo_root: Path, candidate: str) -> str:
    text = str(candidate or "").strip()
    if not text:
        return ""
    return text if (repo_root / text).exists() else ""


def _default_user_docs() -> tuple[str, ...]:
    return ()


def _default_tooling_change_exact(
    repo_root: Path,
    *,
    process_doc: str,
    development_doc: str,
    scripts_readme_doc: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for item in (process_doc, development_doc, scripts_readme_doc):
        _append_unique(values, item)
    _append_unique(values, _existing_relative_path(repo_root, "Makefile"))
    return tuple(values)


def _default_tooling_required_docs(
    *,
    process_doc: str,
    development_doc: str,
    scripts_readme_doc: str,
    tracker_path: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for item in (process_doc, development_doc, scripts_readme_doc, tracker_path):
        _append_unique(values, item)
    return tuple(values)


def _default_evolution_doc(repo_root: Path) -> str:
    return _existing_relative_path(repo_root, EVOLUTION_DOC)


def _default_evolution_change_exact(
    repo_root: Path,
    *,
    process_doc: str,
    development_doc: str,
    scripts_readme_doc: str,
    architecture_doc: str,
    tracker_path: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for item in (
        process_doc,
        development_doc,
        scripts_readme_doc,
        architecture_doc,
        tracker_path,
    ):
        _append_unique(values, item)
    _append_unique(values, _default_evolution_doc(repo_root))
    return tuple(values)


def _default_deprecated_targets(
    repo_root: Path,
    *,
    process_doc: str,
    development_doc: str,
    scripts_readme_doc: str,
) -> tuple[str, ...]:
    values: list[str] = []
    for item in (process_doc, development_doc, scripts_readme_doc):
        _append_unique(values, item)
    _append_unique(values, _existing_relative_path(repo_root, "Makefile"))
    return tuple(values)


def _coerce_string_list(
    raw_value: object,
    fallback: tuple[str, ...] | list[str] | set[str],
) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return tuple(str(item) for item in fallback)
    values: list[str] = []
    for item in raw_value:
        value = str(item).strip()
        if value and value not in values:
            values.append(value)
    return tuple(values) if values else tuple(str(item) for item in fallback)


def _coerce_alias_map(raw_value: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(raw_value, dict):
        return {
            str(key): tuple(str(item) for item in value)
            for key, value in TOOLING_REQUIRED_DOC_ALIASES.items()
        }
    aliases: dict[str, tuple[str, ...]] = {}
    for key, value in raw_value.items():
        alias_key = str(key).strip()
        if not alias_key:
            continue
        alias_values = _coerce_string_list(value, ())
        if alias_values:
            aliases[alias_key] = alias_values
    return aliases


def _default_deprecated_patterns() -> tuple[DeprecatedReferencePattern, ...]:
    return tuple(
        DeprecatedReferencePattern(
            name=str(spec["name"]),
            regex=spec["regex"],
            replacement=str(spec["replacement"]),
        )
        for spec in DEPRECATED_REFERENCE_PATTERNS
    )


def _coerce_deprecated_patterns(
    raw_value: object,
) -> tuple[DeprecatedReferencePattern, ...]:
    if not isinstance(raw_value, list):
        return _default_deprecated_patterns()
    patterns: list[DeprecatedReferencePattern] = []
    for item in raw_value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        regex_text = str(item.get("regex", "")).strip()
        replacement = str(item.get("replacement", "")).strip()
        if not name or not regex_text or not replacement:
            continue
        try:
            compiled = re.compile(regex_text)
        except re.error:
            continue
        patterns.append(
            DeprecatedReferencePattern(
                name=name,
                regex=compiled,
                replacement=replacement,
            )
        )
    return tuple(patterns) if patterns else _default_deprecated_patterns()


def _coerce_tooling_doc_requirement_rules(
    raw_value: object,
) -> tuple[ToolingDocRequirementRule, ...]:
    if not isinstance(raw_value, list):
        return ()
    rules: list[ToolingDocRequirementRule] = []
    for item in raw_value:
        if not isinstance(item, dict):
            continue
        rule_id = str(item.get("id", "")).strip()
        trigger_prefixes = _coerce_string_list(item.get("trigger_prefixes"), ())
        trigger_exact_paths = frozenset(
            _coerce_string_list(item.get("trigger_exact_paths"), ())
        )
        required_docs = _coerce_string_list(item.get("required_docs"), ())
        if not rule_id or not required_docs:
            continue
        if not trigger_prefixes and not trigger_exact_paths:
            continue
        rules.append(
            ToolingDocRequirementRule(
                rule_id=rule_id,
                trigger_prefixes=trigger_prefixes,
                trigger_exact_paths=trigger_exact_paths,
                required_docs=required_docs,
            )
        )
    return tuple(rules)


def _normalize_repo_root(repo_root: Path) -> str:
    return str(repo_root.resolve())


def _normalize_policy_path(policy_path: str | Path | None) -> str | None:
    if policy_path is None:
        return None
    return str(Path(policy_path).resolve())


@lru_cache(maxsize=32)
def _resolve_docs_check_policy_cached(
    repo_root_text: str,
    policy_path_text: str | None,
) -> DocsCheckPolicy:
    repo_root = Path(repo_root_text)
    policy_path = policy_path_text
    section, warnings, resolved_path = load_repo_governance_section(
        "docs_check",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    routing = resolve_governed_doc_routing(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    tooling_change_prefixes = _coerce_string_list(
        section.get("tooling_change_prefixes"),
        routing.tooling_change_prefixes,
    )
    tooling_change_exact = frozenset(
        _coerce_string_list(
            section.get("tooling_change_exact"),
            _default_tooling_change_exact(
                repo_root,
                process_doc=routing.process_doc,
                development_doc=routing.development_doc,
                scripts_readme_doc=routing.scripts_readme_doc,
            ),
        )
    )
    tooling_required_docs = _coerce_string_list(
        section.get("tooling_required_docs"),
        _default_tooling_required_docs(
            process_doc=routing.process_doc,
            development_doc=routing.development_doc,
            scripts_readme_doc=routing.scripts_readme_doc,
            tracker_path=routing.tracker_path,
        ),
    )
    evolution_doc = str(
        section.get("evolution_doc") or _default_evolution_doc(repo_root)
    ).strip()
    return DocsCheckPolicy(
        user_docs=_coerce_string_list(section.get("user_docs"), _default_user_docs()),
        tooling_change_prefixes=tooling_change_prefixes,
        tooling_change_exact=tooling_change_exact,
        tooling_required_docs=tooling_required_docs,
        tooling_required_doc_aliases=_coerce_alias_map(
            section.get("tooling_required_doc_aliases")
        ),
        tooling_doc_requirement_rules=_coerce_tooling_doc_requirement_rules(
            section.get("tooling_doc_requirement_rules")
        ),
        evolution_doc=evolution_doc,
        evolution_change_prefixes=_coerce_string_list(
            section.get("evolution_change_prefixes"),
            tooling_change_prefixes,
        ),
        evolution_change_exact=frozenset(
            _coerce_string_list(
                section.get("evolution_change_exact"),
                _default_evolution_change_exact(
                    repo_root,
                    process_doc=routing.process_doc,
                    development_doc=routing.development_doc,
                    scripts_readme_doc=routing.scripts_readme_doc,
                    architecture_doc=routing.architecture_doc,
                    tracker_path=routing.tracker_path,
                ),
            )
        ),
        deprecated_reference_targets=_coerce_string_list(
            section.get("deprecated_reference_targets"),
            _default_deprecated_targets(
                repo_root,
                process_doc=routing.process_doc,
                development_doc=routing.development_doc,
                scripts_readme_doc=routing.scripts_readme_doc,
            ),
        ),
        deprecated_reference_patterns=_coerce_deprecated_patterns(
            section.get("deprecated_reference_patterns")
        ),
        policy_path=str(resolved_path),
        warnings=warnings,
    )


def resolve_docs_check_policy(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> DocsCheckPolicy:
    """Resolve docs-check path and docs requirements from repo policy."""
    return _resolve_docs_check_policy_cached(
        _normalize_repo_root(repo_root),
        _normalize_policy_path(policy_path),
    )


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
