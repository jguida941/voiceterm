"""Compatibility surface for source-scan helpers."""

from __future__ import annotations

from .source_codeowners import codeowners_match, owners_for_path, parse_codeowners_rules
from .source_git import collect_changed_paths
from .source_paths import iter_source_files, repo_relative, repo_root

__all__ = [
    "codeowners_match",
    "collect_changed_paths",
    "iter_source_files",
    "owners_for_path",
    "parse_codeowners_rules",
    "repo_relative",
    "repo_root",
]
