"""Step handlers for `devctl ship`.

Each function runs one ship step. Keep step logic here so `ship.py` stays a
small orchestrator.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict

from ..common import confirm_or_abort, run_cmd
from ..config import REPO_ROOT
from .release_guard import check_release_version_parity
from .ship_common import (
    changelog_has_version,
    internal_env,
    make_step,
    read_version,
    run_checked,
    tag_exists,
)


def run_verify_step(args, context: Dict) -> Dict:
    """Run pre-release checks before tagging/publishing."""
    parity_ok, parity_details = check_release_version_parity(context["version"])
    if not parity_ok:
        return make_step("verify", False, 2, details=parity_details)

    checks = [
        ("check-release", ["python3", "dev/scripts/devctl.py", "check", "--profile", "release"]),
        ("hygiene", ["python3", "dev/scripts/devctl.py", "hygiene", "--format", "json"]),
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


def run_tag_step(args, context: Dict) -> Dict:
    """Create/push a release tag with branch and clean-tree safety checks."""
    version = context["version"]
    tag = context["tag"]

    rc, branch = run_checked(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return make_step("tag", False, rc or 2, details={"reason": branch or "failed to resolve branch"})
    if branch != "master":
        return make_step("tag", False, 2, details={"reason": f"must run on master (current={branch})"})

    try:
        dirty = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"], cwd=REPO_ROOT, check=False)
    except OSError as exc:
        return make_step("tag", False, 127, details={"reason": str(exc)})
    if dirty.returncode != 0:
        return make_step("tag", False, 2, details={"reason": "working tree is not clean"})

    cargo_version = read_version(REPO_ROOT / "src/Cargo.toml")
    if cargo_version != version:
        return make_step(
            "tag",
            False,
            2,
            details={
                "reason": "src/Cargo.toml version mismatch",
                "cargo_version": cargo_version,
                "expected": version,
            },
        )

    if not changelog_has_version(version):
        try:
            confirm_or_abort(
                f"No CHANGELOG section found for {version}. Continue anyway?",
                args.yes or args.dry_run,
            )
        except SystemExit as exc:
            return make_step("tag", False, int(exc.code or 1), details={"reason": "missing changelog entry"})

    pull = run_cmd("git-pull", ["git", "pull", "--ff-only", "origin", "master"], cwd=REPO_ROOT, dry_run=args.dry_run)
    if pull["returncode"] != 0:
        details = {"reason": "git pull failed"}
        if "error" in pull:
            details["error"] = pull["error"]
        return make_step("tag", False, pull["returncode"], details=details)

    if tag_exists(tag):
        return make_step("tag", True, 0, skipped=True, details={"reason": "tag already exists", "tag": tag})

    create = run_cmd(
        "git-tag",
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
    )
    if create["returncode"] != 0:
        details = {"reason": "tag creation failed"}
        if "error" in create:
            details["error"] = create["error"]
        return make_step("tag", False, create["returncode"], details=details)

    push = run_cmd("git-push-tag", ["git", "push", "origin", tag], cwd=REPO_ROOT, dry_run=args.dry_run)
    if push["returncode"] != 0:
        details = {"reason": "tag push failed"}
        if "error" in push:
            details["error"] = push["error"]
        return make_step("tag", False, push["returncode"], details=details)
    return make_step("tag", True, details={"tag": tag})


def run_notes_step(args, context: Dict) -> Dict:
    """Generate release-notes markdown file."""
    version = context["version"]
    tag = context["tag"]
    notes_file = context["notes_file"]

    cmd = ["./dev/scripts/generate-release-notes.sh", version, "--output", notes_file]
    if tag_exists(tag):
        cmd.extend(["--end-ref", tag])

    result = run_cmd("release-notes", cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
    if result["returncode"] != 0:
        details = {}
        if "error" in result:
            details["error"] = result["error"]
        return make_step("notes", False, result["returncode"], details=details)
    return make_step("notes", True, details={"path": notes_file})


def run_github_step(args, context: Dict) -> Dict:
    """Create a GitHub release and return URL metadata when available."""
    tag = context["tag"]
    notes_file = context["notes_file"]

    if not tag_exists(tag) and not args.dry_run:
        return make_step("github", False, 2, details={"reason": f"tag not found locally: {tag}"})

    auth = run_cmd("gh-auth", ["gh", "auth", "status", "-h", "github.com"], cwd=REPO_ROOT, dry_run=args.dry_run)
    if auth["returncode"] != 0:
        details = {"reason": "gh auth failed"}
        if "error" in auth:
            details["error"] = auth["error"]
        return make_step("github", False, auth["returncode"], details=details)

    if not args.dry_run:
        try:
            exists = subprocess.run(
                ["gh", "release", "view", tag],
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError as exc:
            return make_step("github", False, 127, details={"reason": str(exc)})
        if exists.returncode == 0:
            return make_step("github", True, 0, skipped=True, details={"reason": "release already exists", "tag": tag})

    if not Path(notes_file).exists() and not args.dry_run:
        notes = run_notes_step(args, context)
        if not notes["ok"]:
            return make_step("github", False, notes["returncode"], details={"reason": "failed to auto-generate notes"})

    cmd = ["gh", "release", "create", tag, "--title", tag, "--notes-file", notes_file]
    if args.github_fail_on_no_commits:
        cmd.append("--fail-on-no-commits")
    create = run_cmd("gh-release-create", cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
    if create["returncode"] != 0:
        details = {}
        if "error" in create:
            details["error"] = create["error"]
        return make_step("github", False, create["returncode"], details=details)

    details = {"tag": tag}
    if not args.dry_run:
        rc, raw = run_checked(["gh", "release", "view", tag, "--json", "url"])
        if rc == 0 and raw:
            try:
                details["url"] = json.loads(raw).get("url", "")
            except json.JSONDecodeError:
                pass
    return make_step("github", True, details=details)


def run_pypi_step(args, context: Dict) -> Dict:
    """Publish to PyPI through the wrapper script with parity/CI safeguards."""
    parity_ok, parity_details = check_release_version_parity(context["version"])
    if not parity_ok:
        return make_step("pypi", False, 2, details=parity_details)

    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        return make_step("pypi", False, 2, details={"reason": "refusing to publish in CI without --allow-ci"})
    try:
        confirm_or_abort("Publish package to PyPI?", args.yes or args.dry_run)
    except SystemExit as exc:
        return make_step("pypi", False, int(exc.code or 1), details={"reason": "publish not confirmed"})

    result = run_cmd(
        "pypi",
        ["./dev/scripts/publish-pypi.sh", "--upload"],
        cwd=REPO_ROOT,
        env=internal_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        details = {}
        if "error" in result:
            details["error"] = result["error"]
        return make_step("pypi", False, result["returncode"], details=details)
    return make_step("pypi", True, details={"version": context["version"]})


def run_homebrew_step(args, context: Dict) -> Dict:
    """Update Homebrew tap through the wrapper script with safeguards."""
    parity_ok, parity_details = check_release_version_parity(context["version"])
    if not parity_ok:
        return make_step("homebrew", False, 2, details=parity_details)

    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        return make_step("homebrew", False, 2, details={"reason": "refusing homebrew update in CI without --allow-ci"})
    try:
        confirm_or_abort(f"Update Homebrew tap to {context['version']}?", args.yes or args.dry_run)
    except SystemExit as exc:
        return make_step("homebrew", False, int(exc.code or 1), details={"reason": "homebrew update not confirmed"})

    result = run_cmd(
        "homebrew",
        ["./dev/scripts/update-homebrew.sh", context["version"]],
        cwd=REPO_ROOT,
        env=internal_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        details = {}
        if "error" in result:
            details["error"] = result["error"]
        return make_step("homebrew", False, result["returncode"], details=details)
    return make_step("homebrew", True, details={"version": context["version"]})


def run_verify_pypi_step(args, context: Dict) -> Dict:
    """Check that PyPI reports the expected released version."""
    version = context["version"]
    url = f"https://pypi.org/pypi/voiceterm/{version}/json"
    if args.dry_run:
        return make_step("verify-pypi", True, 0, skipped=True, details={"url": url, "reason": "dry-run"})

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return make_step("verify-pypi", False, 1, details={"reason": str(exc), "url": url})

    resolved = payload.get("info", {}).get("version")
    if resolved != version:
        return make_step(
            "verify-pypi",
            False,
            1,
            details={"url": url, "expected": version, "resolved": resolved},
        )
    return make_step("verify-pypi", True, details={"url": url, "resolved": resolved})


STEP_HANDLERS = {
    "verify": run_verify_step,
    "tag": run_tag_step,
    "notes": run_notes_step,
    "github": run_github_step,
    "pypi": run_pypi_step,
    "homebrew": run_homebrew_step,
    "verify-pypi": run_verify_pypi_step,
}
