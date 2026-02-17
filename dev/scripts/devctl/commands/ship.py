"""devctl ship command implementation."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from ..common import build_env, confirm_or_abort, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _step(
    name: str,
    ok: bool,
    returncode: int = 0,
    *,
    skipped: bool = False,
    details: Dict | None = None,
) -> Dict:
    return {
        "name": name,
        "ok": ok,
        "status": "skipped" if skipped else ("ok" if ok else "failed"),
        "returncode": returncode,
        "skipped": skipped,
        "details": details or {},
    }


def _run_checked(args: List[str], cwd: Path = REPO_ROOT) -> Tuple[int, str]:
    try:
        output = subprocess.check_output(args, cwd=cwd, text=True).strip()
        return 0, output
    except subprocess.CalledProcessError as exc:
        return exc.returncode, (exc.output or "").strip()


def _tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", tag],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _read_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip('"')
    return ""


def _changelog_has_version(version: str) -> bool:
    changelog = REPO_ROOT / "dev/CHANGELOG.md"
    if not changelog.exists():
        return False
    text = changelog.read_text(encoding="utf-8")
    return f"## [{version}]" in text or f"## {version}" in text


def _render_md(report: Dict) -> str:
    lines = ["# devctl ship", ""]
    lines.append(f"- version: {report['version']}")
    lines.append(f"- tag: {report['tag']}")
    lines.append(f"- notes_file: {report['notes_file']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- exit_code: {report['exit_code']}")
    lines.append("")
    lines.append("| Step | Status | Exit | Details |")
    lines.append("|---|---|---:|---|")
    for step in report["steps"]:
        details = ", ".join(f"{k}={v}" for k, v in step.get("details", {}).items()) or "-"
        lines.append(f"| `{step['name']}` | {step['status']} | {step['returncode']} | {details} |")
    return "\n".join(lines)


def _render_text(report: Dict) -> str:
    lines = [
        f"devctl ship version={report['version']} tag={report['tag']}",
        f"notes_file={report['notes_file']}",
        "",
    ]
    for step in report["steps"]:
        lines.append(f"[{step['status']}] {step['name']} (exit={step['returncode']})")
    lines.append("")
    lines.append(f"overall={report['ok']} exit_code={report['exit_code']}")
    return "\n".join(lines)


def _run_verify(args, context: Dict) -> Dict:
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
            return _step("verify", False, result["returncode"], details={"failed_substep": name})
    return _step("verify", True)


def _run_tag(args, context: Dict) -> Dict:
    version = context["version"]
    tag = context["tag"]

    rc, branch = _run_checked(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return _step("tag", False, 2, details={"reason": "failed to resolve branch"})
    if branch != "master":
        return _step("tag", False, 2, details={"reason": f"must run on master (current={branch})"})

    dirty = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"], cwd=REPO_ROOT)
    if dirty.returncode != 0:
        return _step("tag", False, 2, details={"reason": "working tree is not clean"})

    cargo_version = _read_version(REPO_ROOT / "src/Cargo.toml")
    if cargo_version != version:
        return _step(
            "tag",
            False,
            2,
            details={
                "reason": "src/Cargo.toml version mismatch",
                "cargo_version": cargo_version,
                "expected": version,
            },
        )

    if not _changelog_has_version(version):
        try:
            confirm_or_abort(f"No CHANGELOG section found for {version}. Continue anyway?", args.yes or args.dry_run)
        except SystemExit as exc:
            return _step("tag", False, int(exc.code or 1), details={"reason": "missing changelog entry"})

    pull = run_cmd("git-pull", ["git", "pull", "--ff-only", "origin", "master"], cwd=REPO_ROOT, dry_run=args.dry_run)
    if pull["returncode"] != 0:
        return _step("tag", False, pull["returncode"], details={"reason": "git pull failed"})

    if _tag_exists(tag):
        return _step("tag", True, 0, skipped=True, details={"reason": "tag already exists", "tag": tag})

    create = run_cmd("git-tag", ["git", "tag", "-a", tag, "-m", f"Release {tag}"], cwd=REPO_ROOT, dry_run=args.dry_run)
    if create["returncode"] != 0:
        return _step("tag", False, create["returncode"], details={"reason": "tag creation failed"})

    push = run_cmd("git-push-tag", ["git", "push", "origin", tag], cwd=REPO_ROOT, dry_run=args.dry_run)
    if push["returncode"] != 0:
        return _step("tag", False, push["returncode"], details={"reason": "tag push failed"})
    return _step("tag", True, details={"tag": tag})


def _run_notes(args, context: Dict) -> Dict:
    version = context["version"]
    tag = context["tag"]
    notes_file = context["notes_file"]

    cmd = ["./dev/scripts/generate-release-notes.sh", version, "--output", notes_file]
    if _tag_exists(tag):
        cmd.extend(["--end-ref", tag])

    result = run_cmd("release-notes", cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
    if result["returncode"] != 0:
        return _step("notes", False, result["returncode"])
    return _step("notes", True, details={"path": notes_file})


def _run_github(args, context: Dict) -> Dict:
    tag = context["tag"]
    notes_file = context["notes_file"]

    if not _tag_exists(tag) and not args.dry_run:
        return _step("github", False, 2, details={"reason": f"tag not found locally: {tag}"})

    auth = run_cmd("gh-auth", ["gh", "auth", "status", "-h", "github.com"], cwd=REPO_ROOT, dry_run=args.dry_run)
    if auth["returncode"] != 0:
        return _step("github", False, auth["returncode"], details={"reason": "gh auth failed"})

    if not args.dry_run:
        exists = subprocess.run(
            ["gh", "release", "view", tag],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if exists.returncode == 0:
            return _step("github", True, 0, skipped=True, details={"reason": "release already exists", "tag": tag})

    if not Path(notes_file).exists() and not args.dry_run:
        notes = _run_notes(args, context)
        if not notes["ok"]:
            return _step("github", False, notes["returncode"], details={"reason": "failed to auto-generate notes"})

    cmd = ["gh", "release", "create", tag, "--title", tag, "--notes-file", notes_file]
    if args.github_fail_on_no_commits:
        cmd.append("--fail-on-no-commits")
    create = run_cmd("gh-release-create", cmd, cwd=REPO_ROOT, dry_run=args.dry_run)
    if create["returncode"] != 0:
        return _step("github", False, create["returncode"])

    details = {"tag": tag}
    if not args.dry_run:
        rc, raw = _run_checked(["gh", "release", "view", tag, "--json", "url"])
        if rc == 0 and raw:
            try:
                details["url"] = json.loads(raw).get("url", "")
            except json.JSONDecodeError:
                pass
    return _step("github", True, details=details)


def _internal_env(args) -> Dict:
    env = build_env(args)
    env["VOICETERM_DEVCTL_INTERNAL"] = "1"
    if args.yes or args.dry_run:
        env["VOICETERM_DEVCTL_ASSUME_YES"] = "1"
    return env


def _run_pypi(args, context: Dict) -> Dict:
    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        return _step("pypi", False, 2, details={"reason": "refusing to publish in CI without --allow-ci"})
    try:
        confirm_or_abort("Publish package to PyPI?", args.yes or args.dry_run)
    except SystemExit as exc:
        return _step("pypi", False, int(exc.code or 1), details={"reason": "publish not confirmed"})

    result = run_cmd(
        "pypi",
        ["./dev/scripts/publish-pypi.sh", "--upload"],
        cwd=REPO_ROOT,
        env=_internal_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        return _step("pypi", False, result["returncode"])
    return _step("pypi", True, details={"version": context["version"]})


def _run_homebrew(args, context: Dict) -> Dict:
    if os.environ.get("CI") and not args.allow_ci and not args.dry_run:
        return _step("homebrew", False, 2, details={"reason": "refusing homebrew update in CI without --allow-ci"})
    try:
        confirm_or_abort(f"Update Homebrew tap to {context['version']}?", args.yes or args.dry_run)
    except SystemExit as exc:
        return _step("homebrew", False, int(exc.code or 1), details={"reason": "homebrew update not confirmed"})

    result = run_cmd(
        "homebrew",
        ["./dev/scripts/update-homebrew.sh", context["version"]],
        cwd=REPO_ROOT,
        env=_internal_env(args),
        dry_run=args.dry_run,
    )
    if result["returncode"] != 0:
        return _step("homebrew", False, result["returncode"])
    return _step("homebrew", True, details={"version": context["version"]})


def _run_verify_pypi(args, context: Dict) -> Dict:
    version = context["version"]
    url = f"https://pypi.org/pypi/voiceterm/{version}/json"
    if args.dry_run:
        return _step("verify-pypi", True, 0, skipped=True, details={"url": url, "reason": "dry-run"})

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return _step("verify-pypi", False, 1, details={"reason": str(exc), "url": url})

    resolved = payload.get("info", {}).get("version")
    if resolved != version:
        return _step("verify-pypi", False, 1, details={"url": url, "expected": version, "resolved": resolved})
    return _step("verify-pypi", True, details={"url": url, "resolved": resolved})


STEP_HANDLERS = {
    "verify": _run_verify,
    "tag": _run_tag,
    "notes": _run_notes,
    "github": _run_github,
    "pypi": _run_pypi,
    "homebrew": _run_homebrew,
    "verify-pypi": _run_verify_pypi,
}


def run(args) -> int:
    """Run the unified release/distribution control-plane workflow."""
    if not VERSION_RE.match(args.version):
        print("Error: --version must be in format X.Y.Z")
        return 2

    selected_steps: List[str] = []
    if args.verify:
        selected_steps.append("verify")
    if args.tag:
        selected_steps.append("tag")
    if args.notes:
        selected_steps.append("notes")
    if args.github:
        selected_steps.append("github")
    if args.pypi:
        selected_steps.append("pypi")
    if args.homebrew:
        selected_steps.append("homebrew")
    if args.verify_pypi:
        selected_steps.append("verify-pypi")

    if not selected_steps:
        print(
            "Error: no steps selected. Choose one or more of --verify --tag --notes --github --pypi --homebrew --verify-pypi."
        )
        return 2

    context = {
        "version": args.version,
        "tag": f"v{args.version}",
        "notes_file": args.notes_output or f"/tmp/voiceterm-release-v{args.version}.md",
    }

    steps: List[Dict] = []
    exit_code = 0

    for name in selected_steps:
        handler = STEP_HANDLERS[name]
        step = handler(args, context)
        steps.append(step)
        if not step["ok"]:
            exit_code = step["returncode"] or 1
            break

    report = {
        "command": "ship",
        "timestamp": datetime.now().isoformat(),
        "version": context["version"],
        "tag": context["tag"],
        "notes_file": context["notes_file"],
        "selected_steps": selected_steps,
        "steps": steps,
        "ok": exit_code == 0,
        "exit_code": exit_code,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        output = _render_md(report)
    else:
        output = _render_text(report)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return exit_code
