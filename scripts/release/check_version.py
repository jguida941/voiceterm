#!/usr/bin/env python3
"""Verify that every VoiceTerm package surface uses the same version."""

from __future__ import annotations

import argparse
import plistlib
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def read_versions() -> dict[str, str]:
    cargo = _toml(ROOT / "rust" / "Cargo.toml")["package"]["version"]
    lock_packages = _toml(ROOT / "rust" / "Cargo.lock")["package"]
    lock = next(
        package["version"]
        for package in lock_packages
        if package.get("name") == "voiceterm"
    )
    pyproject = _toml(ROOT / "pypi" / "pyproject.toml")["project"]["version"]

    init_text = (ROOT / "pypi" / "src" / "voiceterm" / "__init__.py").read_text(
        encoding="utf-8"
    )
    init_match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, re.M)
    if init_match is None:
        raise ValueError("PyPI package __version__ is missing")

    with (ROOT / "app" / "macos" / "VoiceTerm.app" / "Contents" / "Info.plist").open(
        "rb"
    ) as handle:
        plist = plistlib.load(handle)

    return {
        "rust/Cargo.toml": str(cargo),
        "rust/Cargo.lock": str(lock),
        "pypi/pyproject.toml": str(pyproject),
        "pypi/src/voiceterm/__init__.py": init_match.group(1),
        "Info.plist short version": str(plist["CFBundleShortVersionString"]),
        "Info.plist bundle version": str(plist["CFBundleVersion"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", help="Expected X.Y.Z version")
    args = parser.parse_args()

    try:
        versions = read_versions()
    except (KeyError, OSError, StopIteration, ValueError, tomllib.TOMLDecodeError) as error:
        print(f"version check failed: {error}", file=sys.stderr)
        return 1

    unique = set(versions.values())
    for surface, version in versions.items():
        print(f"{surface}: {version}")

    if len(unique) != 1:
        print("version check failed: package surfaces do not match", file=sys.stderr)
        return 1

    version = next(iter(unique))
    if args.expected and version != args.expected:
        print(
            f"version check failed: expected {args.expected}, found {version}",
            file=sys.stderr,
        )
        return 1

    print(f"VoiceTerm version parity OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
