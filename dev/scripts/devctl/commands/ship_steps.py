"""Step handlers for `devctl ship`.

Each function runs one ship step. Keep step logic here so `ship.py` stays a
small orchestrator.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
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

VERIFY_MAX_WORKERS = 4


def build_verify_checks(*, verify_docs: bool) -> list[tuple[str, list[str]]]:
    """Return ordered subchecks enforced by `ship --verify`."""
    checks: list[tuple[str, list[str]]] = [
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
    if verify_docs:
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
    return checks


def _verify_exception_result(name: str, cmd: list[str], exc: Exception) -> Dict:
    """Return a structured failure result for unexpected worker exceptions."""
    return {
        "name": name,
        "cmd": cmd,
        "cwd": str(REPO_ROOT),
        "returncode": 1,
        "duration_s": 0.0,
        "skipped": False,
        "error": f"verify substep crashed: {exc}",
    }


def run_verify_checks(
    checks: list[tuple[str, list[str]]],
    *,
    dry_run: bool,
    max_workers: int = VERIFY_MAX_WORKERS,
) -> list[Dict]:
    """Run independent verify subchecks in parallel with stable result ordering."""
    if not checks:
        return []
    if len(checks) <= 1 or max_workers <= 1:
        return [
            run_cmd(
                name,
                cmd,
                cwd=REPO_ROOT,
                dry_run=dry_run,
                live_output=False,
            )
            for name, cmd in checks
        ]

    worker_count = min(max_workers, len(checks))
    ordered_results: list[Dict | None] = [None] * len(checks)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(
                run_cmd,
                name,
                cmd,
                cwd=REPO_ROOT,
                dry_run=dry_run,
                live_output=False,
            ): (index, name, cmd)
            for index, (name, cmd) in enumerate(checks)
        }
        for future in as_completed(futures):
            index, name, cmd = futures[future]
            try:
                ordered_results[index] = future.result()
            except Exception as exc:  # pragma: no cover - broad-except: allow reason=parallel verification worker failures must be folded into ordered step results fallback=convert worker failure into ordered step result payload
                ordered_results[index] = _verify_exception_result(name, cmd, exc)
    return [result for result in ordered_results if result is not None]


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

    checks = build_verify_checks(verify_docs=bool(args.verify_docs))

    results = run_verify_checks(checks, dry_run=args.dry_run)
    for result in results:
        if result["returncode"] != 0:
            details = {
                "failed_substep": result["name"],
                "parallelized": len(results) > 1,
                "substep_count": len(results),
            }
            if "error" in result:
                details["reason"] = result["error"]
            return make_step("verify", False, result["returncode"], details=details)
    return make_step(
        "verify",
        True,
        details={
            "parallelized": len(results) > 1,
            "substep_count": len(results),
        },
    )


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
