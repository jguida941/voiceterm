"""Path filtering for the term-consistency review probe."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

if __package__:
    from .config import ProbeConfig, TermRule
else:  # pragma: no cover - direct module loading in tests
    from config import ProbeConfig, TermRule

TEXT_SUFFIXES = frozenset({".py", ".md", ".json", ".yaml", ".yml"})


def normalize_path(path: Path, repo_root: Path) -> str:
    if path.is_absolute():
        return path.relative_to(repo_root).as_posix()
    return path.as_posix()


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    pure_path = PurePosixPath(path)
    for pattern in patterns:
        variants = {pattern}
        if "/**/" in pattern:
            variants.add(pattern.replace("/**/", "/"))
        if any(pure_path.match(variant) for variant in variants):
            return True
    return False


def matches_rule_path(path: str, config: ProbeConfig, rule: TermRule) -> bool:
    if config.include_globs and not matches_any(path, config.include_globs):
        return False
    if config.exclude_globs and matches_any(path, config.exclude_globs):
        return False
    if rule.include_globs and not matches_any(path, rule.include_globs):
        return False
    if rule.exclude_globs and matches_any(path, rule.exclude_globs):
        return False
    return True
