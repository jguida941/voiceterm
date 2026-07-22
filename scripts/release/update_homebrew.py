#!/usr/bin/env python3
"""Update the VoiceTerm Homebrew formula for a tagged source archive."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


REPOSITORY = "jguida941/voiceterm"


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"formula {label} field was not found exactly once")
    return updated


def update_formula(formula: Path, version: str, archive: Path | None = None) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"invalid release version: {version}")

    url = f"https://github.com/{REPOSITORY}/archive/refs/tags/v{version}.tar.gz"
    if archive is None:
        with tempfile.NamedTemporaryFile(prefix="voiceterm-", suffix=".tar.gz") as handle:
            with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310
                handle.write(response.read())
            handle.flush()
            digest = hashlib.sha256(Path(handle.name).read_bytes()).hexdigest()
    else:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    text = formula.read_text(encoding="utf-8")
    text = _replace_once(text, r'^\s*url\s+"[^"]+"\s*$', f'  url "{url}"', "url")
    text = _replace_once(
        text,
        r'^\s*version\s+"[^"]+"\s*$',
        f'  version "{version}"',
        "version",
    )
    text = _replace_once(
        text,
        r'^\s*sha256\s+"[0-9a-f]+"\s*$',
        f'  sha256 "{digest}"',
        "sha256",
    )
    text = text.replace(
        "Backends: codex (default), claude, gemini (in works), or custom command",
        "Backends: codex (default), claude; gemini/custom are experimental",
    )
    formula.write_text(text, encoding="utf-8")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--formula", required=True, type=Path)
    parser.add_argument("--readme", type=Path, help="Optional tap README version badge/text")
    parser.add_argument("--archive", type=Path, help="Use a local archive instead of downloading")
    args = parser.parse_args()
    try:
        digest = update_formula(args.formula, args.version, args.archive)
        if args.readme and args.readme.exists():
            original_readme = args.readme.read_text(encoding="utf-8")
            readme = original_readme
            readme, count = re.subn(
                r"Current:\s*v\d+\.\d+\.\d+",
                f"Current: v{args.version}",
                readme,
            )
            readme = readme.replace(
                "blob/master/dev/CHANGELOG.md",
                "blob/master/CHANGELOG.md",
            )
            if count or readme != original_readme:
                args.readme.write_text(readme, encoding="utf-8")
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"Homebrew update failed: {error}", file=sys.stderr)
        return 1
    print(f"Updated {args.formula} to {args.version} ({digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
