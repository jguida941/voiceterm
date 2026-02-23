"""Python scope helpers for `devctl security` core scanners."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

RunOptionalToolFn = Callable[..., tuple[dict, list[str]]]
MakeInternalStepFn = Callable[..., dict]
AnnotateStepMetadataFn = Callable[..., dict]


def _git_changed_paths(
    repo_root: Path,
    *,
    since_ref: str | None,
    head_ref: str,
) -> tuple[list[str], str | None]:
    if since_ref:
        cmd = [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            f"{since_ref}...{head_ref}",
        ]
    else:
        cmd = ["git", "status", "--porcelain"]

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [], str(exc)

    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip() or "git changed-path probe failed"
        return [], message

    paths: list[str] = []
    if since_ref:
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    else:
        for raw in result.stdout.splitlines():
            if not raw:
                continue
            path = raw[3:]
            if "->" in path:
                path = path.split("->")[-1].strip()
            path = path.strip()
            if path:
                paths.append(path)

    deduped = sorted({path for path in paths if path})
    return deduped, None


def _tracked_python_paths(repo_root: Path) -> tuple[list[str], str | None]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", "*.py"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [], str(exc)

    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip() or "git tracked-python probe failed"
        return [], message

    paths = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
    return paths, None


def resolve_python_scope(args) -> str:
    """Resolve effective Python check scope from args and runtime context."""
    requested = str(getattr(args, "python_scope", "auto") or "auto").strip().lower()
    if requested in ("changed", "all"):
        return requested
    if getattr(args, "since_ref", None):
        return "changed"
    ci_env = str(os.environ.get("CI", "")).strip().lower()
    if ci_env in ("1", "true", "yes", "on"):
        return "all"
    return "changed"


def changed_python_paths(
    repo_root: Path,
    *,
    since_ref: str | None,
    head_ref: str,
    scope: str,
) -> tuple[list[str], str | None]:
    """Return Python paths for the selected scope."""
    if scope == "all":
        return _tracked_python_paths(repo_root)

    changed, error = _git_changed_paths(repo_root, since_ref=since_ref, head_ref=head_ref)
    if error:
        return [], error

    python_paths = [path for path in changed if path.endswith(".py")]
    return python_paths, None


def _python_scope_probe_cmd(scope: str, *, since_ref: str | None, head_ref: str) -> list[str]:
    if scope == "all":
        return ["git", "ls-files", "--", "*.py"]
    if since_ref:
        return [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            f"{since_ref}...{head_ref}",
        ]
    return ["git", "status", "--porcelain"]


def _bandit_targets(paths: list[str]) -> list[str]:
    targets: set[str] = set()
    for path in paths:
        relative = Path(path)
        parent = relative.parent.as_posix()
        if parent and parent != ".":
            targets.add(parent)
        else:
            targets.add(relative.as_posix())
    return sorted(targets)


def run_python_core_steps(
    *,
    args,
    repo_root: Path,
    env: dict,
    run_optional_tool_step: RunOptionalToolFn,
    make_internal_step: MakeInternalStepFn,
    annotate_step_metadata: AnnotateStepMetadataFn,
) -> tuple[list[dict], list[str]]:
    """Run Python quality/security scanners with changed/all scope handling."""
    steps: list[dict] = []
    warnings: list[str] = []
    python_scope = resolve_python_scope(args)
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    scope_probe_cmd = _python_scope_probe_cmd(
        python_scope,
        since_ref=since_ref,
        head_ref=head_ref,
    )

    python_paths, path_error = changed_python_paths(
        repo_root,
        since_ref=since_ref,
        head_ref=head_ref,
        scope=python_scope,
    )
    if path_error:
        if args.require_optional_tools:
            scope_step = make_internal_step(
                name="python-scope",
                cmd=scope_probe_cmd,
                returncode=2,
                duration_s=0.0,
                error=path_error,
            )
            steps.append(annotate_step_metadata(scope_step, tier="core", blocking=True))
            return steps, warnings

        warnings.append(path_error)
        scope_step = make_internal_step(
            name="python-scope",
            cmd=scope_probe_cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": path_error},
        )
        steps.append(annotate_step_metadata(scope_step, tier="core", blocking=True))
        return steps, warnings

    if not python_paths:
        scope_step = make_internal_step(
            name="python-scope",
            cmd=scope_probe_cmd,
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": f"No Python files found for scope '{python_scope}'."},
        )
        steps.append(annotate_step_metadata(scope_step, tier="core", blocking=True))
        return steps, warnings

    scope_step = make_internal_step(
        name="python-scope",
        cmd=scope_probe_cmd,
        returncode=0,
        duration_s=0.0,
        details={
            "scope": python_scope,
            "changed_python_files": len(python_paths),
            "sample": python_paths[:20],
        },
    )
    steps.append(annotate_step_metadata(scope_step, tier="core", blocking=True))

    black_step, black_warnings = run_optional_tool_step(
        name="python-black",
        cmd=["black", "--check", *python_paths],
        required=args.require_optional_tools,
        dry_run=args.dry_run,
        env=env,
        cwd=repo_root,
        tier="core",
        blocking=True,
    )
    steps.append(black_step)
    warnings.extend(black_warnings)

    isort_step, isort_warnings = run_optional_tool_step(
        name="python-isort",
        cmd=["isort", "--check-only", *python_paths],
        required=args.require_optional_tools,
        dry_run=args.dry_run,
        env=env,
        cwd=repo_root,
        tier="core",
        blocking=True,
    )
    steps.append(isort_step)
    warnings.extend(isort_warnings)

    bandit_targets = _bandit_targets(python_paths)
    bandit_step, bandit_warnings = run_optional_tool_step(
        name="bandit",
        cmd=["bandit", "-q", "-r", *bandit_targets],
        required=args.require_optional_tools,
        dry_run=args.dry_run,
        env=env,
        cwd=repo_root,
        tier="core",
        blocking=True,
    )
    steps.append(bandit_step)
    warnings.extend(bandit_warnings)

    return steps, warnings
