"""Compatibility surface for probe topology helpers."""

from __future__ import annotations

from .probe_topology.python_scan import (
    build_python_module_index,
    candidate_python_modules,
    collect_python_edges,
    python_module_name,
    resolve_python_target,
    resolve_relative_python_module,
)
from .probe_topology.rust_scan import (
    build_rust_suffix_index,
    collect_rust_edges,
    normalize_rust_use_prefix,
    resolve_rust_mod_target,
    resolve_rust_target,
    rust_tokens_for_path,
)
from .probe_topology.source_scan import (
    codeowners_match,
    collect_changed_paths,
    iter_source_files,
    owners_for_path,
    parse_codeowners_rules,
    repo_relative,
    repo_root,
)

__all__ = [
    "build_python_module_index",
    "build_rust_suffix_index",
    "candidate_python_modules",
    "codeowners_match",
    "collect_changed_paths",
    "collect_python_edges",
    "collect_rust_edges",
    "iter_source_files",
    "normalize_rust_use_prefix",
    "owners_for_path",
    "parse_codeowners_rules",
    "python_module_name",
    "repo_relative",
    "repo_root",
    "resolve_python_target",
    "resolve_relative_python_module",
    "resolve_rust_mod_target",
    "resolve_rust_target",
    "rust_tokens_for_path",
]
