"""Release metadata preparation helpers for `devctl ship`/`devctl release`."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Callable

from ..config import REPO_ROOT

UpdateFn = Callable[[str, str, str], str]


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"failed to update {label}")
    return updated


def _update_cargo_version(text: str, version: str) -> str:
    return _replace_once(
        text,
        r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'version = "{version}"',
        "src/Cargo.toml version",
    )


def _update_pyproject_version(text: str, version: str) -> str:
    return _replace_once(
        text,
        r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'version = "{version}"',
        "pypi/pyproject.toml version",
    )


def _update_python_package_version(text: str, version: str) -> str:
    return _replace_once(
        text,
        r'^__version__\s*=\s*"[^"]+"\s*$',
        f'__version__ = "{version}"',
        "pypi/src/voiceterm/__init__.py __version__",
    )


def _update_info_plist_versions(text: str, version: str) -> str:
    updated = _replace_once(
        text,
        r"(<key>CFBundleShortVersionString</key>\s*<string>)[^<]+(</string>)",
        rf"\g<1>{version}\g<2>",
        "Info.plist CFBundleShortVersionString",
    )
    updated = _replace_once(
        updated,
        r"(<key>CFBundleVersion</key>\s*<string>)[^<]+(</string>)",
        rf"\g<1>{version}\g<2>",
        "Info.plist CFBundleVersion",
    )
    return updated


def _update_changelog_heading(text: str, version: str, release_date: str) -> str:
    if re.search(rf"^## \[{re.escape(version)}\](?:\s*-.*)?$", text, re.MULTILINE):
        return text

    replacement = f"## [Unreleased]\n\n## [{version}] - {release_date}"
    updated, count = re.subn(r"^## \[Unreleased\]\s*$", replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError("failed to update dev/CHANGELOG.md (missing ## [Unreleased] heading)")
    return updated


def _update_cargo_wrapper(text: str, version: str, _release_date: str) -> str:
    return _update_cargo_version(text, version)


def _update_pyproject_wrapper(text: str, version: str, _release_date: str) -> str:
    return _update_pyproject_version(text, version)


def _update_python_wrapper(text: str, version: str, _release_date: str) -> str:
    return _update_python_package_version(text, version)


def _update_plist_wrapper(text: str, version: str, _release_date: str) -> str:
    return _update_info_plist_versions(text, version)


_RELEASE_METADATA_UPDATERS: list[tuple[str, UpdateFn]] = [
    ("src/Cargo.toml", _update_cargo_wrapper),
    ("pypi/pyproject.toml", _update_pyproject_wrapper),
    ("pypi/src/voiceterm/__init__.py", _update_python_wrapper),
    ("app/macos/VoiceTerm.app/Contents/Info.plist", _update_plist_wrapper),
    ("dev/CHANGELOG.md", _update_changelog_heading),
]


def prepare_release_metadata(
    version: str,
    *,
    release_date: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Apply release version metadata updates across canonical files."""
    resolved_date = release_date or date.today().isoformat()
    changed_files: list[str] = []
    unchanged_files: list[str] = []

    for rel_path, updater in _RELEASE_METADATA_UPDATERS:
        absolute = REPO_ROOT / rel_path
        if not absolute.exists():
            raise RuntimeError(f"missing release metadata file: {rel_path}")

        before = absolute.read_text(encoding="utf-8")
        after = updater(before, version, resolved_date)
        if after == before:
            unchanged_files.append(rel_path)
            continue

        changed_files.append(rel_path)
        if not dry_run:
            absolute.write_text(after, encoding="utf-8")

    return {
        "version": version,
        "release_date": resolved_date,
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
        "dry_run": dry_run,
    }
