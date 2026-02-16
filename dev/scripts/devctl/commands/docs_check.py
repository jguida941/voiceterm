"""devctl docs-check command implementation."""

import json
from datetime import datetime

from ..collect import collect_git_status
from ..common import pipe_output, write_output

USER_DOCS = [
    "README.md",
    "QUICK_START.md",
    "guides/USAGE.md",
    "guides/CLI_FLAGS.md",
    "guides/INSTALL.md",
    "guides/TROUBLESHOOTING.md",
]


def run(args) -> int:
    """Check that user-facing docs and changelog are updated."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        output = json.dumps({"error": git_info["error"]}, indent=2)
        write_output(output, args.output)
        return 2

    changed = {entry["path"] for entry in git_info.get("changes", [])}
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
        else:
            if not updated_docs:
                user_facing_ok = False

    report = {
        "command": "docs-check",
        "timestamp": datetime.now().isoformat(),
        "since_ref": since_ref,
        "head_ref": head_ref,
        "user_facing": args.user_facing,
        "strict": args.strict,
        "changelog_updated": changelog_updated,
        "updated_docs": updated_docs,
        "missing_docs": missing_docs,
        "ok": user_facing_ok,
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
            lines.append(f"- ok: {user_facing_ok}")
        output = "\n".join(lines)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if user_facing_ok else 1
