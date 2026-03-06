#!/usr/bin/env python3
"""Workflow helper for extracting deterministic shell logic from CI YAML."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ZERO_SHA = "0" * 40
USER_FACING_DOCS = frozenset(
    {
        "README.md",
        "QUICK_START.md",
        "guides/USAGE.md",
        "guides/CLI_FLAGS.md",
        "guides/INSTALL.md",
        "guides/TROUBLESHOOTING.md",
    }
)
CLI_SCHEMA_PATHS = frozenset(
    {
        "rust/src/bin/voiceterm/config/cli.rs",
        "rust/src/config/mod.rs",
    }
)


def _append_output(path: Path, fields: list[tuple[str, str]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in fields:
            handle.write(f"{key}={value}\n")


def _git_ref_exists(ref: str) -> bool:
    if not ref:
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _read_changed_files(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"changed-files input not found: {path}")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def resolve_range(args: argparse.Namespace) -> int:
    if args.event_name == "pull_request":
        since_ref = args.pr_base
        head_ref = args.pr_head
    else:
        since_ref = args.push_before
        head_ref = args.push_head

    if not since_ref or since_ref == ZERO_SHA:
        since_ref = "HEAD~1"
    if not _git_ref_exists(since_ref):
        since_ref = "HEAD"
    if not _git_ref_exists(head_ref):
        head_ref = "HEAD"

    diff = subprocess.run(
        ["git", "diff", "--name-only", since_ref, head_ref],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if diff.returncode != 0:
        print(
            f"failed to compute git diff range {since_ref}..{head_ref}: {diff.stderr.strip()}",
            file=sys.stderr,
        )
        return diff.returncode

    changed_files = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    args.changed_files_output.parent.mkdir(parents=True, exist_ok=True)
    args.changed_files_output.write_text("\n".join(changed_files) + ("\n" if changed_files else ""), encoding="utf-8")
    _append_output(
        args.github_output,
        [
            ("since", since_ref),
            ("head", head_ref),
            ("changed_files_count", str(len(changed_files))),
        ],
    )
    return 0


def evaluate_user_docs_gate(args: argparse.Namespace) -> int:
    changed_files = set(_read_changed_files(args.changed_files_input))
    user_doc_change_count = sum(1 for path in USER_FACING_DOCS if path in changed_files)
    cli_schema_changed = bool(CLI_SCHEMA_PATHS.intersection(changed_files))
    run_user_facing_strict = cli_schema_changed or user_doc_change_count >= 3
    reason = (
        "cli-schema-change"
        if cli_schema_changed
        else ("user-doc-threshold" if user_doc_change_count >= 3 else "insufficient-user-doc-signal")
    )
    _append_output(
        args.github_output,
        [
            ("run_user_facing_strict", "true" if run_user_facing_strict else "false"),
            ("user_doc_change_count", str(user_doc_change_count)),
            ("cli_schema_changed", "true" if cli_schema_changed else "false"),
            ("reason", reason),
        ],
    )
    return 0


def resolve_security_scope(args: argparse.Namespace) -> int:
    since_ref = ""
    head_ref = ""
    if args.event_name == "pull_request":
        since_ref = args.pr_base
        head_ref = args.pr_head
    elif args.event_name == "push":
        since_ref = args.push_before
        head_ref = args.push_head
    if since_ref == ZERO_SHA:
        since_ref = ""

    _append_output(
        args.github_output,
        [("since_ref", since_ref or ""), ("head_ref", head_ref or "")],
    )
    return 0


def prepare_failure_artifact_dir(args: argparse.Namespace) -> int:
    workflow_slug = re.sub(r"[^a-z0-9._-]+", "-", args.workflow_name.lower()).strip("-")
    if not workflow_slug:
        workflow_slug = "workflow"
    artifact_dir = args.root / workflow_slug / f"run-{args.run_id}-attempt-{args.run_attempt}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _append_output(
        args.github_output,
        [("artifact_dir", artifact_dir.as_posix()), ("workflow_slug", workflow_slug)],
    )
    return 0


def find_first_file(args: argparse.Namespace) -> int:
    search_root = args.search_root
    output_value = ""
    if search_root.exists():
        matches = sorted(path for path in search_root.rglob(args.pattern) if path.is_file())
        if matches:
            output_value = matches[0].as_posix()
    elif not args.allow_missing:
        print(f"search root does not exist: {search_root}", file=sys.stderr)
        return 1

    if not output_value and not args.allow_missing:
        print(
            f"no files found matching pattern '{args.pattern}' under {search_root}",
            file=sys.stderr,
        )
        return 1

    if args.github_output and args.output_key:
        _append_output(args.github_output, [(args.output_key, output_value)])
    elif args.github_output or args.output_key:
        print("--github-output and --output-key must be provided together", file=sys.stderr)
        return 1

    print(output_value)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_range_parser = sub.add_parser(
        "resolve-range",
        help="Resolve safe git range refs and emit changed files for docs/tooling jobs.",
    )
    resolve_range_parser.add_argument("--event-name", default="")
    resolve_range_parser.add_argument("--push-before", default="")
    resolve_range_parser.add_argument("--push-head", default="")
    resolve_range_parser.add_argument("--pr-base", default="")
    resolve_range_parser.add_argument("--pr-head", default="")
    resolve_range_parser.add_argument(
        "--changed-files-output",
        required=True,
        type=Path,
    )
    resolve_range_parser.add_argument("--github-output", required=True, type=Path)

    evaluate_docs_gate_parser = sub.add_parser(
        "evaluate-user-docs-gate",
        help="Evaluate whether strict user-facing docs gate should run.",
    )
    evaluate_docs_gate_parser.add_argument("--changed-files-input", required=True, type=Path)
    evaluate_docs_gate_parser.add_argument("--github-output", required=True, type=Path)

    resolve_security_scope_parser = sub.add_parser(
        "resolve-security-scope",
        help="Resolve since/head refs for security workflow changed-file scoping.",
    )
    resolve_security_scope_parser.add_argument("--event-name", default="")
    resolve_security_scope_parser.add_argument("--push-before", default="")
    resolve_security_scope_parser.add_argument("--push-head", default="")
    resolve_security_scope_parser.add_argument("--pr-base", default="")
    resolve_security_scope_parser.add_argument("--pr-head", default="")
    resolve_security_scope_parser.add_argument("--github-output", required=True, type=Path)

    prep_failure_dir_parser = sub.add_parser(
        "prepare-failure-artifact-dir",
        help="Create deterministic failure-triage artifact directory and emit outputs.",
    )
    prep_failure_dir_parser.add_argument("--workflow-name", required=True)
    prep_failure_dir_parser.add_argument("--run-id", required=True)
    prep_failure_dir_parser.add_argument("--run-attempt", required=True)
    prep_failure_dir_parser.add_argument("--root", required=True, type=Path)
    prep_failure_dir_parser.add_argument("--github-output", required=True, type=Path)

    find_file_parser = sub.add_parser(
        "find-first-file",
        help="Find the first lexicographically-sorted file matching a pattern.",
    )
    find_file_parser.add_argument("--search-root", required=True, type=Path)
    find_file_parser.add_argument("--pattern", required=True)
    find_file_parser.add_argument("--allow-missing", action="store_true")
    find_file_parser.add_argument("--github-output", type=Path)
    find_file_parser.add_argument("--output-key")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "resolve-range":
        return resolve_range(args)
    if args.command == "evaluate-user-docs-gate":
        return evaluate_user_docs_gate(args)
    if args.command == "resolve-security-scope":
        return resolve_security_scope(args)
    if args.command == "prepare-failure-artifact-dir":
        return prepare_failure_artifact_dir(args)
    if args.command == "find-first-file":
        return find_first_file(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
