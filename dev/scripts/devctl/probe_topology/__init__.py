"""Public probe-topology compatibility surface."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "build_probe_topology_artifact",
    "build_python_module_index",
    "build_review_packet",
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
    "render_hotspot_dot",
    "render_hotspot_mermaid",
    "render_review_packet_markdown",
    "repo_relative",
    "repo_root",
    "resolve_python_target",
    "resolve_relative_python_module",
    "resolve_rust_mod_target",
    "resolve_rust_target",
    "rust_tokens_for_path",
]


def _import_relative(relative_name: str) -> Any:
    return import_module(relative_name, package=__package__)


def __getattr__(name: str) -> Any:
    if name in {"build_probe_topology_artifact", "build_review_packet"}:
        module = _import_relative("..probe_topology_builder")
        return getattr(module, name)
    if name in {"render_hotspot_dot", "render_hotspot_mermaid", "render_review_packet_markdown"}:
        module = _import_relative("..probe_topology_render")
        return getattr(module, name)
    if name in {
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
    }:
        module = _import_relative("..probe_topology_scan")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
