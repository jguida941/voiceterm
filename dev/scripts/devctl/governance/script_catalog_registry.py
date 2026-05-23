"""Canonical script path registry for devctl and tooling checks."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path

from ..config import REPO_ROOT
from .script_catalog_entries import (
    CHECK_SCRIPT_ENTRIES as _CHECK_SCRIPT_ENTRIES,
    LEGACY_ENTRYPOINT_REWRITE_ENTRIES as _LEGACY_ENTRYPOINT_REWRITE_ENTRIES,
    PROBE_SCRIPT_ENTRIES as _PROBE_SCRIPT_ENTRIES,
)

CHECKS_DIR = "dev/scripts/checks"

CHECK_SCRIPT_FILES = dict(_CHECK_SCRIPT_ENTRIES)

CHECK_SCRIPT_RELATIVE_PATHS = {
    name: f"{CHECKS_DIR}/{filename}" for name, filename in CHECK_SCRIPT_FILES.items()
}

CHECK_SCRIPT_PATHS = {
    name: REPO_ROOT / relative for name, relative in CHECK_SCRIPT_RELATIVE_PATHS.items()
}

PROBE_SCRIPT_FILES = dict(_PROBE_SCRIPT_ENTRIES)

PROBE_SCRIPT_RELATIVE_PATHS = {
    name: f"{CHECKS_DIR}/{filename}" for name, filename in PROBE_SCRIPT_FILES.items()
}

PROBE_SCRIPT_PATHS = {
    name: REPO_ROOT / relative for name, relative in PROBE_SCRIPT_RELATIVE_PATHS.items()
}


def probe_script_relative_path(name: str) -> str:
    """Return a probe script's repository-relative path."""
    try:
        return PROBE_SCRIPT_RELATIVE_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown probe script id: {name}") from exc


def probe_script_path(name: str) -> Path:
    """Return a probe script's absolute filesystem path."""
    try:
        return PROBE_SCRIPT_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown probe script id: {name}") from exc


def probe_script_cmd(name: str, *args: str) -> list[str]:
    """Return a python command list for one probe script."""
    return ["python3", probe_script_relative_path(name), *args]


LEGACY_CHECK_SCRIPT_REWRITES = {
    f"dev/scripts/{filename}": relative
    for _name, filename in _CHECK_SCRIPT_ENTRIES
    for relative in (f"{CHECKS_DIR}/{filename}",)
}

LEGACY_ENTRYPOINT_SCRIPT_REWRITES = dict(_LEGACY_ENTRYPOINT_REWRITE_ENTRIES)

LEGACY_SCRIPT_PATH_REWRITES = dict(LEGACY_CHECK_SCRIPT_REWRITES)
LEGACY_SCRIPT_PATH_REWRITES.update(LEGACY_ENTRYPOINT_SCRIPT_REWRITES)


def check_script_relative_path(name: str) -> str:
    """Return a check script's repository-relative path."""
    try:
        return CHECK_SCRIPT_RELATIVE_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_path(name: str) -> Path:
    """Return a check script's absolute filesystem path."""
    try:
        return CHECK_SCRIPT_PATHS[name]
    except KeyError as exc:
        raise KeyError(f"unknown check script id: {name}") from exc


def check_script_cmd(name: str, *args: str) -> list[str]:
    """Return a python command list for one check script."""
    return ["python3", check_script_relative_path(name), *args]


def check_script_shell_command(
    name: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return a shell command string for one check script."""
    return _script_shell_command(check_script_relative_path(name), *args, env=env)


def probe_script_shell_command(
    name: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return a shell command string for one probe script."""
    return _script_shell_command(probe_script_relative_path(name), *args, env=env)


def _script_shell_command(
    relative_path: str,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> str:
    command = shlex.join(["python3", relative_path, *args])
    if not env:
        return command
    prefix = " ".join(
        f"{key}={shlex.quote(str(value))}" for key, value in env.items()
    )
    return f"{prefix} {command}"
