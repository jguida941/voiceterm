"""Step handlers for `devctl ship`.

Each function runs one ship step. Keep step logic here so `ship.py` stays a
small orchestrator.
"""

from __future__ import annotations

import os
from typing import Dict

from ..common import confirm_or_abort, run_cmd
from ..config import REPO_ROOT
from ..script_catalog import check_script_cmd
from .release_guard import check_release_version_parity
from .release_prep import prepare_release_metadata
from .ship_common import internal_env, make_step
from .ship_release_steps import run_github_step, run_notes_step, run_tag_step
from .ship_verify_pypi_step import run_verify_pypi_step


def run_prepare_release_step(args, context: Dict) -> Dict:
    """Auto-update release metadata files before verify/tag/publish steps."""
    try:
        details = prepare_release_metadata(context["version"], dry_run=args.dry_run)
    except RuntimeError as exc:
        return make_step("prepare-release", False, 2, details={"reason": str(exc)})

    return make_step(
        "prepare-release",
        True,
        skipped=args.dry_run,
        details=details,
    )


def _can_skip_parity_in_dry_run(args, parity_details: Dict) -> bool:
    return (
        args.dry_run
        and getattr(args, "prepare_release", False)
        and parity_details.get("reason")
        == "requested version does not match release metadata"
    )


def run_verify_step(args, context: Dict) -> Dict:
    """Run pre-release checks before tagging/publishing."""
    parity_ok, parity_details = check_release_version_parity(context["version"])
    if not parity_ok:
        if _can_skip_parity_in_dry_run(args, parity_details):
            details = dict(parity_details)
            details["reason"] = (
                "dry-run: parity precheck skipped because --prepare-release would update metadata"
            )
            return make_step("verify", True, skipped=True, details=details)
        return make_step("verify", False, 2, details=parity_details)

    checks = [
        (
            "coderabbit-gate",
            check_script_cmd(
                "coderabbit_gate", "--branch", "master", "--format", "json"
            ),
        ),
        (
            "coderabbit-ralph-gate",
            check_script_cmd(
                "coderabbit_ralph_gate", "--branch", "master", "--format", "json"
            ),
        ),
        (
            "check-release",
            ["python3", "dev/scripts/devctl.py", "check", "--profile", "release"],
        ),
        (
            "hygiene",
            ["python3", "dev/scripts/devctl.py", "hygiene", "--format", "json"],
        ),
    ]
    if args.verify_docs:
        checks.append(
            (
                "docs-check",
                [
                    "python3",
                    "dev/scripts/devctl.py",
                    "docs-check",
                    "--user-facing",
                    "--strict-tooling",
                    "--format",
                    "json",
                ],
            )
        )

    for name, cmd in checks:
        result = run_cmd(name, cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
        if result["returncode"] != 0:
            details = {"failed_substep": name}
            if "error" in result:
                details["reason"] = result["error"]
            return make_step("verify", False, result["returncode"], details=details)
    return make_step("verify", True)


def run_pypi_step(args, context: Dict) -> Dict:
    """Publish to PyPI through the wrapper script with parity/CI safeguards."""
    return _run_publish_step(
        args,
        context,
        step_name="pypi",
        command=["./dev/scripts/publish-pypi.sh", "--upload"],
        ci_reason="refusing to publish in CI without --allow-ci",
        prompt="Publish package to PyPI?",
        unconfirmed_reason="publish not confirmed",
    )


def run_homebrew_step(args, context: Dict) -> Dict:
    """Update Homebrew tap through the wrapper script with safeguards."""
    return _run_publish_step(
        args,
        context,
        step_name="homebrew",
        command=["./dev/scripts/update-homebrew.sh", context["version"]],
        ci_reason="refusing homebrew update in CI without --allow-ci",
        prompt=f"Update Homebrew tap to {context['version']}?",
        unconfirmed_reason="homebrew update not confirmed",
    )


def _run_publish_step(
    args,
    context: Dict,
    *,
    step_name: str,
    command: list[str],
    ci_reason: str,
    prompt: str,
    unconfirmed_reason: str,
) -> Dict:
    parity_ok, parity_details = check_release_version_parity(context["version"])
    if not parity_ok:
        if _can_skip_parity_in_dry_run(args, parity_details):
            details = dict(parity_details)
            details["reason"] = (
                "dry-run: parity precheck skipped because --prepare-release would update metadata"
            )
            return make_step(step_name, True, skipped=True, details=details)
        return make_step(step_name, False, 2, details=parity_details)

    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        return make_step(step_name, False, 2, details={"reason": ci_reason})
    try:
        confirm_or_abort(prompt, args.yes or args.dry_run)
    except SystemExit as exc:
        return make_step(
            step_name,
            False,
            int(exc.code or 1),
            details={"reason": unconfirmed_reason},
        )

    result = run_cmd(
        step_name,
        command,
        cwd=REPO_ROOT,
        env=internal_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        details = {}
        if "error" in result:
            details["error"] = result["error"]
        return make_step(step_name, False, result["returncode"], details=details)
    return make_step(step_name, True, details={"version": context["version"]})


STEP_HANDLERS = {
    "prepare-release": run_prepare_release_step,
    "verify": run_verify_step,
    "tag": run_tag_step,
    "notes": run_notes_step,
    "github": run_github_step,
    "pypi": run_pypi_step,
    "homebrew": run_homebrew_step,
    "verify-pypi": run_verify_pypi_step,
}
