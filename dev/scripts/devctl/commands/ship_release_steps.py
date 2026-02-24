"""Release/tag/notes/GitHub step helpers for `devctl ship`."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict

from ..common import confirm_or_abort, run_cmd
from ..config import REPO_ROOT
from .ship_common import (
    changelog_has_version,
    make_step,
    read_version,
    run_checked,
    tag_exists,
)


def run_tag_step(args, context: Dict) -> Dict:
    """Create/push a release tag with branch and clean-tree safety checks."""
    version = context["version"]
    tag = context["tag"]

    rc, branch = run_checked(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return make_step(
            "tag",
            False,
            rc or 2,
            details={"reason": branch or "failed to resolve branch"},
        )
    if branch != "master":
        return make_step(
            "tag",
            False,
            2,
            details={"reason": f"must run on master (current={branch})"},
        )

    try:
        dirty = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD", "--"], cwd=REPO_ROOT, check=False
        )
    except OSError as exc:
        return make_step("tag", False, 127, details={"reason": str(exc)})
    if dirty.returncode != 0:
        return make_step(
            "tag", False, 2, details={"reason": "working tree is not clean"}
        )

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
            return make_step(
                "tag",
                False,
                int(exc.code or 1),
                details={"reason": "missing changelog entry"},
            )

    pull = run_cmd(
        "git-pull",
        ["git", "pull", "--ff-only", "origin", "master"],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
    )
    if pull["returncode"] != 0:
        details = {"reason": "git pull failed"}
        if "error" in pull:
            details["error"] = pull["error"]
        return make_step("tag", False, pull["returncode"], details=details)

    if tag_exists(tag):
        return make_step(
            "tag",
            True,
            0,
            skipped=True,
            details={"reason": "tag already exists", "tag": tag},
        )

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

    push = run_cmd(
        "git-push-tag",
        ["git", "push", "origin", tag],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
    )
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
        return make_step(
            "github", False, 2, details={"reason": f"tag not found locally: {tag}"}
        )

    auth = run_cmd(
        "gh-auth",
        ["gh", "auth", "status", "-h", "github.com"],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
    )
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
            return make_step(
                "github",
                True,
                0,
                skipped=True,
                details={"reason": "release already exists", "tag": tag},
            )

    if not Path(notes_file).exists() and not args.dry_run:
        notes = run_notes_step(args, context)
        if not notes["ok"]:
            return make_step(
                "github",
                False,
                notes["returncode"],
                details={"reason": "failed to auto-generate notes"},
            )

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
