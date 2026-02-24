"""Snapshot metadata helpers for active-plan sync checks."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def read_cargo_release_tag(cargo_toml_path: Path) -> str | None:
    if not cargo_toml_path.exists():
        return None
    cargo_text = cargo_toml_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', cargo_text, re.MULTILINE)
    if not match:
        return None
    return f"v{match.group(1)}"


def latest_git_semver_tag(repo_root: Path, semver_tag_pattern: re.Pattern[str]) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            ["git", "tag", "--list", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-version:refname"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, str(exc)

    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git exited with code {completed.returncode}"
        return None, detail

    for raw in completed.stdout.splitlines():
        candidate = raw.strip()
        if semver_tag_pattern.match(candidate):
            return candidate, None
    return None, None
