"""Shared helpers for `devctl integrations-import`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def run_git_capture(args: list[str], *, cwd: Path) -> tuple[int, str, str]:
    """Run a git command and return `(returncode, stdout, stderr)`."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, (completed.stdout or "").strip(), (completed.stderr or "").strip()


def append_audit_log(path: Path, payload: dict[str, Any]) -> None:
    """Append one JSON line to the integrations audit log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when `path` is under `parent` after resolving symlinks."""
    parent_resolved = parent.resolve()
    path_resolved = path.resolve()
    try:
        path_resolved.relative_to(parent_resolved)
        return True
    except ValueError:
        return False


def relative_or_str(path: Path, root: Path) -> str:
    """Return repo-relative path if possible, else absolute string."""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def list_profiles_payload(
    sources_cfg: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build the list-profiles payload for integrations import."""
    sources_payload: list[dict[str, Any]] = []
    for source_name in sorted(sources_cfg.keys()):
        source_cfg = sources_cfg[source_name]
        profiles = source_cfg.get("profiles")
        profile_rows: list[dict[str, Any]] = []
        if isinstance(profiles, dict):
            for profile_name in sorted(profiles.keys()):
                profile_cfg = profiles[profile_name]
                if not isinstance(profile_cfg, dict):
                    continue
                mappings = profile_cfg.get("mappings")
                mapping_count = len(mappings) if isinstance(mappings, list) else 0
                profile_rows.append(
                    {
                        "profile": profile_name,
                        "description": str(profile_cfg.get("description") or "").strip(),
                        "mapping_count": mapping_count,
                    }
                )
        sources_payload.append(
            {
                "source": source_name,
                "path": str(source_cfg.get("path") or "").strip(),
                "profiles": profile_rows,
            }
        )
    return {"sources": sources_payload}


def collect_mapping_plan(
    *,
    repo_root: Path,
    source_root: Path,
    mapping_from: str,
    mapping_to: str,
    allowed_dest_roots: list[Path],
) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Return planned file copy pairs for one mapping and mapping errors."""
    errors: list[str] = []
    source_path = (source_root / mapping_from).resolve()
    if not is_relative_to(source_path, source_root):
        return [], [f"source mapping escapes source root: {mapping_from}"]
    if not source_path.exists():
        return [], [f"source mapping does not exist: {mapping_from}"]

    destination_root = (repo_root / mapping_to).resolve()
    if not is_relative_to(destination_root, repo_root):
        return [], [f"destination mapping escapes repo root: {mapping_to}"]
    if not any(is_relative_to(destination_root, root.resolve()) for root in allowed_dest_roots):
        return [], [f"destination mapping is not allowlisted: {mapping_to}"]

    file_pairs: list[tuple[Path, Path]] = []
    if source_path.is_file():
        file_pairs.append((source_path, destination_root))
        return file_pairs, []

    for candidate in sorted(source_path.rglob("*")):
        if not candidate.is_file():
            continue
        if ".git" in candidate.parts:
            continue
        rel = candidate.relative_to(source_path)
        file_pairs.append((candidate, destination_root / rel))
    if not file_pairs:
        errors.append(f"no files found for mapping: {mapping_from}")
    return file_pairs, errors


def render_import_md(report: dict[str, Any]) -> str:
    """Render markdown output for preview/apply import mode."""
    lines = ["# devctl integrations-import", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- source: {report.get('source') or 'n/a'}")
    lines.append(f"- profile: {report.get('profile') or 'n/a'}")
    lines.append(f"- planned_files: {report.get('planned_files', 0)}")
    lines.append(f"- applied_files: {report.get('applied_files', 0)}")
    lines.append(f"- audit_log: `{report['audit_log']}`")
    lines.append(f"- errors: {len(report.get('errors', []))}")
    lines.append("")
    lines.append("| From | To | Files |")
    lines.append("|---|---|---:|")
    for row in report.get("mapping_results", []):
        lines.append(
            f"| `{row.get('from')}` | `{row.get('to')}` | {row.get('files', 0)} |"
        )
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines)


def render_profiles_md(report: dict[str, Any]) -> str:
    """Render markdown output for list-profiles mode."""
    lines = ["# devctl integrations-import profiles", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- audit_log: `{report['audit_log']}`")
    lines.append(f"- errors: {len(report.get('errors', []))}")
    lines.append("")
    lines.append("| Source | Path | Profile | Mappings | Description |")
    lines.append("|---|---|---|---:|---|")
    for source_row in report.get("sources", []):
        source = source_row.get("source") or "n/a"
        path = source_row.get("path") or "n/a"
        profiles = source_row.get("profiles", [])
        if not profiles:
            lines.append(f"| `{source}` | `{path}` | `-` | 0 | - |")
            continue
        for profile_row in profiles:
            lines.append(
                f"| `{source}` | `{path}` | `{profile_row.get('profile')}` | "
                f"{profile_row.get('mapping_count', 0)} | "
                f"{profile_row.get('description') or '-'} |"
            )
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines)
