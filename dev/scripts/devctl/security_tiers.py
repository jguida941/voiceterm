"""Scanner-tier helpers for `devctl security`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .security_codeql import repo_from_origin_remote, run_codeql_alerts_step
from .security_python_scope import run_python_core_steps as run_python_core_steps_impl

CORE_SCANNER_IDS = (
    "rustsec-audit",
    "rustsec-policy",
    "zizmor",
    "codeql-alerts",
    "python-black",
    "python-isort",
    "bandit",
)
EXPENSIVE_SCANNER_IDS = (
    "semgrep",
    "cargo-deny",
    "cargo-geiger",
    "cargo-fuzz",
)

RunOptionalToolFn = Callable[..., tuple[dict, list[str]]]
MakeInternalStepFn = Callable[..., dict]


def annotate_step_metadata(step: dict, *, tier: str, blocking: bool) -> dict:
    """Attach tier/blocking metadata so success policy can be evaluated centrally."""
    details = step.get("details")
    if not isinstance(details, dict):
        details = {}
    details["tier"] = tier
    details["blocking"] = bool(blocking)
    step["details"] = details
    return step


def step_is_blocking_failure(step: dict) -> bool:
    """Return True when a step should fail the command."""
    if step.get("returncode") in (None, 0):
        return False
    details = step.get("details")
    if isinstance(details, dict) and details.get("blocking") is False:
        return False
    return True


def run_codeql_core_step(
    *,
    args,
    repo_root: Path,
    env: dict,
    make_internal_step: MakeInternalStepFn,
) -> tuple[dict, list[str]]:
    """Run the CodeQL-alert core scanner with compatibility fallback behavior."""
    repo_slug = (
        args.codeql_repo
        or os.environ.get("GITHUB_REPOSITORY")
        or repo_from_origin_remote(repo_root)
    )
    if not repo_slug:
        message = (
            "Unable to resolve GitHub repo slug for CodeQL alerts. "
            "Set --codeql-repo owner/repo or GITHUB_REPOSITORY."
        )
        if args.require_optional_tools:
            step = make_internal_step(
                name="codeql-alerts",
                cmd=["gh", "api", "/repos/<owner>/<repo>/code-scanning/alerts?..."],
                returncode=2,
                duration_s=0.0,
                error=message,
            )
            return annotate_step_metadata(step, tier="core", blocking=True), []

        step = make_internal_step(
            name="codeql-alerts",
            cmd=["gh", "api", "/repos/<owner>/<repo>/code-scanning/alerts?..."],
            returncode=0,
            duration_s=0.0,
            skipped=True,
            details={"reason": message},
        )
        return annotate_step_metadata(step, tier="core", blocking=True), [message]

    step, warnings = run_codeql_alerts_step(
        repo_root=repo_root,
        repo_slug=repo_slug,
        min_severity=args.codeql_min_severity,
        required=args.require_optional_tools,
        dry_run=args.dry_run,
        env=env,
        make_internal_step=make_internal_step,
    )
    return annotate_step_metadata(step, tier="core", blocking=True), warnings


def run_python_core_steps(
    *,
    args,
    repo_root: Path,
    env: dict,
    run_optional_tool_step: RunOptionalToolFn,
    make_internal_step: MakeInternalStepFn,
) -> tuple[list[dict], list[str]]:
    """Run Python quality/security checks for the core tier."""
    return run_python_core_steps_impl(
        args=args,
        repo_root=repo_root,
        env=env,
        run_optional_tool_step=run_optional_tool_step,
        make_internal_step=make_internal_step,
        annotate_step_metadata=annotate_step_metadata,
    )


def run_expensive_steps(
    *,
    args,
    repo_root: Path,
    src_dir: Path,
    env: dict,
    run_optional_tool_step: RunOptionalToolFn,
) -> tuple[list[dict], list[str]]:
    """Run expensive scanners when tier policy opts in."""
    steps: list[dict] = []
    warnings: list[str] = []

    blocking = bool(
        getattr(args, "expensive_policy", "advisory") == "fail"
        or getattr(args, "require_optional_tools", False)
    )

    expensive_specs = [
        ("semgrep", ["semgrep", "scan", "--config", "auto", "--error"], repo_root),
        ("cargo-deny", ["cargo", "deny", "check"], src_dir),
        ("cargo-geiger", ["cargo", "geiger", "--all-features"], src_dir),
        ("cargo-fuzz", ["cargo", "fuzz", "list"], src_dir),
    ]

    for name, cmd, cwd in expensive_specs:
        step, step_warnings = run_optional_tool_step(
            name=name,
            cmd=cmd,
            required=args.require_optional_tools,
            dry_run=args.dry_run,
            env=env,
            cwd=cwd,
            tier="expensive",
            blocking=blocking,
        )
        steps.append(step)
        warnings.extend(step_warnings)
        if step.get("returncode") not in (None, 0) and not blocking:
            warnings.append(
                f"{name} reported findings/errors in advisory mode; command continues."
            )

    return steps, warnings
