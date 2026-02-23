#!/usr/bin/env python3
"""Check release version parity across Cargo, PyPI, and macOS app metadata."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CARGO_TOML = REPO_ROOT / "src/Cargo.toml"
PYPROJECT_TOML = REPO_ROOT / "pypi/pyproject.toml"
INIT_PY = REPO_ROOT / "pypi/src/voiceterm/__init__.py"
INFO_PLIST = REPO_ROOT / "app/macos/VoiceTerm.app/Contents/Info.plist"


def _read_cargo_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^\"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _read_pyproject_version(path: Path) -> str | None:
    # Prefer TOML parsing when available for correctness.
    try:
        import tomllib  # type: ignore[attr-defined]

        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        return payload.get("project", {}).get("version")
    except Exception:
        pass

    # Fallback parser for environments without tomllib.
    in_project = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            continue
        if not in_project:
            continue
        match = re.match(r'^version\s*=\s*"([^\"]+)"$', line)
        if match:
            return match.group(1)
    return None


def _read_plist_versions(path: Path) -> tuple[str | None, str | None]:
    with path.open("rb") as handle:
        payload = plistlib.load(handle)
    short_version = payload.get("CFBundleShortVersionString")
    bundle_version = payload.get("CFBundleVersion")
    return short_version, bundle_version


def _read_init_version(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _build_report() -> dict:
    cargo_version = _read_cargo_version(CARGO_TOML)
    pyproject_version = _read_pyproject_version(PYPROJECT_TOML)
    init_version = _read_init_version(INIT_PY)
    plist_short, plist_bundle = _read_plist_versions(INFO_PLIST)

    values = {
        "src/Cargo.toml": cargo_version,
        "pypi/pyproject.toml": pyproject_version,
        "pypi/src/voiceterm/__init__.py": init_version,
        "app/macos/VoiceTerm.app/Contents/Info.plist:CFBundleShortVersionString": plist_short,
        "app/macos/VoiceTerm.app/Contents/Info.plist:CFBundleVersion": plist_bundle,
    }

    present_versions = sorted({value for value in values.values() if value})
    missing = [name for name, value in values.items() if not value]

    mismatched = len(present_versions) > 1
    ok = not missing and not mismatched

    return {
        "command": "check_release_version_parity",
        "ok": ok,
        "values": values,
        "versions_present": present_versions,
        "missing": missing,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_release_version_parity", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(
        "- versions_present: "
        + (", ".join(report["versions_present"]) if report["versions_present"] else "none")
    )
    lines.append(f"- missing: {', '.join(report['missing']) if report['missing'] else 'none'}")
    for name, value in report["values"].items():
        lines.append(f"- {name}: {value if value else 'missing'}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
