"""Content update helpers for release metadata preparation."""

from __future__ import annotations

import re
from typing import Callable

UpdateFn = Callable[[str, str, str], str]


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"failed to update {label}")
    return updated


def update_cargo_version(text: str, version: str, _release_date: str) -> str:
    return _replace_once(
        text,
        r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'version = "{version}"',
        "rust/Cargo.toml version",
    )


def update_pyproject_version(text: str, version: str, _release_date: str) -> str:
    return _replace_once(
        text,
        r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$',
        f'version = "{version}"',
        "pypi/pyproject.toml version",
    )


def update_python_package_version(text: str, version: str, _release_date: str) -> str:
    return _replace_once(
        text,
        r'^__version__\s*=\s*"[^"]+"\s*$',
        f'__version__ = "{version}"',
        "pypi/src/voiceterm/__init__.py __version__",
    )


def update_info_plist_versions(text: str, version: str, _release_date: str) -> str:
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


def update_changelog_heading(text: str, version: str, release_date: str) -> str:
    if re.search(rf"^## \[{re.escape(version)}\](?:\s*-.*)?$", text, re.MULTILINE):
        return text

    replacement = f"## [Unreleased]\n\n## [{version}] - {release_date}"
    updated, count = re.subn(
        r"^## \[Unreleased\]\s*$", replacement, text, count=1, flags=re.MULTILINE
    )
    if count != 1:
        raise RuntimeError(
            "failed to update dev/CHANGELOG.md (missing ## [Unreleased] heading)"
        )
    return updated


def update_master_plan_snapshot(text: str, version: str, release_date: str) -> str:
    release_tag = f"v{version}"
    updated = _replace_once(
        text,
        r"^## Status Snapshot \([0-9]{4}-[0-9]{2}-[0-9]{2}\)\s*$",
        f"## Status Snapshot ({release_date})",
        "dev/active/MASTER_PLAN.md status snapshot heading",
    )
    updated = _replace_once(
        updated,
        r"^-\s+Last tagged release:\s+`v[0-9]+\.[0-9]+\.[0-9]+`\s+\([0-9]{4}-[0-9]{2}-[0-9]{2}\)\s*$",
        f"- Last tagged release: `{release_tag}` ({release_date})",
        "dev/active/MASTER_PLAN.md last tagged release",
    )
    updated = _replace_once(
        updated,
        r"^-\s+Current release target:\s+`[^`]+`\s*$",
        f"- Current release target: `post-{release_tag} planning`",
        "dev/active/MASTER_PLAN.md current release target",
    )
    return updated


RELEASE_METADATA_UPDATERS: list[tuple[str, UpdateFn]] = [
    ("rust/Cargo.toml", update_cargo_version),
    ("pypi/pyproject.toml", update_pyproject_version),
    ("pypi/src/voiceterm/__init__.py", update_python_package_version),
    ("app/macos/VoiceTerm.app/Contents/Info.plist", update_info_plist_versions),
    ("dev/CHANGELOG.md", update_changelog_heading),
    ("dev/active/MASTER_PLAN.md", update_master_plan_snapshot),
]


__all__ = ["RELEASE_METADATA_UPDATERS", "UpdateFn"]
