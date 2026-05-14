"""Raw git wrapper that emits typed RawGitBypassReceipt evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ..common import (
    add_standard_output_arguments,
    display_path,
    emit_output,
    resolve_repo_path,
    write_output,
)
from ..config import REPO_ROOT
from ..runtime.raw_git_bypass_receipts import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
    RawGitBypassAuthority,
    RawGitVerb,
    append_raw_git_bypass_receipt,
    build_raw_git_bypass_receipt,
    raw_git_authority_from_value,
)

DEFAULT_OPERATOR_EVIDENCE_REF = "packet:rev_pkt_4022"
GitRunner = Callable[[tuple[str, ...], bool], "GitCommandResult"]


@dataclass(frozen=True, slots=True)
class GitCommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def add_parser(sub) -> None:
    parser = sub.add_parser(
        "raw-git",
        help="Run raw git commit/push while emitting typed bypass receipts",
    )
    parser.add_argument(
        "--store-path",
        default=str(DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL),
        help="RawGitBypassReceipt JSONL store path.",
    )
    parser.add_argument(
        "--bypass-lifecycle-store-path",
        default=str(DEFAULT_BYPASS_LIFECYCLE_STORE_REL),
        help="BypassLifecycle JSONL store used to validate lifecycle-backed authority.",
    )
    parser.add_argument(
        "--governed-exception-store-path",
        default="dev/state/governed_exception_lifecycles.jsonl",
        help="GovernedExceptionLifecycle JSONL store receiving raw-git exception links.",
    )
    parser.add_argument(
        "--actor",
        default="codex",
        help="Actor executing the raw git operation.",
    )
    parser.add_argument(
        "--authority",
        choices=tuple(authority.value for authority in RawGitBypassAuthority),
        default=RawGitBypassAuthority.OPERATOR_WITNESSED.value,
        help="Typed authority source for this raw git bypass receipt.",
    )
    parser.add_argument(
        "--bypass-lifecycle-id",
        default="",
        help="Optional BypassLifecycle id when authority is lifecycle-backed.",
    )
    parser.add_argument(
        "--operator-quote-evidence-ref",
        action="append",
        default=None,
        help="Repeatable operator evidence ref; last value is stored on the receipt.",
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="json",
    )
    actions = parser.add_subparsers(dest="raw_git_action", required=True)
    commit = actions.add_parser(
        "commit",
        help="Run `git commit ...` and append a RawGitBypassReceipt.",
    )
    commit.add_argument("git_args", nargs=argparse.REMAINDER)
    push = actions.add_parser(
        "push",
        help="Run `git push ...` and append a RawGitBypassReceipt.",
    )
    push.add_argument("git_args", nargs=argparse.REMAINDER)


def run(args: Any) -> int:
    report, rc = run_raw_git_action(args)
    output = json.dumps(report, indent=2, sort_keys=True)
    if getattr(args, "format", "json") != "json":
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def run_raw_git_action(
    args: Any,
    *,
    repo_root: Path = REPO_ROOT,
    git_runner: GitRunner | None = None,
) -> tuple[dict[str, object], int]:
    action = str(getattr(args, "raw_git_action", "") or "").strip()
    if action not in {RawGitVerb.COMMIT.value, RawGitVerb.PUSH.value}:
        return _error_report("unknown_raw_git_action", action), 1
    runner = git_runner or _subprocess_git_runner(repo_root)
    git_args = _normalized_git_args(getattr(args, "git_args", ()) or ())
    verb = RawGitVerb(action)
    if _is_git_help_request(git_args):
        return _git_noop_report(verb, git_args, "git_help_noop"), 0

    before_head = _git_stdout(runner, ("rev-parse", "HEAD"))
    before_upstream = _git_stdout(runner, ("rev-parse", "--verify", "@{u}"))
    before_ahead = (
        _git_stdout(runner, ("rev-list", "--reverse", "@{u}..HEAD"))
        if verb is RawGitVerb.PUSH and before_upstream
        else ""
    )
    command_result = runner((verb.value, *git_args), False)
    if command_result.returncode != 0:
        return _git_failure_report(verb, git_args, command_result), command_result.returncode

    after_head = _git_stdout(runner, ("rev-parse", "HEAD"))
    if verb is RawGitVerb.COMMIT and (not after_head or after_head == before_head):
        return (
            _git_noop_report(
                verb,
                git_args,
                "git_commit_head_unchanged",
                command_result,
            ),
            1,
        )

    commit_sha = after_head
    push_range: tuple[str, str] = ()
    if verb is RawGitVerb.PUSH:
        after_ahead = (
            _git_stdout(runner, ("rev-list", "--reverse", "@{u}..HEAD"))
            if before_upstream
            else ""
        )
        if not before_ahead or after_ahead == before_ahead:
            return (
                _git_noop_report(
                    verb,
                    git_args,
                    "git_push_upstream_unchanged",
                    command_result,
                ),
                1,
            )
        if before_upstream and before_head:
            push_range = (before_upstream, before_head)
    affected_paths = _affected_paths(runner, verb=verb, commit_sha=commit_sha, push_range=push_range)
    receipt = build_raw_git_bypass_receipt(
        git_verb=verb,
        executed_at_utc=_now_utc(),
        executed_by_actor=str(getattr(args, "actor", "") or "codex").strip(),
        bypass_authority=raw_git_authority_from_value(getattr(args, "authority", "")),
        commit_sha=commit_sha if verb is RawGitVerb.COMMIT else "",
        push_range=push_range,
        affected_paths=affected_paths,
        bypass_lifecycle_id=str(getattr(args, "bypass_lifecycle_id", "") or "").strip(),
        operator_quote_evidence_ref=_operator_evidence_ref(args),
        skipped_pre_hooks=_skipped_pre_hooks(verb, git_args),
        git_args=git_args,
    )
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
        repo_root=repo_root,
    )
    bypass_lifecycle_store_path = resolve_repo_path(
        getattr(args, "bypass_lifecycle_store_path", ""),
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        repo_root=repo_root,
    )
    governed_exception_store_path = resolve_repo_path(
        getattr(args, "governed_exception_store_path", ""),
        Path("dev/state/governed_exception_lifecycles.jsonl"),
        repo_root=repo_root,
    )
    write_result = append_raw_git_bypass_receipt(
        store_path,
        receipt,
        bypass_lifecycle_store_path=bypass_lifecycle_store_path,
        governed_exception_store_path=governed_exception_store_path,
    )
    receipt = write_result.receipt
    report = {
        "command": "raw-git",
        "action": verb.value,
        "ok": True,
        "receipt_id": receipt.receipt_id,
        "store_path": display_path(store_path),
        "receipt": receipt.to_dict(),
        "write_result": write_result.to_dict(),
        "git_returncode": command_result.returncode,
        "git_stdout": command_result.stdout,
        "git_stderr": command_result.stderr,
    }
    return report, 0


def _subprocess_git_runner(repo_root: Path) -> GitRunner:
    def _run(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        result = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        return GitCommandResult(result.returncode, result.stdout, result.stderr)

    return _run


def _git_stdout(runner: GitRunner, args: tuple[str, ...]) -> str:
    result = runner(args, True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _affected_paths(
    runner: GitRunner,
    *,
    verb: RawGitVerb,
    commit_sha: str,
    push_range: tuple[str, str],
) -> tuple[str, ...]:
    if verb is RawGitVerb.COMMIT and commit_sha:
        output = _git_stdout(
            runner,
            ("diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha),
        )
    elif verb is RawGitVerb.PUSH and push_range:
        output = _git_stdout(runner, ("diff", "--name-only", f"{push_range[0]}..{push_range[1]}"))
    else:
        output = ""
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _normalized_git_args(values: object) -> tuple[str, ...]:
    args = tuple(str(value) for value in values if str(value).strip())
    if args and args[0] == "--":
        return args[1:]
    return args


def _is_git_help_request(git_args: tuple[str, ...]) -> bool:
    return git_args in {("--help",), ("-h",), ("help",)}


def _operator_evidence_ref(args: Any) -> str:
    refs = tuple(
        str(value).strip()
        for value in getattr(args, "operator_quote_evidence_ref", ()) or ()
        if str(value).strip()
    )
    return refs[-1] if refs else DEFAULT_OPERATOR_EVIDENCE_REF


def _skipped_pre_hooks(verb: RawGitVerb, git_args: tuple[str, ...]) -> tuple[str, ...]:
    if "--no-verify" not in git_args and "-n" not in git_args:
        return ()
    if verb is RawGitVerb.COMMIT:
        return ("pre-commit", "commit-msg")
    return ("pre-push",)


def _git_failure_report(
    verb: RawGitVerb,
    git_args: tuple[str, ...],
    result: GitCommandResult,
) -> dict[str, object]:
    return {
        "command": "raw-git",
        "action": verb.value,
        "ok": False,
        "reason": "git_command_failed",
        "git_args": list(git_args),
        "git_returncode": result.returncode,
        "git_stdout": result.stdout,
        "git_stderr": result.stderr,
    }


def _git_noop_report(
    verb: RawGitVerb,
    git_args: tuple[str, ...],
    reason: str,
    result: GitCommandResult | None = None,
) -> dict[str, object]:
    return {
        "command": "raw-git",
        "action": verb.value,
        "ok": False,
        "reason": reason,
        "git_args": list(git_args),
        "receipt_written": False,
        "git_returncode": result.returncode if result is not None else 0,
        "git_stdout": result.stdout if result is not None else "",
        "git_stderr": result.stderr if result is not None else "",
    }


def _error_report(reason: str, detail: str) -> dict[str, object]:
    return {
        "command": "raw-git",
        "ok": False,
        "reason": reason,
        "detail": detail,
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl raw-git", ""]
    for key in ("ok", "action", "receipt_id", "store_path", "reason"):
        if key in report:
            lines.append(f"- {key}: `{report[key]}`")
    receipt = report.get("receipt")
    if isinstance(receipt, dict):
        lines.append(f"- git_verb: `{receipt.get('git_verb')}`")
        lines.append(f"- commit_sha: `{receipt.get('commit_sha')}`")
        lines.append(f"- push_range: `{receipt.get('push_range')}`")
        lines.append(f"- skipped_pre_hooks: `{receipt.get('skipped_pre_hooks')}`")
    return "\n".join(lines) + "\n"


def _now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
