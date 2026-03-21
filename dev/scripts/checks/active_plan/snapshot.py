"""Snapshot metadata helpers for active-plan sync checks."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def read_cargo_release_tag(cargo_toml_path: Path) -> str | None:
    if not cargo_toml_path.exists():
        return None
    cargo_text = cargo_toml_path.read_text(encoding="utf-8")
    match = re.search(
        r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', cargo_text, re.MULTILINE
    )
    if not match:
        return None
    return f"v{match.group(1)}"


def latest_git_semver_tag(
    repo_root: Path, semver_tag_pattern: re.Pattern[str]
) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            [
                "git",
                "tag",
                "--list",
                "v[0-9]*.[0-9]*.[0-9]*",
                "--sort=-version:refname",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, str(exc)

    if completed.returncode != 0:
        detail = (
            completed.stderr.strip() or f"git exited with code {completed.returncode}"
        )
        return None, detail

    for raw in completed.stdout.splitlines():
        candidate = raw.strip()
        if semver_tag_pattern.match(candidate):
            return candidate, None
    return None, None


def read_master_plan_text(master_plan_path: Path) -> tuple[str, list[str]]:
    if not master_plan_path.exists():
        relative_hint = "/".join(master_plan_path.parts[-3:])
        return "", [f"Missing {relative_hint}."]
    return master_plan_path.read_text(encoding="utf-8"), []


def parse_master_plan_snapshot(
    master_plan_text: str,
) -> tuple[dict[str, str | None], list[str]]:
    snapshot_values: dict[str, str | None] = {
        "status_date": None,
        "last_tagged_release": None,
        "last_tagged_release_date": None,
        "current_release_target": None,
        "active_development_branch": None,
        "release_branch": None,
    }
    errors: list[str] = []
    snapshot_patterns = [
        (
            "status_date",
            r"^## Status Snapshot \(([0-9]{4}-[0-9]{2}-[0-9]{2})\)\s*$",
            "MASTER_PLAN status snapshot heading is missing or malformed.",
        ),
        (
            "last_tagged_release",
            r"^-\s+Last tagged release:\s+`(v[0-9]+\.[0-9]+\.[0-9]+)`\s+\(([0-9]{4}-[0-9]{2}-[0-9]{2})\)\s*$",
            "MASTER_PLAN last tagged release line is missing or malformed.",
        ),
        (
            "current_release_target",
            r"^-\s+Current release target:\s+`([^`]+)`\s*$",
            "MASTER_PLAN current release target line is missing or malformed.",
        ),
        (
            "active_development_branch",
            r"^-\s+Active development branch:\s+`([^`]+)`\s*$",
            "MASTER_PLAN active development branch line is missing or malformed.",
        ),
        (
            "release_branch",
            r"^-\s+Release branch:\s+`([^`]+)`\s*$",
            "MASTER_PLAN release branch line is missing or malformed.",
        ),
    ]
    for key, pattern, message in snapshot_patterns:
        match = re.search(pattern, master_plan_text, re.MULTILINE)
        if not match:
            errors.append(message)
            continue
        snapshot_values[key] = match.group(1)
        if key == "last_tagged_release":
            snapshot_values["last_tagged_release_date"] = match.group(2)
    return snapshot_values, errors


def validate_snapshot_policy(
    snapshot_values: dict[str, str | None],
    *,
    expected_active_development_branch: str,
    expected_release_branch: str,
    latest_git_tag: str | None,
    cargo_release_tag: str | None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    release_tag = snapshot_values["last_tagged_release"]
    current_release_target = snapshot_values["current_release_target"]

    if release_tag and current_release_target:
        expected_target = f"post-{release_tag} planning"
        if current_release_target != expected_target:
            errors.append(
                "MASTER_PLAN current release target must match "
                f"`{expected_target}` for snapshot release `{release_tag}`."
            )

    if (
        snapshot_values["active_development_branch"]
        and snapshot_values["active_development_branch"]
        != expected_active_development_branch
    ):
        errors.append(
            "MASTER_PLAN active development branch must be "
            f"`{expected_active_development_branch}`."
        )
    if (
        snapshot_values["release_branch"]
        and snapshot_values["release_branch"] != expected_release_branch
    ):
        errors.append(
            f"MASTER_PLAN release branch must be `{expected_release_branch}`."
        )

    valid_snapshot_tags = {tag for tag in (latest_git_tag, cargo_release_tag) if tag}
    if release_tag and valid_snapshot_tags and release_tag not in valid_snapshot_tags:
        errors.append(
            "MASTER_PLAN last tagged release must match either the latest git semver tag "
            "or the current Cargo release version: "
            f"snapshot={release_tag}, latest_git={latest_git_tag or 'none'}, "
            f"cargo={cargo_release_tag or 'none'}."
        )
    elif (
        release_tag
        and latest_git_tag
        and cargo_release_tag
        and release_tag == cargo_release_tag
        and release_tag != latest_git_tag
    ):
        warnings.append(
            "Snapshot release matches Cargo version but is ahead of latest git tag "
            "(expected during release prep before tagging)."
        )

    return errors, warnings
