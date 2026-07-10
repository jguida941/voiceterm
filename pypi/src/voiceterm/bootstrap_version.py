"""Version helpers for the launcher bootstrap flow."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version


def _launcher_version() -> str:
    try:
        return package_version("voiceterm")
    except PackageNotFoundError:
        try:
            from . import __version__

            return __version__
        except Exception:
            return "unknown"


def _default_repo_ref() -> str:
    version = _launcher_version()
    if version == "unknown":
        raise RuntimeError(
            "Cannot detect installed voiceterm package version. "
            "Set VOICETERM_REPO_REF to an explicit tag/commit."
        )
    return f"v{version}"
