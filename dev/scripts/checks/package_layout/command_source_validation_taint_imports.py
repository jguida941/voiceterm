"""Import-binding helpers for command-source taint classification."""

from __future__ import annotations

import ast

SUBPROCESS_METHODS = frozenset({"Popen", "call", "check_call", "check_output", "run"})


def collect_import_bindings(tree: ast.AST) -> dict[str, set[str]]:
    bindings = {
        "os_modules": {"os"},
        "sys_modules": {"sys"},
        "shlex_modules": {"shlex"},
        "subprocess_modules": {"subprocess"},
        "argv_names": set(),
        "environ_names": set(),
        "getenv_names": set(),
        "shlex_split_names": set(),
        "subprocess_func_names": set(),
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    bindings["os_modules"].add(alias.asname or alias.name)
                elif alias.name == "sys":
                    bindings["sys_modules"].add(alias.asname or alias.name)
                elif alias.name == "shlex":
                    bindings["shlex_modules"].add(alias.asname or alias.name)
                elif alias.name == "subprocess":
                    bindings["subprocess_modules"].add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            _collect_import_from_bindings(bindings, node)
    return bindings


def _collect_import_from_bindings(bindings: dict[str, set[str]], node: ast.ImportFrom) -> None:
    if node.module == "os":
        for alias in node.names:
            if alias.name == "environ":
                bindings["environ_names"].add(alias.asname or alias.name)
            elif alias.name == "getenv":
                bindings["getenv_names"].add(alias.asname or alias.name)
        return
    if node.module == "sys":
        for alias in node.names:
            if alias.name == "argv":
                bindings["argv_names"].add(alias.asname or alias.name)
        return
    if node.module == "shlex":
        for alias in node.names:
            if alias.name == "split":
                bindings["shlex_split_names"].add(alias.asname or alias.name)
        return
    if node.module == "subprocess":
        for alias in node.names:
            if alias.name in SUBPROCESS_METHODS:
                bindings["subprocess_func_names"].add(alias.asname or alias.name)
