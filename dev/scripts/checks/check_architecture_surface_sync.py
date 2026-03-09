#!/usr/bin/env python3
"""Validate that newly added repo surfaces are wired into owning authorities.

This guard is intentionally narrow: it scans only newly added files. The goal
is to catch "added a new surface but forgot the repo wiring" regressions for
active-plan docs, check scripts, devctl commands, app surfaces, and workflow
docs. It is not meant to replace the broader code-quality guards.

Untracked discovery uses `git ls-files --others --exclude-standard`, which is
the repo's canonical non-ignored working-tree view. That does not recurse into
submodules, which is acceptable because this repo currently has no submodules.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Final

REPO_ROOT = Path(__file__).resolve().parents[3]

INDEX_REL: Final[str] = "dev/active/INDEX.md"
MASTER_PLAN_REL: Final[str] = "dev/active/MASTER_PLAN.md"
SCRIPT_CATALOG_REL: Final[str] = "dev/scripts/devctl/script_catalog.py"
BUNDLE_REGISTRY_REL: Final[str] = "dev/scripts/devctl/bundle_registry.py"
CLI_REL: Final[str] = "dev/scripts/devctl/cli.py"
LISTING_REL: Final[str] = "dev/scripts/devctl/commands/listing.py"
COMMAND_DOCS_REL: Final[str] = "dev/scripts/README.md"
WORKFLOW_README_REL: Final[str] = ".github/workflows/README.md"

DISCOVERY_DOCS: Final[tuple[str, ...]] = (
    "AGENTS.md",
    "DEV_INDEX.md",
    "dev/README.md",
)
CHECK_SCRIPT_SUPPORT_SUFFIXES: Final[tuple[str, ...]] = (
    "_support.py",
    "_core.py",
    "_render.py",
    "_parser.py",
)
DEVCTL_COMMAND_EXCLUDES: Final[tuple[str, ...]] = (
    "dev/scripts/devctl/commands/__init__.py",
    "dev/scripts/devctl/commands/*_support.py",
    "dev/scripts/devctl/commands/*_core.py",
    "dev/scripts/devctl/commands/*_render.py",
    "dev/scripts/devctl/commands/*_parser.py",
    "dev/scripts/devctl/commands/*_constants.py",
)

SURFACE_SYNC_ALLOWLIST: Final[dict[str, tuple[str, ...]]] = {
    "active-plan": (),
    "check-script": (),
    "devctl-command": (),
    "app-surface": (),
    "workflow": (),
}

SURFACE_ZONES: Final[tuple[dict[str, object], ...]] = (
    {
        "id": "active-plan",
        "include_globs": ("dev/active/*.md",),
        "exclude_globs": (
            "dev/active/INDEX.md",
            "dev/active/MASTER_PLAN.md",
            "dev/active/README.md",
        ),
    },
    {
        "id": "check-script",
        "include_globs": ("dev/scripts/checks/check_*.py",),
        "exclude_globs": (),
    },
    {
        "id": "devctl-command",
        "include_globs": ("dev/scripts/devctl/commands/*.py",),
        "exclude_globs": DEVCTL_COMMAND_EXCLUDES,
    },
    {
        "id": "app-surface",
        "include_globs": ("app/**",),
        "exclude_globs": (
            "app/**/__pycache__/**",
            "app/**/*.pyc",
            "app/**/__init__.py",
            "app/**/tests/**",
        ),
    },
    {
        "id": "workflow",
        "include_globs": (".github/workflows/*.yml", ".github/workflows/*.yaml"),
        "exclude_globs": (),
    },
)


def _run_git(repo_root: Path, cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _normalize_path(repo_root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.relative_to(repo_root)
    return path


def _discover_new_paths(
    repo_root: Path,
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    candidates: set[Path] = set()

    diff_cmd = ["git", "diff", "--name-only", "--diff-filter=A"]
    if since_ref:
        diff_cmd.extend([since_ref, head_ref])
    else:
        diff_cmd.append("HEAD")
    diff_result = _run_git(repo_root, diff_cmd)
    if diff_result.returncode != 0:
        errors.append(diff_result.stderr.strip() or "git diff failed")
    else:
        for line in diff_result.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                candidates.add(Path(stripped))

    untracked_result = _run_git(
        repo_root,
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    if untracked_result.returncode != 0:
        errors.append(untracked_result.stderr.strip() or "git ls-files failed")
    else:
        for line in untracked_result.stdout.splitlines():
            stripped = line.strip()
            if stripped:
                candidates.add(Path(stripped))

    return sorted(candidates), errors


def _path_matches(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(fnmatch(path_text, pattern) for pattern in patterns)


def _is_allowlisted(path: Path, zone_id: str) -> bool:
    return _path_matches(path, SURFACE_SYNC_ALLOWLIST.get(zone_id, ()))


def _read_text(repo_root: Path, relative_path: str, cache: dict[str, str]) -> str:
    cached = cache.get(relative_path)
    if cached is not None:
        return cached
    try:
        cache[relative_path] = (repo_root / relative_path).read_text(encoding="utf-8")
    except OSError:
        cache[relative_path] = ""
    return cache[relative_path]


def _workflow_files(repo_root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in (".github/workflows/*.yml", ".github/workflows/*.yaml"):
        paths.update(repo_root.glob(pattern))
    return sorted(paths)


def _violation(
    *,
    path: Path,
    zone: str,
    rule: str,
    hint: str,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "path": path.as_posix(),
        "zone": zone,
        "rule": rule,
        "severity": severity,
        "hint": hint,
    }


def _reference_tokens(path: Path) -> tuple[str, ...]:
    filename = path.name
    return (path.as_posix(), f"active/{filename}", filename)


def _contains_any_token(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _validate_active_plan(
    repo_root: Path,
    path: Path,
    cache: dict[str, str],
) -> list[dict[str, str]]:
    tokens = _reference_tokens(path)
    violations: list[dict[str, str]] = []

    index_text = _read_text(repo_root, INDEX_REL, cache)
    if not _contains_any_token(index_text, tokens):
        violations.append(
            _violation(
                path=path,
                zone="active-plan",
                rule="missing-index-reference",
                hint=(
                    f"Register `{path.as_posix()}` in `{INDEX_REL}` with role, "
                    "authority, MP scope, and read trigger."
                ),
            )
        )

    master_plan_text = _read_text(repo_root, MASTER_PLAN_REL, cache)
    if not _contains_any_token(master_plan_text, tokens):
        violations.append(
            _violation(
                path=path,
                zone="active-plan",
                rule="missing-master-plan-reference",
                hint=(
                    f"Mirror `{path.as_posix()}` scope in `{MASTER_PLAN_REL}` "
                    "instead of leaving the plan wiring implicit."
                ),
            )
        )

    if not any(
        _contains_any_token(_read_text(repo_root, doc, cache), tokens)
        for doc in DISCOVERY_DOCS
    ):
        violations.append(
            _violation(
                path=path,
                zone="active-plan",
                rule="missing-discovery-reference",
                hint=(
                    f"Link `{path.as_posix()}` from `AGENTS.md`, `DEV_INDEX.md`, "
                    "or `dev/README.md` so discovery does not rely on chat memory."
                ),
            )
        )

    return violations


def _validate_check_script(
    repo_root: Path,
    path: Path,
    cache: dict[str, str],
) -> list[dict[str, str]]:
    if path.name.endswith(CHECK_SCRIPT_SUPPORT_SUFFIXES):
        return []

    path_text = path.as_posix()
    violations: list[dict[str, str]] = []

    catalog_text = _read_text(repo_root, SCRIPT_CATALOG_REL, cache)
    if path.name not in catalog_text:
        violations.append(
            _violation(
                path=path,
                zone="check-script",
                rule="missing-script-catalog-entry",
                hint=(
                    f"Register `{path.name}` in `{SCRIPT_CATALOG_REL}` so devctl "
                    "can resolve the check path canonically."
                ),
            )
        )

    bundle_text = _read_text(repo_root, BUNDLE_REGISTRY_REL, cache)
    if path_text not in bundle_text:
        violations.append(
            _violation(
                path=path,
                zone="check-script",
                rule="missing-bundle-reference",
                hint=(
                    f"Reference `{path_text}` from at least one bundle in "
                    f"`{BUNDLE_REGISTRY_REL}` or add an allowlist entry if it is "
                    "intentionally local-only."
                ),
            )
        )

    workflow_hits = [
        workflow.relative_to(repo_root).as_posix()
        for workflow in _workflow_files(repo_root)
        if path_text in _read_text(repo_root, workflow.relative_to(repo_root).as_posix(), cache)
    ]
    if not workflow_hits:
        violations.append(
            _violation(
                path=path,
                zone="check-script",
                rule="missing-workflow-reference",
                hint=(
                    f"Wire `{path_text}` into the owning workflow lane if it should "
                    "gate CI, or allowlist it if it is intentionally local-only."
                ),
            )
        )

    return violations


def _extract_command_handlers(cli_text: str) -> dict[str, list[str]]:
    handlers: dict[str, list[str]] = defaultdict(list)
    pattern = re.compile(r'["\']([^"\']+)["\']\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\.run')
    for command_name, module_name in pattern.findall(cli_text):
        handlers[module_name].append(command_name)
    return dict(handlers)


def _has_run_entrypoint(source_text: str) -> bool:
    return re.search(r"^def\s+run\s*\(", source_text, re.MULTILINE) is not None


def _validate_devctl_command(
    repo_root: Path,
    path: Path,
    cache: dict[str, str],
) -> list[dict[str, str]]:
    source_text = _read_text(repo_root, path.as_posix(), cache)
    if not _has_run_entrypoint(source_text):
        return []

    module_name = path.stem
    cli_text = _read_text(repo_root, CLI_REL, cache)
    listing_text = _read_text(repo_root, LISTING_REL, cache)
    docs_text = _read_text(repo_root, COMMAND_DOCS_REL, cache)
    violations: list[dict[str, str]] = []

    if not re.search(rf"^\s*{re.escape(module_name)},\s*$", cli_text, re.MULTILINE):
        violations.append(
            _violation(
                path=path,
                zone="devctl-command",
                rule="missing-cli-import",
                hint=(
                    f"Import `{module_name}` in `{CLI_REL}` so the command module is "
                    "reachable from the public CLI surface."
                ),
            )
        )

    handlers = _extract_command_handlers(cli_text)
    command_names = handlers.get(module_name, [])
    if not command_names:
        violations.append(
            _violation(
                path=path,
                zone="devctl-command",
                rule="missing-command-handler",
                hint=(
                    f"Add a `COMMAND_HANDLERS` entry for `{module_name}.run` in "
                    f"`{CLI_REL}` and wire the parser in the same slice."
                ),
            )
        )
        return violations

    for command_name in command_names:
        quoted_name = f'"{command_name}"'
        alt_quoted_name = f"'{command_name}'"
        if quoted_name not in listing_text and alt_quoted_name not in listing_text:
            violations.append(
                _violation(
                    path=path,
                    zone="devctl-command",
                    rule="missing-list-command",
                    hint=(
                        f"Add `{command_name}` to `{LISTING_REL}` so `devctl list` "
                        "stays aligned with the public command surface."
                    ),
                )
            )

        doc_tokens = (
            f"devctl.py {command_name}",
            f"`{command_name}`",
        )
        if not _contains_any_token(docs_text, doc_tokens):
            violations.append(
                _violation(
                    path=path,
                    zone="devctl-command",
                    rule="missing-command-docs",
                    hint=(
                        f"Document `{command_name}` in `{COMMAND_DOCS_REL}` so the "
                        "maintainer command reference stays authoritative."
                    ),
                )
            )

    return violations


def _app_reference_tokens(path: Path) -> tuple[str, ...]:
    parts = path.parts
    tokens: list[str] = [path.as_posix()]
    for index in range(len(parts) - 1, 1, -1):
        prefix = "/".join(parts[:index])
        if prefix != "app":
            tokens.append(prefix)
    return tuple(tokens)


def _validate_app_surface(
    repo_root: Path,
    path: Path,
    cache: dict[str, str],
) -> list[dict[str, str]]:
    tokens = _app_reference_tokens(path)
    active_docs = sorted(
        doc
        for doc in (repo_root / "dev" / "active").glob("*.md")
        if doc.name != "INDEX.md"
    )
    for active_doc in active_docs:
        rel = active_doc.relative_to(repo_root).as_posix()
        if _contains_any_token(_read_text(repo_root, rel, cache), tokens):
            return []
    return [
        _violation(
            path=path,
            zone="app-surface",
            rule="missing-owning-plan-reference",
            hint=(
                f"Mention `{tokens[1] if len(tokens) > 1 else path.as_posix()}` in an "
                "owning `dev/active/*.md` plan so new app surfaces have explicit "
                "authority."
            ),
        )
    ]


def _validate_workflow(
    repo_root: Path,
    path: Path,
    cache: dict[str, str],
) -> list[dict[str, str]]:
    workflow_readme = _read_text(repo_root, WORKFLOW_README_REL, cache)
    if path.name in workflow_readme or path.as_posix() in workflow_readme:
        return []
    return [
        _violation(
            path=path,
            zone="workflow",
            rule="missing-workflow-readme-reference",
            hint=(
                f"Document `{path.name}` in `{WORKFLOW_README_REL}` so workflow "
                "ownership and local rerun commands stay discoverable."
            ),
        )
    ]


ZONE_VALIDATORS = {
    "active-plan": _validate_active_plan,
    "check-script": _validate_check_script,
    "devctl-command": _validate_devctl_command,
    "app-surface": _validate_app_surface,
    "workflow": _validate_workflow,
}


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
    explicit_paths: list[str] | None = None,
) -> dict[str, object]:
    cache: dict[str, str] = {}
    discovery_errors: list[str] = []
    if explicit_paths is not None:
        candidate_paths = sorted(_normalize_path(repo_root, path) for path in explicit_paths)
    else:
        candidate_paths, discovery_errors = _discover_new_paths(
            repo_root,
            since_ref=since_ref,
            head_ref=head_ref,
        )

    checked_paths: set[str] = set()
    zone_counts: dict[str, int] = defaultdict(int)
    violations: list[dict[str, str]] = []

    for path in candidate_paths:
        for zone in SURFACE_ZONES:
            zone_id = zone["id"]
            include_globs = zone["include_globs"]
            exclude_globs = zone["exclude_globs"]
            if not _path_matches(path, include_globs):
                continue
            if _path_matches(path, exclude_globs):
                continue
            if _is_allowlisted(path, zone_id):
                continue
            zone_counts[zone_id] += 1
            checked_paths.add(path.as_posix())
            validator = ZONE_VALIDATORS[zone_id]
            violations.extend(validator(repo_root, path, cache))

    error_count = sum(1 for item in violations if item["severity"] == "error")
    warning_count = len(violations) - error_count
    return {
        "command": "check_architecture_surface_sync",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not discovery_errors and error_count == 0,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "candidate_paths": [path.as_posix() for path in candidate_paths],
        "checked_path_count": len(checked_paths),
        "zone_counts": dict(zone_counts),
        "discovery_errors": discovery_errors,
        "violations": violations,
        "error_count": error_count,
        "warning_count": warning_count,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# check_architecture_surface_sync",
        "",
        f"- ok: {report['ok']}",
        f"- since_ref: {report['since_ref']}",
        f"- head_ref: {report['head_ref']}",
        f"- candidate_paths: {len(report['candidate_paths'])}",
        f"- checked_path_count: {report['checked_path_count']}",
        f"- discovery_errors: {len(report['discovery_errors'])}",
        f"- violations: {len(report['violations'])}",
        f"- error_count: {report['error_count']}",
        f"- warning_count: {report['warning_count']}",
    ]

    if report["zone_counts"]:
        lines.extend(["", "## Zone Counts"])
        for zone_id, count in sorted(report["zone_counts"].items()):
            lines.append(f"- {zone_id}: {count}")

    if report["discovery_errors"]:
        lines.extend(["", "## Discovery Errors"])
        for error in report["discovery_errors"]:
            lines.append(f"- {error}")

    if report["violations"]:
        lines.extend(["", "## Violations"])
        for violation in report["violations"]:
            lines.append(
                "- [{severity}] {path} ({zone}/{rule}) -> {hint}".format(
                    severity=violation["severity"],
                    path=violation["path"],
                    zone=violation["zone"],
                    rule=violation["rule"],
                    hint=violation["hint"],
                )
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Optional git base ref to diff against.")
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git head ref used with --since-ref (default: HEAD).",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional explicit repository-relative paths to evaluate.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit zero after printing the report.",
    )
    args = parser.parse_args()

    report = build_report(
        repo_root=REPO_ROOT,
        since_ref=args.since_ref,
        head_ref=args.head_ref,
        explicit_paths=args.paths,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if args.report_only or report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
