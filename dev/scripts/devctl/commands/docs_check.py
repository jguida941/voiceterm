"""devctl docs-check command implementation."""

from __future__ import annotations

import json
import re
from datetime import datetime

from ..collect import collect_git_status
from ..common import pipe_output, write_output
from ..config import REPO_ROOT

USER_DOCS = [
    "README.md",
    "QUICK_START.md",
    "guides/USAGE.md",
    "guides/CLI_FLAGS.md",
    "guides/INSTALL.md",
    "guides/TROUBLESHOOTING.md",
]

TOOLING_CHANGE_PREFIXES = (
    "dev/scripts/",
    "scripts/macro-packs/",
    ".github/workflows/",
)
TOOLING_CHANGE_EXACT = {
    "Makefile",
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
}
TOOLING_REQUIRED_DOCS = [
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "dev/active/MASTER_PLAN.md",
]

DEPRECATED_REFERENCE_TARGETS = [
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "scripts/macro-packs/full-dev.yaml",
    "Makefile",
]
DEPRECATED_REFERENCE_PATTERNS = [
    {
        "name": "release-script",
        "regex": re.compile(r"\./dev/scripts/release\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release --version <version>",
    },
    {
        "name": "homebrew-script",
        "regex": re.compile(r"\./dev/scripts/update-homebrew\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py homebrew --version <version>",
    },
    {
        "name": "pypi-script",
        "regex": re.compile(r"\./dev/scripts/publish-pypi\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py pypi --upload",
    },
    {
        "name": "notes-script",
        "regex": re.compile(r"\./dev/scripts/generate-release-notes\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release-notes --version <version>",
    },
]


def _is_tooling_change(path: str) -> bool:
    if path in TOOLING_CHANGE_EXACT:
        return True
    return path.startswith(TOOLING_CHANGE_PREFIXES)


def _scan_deprecated_references() -> list[dict]:
    violations = []
    for relative in DEPRECATED_REFERENCE_TARGETS:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for spec in DEPRECATED_REFERENCE_PATTERNS:
                if spec["regex"].search(line):
                    violations.append(
                        {
                            "file": relative,
                            "line": lineno,
                            "pattern": spec["name"],
                            "line_text": line.strip(),
                            "replacement": spec["replacement"],
                        }
                    )
    return violations


def run(args) -> int:
    """Check docs coverage and maintainer tooling policy alignment."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        output = json.dumps({"error": git_info["error"]}, indent=2)
        write_output(output, args.output)
        return 2

    changed = {entry["path"] for entry in git_info.get("changes", [])}
    strict_tooling = getattr(args, "strict_tooling", False)

    updated_docs = [doc for doc in USER_DOCS if doc in changed]
    changelog_updated = "dev/CHANGELOG.md" in changed
    missing_docs = [doc for doc in USER_DOCS if doc not in changed]

    user_facing_ok = True
    if args.user_facing:
        if not changelog_updated:
            user_facing_ok = False
        if args.strict:
            if missing_docs:
                user_facing_ok = False
        elif not updated_docs:
            user_facing_ok = False

    tooling_changes_detected = sorted(path for path in changed if _is_tooling_change(path))
    updated_tooling_docs = [doc for doc in TOOLING_REQUIRED_DOCS if doc in changed]
    missing_tooling_docs = [doc for doc in TOOLING_REQUIRED_DOCS if doc not in changed]

    tooling_policy_ok = True
    if tooling_changes_detected:
        if strict_tooling:
            tooling_policy_ok = not missing_tooling_docs
        else:
            tooling_policy_ok = bool(updated_tooling_docs)

    deprecated_violations = _scan_deprecated_references()
    deprecated_ok = not deprecated_violations

    ok = user_facing_ok and tooling_policy_ok and deprecated_ok

    report = {
        "command": "docs-check",
        "timestamp": datetime.now().isoformat(),
        "since_ref": since_ref,
        "head_ref": head_ref,
        "user_facing": args.user_facing,
        "strict": args.strict,
        "strict_tooling": strict_tooling,
        "changelog_updated": changelog_updated,
        "updated_docs": updated_docs,
        "missing_docs": missing_docs,
        "tooling_changes_detected": tooling_changes_detected,
        "updated_tooling_docs": updated_tooling_docs,
        "missing_tooling_docs": missing_tooling_docs,
        "tooling_policy_ok": tooling_policy_ok,
        "deprecated_reference_ok": deprecated_ok,
        "deprecated_reference_violations": deprecated_violations,
        "ok": ok,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        lines = ["# devctl docs-check", ""]
        if since_ref:
            lines.append(f"- commit_range: {since_ref}...{head_ref}")
        lines.append(f"- changelog_updated: {changelog_updated}")
        lines.append(f"- updated_docs: {', '.join(updated_docs) if updated_docs else 'none'}")
        if args.user_facing:
            lines.append(f"- missing_docs: {', '.join(missing_docs) if missing_docs else 'none'}")
            lines.append(f"- user_facing_ok: {user_facing_ok}")
        lines.append(
            "- tooling_changes_detected: "
            + (", ".join(tooling_changes_detected) if tooling_changes_detected else "none")
        )
        lines.append(
            "- updated_tooling_docs: "
            + (", ".join(updated_tooling_docs) if updated_tooling_docs else "none")
        )
        if tooling_changes_detected:
            lines.append(
                "- missing_tooling_docs: "
                + (", ".join(missing_tooling_docs) if missing_tooling_docs else "none")
            )
            lines.append(f"- tooling_policy_ok: {tooling_policy_ok}")
        lines.append(f"- deprecated_reference_ok: {deprecated_ok}")
        if deprecated_violations:
            lines.append("")
            lines.append("## Deprecated references")
            for violation in deprecated_violations:
                lines.append(
                    f"- {violation['file']}:{violation['line']} ({violation['pattern']}) -> use `{violation['replacement']}`"
                )
        lines.append(f"- ok: {ok}")
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if ok else 1
