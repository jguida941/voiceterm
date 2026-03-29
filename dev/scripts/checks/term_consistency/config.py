"""Config loading for the term-consistency review probe."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import resolve_guard_config
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import resolve_guard_config

VALID_MATCH_MODES = frozenset({"prefer_canonical", "no_mixed_terms"})


@dataclass(frozen=True, slots=True)
class TermRule:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    severity: str
    match_mode: str
    ai_instruction: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProbeConfig:
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    rules: tuple[TermRule, ...]


def _default_instruction(rule: TermRule) -> str:
    if rule.match_mode == "prefer_canonical":
        return (
            f"Use the canonical term `{rule.canonical}` and retire legacy aliases "
            "from code, docs, and generated surfaces so one public word keeps one meaning."
        )
    return (
        f"Use one stable term family for `{rule.canonical}` in this subsystem. "
        "Mixed vocabulary makes the code and docs harder to scan."
    )


def _coerce_rule(raw_rule: object) -> TermRule | None:
    if not isinstance(raw_rule, dict):
        return None
    canonical = str(raw_rule.get("canonical") or "").strip()
    aliases = tuple(
        alias.strip()
        for alias in raw_rule.get("aliases", ())
        if isinstance(alias, str) and alias.strip()
    )
    if not canonical or not aliases:
        return None
    match_mode = str(raw_rule.get("match_mode") or "prefer_canonical").strip()
    if match_mode not in VALID_MATCH_MODES:
        match_mode = "prefer_canonical"
    severity = str(raw_rule.get("severity") or "medium").strip().lower()
    if severity not in {"low", "medium", "high", "critical"}:
        severity = "medium"
    provisional = TermRule(
        id=str(raw_rule.get("id") or canonical).strip() or canonical,
        canonical=canonical,
        aliases=aliases,
        severity=severity,
        match_mode=match_mode,
        ai_instruction=str(raw_rule.get("ai_instruction") or "").strip(),
        include_globs=tuple(
            pattern.strip()
            for pattern in raw_rule.get("include_globs", ())
            if isinstance(pattern, str) and pattern.strip()
        ),
        exclude_globs=tuple(
            pattern.strip()
            for pattern in raw_rule.get("exclude_globs", ())
            if isinstance(pattern, str) and pattern.strip()
        ),
    )
    return TermRule(
        id=provisional.id,
        canonical=provisional.canonical,
        aliases=provisional.aliases,
        severity=provisional.severity,
        match_mode=provisional.match_mode,
        ai_instruction=provisional.ai_instruction or _default_instruction(provisional),
        include_globs=provisional.include_globs,
        exclude_globs=provisional.exclude_globs,
    )


def load_probe_config(repo_root: Path) -> ProbeConfig:
    raw_config = resolve_guard_config("probe_term_consistency", repo_root=repo_root)
    rules = tuple(
        rule
        for raw_rule in raw_config.get("rules", ())
        for rule in (_coerce_rule(raw_rule),)
        if rule is not None
    )
    include_globs = tuple(
        pattern.strip()
        for pattern in raw_config.get("include_globs", ())
        if isinstance(pattern, str) and pattern.strip()
    )
    exclude_globs = tuple(
        pattern.strip()
        for pattern in raw_config.get("exclude_globs", ())
        if isinstance(pattern, str) and pattern.strip()
    )
    return ProbeConfig(
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        rules=rules,
    )
