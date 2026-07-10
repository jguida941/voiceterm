"""Path helpers shared by doc-authority modules."""

from __future__ import annotations


def is_root_markdown_path(relative_path: str) -> bool:
    return "/" not in relative_path and relative_path.lower().endswith(".md")


def path_in_root(relative_path: str, root_path: str) -> bool:
    if not root_path:
        return False
    return relative_path == root_path or relative_path.startswith(f"{root_path}/")


def registry_managed(relative_path: str, active_docs_root: str, index_path: str) -> bool:
    if relative_path == index_path:
        return False
    return path_in_root(relative_path, active_docs_root)


__all__ = ["is_root_markdown_path", "path_in_root", "registry_managed"]
